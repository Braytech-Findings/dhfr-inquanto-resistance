#!/usr/bin/env python3
"""Regenerate explicit measurement suffixes for the 576 preserved WT groups."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from pytket.circuit import Circuit, Qubit
from pytket.partition import (
    GraphColourMethod,
    PauliPartitionStrat,
    measurement_reduction,
)
from pytket.pauli import Pauli, QubitPauliString
from pytket.qasm import circuit_to_qasm_str

ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"
SOURCE_MAP = WT / "measurement_map.csv"
BASE_SOURCE = WT / "circuits/WT_TMP_G0001.json"
OUT = WT / "regenerated_circuits"


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def qps(text: str) -> QubitPauliString:
    return QubitPauliString(
        {Qubit(int(token[1:])): getattr(Pauli, token[0]) for token in text.split()}
    )


def bit_index(bit: object) -> int:
    return int(bit if isinstance(bit, int) else bit.index[0])


def main() -> None:
    base = Circuit.from_dict(json.loads(BASE_SOURCE.read_text()))
    if base.n_bits != 0 or base.free_symbols():
        raise SystemExit("Base preparation must be bound and contain no measurements")
    OUT.mkdir(parents=True, exist_ok=True)
    groups: dict[int, list[dict[str, str]]] = defaultdict(list)
    with SOURCE_MAP.open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups[int(row["group_index"])].append(row)
    if sorted(groups) != list(range(576)):
        raise SystemExit("Expected exactly 576 preserved groups")
    mappings = []
    records = []
    for index in sorted(groups):
        strings = [qps(row["pauli_string"]) for row in groups[index]]
        setup = measurement_reduction(
            strings,
            PauliPartitionStrat.NonConflictingSets,
            GraphColourMethod.Lazy,
        )
        if len(setup.measurement_circs) != 1 or not setup.verify():
            raise RuntimeError(f"Group {index} did not produce one verified circuit")
        suffix = setup.measurement_circs[0]
        bit_to_qubit = {
            bit_index(command.bits[0]): int(command.qubits[0].index[0])
            for command in suffix.get_commands()
            if command.op.type.name == "Measure"
        }
        full = base.copy()
        full.append(suffix)
        full.name = f"WT_TMP_G{index + 1:04d}"
        suffix_bytes = canonical(suffix.to_dict())
        full_bytes = canonical(full.to_dict())
        suffix_path = OUT / f"WT_TMP_G{index + 1:04d}_suffix.json"
        full_path = OUT / f"WT_TMP_G{index + 1:04d}.json"
        qasm_path = OUT / f"WT_TMP_G{index + 1:04d}.qasm"
        suffix_path.write_bytes(suffix_bytes + b"\n")
        full_path.write_bytes(full_bytes + b"\n")
        qasm_path.write_text(circuit_to_qasm_str(full))
        if Circuit.from_dict(json.loads(full_path.read_text())) != full:
            raise RuntimeError(f"Full-circuit round trip failed for group {index}")
        for row, observable in zip(groups[index], strings, strict=True):
            bitmaps = setup.results[observable]
            if len(bitmaps) != 1:
                raise RuntimeError(
                    f"Observable has ambiguous mapping: {row['pauli_string']}"
                )
            bitmap = bitmaps[0]
            mappings.append(
                {
                    "observable_id": row["observable_id"],
                    "pauli_string": row["pauli_string"],
                    "group_id": f"WT_TMP_G{index + 1:04d}",
                    "circuit_index": bitmap.circ_index,
                    "bits": ";".join(str(bit_index(bit)) for bit in bitmap.bits),
                    "measured_qubits": ";".join(
                        str(bit_to_qubit[bit_index(bit)]) for bit in bitmap.bits
                    ),
                    "invert": str(bitmap.invert).lower(),
                }
            )
        records.append(
            {
                "group_id": f"WT_TMP_G{index + 1:04d}",
                "observable_count": len(strings),
                "suffix_sha256": hashlib.sha256(suffix_bytes).hexdigest(),
                "full_circuit_sha256": hashlib.sha256(full_bytes).hexdigest(),
                "n_qubits": full.n_qubits,
                "n_bits": full.n_bits,
                "commands": len(full.get_commands()),
                "depth": full.depth(),
                "two_qubit_gates": full.n_2qb_gates(),
            }
        )
    with (WT / "regenerated_measurement_map.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mappings[0]))
        writer.writeheader()
        writer.writerows(mappings)
    manifest = {
        "label": "REGENERATED_PYTKET_MEASUREMENT_PROTOCOL",
        "scientific_label": "OBJECTIVE COMPUTATIONAL OUTPUT - RESEARCHER INTERPRETATION REQUIRED",
        "strategy": "PauliPartitionStrat.NonConflictingSets",
        "graph_colour_method": "GraphColourMethod.Lazy",
        "groups": 576,
        "circuits": 576,
        "observables": 1818,
        "base_preparation_sha256": hashlib.sha256(
            canonical(base.to_dict())
        ).hexdigest(),
        "circuit_records": records,
        "mapping_complete": len(mappings) == 1818,
        "protocol_executed": False,
        "nexus_contacted": False,
    }
    (WT / "regenerated_estimator_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print({key: value for key, value in manifest.items() if key != "circuit_records"})


if __name__ == "__main__":
    main()
