#!/usr/bin/env python3
"""Guarded Nexus Bell-circuit test ladder; discovery is the default action.

H2-1SC is a syntax checker: any result is artificial and scientifically
unusable. H2-Emulator needs simulation quota. Visible/online targets do not
prove execution entitlement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

import qnexus as qnx
from pytket import Circuit
from qnexus import QuantinuumConfig

HARDWARE_NAMES = {"H2-1E", "H2-2E", "H2-1", "H2-2", "H1-1"}
DEFAULT_PROJECT = "ee45224b-05fb-4520-9a0e-45b5be2528c3"


def bell() -> Circuit:
    return Circuit(2, 2).H(0).CX(0, 1).measure_all()


def name(label: str) -> str:
    return f"dhfr-bell-{label}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def explain_error(exc: Exception) -> str:
    text = str(exc).lower()
    if "code 14" in text or "access" in text or "entitlement" in text:
        return "Access code 14 / entitlement failure: ask the organization administrator or Quantinuum support about the required user group and machine entitlement."
    if "quota" in text or "depleted" in text:
        return "Simulation quota is unavailable or depleted; H2-Emulator cannot execute until the organization allocation is restored."
    if "group" in text:
        return "A required/default user group may be missing. Supply --user-group only after the administrator confirms its name; do not guess."
    if "auth" in text or "login" in text or "token" in text:
        return "Authentication appears expired; rerun through the normal qnexus browser login flow."
    return f"Nexus operation failed: {type(exc).__name__}: {exc}"


def project_for(args):
    return qnx.projects.get(id=args.project_id) if args.project_id else qnx.projects.get(name=args.project_name)


def wait_and_print(job, project, timeout: int) -> None:
    status = qnx.jobs.wait_for(job, timeout=timeout)
    print(f"Status: {status.status.value}; cost: {status.cost}")
    print(f"Nexus job URL: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}")
    if status.status.value != "COMPLETED":
        raise SystemExit("Job did not complete; see the Nexus job URL.")
    references = qnx.jobs.results(job)
    result = references[0].download_result()
    print("Counts:", {str(key): int(value) for key, value in result.get_counts().items()})


def hosted_bell(args) -> None:
    backend = args.backend.upper()
    if backend in HARDWARE_NAMES and not args.confirm_hardware:
        raise SystemExit("H2-1E/H2-2E or physical hardware needs --confirm-hardware as well as --confirm-submit.")
    if backend not in {"H2-1SC", "H2-EMULATOR", "H2-1E", "H2-2E", "H2-1", "H2-2"}:
        raise SystemExit(f"Unsupported guarded target {args.backend!r}; use a visible Quantinuum target.")
    if args.shots <= 0:
        raise SystemExit("--shots must be positive.")
    if args.max_hqc < 0:
        raise SystemExit("--max-hqc must be non-negative.")
    if args.dry_run:
        print("DRY RUN: Bell circuit width=2, gates=2, depth=2. No login, upload, compile, cost request, or execution occurred.")
        return
    if not args.confirm_submit:
        raise SystemExit("Hosted execution requires --confirm-submit. Use --dry-run first.")
    try:
        qnx.login()
        project = project_for(args)
        circuit = bell()
        stamp = name(backend.lower())
        print(f"Backend: {args.backend}; width={circuit.n_qubits}; gates={circuit.n_gates}; depth={circuit.depth()}")
        uploaded = qnx.circuits.upload(circuit=circuit, project=project, name=f"{stamp}-circuit")
        config = QuantinuumConfig(device_name=args.backend)
        compiled = qnx.compile(programs=uploaded, backend_config=config, project=project, name=f"{stamp}-compile", optimisation_level=0, user_group=args.user_group, timeout=args.timeout)
        compiled_circuit = compiled[0].download_circuit()
        print(f"Compiled width={compiled_circuit.n_qubits}; gates={compiled_circuit.n_gates}; depth={compiled_circuit.depth()}")
        estimated = qnx.circuits.cost(compiled, args.shots, config, project=project, syntax_checker="H2-1SC" if backend == "H2-1SC" else None)
        print(f"Estimated cost: {estimated} HQC (max allowed: {args.max_hqc})")
        if estimated is None:
            raise SystemExit("Nexus did not return a cost estimate; refusing execution.")
        if estimated > args.max_hqc:
            raise SystemExit("Estimated cost exceeds --max-hqc; refusing execution.")
        job = qnx.start_execute_job(programs=compiled, n_shots=args.shots, backend_config=config, project=project, name=f"{stamp}-execute", user_group=args.user_group, max_cost=args.max_hqc)
        print(f"Submitted Nexus job {job.id}")
        print(f"Nexus job URL: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}")
        if backend == "H2-1SC":
            print("H2-1SC output is an artificial syntax-checker result and is scientifically unusable.")
        if args.wait:
            wait_and_print(job, project, args.timeout)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(explain_error(exc)) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--nexus-emulator", action="store_true")
    modes.add_argument("--local-emulator", action="store_true")
    parser.add_argument("--backend", default="H2-1SC")
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT)
    parser.add_argument("--project-name", default="dhfr-h2-hardware")
    parser.add_argument("--user-group")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-hardware", action="store_true")
    parser.add_argument("--max-hqc", type=float, default=0.0)
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.nexus_emulator:
        hosted_bell(args)
        return
    if args.local_emulator:
        raise SystemExit("Use scripts/run_h2_smoke.py for the existing local test; this script guards Nexus-hosted execution.")
    devices = qnx.devices.get_all().df()[["backend_name", "device_name", "nexus_hosted"]]
    print(devices.to_string(index=False))


if __name__ == "__main__":
    main()
