#!/usr/bin/env python3
"""Compile and sample saved QASM on the local noiseless H2-1LE emulator.

Input is one approved system's QASM file. Output is a local JSON counts file.
No login, remote request, or paid job occurs. Counts validate a circuit path;
they are not automatically a molecular energy or physical-hardware result.
Example: ``python scripts/run_local_h2.py --system WT_TMP --shots 100``.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pytket import Circuit
from pytket.qasm import circuit_from_qasm
from pytket.extensions.quantinuum import (
    QuantinuumAPIOffline,
    QuantinuumBackend,
)

try:
    from .audit_core import backend_metadata, canonical_system, total_shots
except ImportError:  # Support direct execution from the repository root.
    from audit_core import backend_metadata, canonical_system, total_shots


def outcome_to_string(outcome) -> str:
    try:
        return "".join(str(int(bit)) for bit in outcome)
    except TypeError:
        return str(outcome)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", required=True, help="Approved molecular system ID.")
    parser.add_argument(
        "--shots", type=int, default=100, help="Positive local samples."
    )
    parser.add_argument(
        "--recompile", action="store_true", help="Ignore the saved local compilation."
    )
    args = parser.parse_args()
    try:
        args.system = canonical_system(args.system)
        total_shots(1, args.shots)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))

    root = Path(__file__).resolve().parents[1]

    qasm_path = root / "data" / "processed" / f"{args.system}_circuit.qasm"

    compiled_path = root / "data" / "processed" / f"{args.system}_H2-1LE_compiled.json"

    results_dir = root / "data" / "results" / "local_h2"

    results_dir.mkdir(parents=True, exist_ok=True)

    if not qasm_path.exists():
        raise SystemExit(f"❌ Missing QASM file: {qasm_path}")

    print(f"📥 Loading {qasm_path}", flush=True)

    circuit = circuit_from_qasm(
        qasm_path,
        maxwidth=4000,
    )

    print(
        f"   Original circuit: "
        f"{circuit.n_qubits} qubits, "
        f"{circuit.n_bits} bits, "
        f"{len(circuit.get_commands())} commands",
        flush=True,
    )

    added_measurements = False

    if circuit.n_bits == 0:
        circuit.measure_all()
        added_measurements = True
        print(
            "ℹ️ Added final Z-basis measurements for pipeline validation.",
            flush=True,
        )

    backend = QuantinuumBackend(
        device_name="H2-1LE",
        api_handler=QuantinuumAPIOffline(),
    )

    if compiled_path.exists() and not args.recompile:
        print(
            f"♻️ Loading cached compiled circuit: {compiled_path}",
            flush=True,
        )

        compiled = Circuit.from_dict(json.loads(compiled_path.read_text()))

    else:
        print(
            "🔧 Compiling locally for H2-1LE at optimization level 0...",
            flush=True,
        )

        compile_start = time.time()

        compiled = backend.get_compiled_circuit(
            circuit,
            optimisation_level=0,
        )

        compile_seconds = time.time() - compile_start

        compiled_path.write_text(json.dumps(compiled.to_dict()))

        print(
            f"✅ Compilation finished in {compile_seconds:.1f} seconds.",
            flush=True,
        )

        print(
            f"💾 Saved compiled circuit: {compiled_path}",
            flush=True,
        )

    if not backend.valid_circuit(compiled):
        raise SystemExit("❌ Compiled circuit is not valid for H2-1LE.")

    print(
        f"   Compiled circuit: "
        f"depth {compiled.depth()}, "
        f"{len(compiled.get_commands())} commands",
        flush=True,
    )

    print(
        f"🚀 Running {args.shots} local shot(s)...",
        flush=True,
    )

    run_start = time.time()

    result = backend.run_circuit(
        compiled,
        n_shots=args.shots,
    )

    run_seconds = time.time() - run_start
    counts = result.get_counts()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output_path = results_dir / (
        f"{args.system}_H2-1LE_{args.shots}shots_{timestamp}.json"
    )

    backend = backend_metadata("H2-1LE")
    payload = {
        "system": args.system,
        "backend": backend["label"],
        "backend_metadata": backend,
        "local": True,
        "noiseless": True,
        "shots": args.shots,
        "total_shots": total_shots(1, args.shots),
        "added_z_basis_measurements": added_measurements,
        "qasm_path": str(qasm_path),
        "compiled_path": str(compiled_path),
        "n_qubits": compiled.n_qubits,
        "n_bits": compiled.n_bits,
        "depth": compiled.depth(),
        "n_commands": len(compiled.get_commands()),
        "runtime_seconds": run_seconds,
        "counts": {
            outcome_to_string(outcome): int(count) for outcome, count in counts.items()
        },
    }

    output_path.write_text(json.dumps(payload, indent=2))

    print(
        f"✅ Local execution finished in {run_seconds:.1f} seconds.",
        flush=True,
    )

    print(
        f"💾 Results saved to {output_path}",
        flush=True,
    )

    print("Counts:", flush=True)

    for outcome, count in counts.most_common(20):
        print(
            f"   {outcome_to_string(outcome)}: {count}",
            flush=True,
        )


if __name__ == "__main__":
    main()
