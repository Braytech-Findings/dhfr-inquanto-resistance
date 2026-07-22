#!/usr/bin/env python3
"""Verify the optional IonQ/Qiskit toolchain without submitting a job.

This script is intentionally read-only:
- it never calls backend.run();
- it never prints an API key;
- it can be used before an IonQ account or credits are available.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def two_qubit_gate_count(circuit: Any) -> int:
    total = 0
    for instruction in circuit.data:
        operation = instruction.operation
        if operation.name not in {"measure", "barrier"} and operation.num_qubits == 2:
            total += 1
    return total


def two_qubit_depth(circuit: Any) -> int:
    try:
        return int(
            circuit.depth(
                filter_function=lambda item: (
                    item.operation.name not in {"measure", "barrier"}
                    and item.operation.num_qubits == 2
                )
            )
        )
    except (AttributeError, TypeError):
        # Older Qiskit fallback. The full circuit depth is conservative.
        return int(circuit.depth())


def circuit_metrics(circuit: Any) -> dict[str, Any]:
    return {
        "name": circuit.name,
        "qubits": circuit.num_qubits,
        "classical_bits": circuit.num_clbits,
        "depth": int(circuit.depth()),
        "two_qubit_depth": two_qubit_depth(circuit),
        "gate_count": int(circuit.size()),
        "two_qubit_gate_count": two_qubit_gate_count(circuit),
        "operations": {str(key): int(value) for key, value in circuit.count_ops().items()},
    }


def build_examples() -> list[Any]:
    from qiskit import QuantumCircuit

    bell = QuantumCircuit(2, name="ionq_preflight_bell")
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()

    ghz = QuantumCircuit(3, name="ionq_preflight_ghz")
    ghz.h(0)
    ghz.cx(0, 1)
    ghz.cx(0, 2)
    ghz.measure_all()
    return [bell, ghz]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend",
        default="simulator",
        help="IonQ backend name used only for local transpilation (default: simulator).",
    )
    parser.add_argument(
        "--optimization-level",
        type=int,
        choices=(0, 1),
        default=1,
        help="Use 0 or 1 before IonQ's own compiler.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        from qiskit import transpile
        from qiskit_ionq import IonQProvider
    except ImportError as exc:
        raise SystemExit(
            "IonQ tooling is not installed. Run: "
            "conda env update -f environment.yml --prune"
        ) from exc

    key_present = bool(os.getenv("IONQ_API_KEY"))
    provider = IonQProvider(os.getenv("IONQ_API_KEY")) if key_present else IonQProvider()
    backend = provider.get_backend(args.backend)
    examples = build_examples()
    compiled = transpile(
        examples,
        backend=backend,
        optimization_level=args.optimization_level,
    )
    if not isinstance(compiled, list):
        compiled = [compiled]

    payload = {
        "status": "ready",
        "submission_performed": False,
        "api_key_configured": key_present,
        "backend_used_for_local_transpilation": args.backend,
        "optimization_level": args.optimization_level,
        "packages": {
            "python": sys.version.split()[0],
            "qiskit": package_version("qiskit"),
            "qiskit-ionq": package_version("qiskit-ionq"),
        },
        "advertised_backends": [backend.name for backend in provider.backends()],
        "compiled_examples": [circuit_metrics(circuit) for circuit in compiled],
        "warning": (
            "These are local Qiskit preflight metrics, not final system-specific "
            "IonQ compiler or QPU resource estimates."
        ),
    }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
