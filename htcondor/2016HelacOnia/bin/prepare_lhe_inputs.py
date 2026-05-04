#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


BIN_DIR = Path(__file__).resolve().parent
BASE_DIR = BIN_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from common.submit_utils import load_paths  # noqa: E402


def split_lhe(input_file: Path, output_dir: Path, events_per_file: int, force: bool) -> int:
    lines = input_file.read_text().splitlines(keepends=True)

    header_lines = []
    footer_lines = []
    events = []

    in_event = False
    current_event = []
    first_event_seen = False

    for line in lines:
        stripped = line.strip()

        if stripped == "<event>":
            in_event = True
            first_event_seen = True
            current_event = [line]
            continue

        if in_event:
            current_event.append(line)
            if stripped == "</event>":
                events.append(current_event)
                current_event = []
                in_event = False
            continue

        if not first_event_seen:
            header_lines.append(line)
        else:
            footer_lines.append(line)

    if in_event:
        raise RuntimeError(f"Malformed LHE: unfinished <event> block in {input_file}")
    if not events:
        raise RuntimeError(f"No events found in {input_file}")

    output_dir.mkdir(parents=True, exist_ok=True)
    if force:
        for old in output_dir.glob("set*.lhe"):
            old.unlink()

    n_chunks = (len(events) + events_per_file - 1) // events_per_file
    for idx in range(n_chunks):
        start = idx * events_per_file
        end = min((idx + 1) * events_per_file, len(events))
        out_file = output_dir / f"set{idx+1}.lhe"
        with out_file.open("w") as out:
            out.writelines(header_lines)
            for event in events[start:end]:
                out.writelines(event)
            out.writelines(footer_lines)
    return n_chunks


def write_set_manifest(output_dir: Path, n_chunks: int) -> Path:
    manifest = output_dir / "set_list.txt"
    lines = [f"set{idx}\n" for idx in range(1, n_chunks + 1)]
    manifest.write_text("".join(lines))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare LHE split inputs under LHE/<process>/job_<ProcID>/setN.lhe")
    parser.add_argument("--process", required=True)
    parser.add_argument("--procid", required=True)
    parser.add_argument("--events-per-file", type=int, default=250)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    paths = load_paths(BASE_DIR / "config" / "paths.sh")
    events_per_file = args.events_per_file or int(paths.get("LHE_SPLIT_EVENTS", "250"))

    process = args.process
    procid = str(args.procid)
    input_lhe = (
        Path(paths["LHE_PACKAGED_BASE"])
        / process
        / f"job_{procid}"
        / "PROC_HO_0"
        / "P0_calc_0"
        / "output"
        / f"sample{process}.lhe"
    )
    output_dir = Path(paths["LHE_OUTPUT_BASE"]) / process / f"job_{procid}"

    if not input_lhe.is_file():
        raise SystemExit(f"Input LHE not found: {input_lhe}")

    chunks = split_lhe(input_lhe, output_dir, events_per_file, args.force)
    manifest = write_set_manifest(output_dir, chunks)
    print(f"Prepared {chunks} LHE chunks in {output_dir}")
    print(f"Wrote set manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
