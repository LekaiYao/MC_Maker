#!/usr/bin/env python3
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from common.submit_utils import (  # noqa: E402
    cleanup_submit_files,
    collect_jobs_from_manifest,
    load_paths,
    select_processes,
    write_per_process_submit,
)


def main() -> None:
    variables = load_paths(BASE_DIR / "config" / "paths.sh")
    processes = variables["MINIAOD_PROCESSES"].split()

    logs_dir = BASE_DIR / "MINIAOD" / "logs"
    submit_dir = BASE_DIR / "MINIAOD" / "submit"
    executable = BASE_DIR / "bin" / "run_miniaod_input_condor.sh"
    logs_dir.mkdir(parents=True, exist_ok=True)
    submit_dir.mkdir(parents=True, exist_ok=True)
    selected_processes = select_processes(processes)
    cleanup_submit_files(submit_dir, selected_processes)

    jobs = collect_jobs_from_manifest(
        processes=selected_processes,
        input_base=Path(variables["RECO_OUTPUT_BASE"]),
        output_base=Path(variables["MINIAOD_OUTPUT_BASE"]),
        input_extension="root",
        manifest_base=Path(variables["LHE_OUTPUT_BASE"]),
    )
    write_per_process_submit(
        jobs,
        submit_dir,
        logs_dir,
        executable,
        request_memory=1500,
        max_runtime=3600,
    )


if __name__ == "__main__":
    main()
