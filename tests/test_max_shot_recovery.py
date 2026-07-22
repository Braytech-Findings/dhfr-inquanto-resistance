from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/max_shot_production"


def test_historical_environment_is_recorded_without_modification() -> None:
    status = json.loads((ARTIFACTS / "environment/environment_status.json").read_text())
    assert status["python"] == "3.11.15"
    assert status["packages"]["inquanto"] == "6.1.0 import confirmed"
    assert status["modified"] is False
    assert status["credentials_inspected"] is False
    assert status["tiny_pyscf"]["converged"] is True


def test_checkpoint_failure_blocks_export_and_remote_work() -> None:
    report = json.loads((ARTIFACTS / "WT_TMP/checkpoint_load_report.json").read_text())
    assert report["failure_category"] == "resource_exhaustion_during_deserialization"
    assert report["circuits_exported"] == 0
    assert report["remote_jobs_created"] == 0
    assert report["bypass_attempted"] is False
    assert report["partition_csv_recovery"]["group_records"] == 576
    assert report["partition_csv_recovery"]["unique_serialized_circuits"] == 1
    assert (
        report["partition_csv_recovery"]["measurement_basis_suffixes_recovered"]
        is False
    )


def test_checkpoint_inventory_preserves_known_checksums() -> None:
    with (ARTIFACTS / "checkpoint_inventory.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    checkpoints = [row for row in rows if row["type"] == "pickle"]
    assert len(checkpoints) == 3
    assert all(len(row["sha256"]) == 64 for row in checkpoints)
    assert all(row["load_status"] == "blocked" for row in checkpoints)
