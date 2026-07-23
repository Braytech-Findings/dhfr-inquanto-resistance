from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_wt_remote_molecular_pilot_sharded import (
    GROUPS,
    classify_wait_failure,
    require_new_submission_slot,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_wt_remote_molecular_pilot_sharded.py"


def test_sharded_runner_has_four_fixed_groups_and_one_program_per_job():
    assert len(GROUPS) == 4
    text = SCRIPT.read_text()
    assert "programs=[uploaded]" in text
    assert "n_shots=[args.shots]" in text
    assert "optimisation_level=args.optimisation_level" in text
    assert "default=2, choices=(1, 2)" in text


def test_sharded_runner_does_not_automatically_replace_a_job():
    with pytest.raises(SystemExit, match="retrieve it instead"):
        require_new_submission_slot({"job_id": "job-1", "state": "SUBMITTED"}, None)
    with pytest.raises(SystemExit, match="exact ID"):
        require_new_submission_slot({"job_id": "job-1", "state": "ERROR"}, None)
    require_new_submission_slot({"job_id": "job-1", "state": "ERROR"}, "job-1")


def test_sharded_runner_has_explicit_guards_and_no_automatic_retry():
    text = SCRIPT.read_text()
    assert '"automatic_retry": False' in text
    assert "Save the only job ID before any polling" in text
    assert "--confirm-submit" in text
    assert "--confirm-partnership-access" in text


def test_wait_timeout_does_not_mislabel_an_active_remote_job():
    assert classify_wait_failure("RUNNING", TimeoutError()) == (
        "client_wait_timeout_job_still_active"
    )
    assert classify_wait_failure("ERROR", TimeoutError()) == (
        "remote_execution_timeout"
    )
    assert classify_wait_failure("ERROR", RuntimeError()) == (
        "remote_execution_failure"
    )


def test_all_sharded_source_circuits_exist():
    circuit_dir = ROOT / "artifacts/max_shot_production/WT_TMP/regenerated_circuits"
    if not circuit_dir.exists():
        pytest.skip("protected regenerated circuits are not included in lightweight CI")
    for group in GROUPS:
        path = circuit_dir / f"{group}.json"
        payload = json.loads(path.read_text())
        assert payload["name"] == group
