#!/usr/bin/env python3
"""Guarded access-test ladder; discovery is the only default action."""
from __future__ import annotations

import argparse
from pathlib import Path

import qnexus as qnx
from pytket import Circuit

try:
    from pytket.extensions.quantinuum import QuantinuumAPIOffline, QuantinuumBackend
except ImportError:  # Keep discovery usable in a public/minimal environment.
    QuantinuumAPIOffline = None
    QuantinuumBackend = None

ROOT = Path(__file__).resolve().parents[1]


def bell() -> Circuit:
    return Circuit(2, 2).H(0).CX(0, 1).measure_all()


def local_backend():
    if QuantinuumBackend is None or QuantinuumAPIOffline is None:
        raise SystemExit(
            "Local H2-1LE test requires pytket-quantinuum in the active environment; "
            "no cloud or hardware request was made."
        )
    return QuantinuumBackend("H2-1LE", api_handler=QuantinuumAPIOffline())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--local-emulator", action="store_true")
    parser.add_argument("--nexus-emulator", action="store_true")
    parser.add_argument("--cloud-emulator", action="store_true")
    parser.add_argument("--hardware-smoke-test", action="store_true")
    parser.add_argument("--syntax-only", action="store_true", help="Validate a Bell circuit locally; never submits.")
    parser.add_argument("--list-jobs", action="store_true", help="Reserved guarded operation; no request is made by default.")
    parser.add_argument("--retrieve-job", action="store_true", help="Requires a job id and performs no submission.")
    parser.add_argument("--target", default="", help="Explicit target name for a guarded hosted request.")
    parser.add_argument("--project-id", default="", help="Explicit Nexus project identifier.")
    parser.add_argument("--user-group", default="", help="Optional entitlement group; never changes settings.")
    parser.add_argument("--max-hqc", type=float, default=0.0, help="Maximum approved HQC cost; zero blocks hosted execution.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--output-dir", default="results/quantinuum_access")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-hardware", action="store_true")
    parser.add_argument("--shots", type=int, default=10)
    args = parser.parse_args()
    if args.local_emulator:
        backend = local_backend()
        result = backend.run_circuit(backend.get_compiled_circuit(bell(), optimisation_level=0), n_shots=args.shots)
        print({"backend": "Quantinuum H2-1LE local noiseless emulator", "counts": {str(k): int(v) for k, v in result.get_counts().items()}})
        return
    if args.syntax_only:
        compiled = local_backend().get_compiled_circuit(bell(), optimisation_level=0)
        print({"mode": "syntax-only local validation", "commands": compiled.n_commands(), "submitted": False})
        return
    if args.list_jobs or args.retrieve_job:
        if args.retrieve_job and not args.job_id:
            raise SystemExit("--retrieve-job requires --job-id; no job was submitted.")
        raise SystemExit("Hosted job retrieval is intentionally unavailable until the documented qnexus job API is verified; no request was made.")
    if args.hardware_smoke_test and not (args.confirm_submit and args.confirm_hardware):
        raise SystemExit("Hardware submission requires both --confirm-submit and --confirm-hardware.")
    if args.nexus_emulator or args.cloud_emulator or args.hardware_smoke_test:
        if not args.confirm_submit or args.max_hqc <= 0:
            raise SystemExit("Hosted execution requires --confirm-submit and a positive --max-hqc. No job was submitted.")
        raise SystemExit("No cloud job was submitted: documented qnexus execution API and entitlement must be reviewed first.")
    devices = qnx.devices.get_all().df()[["backend_name", "device_name", "nexus_hosted"]]
    print(devices.to_string(index=False))


if __name__ == "__main__":
    main()
