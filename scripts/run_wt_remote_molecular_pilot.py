#!/usr/bin/env python3
"""Submit or retrieve the approved four-group WT_TMP H2-Emulator pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pytket.circuit import Circuit


ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"
OUT = ROOT / "artifacts/final_public_release/molecular/WT_TMP/remote_pilot"
MANIFEST = OUT / "job_manifest.json"
GROUPS = ("WT_TMP_G0001", "WT_TMP_G0002", "WT_TMP_G0003", "WT_TMP_G0013")


def write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quota_snapshot(qnx) -> list[dict[str, object]]:
    frame = qnx.quotas.get_all().df()
    allowed = ("name", "description", "usage", "quota")
    return [
        {key: row.get(key) for key in allowed}
        for row in frame.to_dict(orient="records")
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--backend", default="H2-Emulator")
    parser.add_argument("--shots", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--cost-approved", action="store_true")
    parser.add_argument("--retrieve-job")
    parser.add_argument("--adopt-manual-retry-job")
    parser.add_argument("--replaces-job")
    args = parser.parse_args()
    if args.backend != "H2-Emulator":
        raise SystemExit("This approved pilot requires exact backend H2-Emulator.")
    if args.shots != 100:
        raise SystemExit("This approval covers exactly 100 shots per circuit.")
    if args.retrieve_job and args.adopt_manual_retry_job:
        raise SystemExit("Choose saved-job retrieval or manual-retry adoption.")
    retrieval_job = args.retrieve_job or args.adopt_manual_retry_job
    if not retrieval_job and not (args.confirm_submit and args.cost_approved):
        raise SystemExit("Submission requires --confirm-submit and --cost-approved.")

    import qnexus as qnx

    qnx.login()
    project = qnx.projects.get(name=args.project_name)
    config = qnx.models.QuantinuumConfig(device_name=args.backend)
    circuits = []
    circuit_metadata = []
    for group_id in GROUPS:
        path = WT / "regenerated_circuits" / f"{group_id}.json"
        circuit = Circuit.from_dict(json.loads(path.read_text()))
        circuit.name = group_id
        circuits.append(circuit)
        circuit_metadata.append(
            {
                "group_id": group_id,
                "source": str(path.relative_to(ROOT)),
                "sha256": checksum(path),
                "qubits": circuit.n_qubits,
                "bits": circuit.n_bits,
                "gates": circuit.n_gates,
                "depth": circuit.depth(),
            }
        )

    if retrieval_job:
        if not MANIFEST.exists():
            raise SystemExit("Saved manifest is required for retrieval-only resume.")
        payload = json.loads(MANIFEST.read_text())
        if args.adopt_manual_retry_job:
            if not args.replaces_job or payload.get("job_id") != args.replaces_job:
                raise SystemExit(
                    "--replaces-job must exactly match the previously saved job ID."
                )
            payload.setdefault("job_history", []).append(
                {
                    "job_id": payload["job_id"],
                    "state": payload.get("state"),
                    "failure": payload.get("failure"),
                }
            )
            payload["job_id"] = args.adopt_manual_retry_job
            payload["state"] = "MANUAL_RETRY_REPORTED"
            payload["manual_retry"] = {
                "replaces_job": args.replaces_job,
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
                "submitted_by_repository_tooling": False,
            }
            payload["results"] = []
            payload["retrieval_complete"] = False
            write(MANIFEST, payload)
        elif payload.get("job_id") != args.retrieve_job:
            raise SystemExit("Requested job ID does not match the saved manifest.")
        job = qnx.jobs.get(id=retrieval_job, project=project)
    else:
        if MANIFEST.exists() and json.loads(MANIFEST.read_text()).get("job_id"):
            raise SystemExit("A saved pilot job already exists; retrieve it instead.")
        quota_before = quota_snapshot(qnx)
        refs = [
            qnx.circuits.upload(
                circuit=circuit,
                project=project,
                name=f"WT_TMP_REMOTE_PILOT_{circuit.name}",
            )
            for circuit in circuits
        ]
        compiled = list(
            qnx.compile(
                programs=refs,
                backend_config=config,
                name="WT_TMP_REMOTE_PILOT_COMPILE_H2_EMULATOR",
                project=project,
                optimisation_level=0,
            )
        )
        if len(compiled) != len(circuits):
            raise RuntimeError("Nexus compilation changed the four-circuit count.")
        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=[args.shots] * len(compiled),
            backend_config=config,
            name="WT_TMP_REGENERATED_PROTOCOL_REMOTE_PILOT_H2E_S100",
            project=project,
        )
        payload = {
            "evidence_label": "REGENERATED_PROTOCOL_REMOTE_PILOT",
            "scope_label": "PARTIAL_ESTIMATOR_VALIDATION_NOT_A_MOLECULAR_ENERGY",
            "hardware_label": "NOT_PHYSICAL_HARDWARE",
            "requested_backend": args.backend,
            "resolved_backend": args.backend,
            "project": args.project_name,
            "user_group": "Nexus default group",
            "shots_per_circuit": args.shots,
            "circuit_count": len(circuits),
            "total_requested_circuit_shots": args.shots * len(circuits),
            "circuit_metadata": circuit_metadata,
            "job_id": str(job.id),
            "submitted_utc": datetime.now(timezone.utc).isoformat(),
            "state": "SUBMITTED",
            "cost_approval": {
                "approved_by_researcher": True,
                "expected_monetary_cost_usd": 0,
                "expected_hqc_cost": 0,
                "expected_resource": "institutional Nexus simulation-time quota",
                "paid_overage_allowed": False,
            },
            "quota_before": quota_before,
            "results": [],
        }
        write(MANIFEST, payload)  # Persist the ID before polling.

    try:
        status = qnx.jobs.wait_for(job, timeout=args.timeout)
    except Exception as exc:
        terminal = qnx.jobs.status(job)
        payload["state"] = terminal.status.value
        payload["reported_cost"] = terminal.cost
        payload["failure"] = {
            "classification": "remote_execution_timeout",
            "exception_type": type(exc).__name__,
            "detail": str(exc),
            "chemistry_failure": False,
            "automatic_resubmission_allowed": False,
        }
        payload["quota_after"] = quota_snapshot(qnx)
        payload["retrieval_complete"] = False
        payload["updated_utc"] = datetime.now(timezone.utc).isoformat()
        write(MANIFEST, payload)
        raise SystemExit(f"Saved terminal pilot failure: {payload['state']}") from exc
    payload["state"] = status.status.value
    payload["reported_cost"] = status.cost
    write(MANIFEST, payload)
    if status.cost not in (None, 0, 0.0):
        raise SystemExit(f"Unexpected nonzero reported cost: {status.cost}")
    if "COMPLETED" not in payload["state"].upper():
        raise SystemExit(f"Pilot did not complete: {payload['state']}")
    result_refs = list(qnx.jobs.results(job))
    if len(result_refs) != len(circuits):
        raise RuntimeError("Nexus returned an unexpected result count.")
    raw_results = []
    for position, (group_id, result_ref) in enumerate(
        zip(GROUPS, result_refs, strict=True)
    ):
        counts = result_ref.download_result().get_counts()
        raw_results.append(
            {
                "position": position,
                "group_id": group_id,
                "counts": {str(key): int(value) for key, value in counts.items()},
                "returned_shots": int(sum(counts.values())),
            }
        )
    write(OUT / "raw_results.json", raw_results)
    payload["results"] = [
        {
            "position": row["position"],
            "group_id": row["group_id"],
            "returned_shots": row["returned_shots"],
        }
        for row in raw_results
    ]
    payload["total_returned_circuit_shots"] = sum(
        row["returned_shots"] for row in raw_results
    )
    payload["quota_after"] = quota_snapshot(qnx)
    payload["retrieved_utc"] = datetime.now(timezone.utc).isoformat()
    payload["retrieval_complete"] = True
    write(MANIFEST, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
