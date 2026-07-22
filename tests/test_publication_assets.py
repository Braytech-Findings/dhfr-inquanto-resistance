import json
import os
from pathlib import Path
import subprocess
import sys
from argparse import Namespace
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

from scripts import test_quantinuum_access as nexus


ROOT = Path(__file__).resolve().parents[1]


def test_verified_quantum_summary():
    summary = json.loads(
        (ROOT / "results/publication/data/verified_summary.json").read_text()
    )
    assert summary["ideal_vqe_energy_hartree"] == -2587.912001526413
    assert summary["finite_shot_energy_hartree"] == -2587.917118821447
    assert summary["standard_error_hartree"] > 0


def test_figures_have_manifest_and_renderings():
    figures = ROOT / "results/publication/figures"
    manifests = ROOT / "results/publication/manifests"
    for name in (
        "energy_comparison",
        "error_relative_to_exact",
        "hamiltonian_compression",
        "statistical_uncertainty",
        "parameter_distribution",
    ):
        assert (figures / f"{name}.png").exists()
        assert (figures / f"{name}.pdf").exists()
        assert json.loads((manifests / f"{name}.json").read_text())["alt_text"]


def test_molecular_selection_is_conservative_and_relative():
    manifest = json.loads(
        (ROOT / "visualization/molecular_assets_manifest.json").read_text()
    )
    assert manifest["ligand_residue"] == "TOP"
    assert manifest["protein_chain"] == "A"
    assert manifest["pocket_atoms"] > 0
    assert manifest["qm_cluster_mapping_verified"] is False
    assert (
        "/" + "Users/"
        not in (ROOT / "visualization/interactive/WT_TMP_viewer.html").read_text()
    )


def test_public_data_has_no_nan_or_index_column():
    for csv in (ROOT / "results/publication/data").glob("*.csv"):
        data = pd.read_csv(csv)
        assert not data.isna().any().any()
        assert not any(column.lower().startswith("unnamed") for column in data.columns)


def test_hosted_bell_dry_run_never_imports_or_submits():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/test_quantinuum_access.py",
            "--nexus-emulator",
            "--backend",
            "H2-Emulator",
            "--dry-run",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        "DRY RUN: no qnexus import, login, upload, compile, quota use, "
        "or execution occurred."
        in result.stdout
    )
    assert "Submission group: <default>" in result.stdout


def test_hosted_bell_reads_explicit_group_from_environment():
    env = os.environ.copy()
    env["QNEXUS_USER_GROUP"] = "authorized-test-group"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/test_quantinuum_access.py",
            "--nexus-emulator",
            "--backend",
            "H2-Emulator",
            "--require-user-group",
            "--dry-run",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Submission group: authorized-test-group" in result.stdout
    assert "source: QNEXUS_USER_GROUP" in result.stdout


def test_hosted_bell_cli_group_overrides_environment():
    env = os.environ.copy()
    env["QNEXUS_USER_GROUP"] = "group-from-env"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/test_quantinuum_access.py",
            "--nexus-emulator",
            "--backend",
            "H2-Emulator",
            "--user-group",
            "different-cli-group",
            "--dry-run",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        "Submission group: different-cli-group (source: --user-group)" in result.stdout
    )


def test_verified_provenance_is_consistent():
    provenance = json.loads(
        (ROOT / "results/publication/data/verified_quantum_provenance.json").read_text()
    )
    assert (
        provenance["measurement_circuits"] * provenance["shots_per_circuit"]
        == provenance["total_shots"]
    )
    assert provenance["emulator_local"] is True
    assert provenance["standard_error_hartree"] > 0


def test_yaml_configs_parse_and_core_systems_are_consistent():
    configs = {
        path.stem: yaml.safe_load(path.read_text())
        for path in (ROOT / "configs").glob("*.yaml")
    }
    assert {item["id"] for item in configs["core_systems"]["systems"]} == {
        "WT_TMP",
        "WT_4DTMP",
        "L28R_TMP",
        "L28R_4DTMP",
    }
    assert configs["active_space"]["selection"]["electrons"] == 6
    assert configs["active_space"]["selection"]["orbitals"] == 6
    assert configs["classical_protocol"]["primary_model"]["basis"] == "def2-SVP"


def test_no_absolute_workstation_paths_or_transient_tracked_files():
    home_prefix = "/" + "Users/"
    prohibited_suffixes = (".pid", ".backup", "timeout-backup", "_backup.yml")
    for path in subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).splitlines():
        assert not path.endswith(prohibited_suffixes)
        candidate = ROOT / path
        if candidate.suffix.lower() in {
            ".csv",
            ".json",
            ".md",
            ".py",
            ".yml",
            ".yaml",
            ".html",
            ".tex",
            ".r",
            ".sh",
        }:
            assert home_prefix not in candidate.read_text(errors="ignore")


