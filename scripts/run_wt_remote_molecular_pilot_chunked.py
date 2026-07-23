#!/usr/bin/env python3
"""Submit detached 10-shot chunks for one WT_TMP H2-Emulator pilot group."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"
OUT = ROOT / "artifacts/final_public_release/molecular/WT_TMP/remote_pilot"
MANIFEST = OUT / "chunked_job_manifest.json"
GROUPS = ("WT_TMP_G0001", "WT_TMP_G0002", "WT_TMP_G0003", "WT_TMP_G0013")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(payload: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n")


def load() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {
        "schema_version": 1,
        "strategy": "client_side_shot_chunking",
        "backend": "H2-Emulator",
        "noisy_simulation": True,
        "automatic_retry": False,
        "groups": {},
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunk_sizes(total: int, per_job: int) -> list[int]:
    if total <= 0 or per_job <= 0 or total % per_job:
        raise ValueError("total shots must be positive and divisible by shots per job")
    return [per_job] * (total // per_job)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--group", required=True, choices=GROUPS)
    parser.add_argument("--backend", default="H2-Emulator")
    parser.add_argument("--total-shots", type=int, default=100)
    parser.add_argument("--shots-per-job", type=int, default=10)
    parser.add_argument("--optimisation-level", type=int, default=2, choices=(1, 2))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--submit-detached", action="store_true")
    parser.add_argument("--retrieve", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-partnership-access", action="store_true")
    parser.add_argument("--replaces-job")
    return parser.parse_args()


def retrieve(qnx, project, manifest: dict, group: str) -> None:
    record = manifest["groups"].get(group)
    if not record or not record.get("jobs"):
        raise SystemExit("No saved chunk jobs exist for this group.")
    combined: Counter[str] = Counter()
    completed = 0
    for item in record["jobs"]:
        job = qnx.jobs.get(id=item["job_id"], project=project)
        status = qnx.jobs.status(job)
        item["state"] = status.status.value
        if "COMPLETED" not in item["state"].upper() or item.get("counts"):
            continue
        refs = list(qnx.jobs.results(job))
        if len(refs) != 1:
            raise RuntimeError("Each chunk must return exactly one result.")
        counts = refs[0].download_result().get_counts()
        item["counts"] = {str(key): int(value) for key, value in counts.items()}
        item["returned_shots"] = int(sum(counts.values()))
        item["retrieved_utc"] = now()
        save(manifest)
    for item in record["jobs"]:
        if item.get("counts"):
            completed += 1
            combined.update(item["counts"])
    record["completed_chunks"] = completed
    record["combined_counts"] = dict(combined)
    record["total_returned_shots"] = int(sum(combined.values()))
    record["retrieval_complete"] = (
        completed == len(record["jobs"])
        and record["total_returned_shots"] == record["total_shots"]
    )
    record["updated_utc"] = now()
    save(manifest)
    print(json.dumps(record, indent=2))


def main() -> None:
    args = parse_args()
    if args.backend != "H2-Emulator":
        raise SystemExit("Exact H2-Emulator is required; no fallback is allowed.")
    try:
        sizes = chunk_sizes(args.total_shots, args.shots_per_job)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    modes = sum((args.dry_run, args.submit_detached, args.retrieve))
    if modes != 1:
        raise SystemExit(
            "Choose exactly one of --dry-run, --submit-detached, --retrieve."
        )

    path = WT / "regenerated_circuits" / f"{args.group}.json"
    source_meta = {
        "source": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }
    preview = {
        "submission_created": False,
        "backend": args.backend,
        "project": args.project_name,
        "group": args.group,
        "total_shots": args.total_shots,
        "shots_per_job": args.shots_per_job,
        "job_count": len(sizes),
        "noisy_simulation": True,
        "optimisation_level": args.optimisation_level,
        **source_meta,
    }
    if args.dry_run:
        print(json.dumps(preview, indent=2))
        return

    import qnexus as qnx

    qnx.login()
    project = qnx.projects.get(name=args.project_name)
    manifest = load()
    if args.retrieve:
        retrieve(qnx, project, manifest, args.group)
        return
    if not (args.confirm_submit and args.confirm_partnership_access):
        raise SystemExit(
            "Detached submission requires --confirm-submit and "
            "--confirm-partnership-access."
        )
    if manifest["groups"].get(args.group, {}).get("jobs"):
        raise SystemExit("Chunk jobs already exist for this group; retrieve them.")

    from pytket.circuit import Circuit

    circuit = Circuit.from_dict(json.loads(path.read_text()))
    circuit.name = args.group
    config = qnx.models.QuantinuumConfig(
        device_name=args.backend,
        noisy_simulation=True,
        no_opt=False,
        simplify_initial=True,
    )
    uploaded = qnx.circuits.upload(
        circuit=circuit, project=project, name=f"WT_TMP_CHUNKED_{args.group}"
    )
    compiled = list(
        qnx.compile(
            programs=[uploaded],
            backend_config=config,
            name=f"WT_TMP_CHUNKED_COMPILE_{args.group}",
            project=project,
            optimisation_level=args.optimisation_level,
        )
    )
    if len(compiled) != 1:
        raise RuntimeError("Compilation must return exactly one circuit.")
    record = {
        "group_id": args.group,
        **source_meta,
        "total_shots": args.total_shots,
        "shots_per_job": args.shots_per_job,
        "optimisation_level": args.optimisation_level,
        "noisy_simulation": True,
        "replaces_failed_job": args.replaces_job,
        "jobs": [],
        "retrieval_complete": False,
    }
    manifest["groups"][args.group] = record
    save(manifest)
    for index, shots in enumerate(sizes, start=1):
        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=[shots],
            backend_config=config,
            name=f"WT_TMP_{args.group}_H2E_CHUNK_{index:02d}_OF_{len(sizes):02d}",
            project=project,
        )
        record["jobs"].append(
            {
                "chunk": index,
                "job_id": str(job.id),
                "shots": shots,
                "state": "SUBMITTED",
                "submitted_utc": now(),
            }
        )
        save(manifest)  # Persist each accepted ID before submitting the next chunk.
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
