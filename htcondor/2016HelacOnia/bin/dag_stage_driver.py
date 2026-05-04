#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Dict, List, Optional


BIN_DIR = Path(__file__).resolve().parent
BASE_DIR = BIN_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from common.submit_utils import load_paths  # noqa: E402


REQUESTS = {
    "SIM": {"memory": 2000, "runtime": 10800},
    "DIGI": {"memory": 3000, "runtime": 7200},
    "HLT": {"memory": 3000, "runtime": 7200},
    "RECO": {"memory": 4000, "runtime": 10800},
    "MINIAOD": {"memory": 1500, "runtime": 3600},
    "NTUPLE": {"memory": 1000, "runtime": 3600},
}

STAGE_INPUT_SUFFIX = {
    "SIM": "GEN",
    "DIGI": "SIM",
    "HLT": "DIGI",
    "RECO": "HLT",
    "MINIAOD": "RECO",
    "NTUPLE": "MINIAOD",
}

STAGE_EXECUTABLE_HINT = {
    "GEN": "run_gen_condor.sh",
    "SIM": "run_sim_input_condor.sh",
    "DIGI": "run_digi_input_condor.sh",
    "HLT": "run_hlt_input_condor.sh",
    "RECO": "run_reco_input_condor.sh",
    "MINIAOD": "run_miniaod_input_condor.sh",
    "NTUPLE": "run_ntuple_input_condor.sh",
}

STEP_N_MINUS_2_OUTPUT_BASE = {
    "DIGI": "GEN_OUTPUT_BASE",
    "HLT": "SIM_OUTPUT_BASE",
    "RECO": "DIGI_OUTPUT_BASE",
    "MINIAOD": "HLT_OUTPUT_BASE",
    "NTUPLE": "RECO_OUTPUT_BASE",
}


def run(cmd: List[str], check: bool = True, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    prefix = ""
    if cwd is not None:
        prefix = f"(cd {shlex.quote(str(cwd))} && ) "
    print(f"+ {prefix}" + " ".join(shlex.quote(item) for item in cmd), flush=True)
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, cwd=str(cwd) if cwd is not None else None)
    if proc.returncode != 0 and check:
        print(f"Command failed (exit={proc.returncode}): {' '.join(shlex.quote(item) for item in cmd)}", flush=True)
        if proc.stdout:
            print("----- stdout -----", flush=True)
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n", flush=True)
        if proc.stderr:
            print("----- stderr -----", flush=True)
            print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", flush=True)
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
    return proc


def _get_attr(attrs: Dict[str, str], name: str, default: str = "") -> str:
    name_lower = name.lower()
    for key, value in attrs.items():
        if key.lower() == name_lower:
            return value
    return default


def parse_submit_file(submit_file: Path) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for raw in submit_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip()
            continue
        if line.lower().startswith("queue"):
            attrs = dict(current)
            record = {
                "arguments": _get_attr(attrs, "arguments", ""),
                "log": _get_attr(attrs, "log", ""),
                "submit": str(submit_file),
                "attrs": attrs,
            }
            records.append(record)
            current = {}
    return records


def wait_for_logs(records: List[Dict[str, str]], wait_timeout: int) -> None:
    for record in records:
        log_file = record["log"]
        if not log_file:
            continue
        run(["condor_wait", "-wait", str(wait_timeout), log_file], check=False)


