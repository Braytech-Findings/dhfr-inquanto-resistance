import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = (
    ROOT
    / "artifacts/final_public_release/molecular/WT_TMP/local_finite_shot_summary.json"
)


def test_incomplete_convergence_keeps_remote_gate_closed():
    summary = json.loads(SUMMARY.read_text())
    assert summary["completed_shot_levels"] == [100]
    assert summary["all_required_levels_complete"] is False
    assert summary["remote_molecular_gate"] == "closed"


def test_invalid_diagnostic_is_excluded():
    summary = json.loads(SUMMARY.read_text())
    assert summary["valid_replicates"] == 3
    assert summary["invalid_diagnostics"] == 1
    assert summary["all_valid_replicates_within_3sigma"] is True
