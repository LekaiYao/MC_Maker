#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Optional


def read_exports(paths_file: Path) -> dict:
    variables = {}
    for raw_line in paths_file.read_text().splitlines():
        line = raw_line.strip()
        if not line.startswith("export "):
            continue
        key, value = line[len("export ") :].split("=", 1)
        variables[key] = value.strip().strip('"')
    return variables


def expand(value: str, variables: dict) -> str:
    expanded = value
    changed = True
    while changed:
        changed = False
        for key, item in variables.items():
            token = f"${{{key}}}"
            if token in expanded:
                expanded = expanded.replace(token, item)
                changed = True
    return expanded


def load_paths(paths_file: Path) -> dict:
    raw = read_exports(paths_file)
    return {key: expand(value, raw) for key, value in raw.items()}


def discover_input_files(input_base: Path, process_name: str, input_suffix: str) -> list:
    selected = {}
    process_dir = input_base / process_name
    if process_dir.is_dir():
        for input_file in sorted(process_dir.glob(f"*_{input_suffix}.root")):
            stem = input_file.stem
            suffix_token = f"_{input_suffix}"
            if not stem.endswith(suffix_token):
                continue
            job_label = stem[: -len(suffix_token)]
            if job_label not in selected:
                selected[job_label] = input_file

    return [selected[label] for label in sorted(selected)]


def build_job_block(
    executable: Path,
    logs_dir: Path,
    arguments: str,
    job_label: str,
    request_memory: int = 6000,
    request_disk: int = 4000000,
    max_runtime: int = 21600,
) -> str:
    return "\n".join(
        [
            f"executable = {executable}",
            f"arguments = {arguments}",
            f"output = {logs_dir}/{job_label}.out",
            f"error = {logs_dir}/{job_label}.err",
            f"log = {logs_dir}/{job_label}.log",
            "request_cpus = 1",
            f"request_memory = {request_memory}",
            f"request_disk = {request_disk}",
            f"+MaxRuntime = {max_runtime}",
            "should_transfer_files = NO",
            "queue 1",
            "",
        ]
    )


def collect_stage_jobs(
    processes: list,
    input_base: Path,
    output_base: Path,
    input_suffix: str,
    output_suffix: str,
) -> list:
    jobs = []
    for process_name in processes:
        input_files = discover_input_files(input_base, process_name, input_suffix)
        for input_file in input_files:
            stem = input_file.stem
            job_label = stem[: -len(f"_{input_suffix}")]
            output_file = output_base / process_name / f"{job_label}_{output_suffix}.root"
            jobs.append((process_name, job_label, input_file, output_file))
    return jobs


def write_per_process_submit(
    jobs: list,
    submit_dir: Path,
    logs_dir: Path,
    executable: Path,
    request_memory: int = 6000,
    request_disk: int = 4000000,
    max_runtime: int = 21600,
) -> None:
    dag_procid = os.environ.get("DAG_PROCID", "").strip()
    by_process = {}
    for process_name, job_label, input_file, output_file in jobs:
        by_process.setdefault(process_name, []).append((job_label, input_file, output_file))

    for process_name, process_jobs in sorted(by_process.items()):
        blocks = []
        for job_label, input_file, output_file in process_jobs:
            arguments = f"{input_file} {output_file} {process_name} {job_label}"
            blocks.append(
                build_job_block(
                    executable,
                    logs_dir,
                    arguments,
                    job_label,
                    request_memory=request_memory,
                    request_disk=request_disk,
                    max_runtime=max_runtime,
                )
            )
        if dag_procid:
            submit_path = submit_dir / f"{process_name}_job_{dag_procid}.sub"
        else:
            submit_path = submit_dir / f"{process_name}.sub"
        submit_path.write_text("\n".join(blocks))
        print(f"Wrote {submit_path} with {len(process_jobs)} jobs")


def cleanup_submit_files(submit_dir: Path, processes: list) -> None:
    dag_procid = os.environ.get("DAG_PROCID", "").strip()
    for process_name in processes:
        candidates = [submit_dir / f"{process_name}.sub"]
        if dag_procid:
            candidates.append(submit_dir / f"{process_name}_job_{dag_procid}.sub")
        for submit_path in candidates:
            if submit_path.exists():
                submit_path.unlink()
                print(f"Removed stale submit file {submit_path}")


