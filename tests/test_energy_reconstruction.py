from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dhfr_quantum.energy_reconstruction import (
    expectation_from_counts,
    reconstruct,
    reconstruct_from_measurement_table,
)
from src.dhfr_quantum.energy_estimator_manifest import read_manifest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("counts", "observable", "expected"),
    [
        ({"0": 10}, "", 1.0),
        ({"0": 10}, "Z0", 1.0),
        ({"1": 10}, "Z0", -1.0),
        ({"0": 10}, "X0", 1.0),
        ({"0": 10}, "Y0", 1.0),
        ({"00": 5, "11": 5}, "Z0 Z1", 1.0),
        ({"00": 5, "11": 5}, "X0 X1", 1.0),
        ({"01": 5, "10": 5}, "Y0 Y1", -1.0),
    ],
)
def test_known_pauli_expectations(counts, observable, expected) -> None:
    mean, _ = expectation_from_counts(counts, observable)
    assert mean == expected


def test_bit_order_and_mapping() -> None:
    assert expectation_from_counts({"01": 10}, "Z0", bit_order="big")[0] == -1
    assert expectation_from_counts({"01": 10}, "Z0", bit_order="little")[0] == 1
    assert expectation_from_counts({"01": 10}, "Z0", qubit_to_bit={0: 1})[0] == 1


@pytest.mark.parametrize("counts", [{}, {"0": 0}, {"02": 1}, {"0": -1}])
def test_invalid_counts_are_rejected(counts) -> None:
    with pytest.raises(ValueError):
        expectation_from_counts(counts, "Z0")


def test_constant_sign_and_uncertainty() -> None:
    result = reconstruct({"": -2.0, "Z0": 0.5}, {"Z0": (-1.0, 0.2)})
    assert result.energy_hartree == -2.5
    assert result.standard_error_hartree == pytest.approx(0.1)


def test_missing_and_extra_observables_are_rejected() -> None:
    with pytest.raises(ValueError, match="Observable mismatch"):
        reconstruct({"Z0": 1.0}, {})
    with pytest.raises(ValueError, match="Observable mismatch"):
        reconstruct({}, {"Z0": (1.0, 0.0)})


def test_protected_wt_tmp_reconstruction() -> None:
    path = ROOT / "data/processed/WT_TMP_qubit_hamiltonian.json"
    if not path.exists():
        pytest.skip("protected generated Hamiltonian is not included in lightweight CI")
    hamiltonian = json.loads(path.read_text())
    result = reconstruct_from_measurement_table(
        hamiltonian,
        ROOT / "results/quantum/WT_TMP_H2-1LE_100shots_pauli_measurements.csv",
    )
    assert result.observable_count == 1818
    assert result.energy_hartree == pytest.approx(-2587.917118821447, abs=2e-11)
    assert result.standard_error_hartree == pytest.approx(0.007647045140626157)


def test_wt_tmp_estimator_manifest_is_schema_valid() -> None:
    manifest = read_manifest(
        ARTIFACT := ROOT / "artifacts/final_validation/estimators/WT_TMP.json"
    )
    assert manifest["system"] == "WT_TMP"
    assert manifest["measurement"]["portable_circuit_map_complete"] is False
    assert ARTIFACT.exists()
