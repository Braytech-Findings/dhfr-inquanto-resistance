#!/usr/bin/env python3
"""Submit one reviewed QASM circuit to one exact Nexus-hosted emulator.

This guarded path has no fallback. QASM execution is circuit evidence, not a
complete molecular energy unless the saved artifact is a reviewed measurement
protocol with its evaluator. Dry-run is the default safe first step.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .audit_core import canonical_system, classify_access_error
    from .nexus_backend import require_nexus_emulator, resolve_backend
    from .test_quantinuum_access import (
        load_nexus,
        project_for,
        resolve_project_selection,
        resolve_user_group,
        wait_and_print,
    )
except ImportError:
    from audit_core import canonical_system, classify_access_error
    from nexus_backend import require_nexus_emulator, resolve_backend
    from test_quantinuum_access import (
        load_nexus,
        project_for,
        resolve_project_selection,
        resolve_user_group,
        wait_and_print,
    )


def save(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run(args: argparse.Namespace) -> None:
    system = canonical_system(args.system)
    project_id, project_name, _ = resolve_project_selection(args)
    group, _ = resolve_user_group(args)
    resolution = resolve_backend(
        args.backend, project_id=project_id, project_name=project_name, user_group=group
    )
    require_nexus_emulator(resolution)
    if args.shots <= 0:
        raise SystemExit("--shots must be positive")
    metadata = {
        "system": system,
        "scientific_role": "qasm_circuit_execution_not_automatically_energy_evidence",
        "backend_resolution": resolution.to_dict(),
        "qasm": str(args.qasm),
        "shots": args.shots,
        "job_created": False,
        "fallback_attempted": False,
    }
    if not args.qasm.is_file():
        raise SystemExit(f"Missing QASM: {args.qasm}")
    if args.dry_run or args.compile_only:
        metadata["operation"] = "compile_only" if args.compile_only else "dry_run"
        save(args.metadata_output, metadata)
        print("No login, upload, compile job, execution job, or credits were used.")
        return
    if not args.confirm_submit:
        raise SystemExit(
            "Remote execution requires --confirm-submit; use --dry-run first."
        )
    qnx, QuantinuumConfig = load_nexus()
    try:
        from pytket.qasm import circuit_from_qasm

        qnx.login()
        project = project_for(qnx, args)
        circuit = circuit_from_qasm(args.qasm)
        config = QuantinuumConfig(device_name=resolution.resolved_backend)
        uploaded = qnx.circuits.upload(
            circuit=circuit, project=project, name=f"{system}-qasm"
        )
        compiled = qnx.compile(
            programs=uploaded,
            backend_config=config,
            project=project,
            name=f"{system}-{resolution.resolved_backend}-compile",
            optimisation_level=0,
            user_group=group,
            timeout=args.timeout,
        )
        # Reuse the identical config object so compile and execution cannot diverge.
        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=args.shots,
            backend_config=config,
            project=project,
            name=f"{system}-{resolution.resolved_backend}-execute",
            user_group=group,
        )
        metadata.update(
            {"operation": "submission", "job_created": True, "job_id": str(job.id)}
        )
        save(args.metadata_output, metadata)
        if args.wait:
            wait_and_print(qnx, job, project, args.timeout)
    except Exception as exc:
        metadata.update(
            {
                "operation": "failure",
                "classification": classify_access_error(exc),
                "project_selected": bool(project_id or project_name),
                "user_group_selected": bool(group),
                "retry_attempted": False,
            }
        )
        save(args.metadata_output, metadata)
        raise SystemExit(
            f"{metadata['classification']}: remote QASM operation failed; no fallback was attempted."
        ) from exc


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--system", required=True)
    result.add_argument("--qasm", type=Path, required=True)
    result.add_argument("--backend", default="H2-Emulator")
    result.add_argument("--shots", type=int, default=10)
    result.add_argument("--project-id")
    result.add_argument("--project-name")
    result.add_argument("--user-group")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--compile-only", action="store_true")
    result.add_argument("--confirm-submit", action="store_true")
    result.add_argument("--wait", action="store_true")
    result.add_argument("--timeout", type=int, default=300)
    result.add_argument(
        "--metadata-output",
        type=Path,
        default=Path("results/quantinuum_access/qasm_operation.json"),
    )
    return result


if __name__ == "__main__":
    run(parser().parse_args())