def write_combined_submit(
    jobs: list,
    submit_path: Path,
    logs_dir: Path,
    executable: Path,
    request_memory: int = 6000,
    request_disk: int = 4000000,
    max_runtime: int = 21600,
) -> None:
    blocks = []
    for process_name, job_label, input_file, output_file in jobs:
        arguments = f"{input_file} {output_file} {process_name} {job_label}"
        blocks.append(
            build_job_block(
                executable,
                logs_dir,
                arguments,
                job_label,
                request_memory=request_memory,
                request_disk=request_disk,
                max_runtime=max_runtime,
            )
        )
    submit_path.write_text("\n".join(blocks))
    print(f"Wrote {submit_path} with {len(jobs)} jobs")


def select_processes(processes: list) -> list:
    dag_process = os.environ.get("DAG_PROCESS", "").strip()
    if not dag_process:
        return processes
    selected = [item for item in processes if item == dag_process]
    if not selected:
        print(f"Skip DAG_PROCESS={dag_process}: not in configured process list")
    return selected


def _procid_allowed(job_dir_name: str) -> bool:
    dag_procid = os.environ.get("DAG_PROCID", "").strip()
    if not dag_procid:
        return True
    return job_dir_name == f"job_{dag_procid}"


def discover_step_files(input_base: Path, process_name: str, extension: str) -> list:
    selected = {}
    process_dir = input_base / process_name
    if process_dir.is_dir():
        for job_dir in sorted(item for item in process_dir.glob("job_*") if item.is_dir()):
            if not _procid_allowed(job_dir.name):
                continue
            for input_file in sorted(job_dir.glob(f"set*.{extension}")):
                key = f"{job_dir.name}/{input_file.stem}"
                if key not in selected:
                    selected[key] = input_file

    return [selected[key] for key in sorted(selected)]


def collect_step_jobs(
    processes: list,
    input_base: Path,
    output_base: Path,
    extension: str = "root",
) -> list:
    jobs = []
    for process_name in select_processes(processes):
        input_files = discover_step_files(input_base, process_name, extension)
        for input_file in input_files:
            job_dir = input_file.parent.name
            set_name = input_file.stem
            job_label = f"{job_dir}_{set_name}"
            output_file = output_base / process_name / job_dir / f"{set_name}.root"
            jobs.append((process_name, job_label, input_file, output_file))
    return jobs


def load_set_manifest(manifest_path: Path) -> list:
    if not manifest_path.is_file():
        raise RuntimeError(f"Set manifest not found: {manifest_path}")

    set_names = []
    for raw in manifest_path.read_text().splitlines():
        item = raw.strip()
        if not item:
            continue
        if not item.startswith("set"):
            raise RuntimeError(f"Invalid set name in manifest {manifest_path}: {item}")
        set_names.append(item)

    if not set_names:
        raise RuntimeError(f"Empty set manifest: {manifest_path}")
    return set_names


def collect_jobs_from_manifest(
    processes: list,
    input_base: Path,
    output_base: Path,
    input_extension: str = "root",
    manifest_base: Optional[Path] = None,
) -> list:
    dag_procid = os.environ.get("DAG_PROCID", "").strip()
    if not dag_procid:
        raise RuntimeError("DAG_PROCID is required for manifest-based job collection")

    jobs = []
    job_dir = f"job_{dag_procid}"
    manifest_root = manifest_base if manifest_base is not None else input_base
    for process_name in select_processes(processes):
        manifest = manifest_root / process_name / job_dir / "set_list.txt"
        set_names = load_set_manifest(manifest)
        for set_name in set_names:
            input_file = input_base / process_name / job_dir / f"{set_name}.{input_extension}"
            job_label = f"{job_dir}_{set_name}"
            output_file = output_base / process_name / job_dir / f"{set_name}.root"
            jobs.append((process_name, job_label, input_file, output_file))

    return jobs
