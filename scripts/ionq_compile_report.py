#!/usr/bin/env python3
"""Create a no-submit IonQ-oriented compilation report for Qiskit circuits.

Accepted inputs:
- OpenQASM 2 files: .qasm
- OpenQASM 3 files: .qasm3
- Qiskit QPY bundles: .qpy

The script performs local transpilation only. It never submits a circuit.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from pathlib import Path
from typing import Any


def load_circuits(path: Path) -> list[Any]:
    suffix = path.suffix.lower()
    if suffix == ".qpy":
        from qiskit import qpy

        with path.open("rb") as handle:
            return list(qpy.load(handle))
    if suffix == ".qasm":
        from qiskit import QuantumCircuit

        return [QuantumCircuit.from_qasm_file(str(path))]
    if suffix == ".qasm3":
        from qiskit import qasm3

        return [qasm3.load(str(path))]
    raise ValueError(f"Unsupported circuit file: {path}")


def two_qubit_gate_count(circuit: Any) -> int:
    return sum(
        instruction.operation.name not in {"measure", "barrier"}
        and instruction.operation.num_qubits == 2
        for instruction in circuit.data
    )


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
        return int(circuit.depth())


def metric_row(source: Path, index: int, circuit: Any) -> dict[str, Any]:
    return {
        "source": str(source),
        "circuit_index": index,
        "name": circuit.name or f"circuit_{index}",
        "qubits": int(circuit.num_qubits),
        "classical_bits": int(circuit.num_clbits),
        "depth": int(circuit.depth()),
        "two_qubit_depth": two_qubit_depth(circuit),
        "gate_count": int(circuit.size()),
        "two_qubit_gate_count": int(two_qubit_gate_count(circuit)),
        "operations_json": json.dumps(
            {str(key): int(value) for key, value in circuit.count_ops().items()},
            sort_keys=True,
        ),
    }


def percentile(values: list[int], probability: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    two_depths = [int(row["two_qubit_depth"]) for row in rows]
    two_counts = [int(row["two_qubit_gate_count"]) for row in rows]
    return {
        "circuit_count": len(rows),
        "qubit_counts": sorted({int(row["qubits"]) for row in rows}),
        "two_qubit_depth": {
            "median": statistics.median(two_depths) if two_depths else 0,
            "p95": percentile(two_depths, 0.95),
            "maximum": max(two_depths, default=0),
        },
        "two_qubit_gate_count": {
            "median": statistics.median(two_counts) if two_counts else 0,
            "p95": percentile(two_counts, 0.95),
            "maximum": max(two_counts, default=0),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("circuits", nargs="+", type=Path)
    parser.add_argument(
        "--backend",
        default="qpu.forte-1",
        help="IonQ backend definition used for local transpilation.",
    )
    parser.add_argument(
        "--optimization-level",
        type=int,
        choices=(0, 1),
        default=1,
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    try:
        from qiskit import transpile
        from qiskit_ionq import IonQProvider
    except ImportError as exc:
        raise SystemExit(
            "Install the optional IonQ toolchain with: "
            "conda env update -f environment.yml --prune"
        ) from exc

    for path in args.circuits:
        if not path.exists():
            raise FileNotFoundError(path)

    key = os.getenv("IONQ_API_KEY")
    provider = IonQProvider(key) if key else IonQProvider()
    backend = provider.get_backend(args.backend)

    rows: list[dict[str, Any]] = []
    for source in args.circuits:
        originals = load_circuits(source)
        compiled = transpile(
            originals,
            backend=backend,
            optimization_level=args.optimization_level,
        )
        if not isinstance(compiled, list):
            compiled = [compiled]
        rows.extend(
            metric_row(source, index, circuit)
            for index, circuit in enumerate(compiled)
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(rows[0]) if rows else [
            "source",
            "circuit_index",
            "name",
            "qubits",
            "classical_bits",
            "depth",
            "two_qubit_depth",
            "gate_count",
            "two_qubit_gate_count",
            "operations_json",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "submission_performed": False,
        "backend_used_for_local_transpilation": args.backend,
        "optimization_level": args.optimization_level,
        "api_key_configured": bool(key),
        "summary": summary(rows),
        "circuits": rows,
        "limitations": [
            "No circuit was submitted to IonQ.",
            "Local Qiskit transpilation is a preflight estimate.",
            "Final IonQ compiler and system-specific resource values may differ.",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
