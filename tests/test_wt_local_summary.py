import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = (
    ROOT
    / "artifacts/final_public_release/molecular/WT_TMP/local_finite_shot_summary.json"
)


def test_complete_convergence_passes_local_gate_but_requires_cost_approval():
    summary = json.loads(SUMMARY.read_text())
    assert summary["completed_shot_levels"] == [100, 250, 500, 1000, 2500, 5000, 10000]
    assert summary["all_required_levels_complete"] is True
    assert summary["local_numerical_gate_passed"] is True
    assert summary["remote_molecular_gate"] == "local_pass_cost_approval_required"


def test_invalid_diagnostic_is_excluded():
    summary = json.loads(SUMMARY.read_text())
    assert summary["valid_replicates"] == 21
    assert summary["invalid_diagnostics"] == 1
    assert summary["all_valid_replicates_within_3sigma"] is True
