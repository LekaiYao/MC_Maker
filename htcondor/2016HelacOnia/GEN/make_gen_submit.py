#!/usr/bin/env python3
import os
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from common.submit_utils import cleanup_submit_files, load_set_manifest, select_processes  # noqa: E402


def read_processes(paths_file):
    processes = []
    for line in paths_file.read_text().splitlines():
        if line.startswith("export GEN_PROCESSES="):
            value = line.split("=", 1)[1].strip().strip('"')
            processes = [item for item in value.split() if item]
            break
    if not processes:
        raise RuntimeError("GEN_PROCESSES is not configured in config/paths.sh")
    return processes


def read_lhe_output_base(paths_file):
    variables = {}
    for raw_line in paths_file.read_text().splitlines():
        line = raw_line.strip()
        if not line.startswith("export "):
            continue
        key, value = line[len("export "):].split("=", 1)
        variables[key] = value.strip().strip('"')

    cmssw_base = variables.get("CMSSW_BASE")
    data_src_dir = variables.get("DATA_SRC_DIR")
    lhe_output_base = variables.get("LHE_OUTPUT_BASE")
    if not cmssw_base or not data_src_dir or not lhe_output_base:
        raise RuntimeError("CMSSW_BASE, DATA_SRC_DIR, or LHE_OUTPUT_BASE is missing in config/paths.sh")

    expanded_data_src_dir = data_src_dir.replace("${CMSSW_BASE}", cmssw_base)
    return Path(lhe_output_base.replace("${DATA_SRC_DIR}", expanded_data_src_dir))


def build_job_block(executable, logs_dir, process_name, job_tag):
    return "\n".join(
        [
            f"executable = {executable}",
            f"arguments = {process_name} {job_tag}",
            f"output = {logs_dir}/{process_name}_{job_tag}.out",
            f"error = {logs_dir}/{process_name}_{job_tag}.err",
            f"log = {logs_dir}/{process_name}_{job_tag}.log",
            "request_cpus = 1",
            "request_memory = 1000",
            "request_disk = 2000000",
            "+MaxRuntime = 7200",
            "should_transfer_files = NO",
            "queue 1",
            "",
        ]
    )


def main():
    base_dir = BASE_DIR
    paths_file = base_dir / "config" / "paths.sh"
    logs_dir = base_dir / "GEN" / "logs"
    submit_dir = base_dir / "GEN" / "submit"
    executable = base_dir / "bin" / "run_gen_condor.sh"
    lhe_output_base = read_lhe_output_base(paths_file)
    processes = select_processes(read_processes(paths_file))
    dag_procid = os.environ.get("DAG_PROCID", "").strip()

    submit_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    cleanup_submit_files(submit_dir, processes)

    for process_name in processes:
        if not dag_procid:
            raise RuntimeError("DAG_PROCID is required for GEN submit generation")
        job_dir = f"job_{dag_procid}"
        set_manifest = lhe_output_base / process_name / job_dir / "set_list.txt"
        set_names = load_set_manifest(set_manifest)

        job_blocks = []
        for set_name in set_names:
            job_tag = f"{job_dir}_{set_name}"
            job_blocks.append(build_job_block(executable, logs_dir, process_name, job_tag))

        if dag_procid:
            submit_path = submit_dir / f"{process_name}_job_{dag_procid}.sub"
        else:
            submit_path = submit_dir / f"{process_name}.sub"
        submit_path.write_text("\n".join(job_blocks))
        print(f"Wrote {submit_path} with {len(set_names)} jobs")


if __name__ == "__main__":
    main()
