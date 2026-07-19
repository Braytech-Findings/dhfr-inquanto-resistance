import json
from pathlib import Path
import subprocess
import sys

import pandas as pd


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
        "/Users/"
        not in (ROOT / "visualization/interactive/WT_TMP_viewer.html").read_text()
    )


def test_public_data_has_no_nan_or_index_column():
    for csv in (ROOT / "results/publication/data").glob("*.csv"):
        data = pd.read_csv(csv)
        assert not data.isna().any().any()
        assert not any(column.lower().startswith("unnamed") for column in data.columns)


def test_hosted_bell_dry_run_never_logs_in_or_submits():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/test_quantinuum_access.py",
            "--nexus-emulator",
            "--backend",
            "H2-1SC",
            "--dry-run",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "No login, upload, compile, cost request, or execution occurred" in result.stdout
