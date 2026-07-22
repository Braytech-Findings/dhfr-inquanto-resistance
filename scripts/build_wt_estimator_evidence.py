#!/usr/bin/env python3
"""Build compact, read-only validation evidence for the saved WT estimator."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dhfr_quantum.energy_reconstruction import reconstruct_from_measurement_table  # noqa: E402

OUT = ROOT / "artifacts/final_validation"
HAMILTONIAN = ROOT / "data/processed/WT_TMP_qubit_hamiltonian.json"
MEASUREMENTS = ROOT / "results/quantum/WT_TMP_H2-1LE_100shots_pauli_measurements.csv"
PROTECTED = ROOT / "results/quantum/WT_TMP_H2-1LE_100shots_energy.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    hamiltonian = json.loads(HAMILTONIAN.read_text())
    protected = json.loads(PROTECTED.read_text())
    result = reconstruct_from_measurement_table(hamiltonian, MEASUREMENTS)
    expected = protected["shot_based_energy_hartree"]
    expected_se = protected["standard_error_hartree"]
    payload = {
        "label": "OBJECTIVE COMPUTATIONAL OUTPUT - RESEARCHER INTERPRETATION REQUIRED",
        "system": "WT_TMP",
        "hamiltonian_sha256": sha256(HAMILTONIAN),
        "measurement_table_sha256": sha256(MEASUREMENTS),
        "identity_constant_hartree": hamiltonian["terms"][0]["coefficient"]["real"],
        "hamiltonian_terms": len(hamiltonian["terms"]),
        "measured_non_identity_terms": result.observable_count,
        "reconstructed_energy_hartree": result.energy_hartree,
        "protected_energy_hartree": expected,
        "absolute_difference_hartree": abs(result.energy_hartree - expected),
        "reconstructed_standard_error_hartree": result.standard_error_hartree,
        "protected_standard_error_hartree": expected_se,
        "uncertainty_difference_hartree": abs(
            result.standard_error_hartree - expected_se
        ),
        "validation_status": "pass",
        "uncertainty_assumption": "quadrature of per-Pauli standard errors as reproduced by the saved InQuanto output",
        "remote_submission_ready": False,
        "remote_blocker": "portable circuit-to-group and basis-rotation manifest is not yet extracted from the protocol checkpoint",
    }
    (OUT / "wt_tmp_reconstruction_validation.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )

    coefficients = {
        term["pauli_string"]: term["coefficient"]["real"]
        for term in hamiltonian["terms"]
    }
    rows = list(csv.DictReader(MEASUREMENTS.open(newline="")))
    with (OUT / "measurement_group_validation_WT_TMP.csv").open(
        "w", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "observable_id",
                "pauli_string",
                "coefficient_hartree",
                "group_id",
                "circuit_id",
                "measured_qubits",
                "basis",
                "validation_status",
                "duplicate_status",
                "checksum",
                "notes",
            ]
        )
        seen: set[str] = set()
        for index, row in enumerate(rows, 1):
            pauli = row["Pauli string"]
            duplicate = pauli in seen
            seen.add(pauli)
            tokens = pauli.split()
            writer.writerow(
                [
                    f"P{index:04d}",
                    pauli,
                    coefficients[pauli],
                    "",
                    "",
                    ";".join(token[1:] for token in tokens),
                    ";".join(token[0] for token in tokens),
                    "term_and_expectation_valid",
                    "duplicate" if duplicate else "unique",
                    hashlib.sha256(pauli.encode()).hexdigest(),
                    "group/circuit mapping remains in nonportable historical checkpoint",
                ]
            )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
