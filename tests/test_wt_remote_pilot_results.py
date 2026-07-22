import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/final_public_release/molecular/WT_TMP/remote_pilot"


def test_failed_remote_results_remain_missing_not_zero():
    raw = json.loads((OUT / "raw_results.json").read_text())
    assert raw["state"] == "ERROR"
    assert raw["raw_results"] is None
    assert raw["returned_result_count"] == 0
    assert raw["missing_values_are_not_zero"] is True


def test_comparison_does_not_impute_remote_energy():
    with (OUT / "local_remote_comparison.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert all(row["remote_group_contribution_hartree"] == "" for row in rows)
    assert all(row["returned_shots"] == "" for row in rows)
