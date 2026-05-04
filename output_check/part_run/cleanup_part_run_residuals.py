#!/usr/bin/env python3
import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


PATHS_SH = Path("/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh")


@dataclass(frozen=True)
class StepDef:
    name: str
    base_key: str


@dataclass(frozen=True)
class FailedSet:
    job_id: int
    set_name: str
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


def parse_report(report_path: Path) -> List[FailedSet]:
    if not report_path.is_file():
        raise FileNotFoundError(f"part_run output report not found: {report_path}")

    failed: List[FailedSet] = []
    in_table = False
    for raw in report_path.read_text().splitlines():
        line = raw.strip()
        if line == "| job | set | failed_step | last_existing_step |":
            in_table = True
            continue
        if in_table and (not line or line.startswith("## ")):
            break
        if not in_table or line.startswith("| ---"):
            continue
        if "(none)" in line:
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        job_match = re.fullmatch(r"job_(\d+)", cells[0])
        if not job_match:
            continue
        failed.append(
            FailedSet(
                job_id=int(job_match.group(1)),
                set_name=cells[1],
                failed_step=cells[2],
                last_existing_step=cells[3],
            )
        )
    return failed


def cleanup_steps_for_failed_step(failed_step: str) -> List[StepDef]:
    if failed_step not in STEP_INDEX:
        raise ValueError(f"Unknown failed_step: {failed_step}")
    idx = STEP_INDEX[failed_step]
    start = max(0, idx - 2)
    return STEPS[start:idx]


def cleanup(process: str, failed_sets: List[FailedSet], paths: Dict[str, str], apply: bool) -> int:
    count = 0
    for item in failed_sets:
        for step in cleanup_steps_for_failed_step(item.failed_step):
            root_path = Path(paths[step.base_key]) / process / f"job_{item.job_id}" / f"{item.set_name}.root"
            if not root_path.exists():
                print(f"[MISS] {step.name} job_{item.job_id} {item.set_name}: {root_path}")
                continue
            if apply:
                root_path.unlink()
                print(f"[DEL] {root_path}")
            else:
                print(f"[DRY] {root_path}")
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Clean same-set ROOT files in the two steps before each failed_step "
            "reported by check_part_run_outputs.py. Default is dry-run."
        )
    )
    parser.add_argument("--process", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--apply", action="store_true", help="Actually delete files. Default is dry-run.")
    args = parser.parse_args()

    paths = read_paths(PATHS_SH)
    failed_sets = parse_report(Path(args.report))
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] process={args.process}")
    print(f"[{mode}] report={args.report}")
    print(f"[{mode}] failed_sets={len(failed_sets)}")
    touched = cleanup(args.process, failed_sets, paths, args.apply)
    print(f"[{mode}] root_files_{'deleted' if args.apply else 'would_delete'}={touched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
