from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"


def test_all_groups_are_qwc_and_valid() -> None:
    with (WT / "group_commutation_audit.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 576
    assert Counter(row["notes"] for row in rows) == {"QWC": 576}
    assert all(row["validation_status"] == "pass" for row in rows)


def test_regenerated_protocol_covers_every_observable() -> None:
    manifest = json.loads((WT / "regenerated_estimator_manifest.json").read_text())
    assert manifest["label"] == "REGENERATED_PYTKET_MEASUREMENT_PROTOCOL"
    assert manifest["circuits"] == manifest["groups"] == 576
    assert manifest["observables"] == 1818
    assert manifest["mapping_complete"] is True
    with (WT / "regenerated_measurement_map.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len({row["pauli_string"] for row in rows}) == 1818


def test_regenerated_exact_semantics_and_energy_pass() -> None:
    report = json.loads((WT / "regenerated_exact_energy_validation.json").read_text())
    assert report["failed_exact_comparisons"] == 0
    assert report["maximum_absolute_expectation_difference"] <= report["tolerance"]
    assert report["absolute_energy_difference_hartree"] <= report["tolerance"]
    assert report["validation_status"] == "pass"
