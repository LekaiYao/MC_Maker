#!/usr/bin/env python3
import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


OUTPUT_ROOT = Path("/eos/home-l/leyao/26JJ/MC_Maker/output_check")
DAG_BASE = Path("/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia")

STEPS = ["GEN", "SIM", "DIGI", "HLT", "RECO", "MINIAOD", "NTUPLE"]


@dataclass
class SubjobFailure:
    stage: str
    subjob_log: Path
    reason: str
    evidence: str
    ret_code: Optional[int]


@dataclass
class JobDiagnosis:
    job_id: int
    output_check_step: str
    inspected_steps: List[str]
    real_fail_step: Optional[str]
    failures: List[SubjobFailure]
    note: str = ""


def parse_skip(raw: str) -> Set[int]:
    if not raw:
        return set()
    result: Set[int] = set()
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


def parse_output_check_report(report_path: Path) -> Dict[str, List[int]]:
    if not report_path.is_file():
        raise FileNotFoundError(f"output_check report not found: {report_path}")

    failed_by_step: Dict[str, List[int]] = {step: [] for step in STEPS}
    current_step: Optional[str] = None

    for raw in report_path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("### "):
            name = line[4:].strip()
            current_step = name if name in failed_by_step else None
            continue
        if current_step and line.startswith("- 失败 job:"):
            if "(none)" in line:
                failed_by_step[current_step] = []
                continue
            ids = [int(x) for x in re.findall(r"job_(\d+)", line)]
            failed_by_step[current_step] = ids

    return failed_by_step


def previous_step(step: str) -> Optional[str]:
    idx = STEPS.index(step)
    if idx == 0:
        return None
    return STEPS[idx - 1]


def parse_failed_subjobs_from_stage_out(stage_out: Path) -> List[Path]:
    if not stage_out.is_file():
        return []
    paths: List[Path] = []
    for line in stage_out.read_text(errors="ignore").splitlines():
        if " log=" in line and " arguments=" in line and "submit=" in line:
            m = re.search(r"log=([^\s]+)", line)
            if m:
                paths.append(Path(m.group(1)))
    return paths


def read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(errors="ignore")


def extract_return_code(log_text: str) -> Optional[int]:
    m = re.search(r"return value (\d+)", log_text)
    if m:
        return int(m.group(1))
    m2 = re.search(r"exit-code (\d+)", log_text)
    if m2:
        return int(m2.group(1))
    return None


def classify_reason(log_text: str, out_text: str, err_text: str) -> Tuple[str, str]:
    merged = "\n".join([log_text, out_text, err_text]).lower()

    if "system_periodic_remove" in merged or "wall time exceeded allowed max" in merged:
        return "TIMEOUT", "SYSTEM_PERIODIC_REMOVE / wall time exceeded"
    if "fatal exception" in merged:
        m = re.search(r"an exception of category '([^']+)'", "\n".join([out_text, err_text]), re.IGNORECASE)
        detail = m.group(1) if m else "Fatal Exception"
        return "FATAL_EXCEPTION", detail
    if "segmentation violation" in merged or "segmentation fault" in merged:
        m = re.search(r"module:\s*([^\n]+)\(crashed\)", "\n".join([out_text, err_text]), re.IGNORECASE)
        detail = m.group(1).strip() if m else "segmentation violation"
        return "SEGFAULT", detail
    if "aborted" in merged:
        return "ABORTED", "process aborted"

    ret = extract_return_code(log_text)
    if ret is not None and ret != 0:
        return "NONZERO_EXIT", f"return value {ret}"

    return "UNKNOWN", "no clear signature found"


def diagnose_subjob(stage: str, subjob_log: Path) -> SubjobFailure:
    log_text = read_text_if_exists(subjob_log)
    out_text = read_text_if_exists(subjob_log.with_suffix(".out"))
    err_text = read_text_if_exists(subjob_log.with_suffix(".err"))
    reason, evidence = classify_reason(log_text, out_text, err_text)
    ret_code = extract_return_code(log_text)
    return SubjobFailure(
        stage=stage,
        subjob_log=subjob_log,
        reason=reason,
        evidence=evidence,
        ret_code=ret_code,
    )


def diagnose_job(process: str, job_id: int, output_check_step: str) -> JobDiagnosis:
    stages_to_check: List[str] = []
    prev = previous_step(output_check_step)
    if prev:
        stages_to_check.append(prev)
    stages_to_check.append(output_check_step)

    all_failures: List[SubjobFailure] = []
    real_fail_stage: Optional[str] = None

    for stage in stages_to_check:
        stage_out = DAG_BASE / "DAG" / "logs" / f"{process}_job_{job_id}_{stage}.out"
        subjob_logs = parse_failed_subjobs_from_stage_out(stage_out)
        if subjob_logs:
            stage_failures = [diagnose_subjob(stage, item) for item in subjob_logs]
            all_failures.extend(stage_failures)
            if real_fail_stage is None:
                real_fail_stage = stage

    note = ""
    if not all_failures:
        note = "No failed subjob lines found in inspected stage logs."

    return JobDiagnosis(
        job_id=job_id,
        output_check_step=output_check_step,
        inspected_steps=stages_to_check,
        real_fail_step=real_fail_stage,
        failures=all_failures,
        note=note,
    )


def format_report(
    process: str,
    start: int,
    end: int,
    skip_raw: str,
    diagnoses: List[JobDiagnosis],
) -> str:
    n = len(diagnoses)
    lines: List[str] = []
    lines.append(f"Failure Reason Report: {process} job_{start}~job_{end}")
    lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    lines.append(f"Input: process={process}, start={start}, end={end}, skip={skip_raw if skip_raw else '(none)'}")
    lines.append(f"Failed jobs to inspect: {n}")
    lines.append("")

    for item in diagnoses:
        lines.append(f"[job_{item.job_id}]")
        lines.append(f"- output_check first-fail step: {item.output_check_step}")
        lines.append(f"- inspected steps (prev + current): {', '.join(item.inspected_steps)}")
        lines.append(f"- real fail step (from logs): {item.real_fail_step if item.real_fail_step else '(unknown)'}")
        if item.failures:
            for failure in item.failures:
                ret = f", return={failure.ret_code}" if failure.ret_code is not None else ""
                lines.append(
                    f"  * [{failure.stage}] {failure.subjob_log.name}: {failure.reason} ({failure.evidence}{ret})"
                )
        if item.note:
            lines.append(f"  * note: {item.note}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose failed jobs by checking output_check first-fail step and its previous step."
    )
    parser.add_argument("--process", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--skip", default="")
    args = parser.parse_args()

    if args.start < 0 or args.end < 0 or args.start > args.end:
        raise SystemExit(f"Invalid range: start={args.start}, end={args.end}")

    skip = parse_skip(args.skip)
    report_md = OUTPUT_ROOT / args.process / f"job{args.start}_{args.end}.md"
    failed_by_step = parse_output_check_report(report_md)

    candidates: Dict[int, str] = {}
    for step in STEPS:
        for job_id in failed_by_step.get(step, []):
            if args.start <= job_id <= args.end and job_id not in skip:
                candidates[job_id] = step

    diagnoses = [diagnose_job(args.process, job_id, candidates[job_id]) for job_id in sorted(candidates)]

    out_dir = OUTPUT_ROOT / args.process
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"failure_reason_job{args.start}_{args.end}.txt"
    out_file.write_text(format_report(args.process, args.start, args.end, args.skip, diagnoses))
    print(f"Wrote report: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
