#!/usr/bin/env python3
"""Submit and retrieve one four-circuit Nexus batch pilot."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/final_validation/quantinuum/multicircuit_pilot.json"


def circuits():
    from pytket.circuit import Circuit

    bell_z = Circuit(2, 2, name="bell_z").H(0).CX(0, 1).measure_all()
    bell_x = Circuit(2, 2, name="bell_x").H(0).CX(0, 1).H(0).H(1).measure_all()
    bell_y = (
        Circuit(2, 2, name="bell_y").H(0).CX(0, 1).Sdg(0).H(0).Sdg(1).H(1).measure_all()
    )
    product_01 = Circuit(2, 2, name="product_01").X(0).measure_all()
    return [bell_z, bell_x, bell_y, product_01]


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--backend", default="H2-Emulator")
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--retrieve-job")
    args = parser.parse_args()
    if not args.retrieve_job and not args.confirm_submit:
        raise SystemExit("Remote batch submission requires --confirm-submit.")
    if args.backend not in {"H2-Emulator", "H1-Emulator"}:
        raise SystemExit("Pilot backend must be an exact maintained Nexus emulator.")

    import qnexus as qnx

    qnx.login()
    project = qnx.projects.get(name=args.project_name)
    config = qnx.models.QuantinuumConfig(device_name=args.backend)
    logical = circuits()
    if args.retrieve_job:
        if not args.output.exists():
            raise SystemExit("Saved pilot manifest is required for retrieval.")
        payload = json.loads(args.output.read_text())
        if payload.get("job_id") != args.retrieve_job:
            raise SystemExit("Requested job does not match the saved pilot manifest.")
        job = qnx.jobs.get(id=args.retrieve_job, project=project)
    else:
        refs = [
            qnx.circuits.upload(circuit=item, project=project, name=item.name)
            for item in logical
        ]
        compiled = list(
            qnx.compile(
                programs=refs,
                backend_config=config,
                name="DHFR_MULTICIRCUIT_PILOT_COMPILE",
                project=project,
                optimisation_level=0,
            )
        )
        if len(compiled) != len(logical):
            raise RuntimeError("Nexus compilation dropped or added circuits")
        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=[args.shots] * len(compiled),
            backend_config=config,
            name="DHFR_MULTICIRCUIT_PILOT_H2E_S10",
            project=project,
        )
        payload = {
            "label": "SMOKE_TEST_ONLY",
            "requested_backend": args.backend,
            "resolved_backend": args.backend,
            "project": args.project_name,
            "user_group": "Nexus default group",
            "circuit_names": [item.name for item in logical],
            "shots_per_circuit": args.shots,
            "job_id": str(job.id),
            "submitted_utc": datetime.now(timezone.utc).isoformat(),
            "state": "SUBMITTED",
            "results": [],
        }
        write(args.output, payload)  # Persist before waiting.
    status = qnx.jobs.wait_for(job, timeout=args.timeout)
    payload["state"] = status.status.value
    payload["reported_cost"] = status.cost
    write(args.output, payload)
    if "COMPLETED" not in payload["state"].upper():
        raise SystemExit(f"Batch did not complete: {payload['state']}")
    result_refs = list(qnx.jobs.results(job))
    if len(result_refs) != len(logical):
        raise RuntimeError("Nexus returned an unexpected result count")
    payload["results"] = []
    for position, (name, result_ref) in enumerate(
        zip(payload["circuit_names"], result_refs, strict=True)
    ):
        counts = result_ref.download_result().get_counts()
        payload["results"].append(
            {
                "position": position,
                "circuit_name": name,
                "counts": {str(key): int(value) for key, value in counts.items()},
                "returned_shots": int(sum(counts.values())),
            }
        )
    payload["retrieved_utc"] = datetime.now(timezone.utc).isoformat()
    payload["retrieval_complete"] = True
    write(args.output, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
