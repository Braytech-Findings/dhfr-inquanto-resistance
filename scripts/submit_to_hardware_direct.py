#!/usr/bin/env python3
"""Guarded UCCSD state-preparation smoke test for Nexus.

This is *not* a molecular-energy calculation.  It submits one parameterized
state-preparation circuit only; a complete VQE energy requires every Hamiltonian
measurement circuit and the corresponding Pauli reconstruction.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="WT_TMP")
    parser.add_argument("--backend", default="H2-1SC")
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--project-id", default="ee45224b-05fb-4520-9a0e-45b5be2528c3")
    parser.add_argument("--user-group")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-hardware", action="store_true")
    parser.add_argument("--max-hqc", type=float, default=0.0)
    args = parser.parse_args()
    print("STATE-CIRCUIT SMOKE TEST ONLY — this cannot calculate molecular energy.")
    if args.backend.upper() in {"H2-1E", "H2-2E", "H2-1", "H2-2"} and not args.confirm_hardware:
        raise SystemExit("Hardware/high-performance emulator requires --confirm-hardware.")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "test_quantinuum_access.py"),
        "--nexus-emulator",
        "--backend", args.backend,
        "--shots", str(args.shots),
        "--project-id", args.project_id,
        "--max-hqc", str(args.max_hqc),
    ]
    if args.user_group:
        command.extend(["--user-group", args.user_group])
    if args.dry_run:
        command.append("--dry-run")
    if args.confirm_submit:
        command.append("--confirm-submit")
    if args.confirm_hardware:
        command.append("--confirm-hardware")
    raise SystemExit(subprocess.call(command, cwd=ROOT))


if __name__ == "__main__":
    main()
