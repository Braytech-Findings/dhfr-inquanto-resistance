#!/usr/bin/env python3
"""Run one WT_TMP pilot group per resumable H2-Emulator job.

This avoids making all four pilot results depend on one long provider job. It
never retries automatically and never submits during retrieval or dry-run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"
OUT = ROOT / "artifacts/final_public_release/molecular/WT_TMP/remote_pilot"
MANIFEST = OUT / "sharded_job_manifest.json"
GROUPS = ("WT_TMP_G0001", "WT_TMP_G0002", "WT_TMP_G0003", "WT_TMP_G0013")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write(payload: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n")


def read_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {
        "schema_version": 1,
        "strategy": "one_measurement_group_per_job",
        "backend": "H2-Emulator",
        "shots_per_circuit": 100,
        "automatic_retry": False,
        "groups": {},
    }


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_new_submission_slot(record: dict | None, replace_job: str | None) -> None:
    if not record or not record.get("job_id"):
        if replace_job:
            raise SystemExit(
                "--replace-terminal-job was given, but no saved job exists."
            )
        return
    saved_job = str(record["job_id"])
    state = str(record.get("state", "UNKNOWN")).upper()
    terminal = state in {"ERROR", "FAILED", "CANCELLED", "CANCELED"}
    if not (terminal and replace_job == saved_job):
        raise SystemExit(
            f"Group already has job {saved_job} in state {state}; retrieve it instead. "
            "A terminal job can be replaced only by passing its exact ID with "
            "--replace-terminal-job."
        )


def classify_wait_failure(state: str, exc: Exception) -> str:
    normalized = state.upper()
    if normalized not in {"ERROR", "FAILED", "CANCELLED", "CANCELED"}:
        return "client_wait_timeout_job_still_active"
    if isinstance(exc, TimeoutError):
        return "remote_execution_timeout"
    return "remote_execution_failure"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--group", required=True, choices=GROUPS)
    parser.add_argument("--backend", default="H2-Emulator")
    parser.add_argument("--shots", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--optimisation-level", type=int, default=2, choices=(1, 2))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-partnership-access", action="store_true")
    parser.add_argument("--retrieve-job")
    parser.add_argument("--replace-terminal-job")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.backend != "H2-Emulator":
        raise SystemExit("This pilot requires exact backend H2-Emulator.")
    if args.shots != 100:
        raise SystemExit("This pilot is fixed at exactly 100 shots per group.")
    if args.retrieve_job and args.dry_run:
        raise SystemExit("Choose retrieval or dry-run, not both.")

    path = WT / "regenerated_circuits" / f"{args.group}.json"
    source = json.loads(path.read_text())
    source_metadata = {
        "group_id": args.group,
        "source": str(path.relative_to(ROOT)),
        "sha256": checksum(path),
        "qubits": len(source.get("qubits", [])),
        "bits": len(source.get("bits", [])),
    }
    manifest = read_manifest()
    record = manifest["groups"].get(args.group)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "submission_created": False,
                    "backend": args.backend,
                    "project": args.project_name,
                    "strategy": manifest["strategy"],
                    "shots": args.shots,
                    "optimisation_level": args.optimisation_level,
                    "source": source_metadata,
                },
                indent=2,
            )
        )
        return

    import qnexus as qnx

    qnx.login()
    project = qnx.projects.get(name=args.project_name)

    if args.retrieve_job:
        if not record or str(record.get("job_id")) != args.retrieve_job:
            raise SystemExit("Retrieval job ID must match this group's saved manifest.")
        job = qnx.jobs.get(id=args.retrieve_job, project=project)
    else:
        if not (args.confirm_submit and args.confirm_partnership_access):
            raise SystemExit(
                "Submission requires --confirm-submit and --confirm-partnership-access."
            )
        require_new_submission_slot(record, args.replace_terminal_job)
        from pytket.circuit import Circuit

        circuit = Circuit.from_dict(source)
        circuit.name = args.group
        config = qnx.models.QuantinuumConfig(device_name=args.backend)
        uploaded = qnx.circuits.upload(
            circuit=circuit,
            project=project,
            name=f"WT_TMP_SHARDED_{args.group}",
        )
        compiled = list(
            qnx.compile(
                programs=[uploaded],
                backend_config=config,
                name=f"WT_TMP_SHARDED_COMPILE_{args.group}",
                project=project,
                optimisation_level=args.optimisation_level,
            )
        )
        if len(compiled) != 1:
            raise RuntimeError("Compilation must return exactly one program.")
        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=[args.shots],
            backend_config=config,
            name=f"WT_TMP_SHARDED_{args.group}_H2E_S100",
            project=project,
        )
        record = {
            **source_metadata,
            "job_id": str(job.id),
            "state": "SUBMITTED",
            "submitted_utc": utc_now(),
            "optimisation_level": args.optimisation_level,
            "shots": args.shots,
            "replacement_for": args.replace_terminal_job,
            "result": None,
        }
        manifest["groups"][args.group] = record
        write(manifest)  # Save the only job ID before any polling.

    try:
        status = qnx.jobs.wait_for(job, timeout=args.timeout)
    except Exception as exc:
        terminal = qnx.jobs.status(job)
        record["state"] = terminal.status.value
        record["failure"] = {
            "classification": classify_wait_failure(record["state"], exc),
            "exception_type": type(exc).__name__,
            "detail": str(exc),
            "automatic_retry": False,
        }
        record["updated_utc"] = utc_now()
        write(manifest)
        raise SystemExit(f"Saved failure for {args.group}: {record['state']}") from exc

    record["state"] = status.status.value
    record["updated_utc"] = utc_now()
    if "COMPLETED" not in record["state"].upper():
        write(manifest)
        raise SystemExit(f"Group did not complete: {record['state']}")
    refs = list(qnx.jobs.results(job))
    if len(refs) != 1:
        raise RuntimeError("A sharded job must return exactly one result.")
    counts = refs[0].download_result().get_counts()
    record["result"] = {
        "counts": {str(key): int(value) for key, value in counts.items()},
        "returned_shots": int(sum(counts.values())),
    }
    record["retrieved_utc"] = utc_now()
    write(manifest)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
