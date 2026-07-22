#!/usr/bin/env python3
"""Stream the historical WT partition CSV into portable circuit JSON files."""

from __future__ import annotations

import ast
import csv
import gc
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pytket.circuit import Circuit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/quantum/measurement_plans/WT_TMP_pauli_partitioning.csv"
OUT = ROOT / "artifacts/max_shot_production/WT_TMP"
CIRCUITS = OUT / "circuits"

ALLOWED_AST = (
    ast.Expression,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Tuple,
    ast.Set,
    ast.Constant,
    ast.UnaryOp,
    ast.USub,
)


def validate_expression(text: str) -> ast.Expression:
    tree = ast.parse(text, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST):
            raise ValueError(
                f"Disallowed serialized-circuit syntax: {type(node).__name__}"
            )
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id != "frozenset":
                raise ValueError("Only frozenset calls are permitted")
            if node.keywords:
                raise ValueError("Serialized frozenset cannot have keywords")
        if isinstance(node, ast.Name) and node.id != "frozenset":
            raise ValueError(f"Disallowed serialized name: {node.id}")
    return tree


def thaw(value):
    if isinstance(value, frozenset):
        return {key: thaw(item) for key, item in value}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


def parse_circuit(text: str, expected_index: int) -> Circuit:
    tree = validate_expression(text)
    value = eval(  # noqa: S307 - restricted AST and empty builtins above.
        compile(tree, "<historical-circuit>", "eval"),
        {"__builtins__": {}, "frozenset": frozenset},
        {},
    )
    if not isinstance(value, tuple) or len(value) != 2:
        raise ValueError("Historical circuit cell is not a (payload, index) tuple")
    payload, embedded_index = value
    if int(embedded_index) != expected_index:
        raise ValueError("Embedded circuit index does not match CSV index")
    return Circuit.from_dict(thaw(payload))


def canonical_json(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_worker(index: int) -> None:
    text = sys.stdin.read()
    path = CIRCUITS / f"WT_TMP_G{index + 1:04d}.json"
    meta_path = CIRCUITS / f"WT_TMP_G{index + 1:04d}.meta.json"
    if path.exists():
        encoded = path.read_bytes().strip()
        circuit = Circuit.from_dict(json.loads(encoded))
    else:
        circuit = parse_circuit(text, index)
        encoded = canonical_json(circuit.to_dict())
        path.write_bytes(encoded + b"\n")
    loaded = Circuit.from_dict(json.loads(path.read_text()))
    if loaded != circuit:
        raise RuntimeError(f"Circuit round trip failed for group {index}")
    metadata = {
        "circuit_id": f"WT_TMP_G{index + 1:04d}",
        "group_index": index,
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "n_qubits": circuit.n_qubits,
        "n_bits": circuit.n_bits,
        "commands": len(circuit.get_commands()),
        "depth": circuit.depth(),
        "two_qubit_gates": circuit.n_2qb_gates(),
    }
    meta_path.write_text(json.dumps(metadata, separators=(",", ":")) + "\n")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker-index":
        export_worker(int(sys.argv[2]))
        return
    csv.field_size_limit(sys.maxsize)
    CIRCUITS.mkdir(parents=True, exist_ok=True)
    seen: dict[int, tuple[str, dict]] = {}
    measurement_rows: list[dict[str, str | int]] = []
    with SOURCE.open(newline="") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=1):
            index = int(row["Circuit index"])
            text = row["Circuit name"]
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            if index not in seen:
                meta_path = CIRCUITS / f"WT_TMP_G{index + 1:04d}.meta.json"
                if not meta_path.exists():
                    subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--worker-index",
                            str(index),
                        ],
                        input=text,
                        text=True,
                        check=True,
                    )
                seen[index] = (text_hash, json.loads(meta_path.read_text()))
                gc.collect()
            elif seen[index][0] != text_hash:
                raise RuntimeError(f"Circuit {index} has inconsistent serializations")
            measurement_rows.append(
                {
                    "observable_id": f"P{row_number:04d}",
                    "pauli_string": row["Pauli string"],
                    "group_index": index,
                    "circuit_id": f"WT_TMP_G{index + 1:04d}",
                }
            )

    indices = sorted(seen)
    if indices != list(range(576)):
        raise RuntimeError(
            f"Expected circuit indices 0..575, found {indices[:3]}..{indices[-3:]}"
        )
    if len(measurement_rows) != 1818:
        raise RuntimeError(f"Expected 1818 observables, found {len(measurement_rows)}")
    paulis = [str(row["pauli_string"]) for row in measurement_rows]
    if len(paulis) != len(set(paulis)):
        raise RuntimeError("Duplicate Pauli observables found")

    with (OUT / "measurement_map.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(measurement_rows[0]))
        writer.writeheader()
        writer.writerows(measurement_rows)
    manifest = {
        "label": "OBJECTIVE COMPUTATIONAL OUTPUT - RESEARCHER INTERPRETATION REQUIRED",
        "system": "WT_TMP",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE),
        "export_method": "restricted-AST streaming recovery from historical dataframe_partitioning CSV",
        "partition_group_records": 576,
        "unique_serialized_circuits": len(
            {seen[index][1]["sha256"] for index in indices}
        ),
        "non_identity_observables": 1818,
        "identity_term_separate": True,
        "circuit_records": [seen[index][1] for index in indices],
        "serialization_roundtrip_validation": "pass",
        "portable_measurement_circuits_complete": False,
        "validation_status": "blocked",
        "blocker": "All 576 records contain the same bound state-preparation circuit; measurement-basis suffixes remain inside the InQuanto protocol checkpoint.",
        "protocol_executed": False,
        "nexus_contacted": False,
    }
    (OUT / "estimator_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in manifest.items() if key != "circuit_records"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
