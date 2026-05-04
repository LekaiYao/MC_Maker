#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List


PATHS_SH = Path("/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh")


def read_paths(paths_file: Path) -> Dict[str, str]:
    variables: Dict[str, str] = {}
    for raw in paths_file.read_text().splitlines():
        line = raw.strip()
        if not line.startswith("export "):
            continue
        key, value = line[len("export ") :].split("=", 1)
        variables[key] = value.strip().strip('"')

    changed = True
    while changed:
        changed = False
        for key in list(variables.keys()):
            value = variables[key]
            for token_key, token_value in variables.items():
                token = f"${{{token_key}}}"
                if token in value:
                    value = value.replace(token, token_value)
                    changed = True
            variables[key] = value
    return variables


def run_hadd(output_file: Path, inputs: List[Path], dry_run: bool) -> None:
    cmd = ["hadd", "-f", str(output_file)] + [str(x) for x in inputs]
    if dry_run:
        print("[DRY] " + " ".join(cmd))
        return
    subprocess.run(cmd, check=True)


def merge_in_batches(output_file: Path, inputs: List[Path], batch_size: int, dry_run: bool) -> None:
    if len(inputs) <= batch_size:
        run_hadd(output_file, inputs, dry_run)
        return

    if dry_run:
        print(f"[DRY] total inputs={len(inputs)}, batch_size={batch_size}, use staged merge")
        return

    with tempfile.TemporaryDirectory(prefix="ntuple_merge_", dir=str(output_file.parent)) as tmpdir:
        tmpdir_path = Path(tmpdir)
        partials: List[Path] = []
        for i in range(0, len(inputs), batch_size):
            chunk = inputs[i : i + batch_size]
            partial = tmpdir_path / f"part_{i // batch_size:04d}.root"
            run_hadd(partial, chunk, dry_run=False)
            partials.append(partial)
        run_hadd(output_file, partials, dry_run=False)


def collect_inputs(ntuple_base: Path, process: str, begin: int, end: int) -> List[Path]:
    inputs: List[Path] = []
    process_dir = ntuple_base / process
    for job_id in range(begin, end + 1):
        job_dir = process_dir / f"job_{job_id}"
        if not job_dir.is_dir():
            continue
        for root_file in sorted(job_dir.glob("*.root")):
            if root_file.is_file():
                inputs.append(root_file)
    return inputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge NTUPLE ROOT files from existing job_{begin..end} folders into one ROOT."
    )
    parser.add_argument("--process", required=True)
    parser.add_argument("--begin", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=200, help="max input files per single hadd call")
    parser.add_argument("--dry-run", action="store_true", help="print actions only")
    args = parser.parse_args()

    if args.begin < 0 or args.end < 0 or args.begin > args.end:
        raise SystemExit(f"Invalid range: begin={args.begin}, end={args.end}")
    if args.batch_size <= 0:
        raise SystemExit(f"Invalid batch-size: {args.batch_size}")

    paths = read_paths(PATHS_SH)
    ntuple_base = Path(paths["NTUPLE_OUTPUT_BASE"])
    process_dir = ntuple_base / args.process
    output_file = process_dir / f"job_{args.begin}_{args.end}.root"

    if not process_dir.is_dir():
        raise SystemExit(f"Process dir not found: {process_dir}")
    if not shutil.which("hadd"):
        raise SystemExit("Command not found: hadd")

    inputs = collect_inputs(ntuple_base, args.process, args.begin, args.end)
    print(f"process={args.process}")
    print(f"range=job_{args.begin}..job_{args.end}")
    print(f"ntuple_base={ntuple_base}")
    print(f"output={output_file}")
    print(f"input_files={len(inputs)}")

    if not inputs:
        raise SystemExit("No input ROOT files found in existing job directories.")

    merge_in_batches(output_file, inputs, args.batch_size, args.dry_run)
    if args.dry_run:
        print("[DRY] done")
    else:
        print(f"done: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
