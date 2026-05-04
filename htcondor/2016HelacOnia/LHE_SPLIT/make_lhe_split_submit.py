#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from common.submit_utils import load_paths  # noqa: E402


def parse_skip_list(raw: str) -> set[int]:
    if not raw:
        return set()
    result: set[int] = set()
    for token in raw.split(","):
        item = token.strip()
        if not item:
            continue
        if item.startswith("job_"):
            item = item[4:]
        if not item.isdigit():
            raise ValueError(f"Invalid skip item: {token}")
        result.add(int(item))
    return result


def build_job_block(
    executable: Path,
    logs_dir: Path,
    process: str,
    procid: int,
    request_memory: int,
    request_disk: int,
    max_runtime: int,
) -> str:
    tag = f"{process}_job_{procid}"
    return "\n".join(
        [
            f"executable = {executable}",
            f"arguments = {process} {procid}",
            f"output = {logs_dir}/{tag}.out",
            f"error = {logs_dir}/{tag}.err",
            f"log = {logs_dir}/{tag}.log",
            "request_cpus = 1",
            f"request_memory = {request_memory}",
            f"request_disk = {request_disk}",
            f"+MaxRuntime = {max_runtime}",
            "should_transfer_files = NO",
            "queue 1",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Condor submit for LHE split preparation jobs."
    )
    parser.add_argument("--process", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--skip", default="")
    parser.add_argument("--request-memory", type=int, default=2000)
    parser.add_argument("--request-disk", type=int, default=1000000)
    parser.add_argument("--max-runtime", type=int, default=21600)
    args = parser.parse_args()

    if args.start < 0 or args.end < 0 or args.start > args.end:
        raise SystemExit(f"Invalid range: start={args.start}, end={args.end}")

    skip_ids = parse_skip_list(args.skip)

    paths = load_paths(BASE_DIR / "config" / "paths.sh")
    logs_dir = BASE_DIR / "LHE_SPLIT" / "logs"
    submit_dir = BASE_DIR / "LHE_SPLIT" / "submit"
    executable = BASE_DIR / "bin" / "run_lhe_split_condor.sh"
    logs_dir.mkdir(parents=True, exist_ok=True)
    submit_dir.mkdir(parents=True, exist_ok=True)

    process = args.process
    submit_path = submit_dir / f"{process}_jobs_{args.start}_{args.end}.sub"

    blocks = []
    for procid in range(args.start, args.end + 1):
        if procid in skip_ids:
            continue
        packaged_lhe = (
            Path(paths["LHE_PACKAGED_BASE"])
            / process
            / f"job_{procid}"
            / "PROC_HO_0"
            / "P0_calc_0"
            / "output"
            / f"sample{process}.lhe"
        )
        if not packaged_lhe.is_file():
            print(f"[WARN] skip job_{procid}: input LHE missing: {packaged_lhe}")
            continue

        blocks.append(
            build_job_block(
                executable=executable,
                logs_dir=logs_dir,
                process=process,
                procid=procid,
                request_memory=args.request_memory,
                request_disk=args.request_disk,
                max_runtime=args.max_runtime,
            )
        )

    if not blocks:
        raise RuntimeError("No valid jobs to write. Check range/skip/input LHE paths.")

    submit_path.write_text("\n".join(blocks))
    print(f"Wrote {submit_path} with {len(blocks)} jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
