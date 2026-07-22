from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_nexus_multicircuit_pilot import circuits

ROOT = Path(__file__).resolve().parents[1]


def test_pilot_has_four_distinct_named_circuits() -> None:
    values = circuits()
    assert [item.name for item in values] == [
        "bell_z",
        "bell_x",
        "bell_y",
        "product_01",
    ]
    assert all(item.n_qubits == 2 for item in values)


def test_pilot_requires_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["run_nexus_multicircuit_pilot.py", "--project-name", "test"],
    )
    from scripts.run_nexus_multicircuit_pilot import main

    with pytest.raises(SystemExit, match="requires --confirm-submit"):
        main()


def test_saved_multicircuit_pilot_is_complete_and_ordered() -> None:
    payload = json.loads(
        (
            ROOT / "artifacts/final_validation/quantinuum/multicircuit_pilot.json"
        ).read_text()
    )
    assert payload["state"] == "COMPLETED"
    assert payload["retrieval_complete"] is True
    assert [item["circuit_name"] for item in payload["results"]] == payload[
        "circuit_names"
    ]
    assert all(item["returned_shots"] == 10 for item in payload["results"])
    assert len(payload["results"]) == 4
