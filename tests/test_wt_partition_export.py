from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("pytket", reason="requires the optional local quantum stack")

from scripts.export_wt_partition_streaming import parse_circuit

ROOT = Path(__file__).resolve().parents[1]


def test_restricted_parser_rejects_arbitrary_calls() -> None:
    try:
        parse_circuit("open('secret'),0", 0)
    except ValueError as exc:
        assert "Only frozenset calls" in str(exc)
    else:
        raise AssertionError("arbitrary call was not rejected")


def test_restricted_parser_rejects_index_mismatch() -> None:
    try:
        parse_circuit("frozenset(),1", 0)
    except ValueError as exc:
        assert "index" in str(exc)
    else:
        raise AssertionError("index mismatch was not rejected")


def test_partition_recovery_does_not_claim_measurement_circuits() -> None:
    manifest = json.loads(
        (
            ROOT / "artifacts/max_shot_production/WT_TMP/estimator_manifest.json"
        ).read_text()
    )
    assert manifest["partition_group_records"] == 576
    assert manifest["non_identity_observables"] == 1818
    assert manifest["unique_serialized_circuits"] == 1
    assert manifest["portable_measurement_circuits_complete"] is False
    assert manifest["validation_status"] == "blocked"
