"""Tests for local safety, naming, provenance, and reproducibility rules."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.audit_core import (
    VERIFIED_WT_TMP,
    backend_metadata,
    canonical_system,
    classify_access_error,
    load_json_object,
    sha256_file,
    total_shots,
    validate_verified_wt_tmp,
)

ROOT = Path(__file__).resolve().parents[1]


def test_system_names_and_aliases() -> None:
    assert canonical_system("WT_TMP") == "WT_TMP"
    assert canonical_system("WT_4-DTMP") == "WT_4DTMP"
    assert canonical_system("L28R_4′DTMP") == "L28R_4DTMP"
    with pytest.raises(ValueError, match="Unknown molecular system"):
        canonical_system("example")


def test_shot_total_includes_replicates_and_rejects_bad_values() -> None:
    assert total_shots(576, 100) == 57_600
    assert total_shots(2, 10, 3) == 60
    with pytest.raises(ValueError):
        total_shots(1, 0)
    with pytest.raises(TypeError):
        total_shots(True, 100)


def test_backend_classification_is_explicit() -> None:
    local = backend_metadata("H2-1LE")
    assert local["kind"] == "noiseless_emulator"
    assert local["location"] == "local"
    assert local["physical_hardware"] is False
    assert backend_metadata("H2-1SC")["kind"] == "syntax_checker"
    assert backend_metadata("H2-Emulator")["kind"] == "hosted_emulator"
    assert backend_metadata("H2-1E")["kind"] == "physical_hardware"
    assert backend_metadata("invented")["kind"] == "unknown_unverified"


def test_access_code_14_is_not_a_scientific_failure() -> None:
    assert classify_access_error("access code 14") == "access_or_entitlement"
    assert classify_access_error("SCF did not converge") == "unknown"


def test_json_errors_and_checksum(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_json_object(missing)
    corrupt = tmp_path / "bad.json"
    corrupt.write_text("{")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_json_object(corrupt)
    good = tmp_path / "good.json"
    good.write_text(json.dumps({"ok": True}))
    assert load_json_object(good) == {"ok": True}
    assert sha256_file(good) == sha256_file(good)


def test_verified_wt_tmp_metadata_and_placeholder_rejection() -> None:
    record = {**VERIFIED_WT_TMP, "local": True, "physical_hardware": False}
    validate_verified_wt_tmp(record)
    with pytest.raises(ValueError, match="Placeholder"):
        validate_verified_wt_tmp({**record, "placeholder": True})
    with pytest.raises(ValueError, match="local emulation"):
        validate_verified_wt_tmp({**record, "physical_hardware": True})


def test_nexus_command_without_mode_is_offline() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/test_quantinuum_access.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "No mode was selected" in result.stdout
    assert "No login, network request" in result.stdout


def test_remote_submission_still_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/test_quantinuum_access.py",
            "--nexus-emulator",
            "--backend",
            "H2-Emulator",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "--confirm-submit" in (result.stdout + result.stderr)


def test_endpoint_rejects_singleton_rows_as_replicates(tmp_path: Path) -> None:
    csv = tmp_path / "singletons.csv"
    csv.write_text(
        "system_id,replicate,interaction_energy_hartree\n"
        "WT_TMP,1,-1\nWT_4DTMP,1,-2\n"
        "L28R_TMP,1,-3\nL28R_4DTMP,1,-4\n"
    )
    result = subprocess.run(
        [sys.executable, "scripts/analyze_endpoint.py", str(csv)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "at least two independent replicates" in (result.stdout + result.stderr)


def test_endpoint_is_reproducible_with_fixed_seed(tmp_path: Path) -> None:
    csv = tmp_path / "replicates.csv"
    csv.write_text(
        "system_id,replicate,interaction_energy_hartree\n"
        "WT_TMP,1,-1.0\nWT_TMP,2,-1.1\n"
        "WT_4DTMP,1,-2.0\nWT_4DTMP,2,-2.1\n"
        "L28R_TMP,1,-3.0\nL28R_TMP,2,-3.1\n"
        "L28R_4DTMP,1,-4.0\nL28R_4DTMP,2,-4.1\n"
    )
    outputs = [tmp_path / "one.json", tmp_path / "two.json"]
    for output in outputs:
        subprocess.run(
            [
                sys.executable,
                "scripts/analyze_endpoint.py",
                str(csv),
                "--bootstrap",
                "100",
                "--seed",
                "7",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    assert load_json_object(outputs[0]) == load_json_object(outputs[1])
