#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from common.submit_utils import load_paths, load_set_manifest  # noqa: E402


STAGES = ("GEN", "SIM", "DIGI", "HLT", "RECO", "MINIAOD", "NTUPLE")

STAGE_CONFIG = {
    "GEN": {
        "executable": "run_gen_condor.sh",
        "memory": 1000,
        "runtime": 7200,
    },
    "SIM": {
        "executable": "run_sim_input_condor.sh",
        "memory": 2000,
        "runtime": 10800,
        "input_base": "GEN_OUTPUT_BASE",
        "output_base": "SIM_OUTPUT_BASE",
    },
    "DIGI": {
        "executable": "run_digi_input_condor.sh",
        "memory": 3000,
        "runtime": 7200,
        "input_base": "SIM_OUTPUT_BASE",
        "output_base": "DIGI_OUTPUT_BASE",
    },
    "HLT": {
        "executable": "run_hlt_input_condor.sh",
        "memory": 3000,
        "runtime": 7200,
        "input_base": "DIGI_OUTPUT_BASE",
        "output_base": "HLT_OUTPUT_BASE",
    },
    "RECO": {
        "executable": "run_reco_input_condor.sh",
        "memory": 4000,
        "runtime": 10800,
        "input_base": "HLT_OUTPUT_BASE",
        "output_base": "RECO_OUTPUT_BASE",
    },
    "MINIAOD": {
        "executable": "run_miniaod_input_condor.sh",
        "memory": 1500,
        "runtime": 3600,
        "input_base": "RECO_OUTPUT_BASE",
        "output_base": "MINIAOD_OUTPUT_BASE",
    },
    "NTUPLE": {
        "executable": "run_ntuple_input_condor.sh",
        "memory": 1000,
        "runtime": 3600,
        "input_base": "MINIAOD_OUTPUT_BASE",
        "output_base": "NTUPLE_OUTPUT_BASE",
    },
}


def submit_text(
    executable: Path,
    arguments: str,
    log_stem: Path,
    memory: int,
    runtime: int,
) -> str:
    return "\n".join(
        [
            f"executable = {executable}",
            f"arguments = {arguments}",
            f"output = {log_stem}.out",
            f"error = {log_stem}.err",
            f"log = {log_stem}.log",
            "request_cpus = 1",
            f"request_memory = {memory}",
            "request_disk = 4000000",
            f"+MaxRuntime = {runtime}",
            "should_transfer_files = NO",
            "queue 1",
            "",
        ]
    )


def stage_arguments(paths: Dict[str, str], process: str, procid: str, set_name: str, stage: str) -> str:
    job_dir = f"job_{procid}"
    job_label = f"{job_dir}_{set_name}"

    if stage == "GEN":
        return f"{process} {job_label}"

    cfg = STAGE_CONFIG[stage]
    input_file = Path(paths[cfg["input_base"]]) / process / job_dir / f"{set_name}.root"
    output_file = Path(paths[cfg["output_base"]]) / process / job_dir / f"{set_name}.root"
    return f"{input_file} {output_file} {process} {job_label}"


def write_part_run(process: str, procid: str) -> Path:
    paths = load_paths(BASE_DIR / "config" / "paths.sh")
    job_dir = f"job_{procid}"
    run_tag = f"{process}_job_{procid}"
    manifest = Path(paths["LHE_OUTPUT_BASE"]) / process / job_dir / "set_list.txt"
    set_names = load_set_manifest(manifest)

    run_dir = BASE_DIR / "DAG" / "part_runs" / run_tag
    submit_dir = run_dir / "submit"
    log_dir = BASE_DIR / "DAG" / "part_logs" / run_tag
    submit_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    dag_lines: List[str] = []
    for set_name in set_names:
        previous_node = ""
        for stage in STAGES:
            cfg = STAGE_CONFIG[stage]
            node_name = f"{stage}_{set_name}"
            submit_file = submit_dir / f"{node_name}.sub"
            log_stem = log_dir / node_name
            arguments = stage_arguments(paths, process, procid, set_name, stage)
            submit_file.write_text(
                submit_text(
                    BASE_DIR / "bin" / cfg["executable"],
                    arguments,
                    log_stem,
                    cfg["memory"],
                    cfg["runtime"],
                )
            )

            dag_lines.append(f"JOB {node_name} {submit_file}")
            dag_lines.append(f"RETRY {node_name} 2")
            if previous_node:
                dag_lines.append(f"PARENT {previous_node} CHILD {node_name}")
            previous_node = node_name
        dag_lines.append("")

    dag_path = run_dir / f"part_run_{run_tag}.dag"
    dag_path.write_text("\n".join(dag_lines))
    print(f"Wrote {dag_path} with {len(set_names)} independent set chains")
    return dag_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build per-set DAGMan workflow for one process/job.")
    parser.add_argument("process")
    parser.add_argument("procid")
    args = parser.parse_args()

    write_part_run(args.process, args.procid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
