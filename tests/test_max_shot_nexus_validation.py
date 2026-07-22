from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/max_shot_production/nexus/four_circuit_40000_total"


def test_max_shot_validation_has_10000_shots_per_circuit() -> None:
    result = json.loads((RUN / "normalized_result.json").read_text())
    assert result["requested_shots_per_circuit"] == 10_000
    assert len(result["results"]) == 4
    assert all(item["shots"] == 10_000 for item in result["results"])
    assert all(sum(item["counts"].values()) == 10_000 for item in result["results"])
    assert result["combined_returned_shots"] == 40_000


def test_max_shot_result_order_and_identity_are_preserved() -> None:
    result = json.loads((RUN / "normalized_result.json").read_text())
    assert [item["circuit_name"] for item in result["results"]] == [
        "bell_z",
        "bell_x",
        "bell_y",
        "product_01",
    ]
    validation = json.loads((RUN / "validation_report.json").read_text())
    assert validation["validation_status"] == "pass"
    assert validation["order_preserved"] is True
    assert validation["truncation_detected"] is False