def test_workflow_yaml_is_valid_and_public():
    workflow = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())
    rendered = json.dumps(workflow)
    assert "cache" not in rendered.lower()
    assert "pytest -q" in rendered


def test_readme_visual_assets_and_key_documents_exist():
    readme = (ROOT / "README.md").read_text()
    for relative_path in (
        "docs/assets/dhfr_quantum_hero.svg",
        "docs/backend-status.md",
        "docs/scientific-background.md",
        "docs/RESULTS.md",
        "docs/LIMITATIONS.md",
    ):
        assert relative_path in readme
        assert (ROOT / relative_path).exists()


def test_no_hard_coded_nexus_identifiers_in_maintained_sources():
    import re

    pattern = re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
    )
    for path in (ROOT / "scripts").glob("*.py"):
        assert not pattern.search(path.read_text())


class _FakeCircuit:
    n_qubits = 2
    n_gates = 4

    def depth(self):
        return 3


class _FakeCompiledCircuit(_FakeCircuit):
    n_gates = 9

    def depth(self):
        return 6


def _nexus_args(backend: str, max_hqc: float = 0.0) -> Namespace:
    return Namespace(
        backend=backend,
        shots=10,
        max_hqc=max_hqc,
        confirm_hardware=True,
        confirm_submit=True,
        user_group=None,
        require_user_group=False,
        dry_run=False,
        project_id="project-id",
        project_name=None,
        timeout=1,
        wait=False,
    )


def _fake_nexus(cost: float = 1.0):
    calls = {"cost": 0, "execute": []}

    class Circuits:
        @staticmethod
        def upload(**_kwargs):
            return "uploaded"

        @staticmethod
        def cost(**_kwargs):
            calls["cost"] += 1
            return cost

    class FakeQnx:
        circuits = Circuits()
        projects = SimpleNamespace(
            get=lambda **_kwargs: SimpleNamespace(id="project-id")
        )

        @staticmethod
        def login():
            return None

        @staticmethod
        def compile(**_kwargs):
            return [SimpleNamespace(download_circuit=lambda: _FakeCompiledCircuit())]

        @staticmethod
        def start_execute_job(**kwargs):
            calls["execute"].append(kwargs)
            return SimpleNamespace(id="job-id")

    return FakeQnx(), lambda **kwargs: SimpleNamespace(**kwargs), calls


@pytest.mark.parametrize("backend", ["H1-Emulator", "H2-Emulator"])
def test_nexus_hosted_emulators_do_not_estimate_hqc(monkeypatch, backend):
    qnx, config, calls = _fake_nexus()
    monkeypatch.setattr(nexus, "load_nexus", lambda: (qnx, config))
    monkeypatch.setattr(nexus, "bell", _FakeCircuit)
    nexus.hosted_bell(_nexus_args(backend))
    assert calls["cost"] == 0
    assert "max_cost" not in calls["execute"][0]


@pytest.mark.parametrize("backend", ["H2-1E", "H2-1SC"])
def test_unsupported_hardware_tier_endpoints_are_rejected(monkeypatch, backend):
    qnx, config, calls = _fake_nexus(cost=1.0)
    monkeypatch.setattr(nexus, "load_nexus", lambda: (qnx, config))
    monkeypatch.setattr(nexus, "bell", _FakeCircuit)
    with pytest.raises(SystemExit, match="Unsupported endpoint"):
        nexus.hosted_bell(_nexus_args(backend, max_hqc=90_000.0))
    assert calls["cost"] == 0
    assert calls["execute"] == []


def test_project_selection_is_unambiguous(monkeypatch):
    args = Namespace(project_id=None, project_name=None)
    monkeypatch.setenv("QNEXUS_PROJECT_ID", " ")
    monkeypatch.setenv("QNEXUS_PROJECT_NAME", "named-project")
    assert nexus.resolve_project_selection(args) == (
        None,
        "named-project",
        "QNEXUS_PROJECT_NAME",
    )
    args.project_id = "explicit-project"
    assert nexus.resolve_project_selection(args) == (
        "explicit-project",
        None,
        "--project-id",
    )


def test_project_selection_rejects_ambiguous_environment(monkeypatch):
    args = Namespace(project_id=None, project_name=None)
    monkeypatch.setenv("QNEXUS_PROJECT_ID", "id")
    monkeypatch.setenv("QNEXUS_PROJECT_NAME", "name")
    with pytest.raises(SystemExit, match="Set only one"):
        nexus.resolve_project_selection(args)
