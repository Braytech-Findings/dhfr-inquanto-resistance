"""Validate the final evidence package without network or expensive chemistry."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from scripts.audit_core import SYSTEMS, VERIFIED_WT_TMP
from scripts.four_system_workflow import build_project_status, run_local_all

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/final_validation"


def test_central_scientific_configuration_matches_code() -> None:
    config = yaml.safe_load((ROOT / "configs/scientific_defaults.yaml").read_text())
    assert tuple(config["systems"]) == SYSTEMS
    assert config["units"]["energy"] == "Hartree"
    assert config["sampling"]["default_shots_per_circuit"] == 100
    assert config["quantum_model"]["active_space_status"] == "needs_researcher_decision"


def test_project_status_uses_allowed_transitions_and_null_missing_values() -> None:
    payload = build_project_status()
    allowed = set(payload["allowed_statuses"])
    for system in SYSTEMS:
        for stage in payload["systems"][system].values():
            assert stage["status"] in allowed
        assert payload["systems"][system]["nexus_emulator_result"]["value"] is None
    assert payload["systems"]["WT_4DTMP"]["hamiltonian"]["status"] == "not_started"


def test_four_system_local_preflight_prevents_partial_execution(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "scripts.four_system_workflow.subprocess.run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    with pytest.raises(SystemExit, match="before any execution"):
        run_local_all(type("Args", (), {"shots": 10})())
    assert calls == []


def test_result_manifest_matches_schema_and_protected_result() -> None:
    manifest = json.loads((ARTIFACTS / "result_manifest.json").read_text())
    schema = json.loads((ARTIFACTS / "result_manifest.schema.json").read_text())
    jsonschema.validate(manifest, schema)
    record = manifest["results"][0]
    assert record["energy"] == VERIFIED_WT_TMP["finite_shot_energy_hartree"]
    assert record["backend"] == VERIFIED_WT_TMP["backend"]
    assert record["evidence_level"] == 2


def test_saved_hamiltonian_is_hermitian_and_well_formed() -> None:
    path = ROOT / "data/processed/WT_TMP_qubit_hamiltonian.json"
    if not path.exists():
        pytest.skip("protected generated Hamiltonian is not included in lightweight CI")
    payload = json.loads(path.read_text())
    assert payload["system"] == "WT_TMP"
    assert payload["n_terms"] == len(payload["terms"]) > 0
    for term in payload["terms"]:
        assert set(term["coefficient"]) == {"real", "imag"}
        assert abs(float(term["coefficient"]["imag"])) < 1e-12


def test_only_wt_tmp_has_compatible_saved_parameters() -> None:
    exact_path = ROOT / "results/quantum/WT_TMP_saved_params_exact.json"
    if not exact_path.exists():
        pytest.skip("protected generated exact result is not included in lightweight CI")
    params = json.loads((ROOT / "data/params/WT_TMP_params.json").read_text())["params"]
    exact = json.loads(exact_path.read_text())
    assert len(params) == exact["n_parameters"] == 117
    for system in SYSTEMS[1:]:
        assert not (ROOT / "data/params" / f"{system}_params.json").exists()


def test_qasm_round_trip_when_pytket_is_available() -> None:
    qasm = pytest.importorskip("pytket.qasm")
    source = ROOT / "data/processed/WT_TMP_circuit.qasm"
    circuit = qasm.circuit_from_qasm(source)
    assert circuit.n_qubits == 12
    assert len(circuit.get_commands()) > 0


def test_evidence_tables_never_replace_missing_with_zero() -> None:
    with (ARTIFACTS / "evidence_matrix.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["system"] for row in rows} == set(SYSTEMS)
    pending = [row for row in rows if row["system"] != "WT_TMP"]
    assert all(row["local_finite_shot"] == "missing" for row in pending)
    assert all(row["nexus_emulator"] == "missing" for row in rows)


def test_live_backend_catalog_is_visibility_only() -> None:
    catalog = json.loads(
        (ARTIFACTS / "backend_catalog" / "live_catalog.json").read_text()
    )
    assert catalog["visible_backends"] == ["H1-Emulator", "H2-Emulator"]
    assert catalog["authenticated"] is True
    assert catalog["entitlement_verified"] is False
    assert catalog["submission_created"] is False
    assert catalog["credits_consumed"] is False


def test_remote_job_manifest_records_separate_retrieved_smoke_tests() -> None:
    manifest = json.loads((ARTIFACTS / "quantinuum" / "job_manifest.json").read_text())
    assert len(manifest["jobs"]) == 3
    assert {job["backend"] for job in manifest["jobs"]} == {
        "H1-Emulator",
        "H2-Emulator",
    }
    assert len({job["job_identifier"] for job in manifest["jobs"]}) == 3
    assert all("SMOKE_TEST_ONLY" in job["purpose"] for job in manifest["jobs"])
    assert all(job["final_state"] == "COMPLETED" for job in manifest["jobs"])
    assert all(job["retrieved"] is True for job in manifest["jobs"])
    assert manifest["stopping_reason"] == "STOPPED_BY_SCIENTIFIC_BLOCKER"
