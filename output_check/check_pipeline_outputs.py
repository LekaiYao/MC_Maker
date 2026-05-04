#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set


PATHS_SH = Path("/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh")
OUTPUT_ROOT = Path("/eos/home-l/leyao/26JJ/MC_Maker/output_check")


@dataclass(frozen=True)
class StepDef:
    name: str
    base_key: str


STEPS: List[StepDef] = [
    StepDef("GEN", "GEN_OUTPUT_BASE"),
    StepDef("SIM", "SIM_OUTPUT_BASE"),
    StepDef("DIGI", "DIGI_OUTPUT_BASE"),
    StepDef("HLT", "HLT_OUTPUT_BASE"),
    StepDef("RECO", "RECO_OUTPUT_BASE"),
    StepDef("MINIAOD", "MINIAOD_OUTPUT_BASE"),
    StepDef("NTUPLE", "NTUPLE_OUTPUT_BASE"),
]


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


def check_outputs(process: str, start: int, end: int, skip: Set[int], paths: Dict[str, str]) -> Dict[str, List[int]]:
    all_jobs = [job_id for job_id in range(start, end + 1) if job_id not in skip]
    alive_jobs = set(all_jobs)
    failed_by_step: Dict[str, List[int]] = {step.name: [] for step in STEPS}

    for step in STEPS:
        base_dir = Path(paths[step.base_key])
        current_fail: List[int] = []
        for job_id in sorted(alive_jobs):
            job_dir = base_dir / process / f"job_{job_id}"
            if not job_dir.is_dir():
                current_fail.append(job_id)
        failed_by_step[step.name] = current_fail
        alive_jobs -= set(current_fail)

    return failed_by_step


def format_report(
    process: str,
    start: int,
    end: int,
    skip_raw: str,
    skip: Set[int],
    failed_by_step: Dict[str, List[int]],
) -> str:
    checked_jobs = [job_id for job_id in range(start, end + 1) if job_id not in skip]
    fail_set = sorted({job_id for items in failed_by_step.values() for job_id in items})
    n_total = len(checked_jobs)
    n_fail = len(fail_set)
    ratio = 0.0 if n_total == 0 else 100.0 * n_fail / n_total

    lines: List[str] = []
    lines.append(f"# Output Check Report: {process} job_{start}~job_{end}")
    lines.append("")
    lines.append(f"- 失败比例: **{ratio:.2f}% ({n_fail}/{n_total})**")
    lines.append(f"- process: `{process}`")
    lines.append(f"- job_start: `{start}`")
    lines.append(f"- job_end: `{end}`")
    lines.append(f"- job_skip: `{skip_raw if skip_raw else '(none)'}`")
    lines.append(f"- 失败 job ID: `{', '.join(f'job_{j}' for j in fail_set) if fail_set else '(none)'}`")
    lines.append(f"- 检查时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}`")
    lines.append("")
    lines.append("## 按步骤首次失败列表")
    lines.append("")

    for step in STEPS:
        failed = failed_by_step[step.name]
        lines.append(f"### {step.name}")
        if failed:
            lines.append(f"- 失败 job: `{', '.join(f'job_{j}' for j in failed)}`")
        else:
            lines.append("- 失败 job: `(none)`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check missing output directories across GEN->NTUPLE by job range.")
    parser.add_argument("--process", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--skip", default="", help="Comma separated list, e.g. 8,9 or job_8,job_9")
    args = parser.parse_args()

    if args.start < 0 or args.end < 0 or args.start > args.end:
        raise SystemExit(f"Invalid range: start={args.start}, end={args.end}")

    skip = parse_skip(args.skip)
    paths = read_paths(PATHS_SH)
    failed_by_step = check_outputs(args.process, args.start, args.end, skip, paths)

    out_dir = OUTPUT_ROOT / args.process
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"job{args.start}_{args.end}.md"
    out_file.write_text(
        format_report(
            process=args.process,
            start=args.start,
            end=args.end,
            skip_raw=args.skip,
            skip=skip,
            failed_by_step=failed_by_step,
        )
    )

    print(f"Wrote report: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
