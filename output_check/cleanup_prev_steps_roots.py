#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


PATHS_SH = Path("/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh")
OUTPUT_ROOT = Path("/eos/home-l/leyao/26JJ/MC_Maker/output_check")


class StepDef:
    def __init__(self, name: str, base_key: str):
        self.name = name
        self.base_key = base_key


STEPS: List[StepDef] = [
    StepDef("GEN", "GEN_OUTPUT_BASE"),
    StepDef("SIM", "SIM_OUTPUT_BASE"),
    StepDef("DIGI", "DIGI_OUTPUT_BASE"),
    StepDef("HLT", "HLT_OUTPUT_BASE"),
    StepDef("RECO", "RECO_OUTPUT_BASE"),
    StepDef("MINIAOD", "MINIAOD_OUTPUT_BASE"),
    StepDef("NTUPLE", "NTUPLE_OUTPUT_BASE"),
]

STEP_INDEX = {step.name: idx for idx, step in enumerate(STEPS)}


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


def parse_skip(raw: str) -> Set[int]:
    if not raw:
        return set()
    items: Set[int] = set()
    for token in raw.split(","):
        item = token.strip()
        if not item:
            continue
        if item.startswith("job_"):
            item = item[4:]
        if not item.isdigit():
            raise ValueError(f"Invalid skip item: {token}")
        items.add(int(item))
    return items


def parse_output_check_report(report_path: Path) -> Dict[str, List[int]]:
    if not report_path.is_file():
        raise FileNotFoundError(f"output_check report not found: {report_path}")

    failed_by_step: Dict[str, List[int]] = {step.name: [] for step in STEPS}
    current_step: Optional[str] = None

    for raw in report_path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("### "):
            step_name = line[4:].strip()
            current_step = step_name if step_name in failed_by_step else None
            continue
        if current_step and line.startswith("- 失败 job:"):
            if "(none)" in line:
                failed_by_step[current_step] = []
                continue
            failed_by_step[current_step] = [int(x) for x in re.findall(r"job_(\d+)", line)]
    return failed_by_step


def collect_cleanup_targets(
    failed_by_step: Dict[str, List[int]], start: int, end: int, skip: Set[int]
) -> Dict[int, List[str]]:
    targets: Dict[int, List[str]] = {}
    for step_name, jobs in failed_by_step.items():
        step_idx = STEP_INDEX[step_name]
        prev_steps: List[str] = []
        if step_idx - 1 >= 0:
            prev_steps.append(STEPS[step_idx - 1].name)
        if step_idx - 2 >= 0:
            prev_steps.append(STEPS[step_idx - 2].name)

        for job_id in jobs:
            if job_id < start or job_id > end or job_id in skip:
                continue
            if job_id not in targets:
                targets[job_id] = []
            for prev in prev_steps:
                if prev not in targets[job_id]:
                    targets[job_id].append(prev)
    return targets


def cleanup_roots(
    process: str,
    targets: Dict[int, List[str]],
    paths: Dict[str, str],
    apply: bool,
) -> int:
    deleted = 0
    for job_id in sorted(targets):
        for step_name in targets[job_id]:
            step = next(item for item in STEPS if item.name == step_name)
            base = Path(paths[step.base_key])
            job_dir = base / process / f"job_{job_id}"
            if not job_dir.is_dir():
                print(f"[MISS] {step_name} job_{job_id}: dir missing: {job_dir}")
                continue
            roots = sorted(job_dir.glob("*.root"))
            if not roots:
                print(f"[NONE] {step_name} job_{job_id}: no root to clean")
                continue

            for root in roots:
                if apply:
                    root.unlink()
                    print(f"[DEL] {root}")
                else:
                    print(f"[DRY] {root}")
                deleted += 1
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read output_check report and clean all ROOT files in step-1/step-2 for each failed job."
    )
    parser.add_argument("--process", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--skip", default="", help="Comma separated list, e.g. 8,9 or job_8,job_9")
    parser.add_argument(
        "--report",
        default="",
        help="Optional report path. Default: output_check/{process}/job{start}_{end}.md",
    )
    parser.add_argument("--apply", action="store_true", help="Actually delete files. Default is dry-run.")
    args = parser.parse_args()

    if args.start < 0 or args.end < 0 or args.start > args.end:
        raise SystemExit(f"Invalid range: start={args.start}, end={args.end}")

    skip = parse_skip(args.skip)
    report_path = Path(args.report) if args.report else (OUTPUT_ROOT / args.process / f"job{args.start}_{args.end}.md")
    failed_by_step = parse_output_check_report(report_path)
    targets = collect_cleanup_targets(failed_by_step, args.start, args.end, skip)
    paths = read_paths(PATHS_SH)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] process={args.process} range=job_{args.start}..job_{args.end} skip={args.skip or '(none)'}")
    print(f"[{mode}] report={report_path}")
    print(f"[{mode}] failed_jobs={len(targets)}")

    deleted = cleanup_roots(args.process, targets, paths, args.apply)
    print(f"[{mode}] root_files_{'deleted' if args.apply else 'would_delete'}={deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