def failed_records(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    bad = []
    for record in records:
        log_path = Path(record["log"])
        if not log_path.exists():
            bad.append(record)
            continue
        content = log_path.read_text(errors="ignore")
        if "return value 0" not in content:
            bad.append(record)
    return bad


def submit_and_wait(submit_files: List[Path], wait_timeout: int) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for submit_file in submit_files:
        run(["condor_submit", str(submit_file)], cwd=BASE_DIR)
        records.extend(parse_submit_file(submit_file))
    wait_for_logs(records, wait_timeout)
    failed = failed_records(records)
    max_resubmit = int(os.environ.get("DAG_MAX_RESUBMIT", "2"))

    for retry in range(1, max_resubmit + 1):
        if not failed:
            break
        print(f"Retry submit for {len(failed)} failed jobs (attempt {retry}/{max_resubmit})", flush=True)
        failed = resubmit_failed_records(failed, retry, wait_timeout)

    return failed


def _retry_path(original: str, retry_idx: int, suffix: str) -> str:
    path = Path(original)
    stem = path.stem
    if path.suffix:
        return str(path.with_name(f"{stem}.retry{retry_idx}{suffix}{path.suffix}"))
    return f"{original}.retry{retry_idx}{suffix}"


def _write_retry_submit(record: Dict[str, str], retry_idx: int, index: int) -> Path:
    submit_dir = BASE_DIR / "DAG" / "submit"
    submit_dir.mkdir(parents=True, exist_ok=True)
    submit_name = f"retry_{Path(record['submit']).stem}_{retry_idx}_{index}.sub"
    submit_path = submit_dir / submit_name

    attrs: Dict[str, str] = dict(record.get("attrs", {}))
    if _get_attr(attrs, "log", ""):
        attrs["log"] = _retry_path(_get_attr(attrs, "log"), retry_idx, "")
    if _get_attr(attrs, "output", ""):
        attrs["output"] = _retry_path(_get_attr(attrs, "output"), retry_idx, "")
    if _get_attr(attrs, "error", ""):
        attrs["error"] = _retry_path(_get_attr(attrs, "error"), retry_idx, "")

    lines = [f"{k} = {v}" for k, v in attrs.items()]
    lines.append("queue 1")
    lines.append("")
    submit_path.write_text("\n".join(lines))
    return submit_path


def resubmit_failed_records(failed: List[Dict[str, str]], retry_idx: int, wait_timeout: int) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for idx, rec in enumerate(failed, start=1):
        retry_submit = _write_retry_submit(rec, retry_idx, idx)
        run(["condor_submit", str(retry_submit)], cwd=BASE_DIR)
        records.extend(parse_submit_file(retry_submit))
    wait_for_logs(records, wait_timeout)
    return failed_records(records)


def valid_submit_files(stage: str, submit_files: List[Path]) -> List[Path]:
    hint = STAGE_EXECUTABLE_HINT.get(stage, "")
    selected: List[Path] = []
    for submit_file in submit_files:
        if not submit_file.exists() or submit_file.stat().st_size == 0:
            continue
        content = submit_file.read_text(errors="ignore")
        if hint and hint not in content:
            print(f"Skip stale submit file {submit_file}: missing executable hint {hint}", flush=True)
            continue
        selected.append(submit_file)
    return selected


def cleanup_step_n_minus_2_outputs(stage: str, paths: Dict[str, str], dag_process: str, dag_procid: str) -> None:
    output_base_key = STEP_N_MINUS_2_OUTPUT_BASE.get(stage)
    if not output_base_key:
        return

    output_base = paths.get(output_base_key, "").strip()
    if not output_base:
        print(f"Skip cleanup for {stage}: {output_base_key} is not configured.", flush=True)
        return

    if dag_process:
        processes = [dag_process]
    else:
        process_key = f"{stage}_PROCESSES"
        processes = paths.get(process_key, "").split()

    if dag_procid:
        job_dirs = [f"job_{dag_procid}"]
    else:
        job_dirs = []

    for process_name in processes:
        process_dir = Path(output_base) / process_name
        if not process_dir.is_dir():
            continue
        targets = [process_dir / job_dir for job_dir in job_dirs] if job_dirs else sorted(process_dir.glob("job_*"))
        for target in targets:
            if not target.is_dir():
                continue
            removed = 0
            for root_file in sorted(target.glob("*.root")):
                root_file.unlink()
                removed += 1
            print(
                f"Cleanup {stage}: kept directory {target}, removed {removed} ROOT files",
                flush=True,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="DAG stage driver: submit existing stage files, wait, fail fast.")
    parser.add_argument("stage", choices=sorted(STAGE_EXECUTABLE_HINT))
    args = parser.parse_args()

    stage = args.stage
    paths = load_paths(BASE_DIR / "config" / "paths.sh")
    dag_process = os.environ.get("DAG_PROCESS", "").strip()
    dag_procid = os.environ.get("DAG_PROCID", "").strip()
    wait_timeout = int(os.environ.get("DAG_CONDOR_WAIT_TIMEOUT", "216000"))

    cleanup_step_n_minus_2_outputs(stage, paths, dag_process, dag_procid)

    process_key = f"{stage}_PROCESSES"
    processes = paths.get(process_key, "").split()
    if dag_process:
        processes = [item for item in processes if item == dag_process]
    if dag_procid:
        submit_files = [BASE_DIR / stage / "submit" / f"{proc}_job_{dag_procid}.sub" for proc in processes]
    else:
        submit_files = [BASE_DIR / stage / "submit" / f"{proc}.sub" for proc in processes]
    submit_files = valid_submit_files(stage, submit_files)
    if not submit_files:
        raise RuntimeError(f"No submit files found for stage {stage}")

    failed = submit_and_wait(submit_files, wait_timeout)

    if failed:
        print(f"Stage {stage} failed jobs:", flush=True)
        for rec in failed:
            print(f"  submit={rec['submit']} log={rec['log']} arguments={rec['arguments']}", flush=True)
        return 1

    print(f"Stage {stage} completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
