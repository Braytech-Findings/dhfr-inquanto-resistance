#!/usr/bin/env python3
"""Exactly validate all regenerated WT measurement circuits and energy."""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from pytket.circuit import Circuit, Qubit
from pytket.extensions.qiskit import AerStateBackend
from pytket.pauli import Pauli, QubitPauliString

ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"
TOLERANCE = 1e-10


def qps(text: str) -> QubitPauliString:
    return QubitPauliString(
        {Qubit(int(token[1:])): getattr(Pauli, token[0]) for token in text.split()}
    )


def state(backend: AerStateBackend, circuit: Circuit):
    compiled = backend.get_compiled_circuit(circuit, optimisation_level=0)
    return backend.run_circuit(compiled).get_state()


def suffix_unitary(suffix: Circuit) -> Circuit:
    result = Circuit(12)
    for command in suffix.get_commands():
        if command.op.type.name != "Measure":
            result.add_gate(command.op, list(command.qubits))
    return result


def main() -> None:
    base = Circuit.from_dict(
        json.loads((WT / "circuits/WT_TMP_G0001.json").read_text())
    )
    backend = AerStateBackend()
    started = time.time()
    base_state = state(backend, base)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    with (WT / "regenerated_measurement_map.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups[row["group_id"]].append(row)
    coefficients = {
        term["pauli_string"]: float(term["coefficient"]["real"])
        for term in json.loads(
            (ROOT / "data/processed/WT_TMP_qubit_hamiltonian.json").read_text()
        )["terms"]
    }
    output = WT / "regenerated_measurement_validation.csv"
    fields = [
        "observable_id",
        "pauli_string",
        "group_id",
        "bits",
        "measured_qubits",
        "invert",
        "path_a_exact_expectation",
        "path_b_measurement_expectation",
        "absolute_difference",
        "coefficient_hartree",
        "energy_contribution_hartree",
        "validation_status",
    ]
    rows = []
    for group_id in sorted(groups):
        suffix = Circuit.from_dict(
            json.loads(
                (WT / "regenerated_circuits" / f"{group_id}_suffix.json").read_text()
            )
        )
        bit_to_qubit = {
            int(command.bits[0].index[0]): int(command.qubits[0].index[0])
            for command in suffix.get_commands()
            if command.op.type.name == "Measure"
        }
        full = base.copy()
        full.append(suffix_unitary(suffix))
        measured_state = state(backend, full)
        for mapping in groups[group_id]:
            direct = float(
                qps(mapping["pauli_string"]).state_expectation(base_state).real
            )
            bit_indices = [int(value) for value in mapping["bits"].split(";") if value]
            measured_qubits = [bit_to_qubit[index] for index in bit_indices]
            parity = QubitPauliString(
                {Qubit(index): Pauli.Z for index in measured_qubits}
            )
            measured = float(parity.state_expectation(measured_state).real)
            if mapping["invert"] == "true":
                measured *= -1
            difference = abs(direct - measured)
            coefficient = coefficients[mapping["pauli_string"]]
            rows.append(
                {
                    **{
                        key: mapping[key]
                        for key in (
                            "observable_id",
                            "pauli_string",
                            "group_id",
                            "bits",
                            "invert",
                        )
                    },
                    "measured_qubits": ";".join(map(str, measured_qubits)),
                    "path_a_exact_expectation": direct,
                    "path_b_measurement_expectation": measured,
                    "absolute_difference": difference,
                    "coefficient_hartree": coefficient,
                    "energy_contribution_hartree": coefficient * direct,
                    "validation_status": "pass" if difference <= TOLERANCE else "fail",
                }
            )
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["validation_status"] != "pass"]
    energy = coefficients[""] + sum(
        float(row["energy_contribution_hartree"]) for row in rows
    )
    protected = -2587.912001526413
    report = {
        "label": "OBJECTIVE COMPUTATIONAL OUTPUT - RESEARCHER INTERPRETATION REQUIRED",
        "protocol": "REGENERATED_PYTKET_MEASUREMENT_PROTOCOL",
        "groups": len(groups),
        "circuits": len(groups),
        "observables": len(rows),
        "failed_exact_comparisons": len(failures),
        "maximum_absolute_expectation_difference": max(
            float(row["absolute_difference"]) for row in rows
        ),
        "tolerance": TOLERANCE,
        "identity_constant_hartree": coefficients[""],
        "regenerated_exact_energy_hartree": energy,
        "protected_ideal_energy_hartree": protected,
        "absolute_energy_difference_hartree": abs(energy - protected),
        "runtime_seconds": time.time() - started,
        "validation_status": "pass"
        if not failures and abs(energy - protected) <= TOLERANCE
        else "fail",
    }
    (WT / "regenerated_exact_energy_validation.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
    if report["validation_status"] != "pass":
        raise SystemExit("Regenerated exact protocol validation failed")


if __name__ == "__main__":
    main()
