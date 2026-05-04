#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


PATHS_SH = Path("/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh")
OUTPUT_ROOT = Path("/eos/home-l/leyao/26JJ/MC_Maker/output_check/part_run")


@dataclass(frozen=True)
class StepDef:
    name: str
    base_key: str


@dataclass(frozen=True)
class SetStatus:
    job_id: int
    set_name: str
    success: bool
    failed_step: str
    last_existing_step: str


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


def load_set_manifest(paths: Dict[str, str], process: str, job_id: int) -> List[str]:
    manifest = Path(paths["LHE_OUTPUT_BASE"]) / process / f"job_{job_id}" / "set_list.txt"
    if not manifest.is_file():
        raise FileNotFoundError(f"set_list.txt not found: {manifest}")

    set_names = [line.strip() for line in manifest.read_text().splitlines() if line.strip()]
    bad = [item for item in set_names if not item.startswith("set")]
    if bad:
        raise ValueError(f"Invalid set names in {manifest}: {bad}")
    if not set_names:
        raise ValueError(f"Empty set manifest: {manifest}")
    return set_names


def step_root(paths: Dict[str, str], step: StepDef, process: str, job_id: int, set_name: str) -> Path:
    return Path(paths[step.base_key]) / process / f"job_{job_id}" / f"{set_name}.root"


def check_set(paths: Dict[str, str], process: str, job_id: int, set_name: str) -> SetStatus:
    existing_steps: List[str] = []
    for step in STEPS:
        if step_root(paths, step, process, job_id, set_name).is_file():
            existing_steps.append(step.name)

    if "NTUPLE" in existing_steps:
        return SetStatus(
            job_id=job_id,
            set_name=set_name,
            success=True,
            failed_step="(none)",
            last_existing_step="NTUPLE",
        )

    last_existing: Optional[str] = existing_steps[-1] if existing_steps else None
    if last_existing is None:
        failed_step = "GEN"
        last_label = "(none)"
    else:
        last_idx = next(idx for idx, step in enumerate(STEPS) if step.name == last_existing)
        failed_step = STEPS[last_idx + 1].name if last_idx + 1 < len(STEPS) else "NTUPLE"
        last_label = last_existing

    return SetStatus(
        job_id=job_id,
        set_name=set_name,
        success=False,
        failed_step=failed_step,
        last_existing_step=last_label,
    )


def check_range(process: str, start: int, end: int, skip: Set[int], paths: Dict[str, str]) -> List[SetStatus]:
    statuses: List[SetStatus] = []
    for job_id in range(start, end + 1):
        if job_id in skip:
            continue
        for set_name in load_set_manifest(paths, process, job_id):
            statuses.append(check_set(paths, process, job_id, set_name))
    return statuses


def format_report(process: str, start: int, end: int, skip_raw: str, skip: Set[int], statuses: List[SetStatus]) -> str:
    failed = [item for item in statuses if not item.success]
    total_sets = len(statuses)
    failed_sets = len(failed)
    success_sets = total_sets - failed_sets
    ratio = 0.0 if total_sets == 0 else 100.0 * failed_sets / total_sets
    checked_jobs = [job_id for job_id in range(start, end + 1) if job_id not in skip]
    failed_jobs = sorted({item.job_id for item in failed})

    lines: List[str] = []
    lines.append(f"# part_run Output Check: {process} job_{start}~job_{end}")
    lines.append("")
    lines.append(f"- 失败 set 比例: **{ratio:.2f}% ({failed_sets}/{total_sets})**")
    lines.append(f"- 成功 set: `{success_sets}`")
    lines.append(f"- process: `{process}`")
    lines.append(f"- job_start: `{start}`")
    lines.append(f"- job_end: `{end}`")
    lines.append(f"- job_skip: `{skip_raw if skip_raw else '(none)'}`")
    lines.append(f"- 检查 job 数: `{len(checked_jobs)}`")
    lines.append(f"- 失败 job ID: `{', '.join(f'job_{j}' for j in failed_jobs) if failed_jobs else '(none)'}`")
    lines.append(f"- 检查时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append("")
    lines.append("## 失败 set 列表")
    lines.append("")
    lines.append("| job | set | failed_step | last_existing_step |")
    lines.append("| --- | --- | --- | --- |")
    if failed:
        for item in failed:
            lines.append(
                f"| job_{item.job_id} | {item.set_name} | {item.failed_step} | {item.last_existing_step} |"
            )
    else:
        lines.append("| (none) | (none) | (none) | (none) |")
    lines.append("")
    lines.append("## 按 job 汇总")
    lines.append("")
    lines.append("| job | success_sets | failed_sets |")
    lines.append("| --- | ---: | ---: |")
    for job_id in checked_jobs:
        job_status = [item for item in statuses if item.job_id == job_id]
        job_failed = sum(1 for item in job_status if not item.success)
        lines.append(f"| job_{job_id} | {len(job_status) - job_failed} | {job_failed} |")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check per-set part_run outputs by NTUPLE setN.root existence.")
    parser.add_argument("--process", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--skip", default="", help="Comma separated list, e.g. 8,9 or job_8,job_9")
    args = parser.parse_args()

    if args.start < 0 or args.end < 0 or args.start > args.end:
        raise SystemExit(f"Invalid range: start={args.start}, end={args.end}")

    skip = parse_skip(args.skip)
    paths = read_paths(PATHS_SH)
    statuses = check_range(args.process, args.start, args.end, skip, paths)

    out_dir = OUTPUT_ROOT / args.process
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"job{args.start}_{args.end}.md"
    out_file.write_text(format_report(args.process, args.start, args.end, args.skip, skip, statuses))
    print(f"Wrote report: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
