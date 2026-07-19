#!/usr/bin/env python3
"""Guarded access-test ladder; discovery is the only default action."""
from __future__ import annotations

import argparse
from pathlib import Path

import qnexus as qnx
from pytket import Circuit
from pytket.extensions.quantinuum import QuantinuumAPIOffline, QuantinuumBackend

ROOT = Path(__file__).resolve().parents[1]


def bell() -> Circuit:
    return Circuit(2, 2).H(0).CX(0, 1).measure_all()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--local-emulator", action="store_true")
    parser.add_argument("--nexus-emulator", action="store_true")
    parser.add_argument("--cloud-emulator", action="store_true")
    parser.add_argument("--hardware-smoke-test", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-hardware", action="store_true")
    parser.add_argument("--shots", type=int, default=10)
    args = parser.parse_args()
    if args.local_emulator:
        backend = QuantinuumBackend("H2-1LE", api_handler=QuantinuumAPIOffline())
        result = backend.run_circuit(backend.get_compiled_circuit(bell(), optimisation_level=0), n_shots=args.shots)
        print({"backend": "Quantinuum H2-1LE local noiseless emulator", "counts": {str(k): int(v) for k, v in result.get_counts().items()}})
        return
    if args.hardware_smoke_test and not (args.confirm_submit and args.confirm_hardware):
        raise SystemExit("Hardware submission requires both --confirm-submit and --confirm-hardware.")
    if args.nexus_emulator or args.cloud_emulator or args.hardware_smoke_test:
        if not args.confirm_submit:
            raise SystemExit("Cloud submission requires --confirm-submit. Use diagnose_quantinuum_access.py first.")
        raise SystemExit("No cloud job was submitted: choose a documented target only after reviewing the access report.")
    devices = qnx.devices.get_all().df()[["backend_name", "device_name", "nexus_hosted"]]
    print(devices.to_string(index=False))


if __name__ == "__main__":
    main()
