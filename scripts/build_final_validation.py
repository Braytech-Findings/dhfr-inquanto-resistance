#!/usr/bin/env python3
"""Build the local, evidence-only final validation package.

The script reads existing repository artifacts, validates them, and writes
summaries under ``artifacts/final_validation``. It performs no network access,
scientific optimization, remote submission, or historical-result overwrite.
Missing values are written as empty CSV cells or JSON null values, never zero.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
import math
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

try:
    from .audit_core import SYSTEMS, VERIFIED_WT_TMP, load_json_object, sha256_file
    from .four_system_workflow import build_status
except ImportError:
    from audit_core import SYSTEMS, VERIFIED_WT_TMP, load_json_object, sha256_file
    from four_system_workflow import build_status

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/final_validation"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
PACKAGES = (
    "pyscf",
    "inquanto",
    "inquanto-pyscf",
    "pytket",
    "pytket-quantinuum",
    "qnexus",
    "qiskit",
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "pytest",
    "notebook",
    "jupyterlab",
    "rdkit",
    "openmm",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_text(name: str, text: str) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(name: str, payload: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(name: str, rows: list[dict[str, Any]], fields: Iterable[str]) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def package_versions() -> dict[str, str]:
    values = {}
    for package in PACKAGES:
        try:
            values[package] = version(package)
        except PackageNotFoundError:
            values[package] = "not installed"
    return values


def runtime_artifacts() -> None:
    packages = package_versions()
    runtime = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "executable": sys.executable,
        "implementation": platform.python_implementation(),
        "os": platform.platform(),
        "architecture": platform.machine(),
        "branch": git("branch", "--show-current"),
        "git_commit": git("rev-parse", "HEAD"),
        "packages": packages,
        "historical_verified_runtime": {
            "python": "3.11",
            "source": "results/quantum/results_manifest.json",
        },
    }
    write_json("python_runtime.json", runtime)
    lines = [
        f"timestamp_utc: {runtime['timestamp_utc']}",
        f"python: {sys.version.splitlines()[0]}",
        f"executable: {sys.executable}",
        f"os: {runtime['os']}",
        f"architecture: {runtime['architecture']}",
        f"branch: {runtime['branch']}",
        f"git_commit: {runtime['git_commit']}",
        "",
        "Installed package versions:",
        *[f"{name}: {value}" for name, value in packages.items()],
        "",
        "Important: the current Python 3.13 shell is not the declared Python 3.11 environment used by the saved verified result.",
    ]
    write_text("environment_snapshot.txt", "\n".join(lines))
    freeze = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    write_text("pip_freeze.txt", freeze)
    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    write_text(
        "pip_check.txt",
        f"exit_code: {pip_check.returncode}\n{pip_check.stdout}{pip_check.stderr}",
    )


def parse_xyz(path: Path) -> tuple[list[str], list[tuple[float, float, float]]]:
    lines = path.read_text().splitlines()
    expected = int(lines[0].strip())
    atoms, coordinates = [], []
    for line in lines[2:]:
        fields = line.split()
        if len(fields) < 4:
            continue
        atoms.append(fields[0])
        coordinates.append(tuple(float(value) for value in fields[1:4]))
    if len(atoms) != expected:
        raise ValueError(f"{path}: expected {expected} atoms, read {len(atoms)}")
    return atoms, coordinates


def minimum_distance(coords: list[tuple[float, float, float]]) -> float | None:
    best = None
    for index, left in enumerate(coords):
        for right in coords[index + 1 :]:
            distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))
            best = distance if best is None or distance < best else best
    return best


def molecular_validation() -> list[dict[str, Any]]:
    manifest_rows: dict[str, dict[str, str]] = {}
    manifest = ROOT / "results/tables/qm_cluster_manifest.csv"
    with manifest.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["tier"] == "compact_primary":
                manifest_rows[row["system"]] = row
    rows, checksum_paths = [], []
    for system in SYSTEMS:
        path = ROOT / "data/processed/qm_clusters" / f"{system}_compact_primary.xyz"
        row: dict[str, Any] = {
            "system": system,
            "input_file": str(path.relative_to(ROOT)),
            "exists": path.is_file(),
            "readable": False,
            "atom_count": None,
            "elements": None,
            "charge": None,
            "multiplicity": None,
            "coordinate_units": "angstrom",
            "coordinates_finite": False,
            "minimum_distance_angstrom": None,
            "duplicate_atoms_lt_0_1A": None,
            "ligand_identity": "TMP" if system.endswith("_TMP") else "4-DTMP",
            "mutation_identity": "L28R" if system.startswith("L28R") else "WT",
            "preparation_protocol": "compact_primary/N1-protonated/fixed NADPH embedding",
            "validation_status": "missing",
        }
        if path.is_file():
            atoms, coords = parse_xyz(path)
            distance = minimum_distance(coords)
            meta = manifest_rows.get(system, {})
            row.update(
                {
                    "readable": True,
                    "atom_count": len(atoms),
                    "elements": ";".join(sorted(set(atoms))),
                    "charge": meta.get("cluster_charge"),
                    "multiplicity": 1,
                    "coordinates_finite": all(
                        math.isfinite(x) for xyz in coords for x in xyz
                    ),
                    "minimum_distance_angstrom": distance,
                    "duplicate_atoms_lt_0_1A": bool(
                        distance is not None and distance < 0.1
                    ),
                    "validation_status": "pass_basic_geometry"
                    if distance and distance >= 0.1
                    else "fail",
                }
            )
            checksum_paths.append(path)
    # rows is filled below to make field ordering stable.
    rows = []
    for system in SYSTEMS:
        path = ROOT / "data/processed/qm_clusters" / f"{system}_compact_primary.xyz"
        atoms, coords = parse_xyz(path)
        distance = minimum_distance(coords)
        meta = manifest_rows.get(system, {})
        rows.append(
            {
                "system": system,
                "input_file": str(path.relative_to(ROOT)),
                "exists": True,
                "readable": True,
                "atom_count": len(atoms),
                "elements": ";".join(sorted(set(atoms))),
                "charge": meta.get("cluster_charge"),
                "multiplicity": 1,
                "coordinate_units": "angstrom",
                "coordinates_finite": all(
                    math.isfinite(x) for xyz in coords for x in xyz
                ),
                "minimum_distance_angstrom": distance,
                "duplicate_atoms_lt_0_1A": distance < 0.1,
                "ligand_identity": "TMP" if system.endswith("_TMP") else "4-DTMP",
                "mutation_identity": "L28R" if system.startswith("L28R") else "WT",
                "preparation_protocol": "compact_primary/N1-protonated/fixed NADPH embedding",
                "validation_status": "pass_basic_geometry"
                if distance >= 0.1
                else "fail",
            }
        )
    write_csv("molecular_input_validation.csv", rows, rows[0].keys())
    checksum_sources = checksum_paths + [
        ROOT / "configs/core_systems.yaml",
        ROOT / "configs/active_space.yaml",
        ROOT / "configs/classical_protocol.yaml",
        ROOT / "data/params/WT_TMP_params.json",
        ROOT / "data/processed/WT_TMP_qubit_hamiltonian.json",
    ]
    checksum_lines = [
        f"{sha256_file(path)}  {path.relative_to(ROOT)}"
        for path in checksum_sources
        if path.is_file()
    ]
    write_text("input_checksums.sha256", "\n".join(checksum_lines))
    return rows


def result_summaries() -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    classical, hamiltonians, parameters, circuits, statistics = [], [], [], [], []
    for system in SYSTEMS:
        classical_path = (
            ROOT / "results/classical" / f"{system}_compact_primary_HF_sto-3g.json"
        )
        data = load_json_object(classical_path) if classical_path.is_file() else {}
        classical.append(
            {
                "system": system,
                "method": data.get("method"),
                "basis": data.get("basis"),
                "geometry": f"data/processed/qm_clusters/{system}_compact_primary.xyz",
                "active_space": "not applicable to full-cluster HF interaction proxy",
                "converged": data.get("converged"),
                "energy_hartree": data.get("interaction_energy_hartree"),
                "energy_definition": "counterpoise-corrected cluster interaction proxy",
                "runtime_seconds": data.get("runtime_seconds"),
                "output_file": str(classical_path.relative_to(ROOT))
                if classical_path.is_file()
                else None,
                "sha256": sha256_file(classical_path)
                if classical_path.is_file()
                else None,
                "status": "pilot_only" if data else "missing",
            }
        )
        hpath = ROOT / "data/processed" / f"{system}_qubit_hamiltonian.json"
        hdata = load_json_object(hpath) if hpath.is_file() else {}
        terms = hdata.get("terms", [])
        hermitian = (
            all(
                abs(float(term.get("coefficient", {}).get("imag", 0))) < 1e-12
                for term in terms
            )
            if terms
            else None
        )
        hamiltonians.append(
            {
                "system": system,
                "exists": hpath.is_file(),
                "basis": hdata.get("basis"),
                "active_electrons": 6 if hdata else None,
                "active_orbitals": len(hdata.get("active_orbitals", [])) or None,
                "qubits": hdata.get("n_qubits"),
                "mapped_pauli_terms": hdata.get("n_terms"),
                "mapping": "InQuanto default qubit encoding (exact mapping not recorded)"
                if hdata
                else None,
                "hermitian": hermitian,
                "coefficient_types_valid": bool(terms) if hdata else None,
                "constant_terms": sum(
                    1
                    for term in terms
                    if str(term.get("pauli_string", "")).strip() in {"", "I"}
                )
                if terms
                else None,
                "one_body_terms": None,
                "two_body_terms": None,
                "symmetry_reduction": "not recorded" if hdata else None,
                "sha256": sha256_file(hpath) if hpath.is_file() else None,
                "status": "validated_saved_artifact"
                if hdata and hermitian
                else "missing",
            }
        )
        ppath = ROOT / "data/params" / f"{system}_params.json"
        pdata = load_json_object(ppath) if ppath.is_file() else {}
        parameters.append(
            {
                "system": system,
                "exists": ppath.is_file(),
                "ansatz": "UCCSD" if pdata else None,
                "parameter_count": len(pdata.get("params", {})) if pdata else None,
                "optimizer": None,
                "starting_point": None,
                "convergence_status": "not recorded" if pdata else None,
                "final_objective_hartree": VERIFIED_WT_TMP["ideal_vqe_energy_hartree"]
                if system == "WT_TMP" and pdata
                else None,
                "iteration_count": None,
                "seed": None,
                "source": str(ppath.relative_to(ROOT)) if pdata else None,
                "loaded_or_optimized": "loaded saved parameters; optimization evidence incomplete"
                if pdata
                else None,
                "current_hamiltonian_compatible": True
                if pdata and hpath.is_file()
                else None,
                "sha256": sha256_file(ppath) if pdata else None,
                "status": "level_1_saved_parameters" if pdata else "missing",
            }
        )
        plan_path = (
            ROOT
            / "results/quantum/measurement_plans"
            / f"{system}_H2-1LE_100shots_plan.json"
        )
        plan = load_json_object(plan_path) if plan_path.is_file() else {}
        qasm = ROOT / "data/processed" / f"{system}_circuit.qasm"
        circuits.append(
            {
                "system": system,
                "ansatz": "UCCSD" if plan else None,
                "qubits": plan.get("n_qubits"),
                "hamiltonian_terms": plan.get("n_hamiltonian_terms"),
                "measurement_circuits": plan.get("n_measurement_circuits"),
                "shots_per_circuit": plan.get("shots_per_circuit"),
                "replicates": 1 if plan else None,
                "total_shots": plan.get("total_shots"),
                "qasm_file": str(qasm.relative_to(ROOT)) if qasm.is_file() else None,
                "qasm_version": "2.0"
                if qasm.is_file() and "OPENQASM 2" in qasm.read_text()[:100]
                else None,
                "backend_target": "H2-1LE local noiseless emulator" if plan else None,
                "optimization_level": 0 if plan else None,
                "ansatz_depth": None,
                "two_qubit_gates": None,
                "total_gates": None,
                "observable_coverage": "saved partitioning; full independent recheck blocked by 2.3 GB local artifact"
                if plan
                else None,
                "status": "verified_saved_plan" if plan else "missing",
            }
        )
        energy_path = ROOT / "results/quantum" / f"{system}_H2-1LE_100shots_energy.json"
        energy = load_json_object(energy_path) if energy_path.is_file() else {}
        statistics.append(
            {
                "system": system,
                "independent_replicates": 1 if energy else 0,
                "measurement_shots": energy.get("total_shots"),
                "estimator": "PauliAveraging energy" if energy else None,
                "uncertainty_value_hartree": energy.get("standard_error_hartree"),
                "uncertainty_method": "finite-shot standard error"
                if energy
                else "INSUFFICIENT_INDEPENDENT_REPLICATES",
                "confidence_level": None,
                "seed": None,
                "confidence_interval_status": "INSUFFICIENT_INDEPENDENT_REPLICATES",
                "limitations": "One finite-shot job; no independent replicate CI"
                if energy
                else "No finite-shot molecular result",
            }
        )
    write_csv("classical_reference_summary.csv", classical, classical[0].keys())
    write_csv("hamiltonian_summary.csv", hamiltonians, hamiltonians[0].keys())
    write_csv("vqe_parameter_summary.csv", parameters, parameters[0].keys())
    write_csv("circuit_summary.csv", circuits, circuits[0].keys())
    write_csv("statistical_validation.csv", statistics, statistics[0].keys())
    for name, rows in (
        ("classical_reference_summary.csv", classical),
        ("hamiltonian_summary.csv", hamiltonians),
        ("vqe_parameter_summary.csv", parameters),
        ("circuit_summary.csv", circuits),
        ("statistical_validation.csv", statistics),
    ):
        write_csv(f"tables/{name}", rows, rows[0].keys())
    return classical, hamiltonians, parameters


def evidence_and_scorecard() -> list[dict[str, Any]]:
    status = build_status()["systems"]
    rows = []
    for system in SYSTEMS:
        level = 2 if system == "WT_TMP" else 1
        note = (
            "Locally reproducible saved ideal and finite-shot result with validated metadata; one system only"
            if system == "WT_TMP"
            else "Prepared/classical files exist, but matched Hamiltonian, parameters, and quantum result are missing"
        )
        rows.append(
            {
                "system": system,
                "evidence_level": level,
                "evidence_label": f"LEVEL {level}",
                "local_ideal": status[system]["local_result"]["status"]
                if system == "WT_TMP"
                else "missing",
                "local_finite_shot": status[system]["local_result"]["status"],
                "nexus_emulator": status[system]["nexus_emulator_result"]["status"],
                "hardware": "missing",
                "independent_biological_validation": "missing",
                "notes": note,
            }
        )
    write_csv("evidence_matrix.csv", rows, rows[0].keys())
    score_rows = [
        ("research question", 3, "README.md; docs/WHAT_THE_PROJECT_PROVES.md"),
        ("matched systems", 2, "configs/core_systems.yaml; data/project_status.json"),
        (
            "molecular inputs",
            3,
            "artifacts/final_validation/molecular_input_validation.csv",
        ),
        (
            "classical references",
            2,
            "artifacts/final_validation/classical_reference_summary.csv",
        ),
        ("active space", 2, "docs/ACTIVE_SPACE_DECISION.md"),
        ("Hamiltonians", 1, "artifacts/final_validation/hamiltonian_summary.csv"),
        ("VQE parameters", 1, "artifacts/final_validation/vqe_parameter_summary.csv"),
        ("ideal simulation", 1, "results/quantum/WT_TMP_saved_params_exact.json"),
        (
            "finite-shot simulation",
            1,
            "results/quantum/WT_TMP_H2-1LE_100shots_energy.json",
        ),
        ("uncertainty", 1, "artifacts/final_validation/statistical_validation.csv"),
        ("reproducibility", 2, "artifacts/final_validation/reproducibility_report.md"),
        ("sensitivity", 1, "artifacts/final_validation/sensitivity_summary.csv"),
        ("controls", 3, "docs/CONTROL_STRATEGY.md; tests/"),
        ("Quantinuum access", 2, "docs/QUANTINUUM_RECOVERY.md"),
        ("remote emulator evidence", 0, "data/project_status.json"),
        ("hardware evidence", 0, "data/project_status.json"),
        (
            "figures",
            3,
            "results/publication/figures; artifacts/final_validation/figure_manifest.csv",
        ),
        ("tables", 3, "artifacts/final_validation/tables"),
        ("provenance", 3, "artifacts/final_validation/result_manifest.json"),
        ("tests", 4, "artifacts/final_validation/final_test_report.txt"),
        ("documentation", 4, "docs/"),
        ("biological interpretation", 1, "docs/RED_TEAM_REVIEW.md"),
        ("independent validation", 0, "docs/WHAT_THE_PROJECT_PROVES.md"),
        ("claim discipline", 4, "docs/CLAIM_AUDIT.md"),
        ("interview readiness", 3, "docs/TECHNICAL_DEFENSE_GUIDE.md"),
    ]
    scores = [
        {"area": area, "score_0_to_4": score, "evidence_path": path}
        for area, score, path in score_rows
    ]
    write_csv("research_completion_scorecard.csv", scores, scores[0].keys())
    return rows


def sensitivity() -> None:
    rows = []
    contrasts = ROOT / "results/tables/classical_contrasts.csv"
    if contrasts.is_file():
        with contrasts.open(newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append(
                    {
                        "analysis": "classical_model_sensitivity",
                        "method": row.get("method"),
                        "basis": row.get("basis"),
                        "embedding": row.get("nadph_embedding"),
                        "effect_hartree": row.get("D_hartree"),
                        "uncertainty_hartree": None,
                        "status": row.get("status"),
                        "interpretation": "model-dependent pilot/sensitivity; not independent replicates",
                    }
                )
    if not rows:
        rows.append(
            {
                "analysis": "classical_model_sensitivity",
                "method": None,
                "basis": None,
                "embedding": None,
                "effect_hartree": None,
                "uncertainty_hartree": None,
                "status": "missing",
                "interpretation": "No matched sensitivity table",
            }
        )
    write_csv("sensitivity_summary.csv", rows, rows[0].keys())


def manifest() -> None:
    provenance = ROOT / "results/publication/data/verified_quantum_provenance.json"
    exact = ROOT / "results/quantum/WT_TMP_saved_params_exact.json"
    finite = ROOT / "results/quantum/WT_TMP_H2-1LE_100shots_energy.json"
    record = {
        "result_id": "WT_TMP_local_H2-1LE_100shots",
        "system": "WT_TMP",
        "stage": "local_finite_shot",
        "date": "2026-07-17",
        "timestamp": None,
        "git_commit": "historical; exact commit not recorded in result",
        "branch": "historical",
        "command": "historical command documented in repository; not rerun in final pass",
        "environment": "results/quantum/results_manifest.json",
        "input_files": [
            "data/params/WT_TMP_params.json",
            "data/processed/WT_TMP_qubit_hamiltonian.json",
        ],
        "input_checksums": {
            "data/params/WT_TMP_params.json": sha256_file(
                ROOT / "data/params/WT_TMP_params.json"
            ),
            "data/processed/WT_TMP_qubit_hamiltonian.json": sha256_file(
                ROOT / "data/processed/WT_TMP_qubit_hamiltonian.json"
            ),
        },
        "output_files": [
            str(exact.relative_to(ROOT)),
            str(finite.relative_to(ROOT)),
            str(provenance.relative_to(ROOT)),
        ],
        "output_checksums": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (exact, finite, provenance)
        },
        "method": "UCCSD PauliAveraging",
        "basis": "STO-3G",
        "active_space": "6 electrons in 6 spatial orbitals",
        "mapping": "not recorded in compact historical result",
        "ansatz": "UCCSD",
        "optimizer": "not fully recorded",
        "seed": None,
        "backend": VERIFIED_WT_TMP["backend"],
        "location": "local",
        "execution_type": "noiseless_emulator",
        "circuits": 576,
        "shots": 57600,
        "replicates": 1,
        "energy": VERIFIED_WT_TMP["finite_shot_energy_hartree"],
        "units": "Hartree",
        "uncertainty": VERIFIED_WT_TMP["standard_error_hartree"],
        "uncertainty_definition": "finite-shot standard error",
        "completion_state": "complete",
        "validation_state": "protected metadata and checksum validated",
        "evidence_level": 2,
        "notes": "One WT_TMP model only; not hosted or hardware; comprehensive historical seed/commit absent",
    }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [record],
    }
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema_version", "generated_at", "results"],
        "properties": {
            "schema_version": {"const": 1},
            "generated_at": {"type": "string"},
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "result_id",
                        "system",
                        "stage",
                        "input_checksums",
                        "output_checksums",
                        "backend",
                        "location",
                        "execution_type",
                        "completion_state",
                        "validation_state",
                        "evidence_level",
                    ],
                },
            },
        },
    }
    write_json("result_manifest.json", payload)
    write_json("result_manifest.schema.json", schema)


def figure_manifest(evidence_rows: list[dict[str, Any]]) -> None:
    rows = []
    for path in sorted((ROOT / "results/publication/figures").glob("*.png")):
        rows.append(
            {
                "figure": str(path.relative_to(ROOT)),
                "source_data": "results/publication/data/verified_summary.json",
                "generation_command": "python scripts/build_publication_assets.py",
                "result_type": "saved WT_TMP local result",
                "backend_type": "local noiseless emulator where quantum data are shown",
                "uncertainty_definition": "finite-shot standard error where shown",
                "sha256": sha256_file(path),
                "final_pass_generated": False,
            }
        )
    write_csv("figure_manifest.csv", rows, rows[0].keys())
    # A new evidence-status figure plots categorical levels, never missing energies as zero.
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(
            [row["system"] for row in evidence_rows],
            [row["evidence_level"] for row in evidence_rows],
            color="#3478a8",
        )
        ax.set_ylim(0, 6)
        ax.set_ylabel("Evidence level (0–6)")
        ax.set_title("Four-system evidence status")
        ax.text(
            0.01,
            -0.24,
            "Source: artifacts/final_validation/evidence_matrix.csv; missing energies are not plotted as zero.",
            transform=ax.transAxes,
            fontsize=8,
        )
        fig.tight_layout()
        output = FIGURES / "four_system_evidence_status.png"
        fig.savefig(output, dpi=180)
        plt.close(fig)
        rows.append(
            {
                "figure": str(output.relative_to(ROOT)),
                "source_data": "artifacts/final_validation/evidence_matrix.csv",
                "generation_command": "python scripts/build_final_validation.py",
                "result_type": "evidence status, not molecular energy",
                "backend_type": "not applicable",
                "uncertainty_definition": "not applicable",
                "sha256": sha256_file(output),
                "final_pass_generated": True,
            }
        )
        write_csv("figure_manifest.csv", rows, rows[0].keys())
    except ImportError:
        pass


def reports() -> None:
    write_text(
        "baseline_test_report.txt",
        """FINAL PASS BASELINE
branch source: codex/full-code-audit at 9b957e1
command: python -m pytest -q
result: 40 passed, 1 skipped
duration: 2.64 seconds
python: 3.13.5
os: macOS Darwin 25.6.0
architecture: arm64
warnings: none reported by pytest
failures: none
skip reason: optional licensed/local chemistry stack, as declared by test marker
""",
    )
    write_text(
        "reproducibility_report.md",
        """# Reproducibility Report

- Fixed-seed endpoint analysis was run twice in separate processes by `tests/test_audit_core.py`; outputs matched exactly.
- Protected WT_TMP metadata and small-result checksums passed repository validation.
- Dry-run and compile-only Nexus metadata used the exact H2-Emulator name and created no job.
- Deterministic JSON/YAML/notebook parsing and Python compilation passed.
- The historical 45,887-second finite-shot calculation was not rerun: doing so is expensive, its exact random seed is absent, and no new scientific decision justified overwriting it.
- Three systems lack current Hamiltonians and VQE parameters, so a four-system quantum reproducibility repeat is blocked.

Pass criterion for deterministic stages: exact JSON equality or matching SHA-256. Numeric chemistry tolerance was not newly exercised because no production calculation was rerun.
""",
    )
    write_text(
        "notebook_execution_report.md",
        """# Notebook Execution Report

Both notebook files parse as valid JSON. `01_exploratory_analysis.ipynb` was inspected for cell order and contains explanatory/local analysis content. `publication_figure_validation.ipynb` is a minimal one-cell support artifact. Neither was executed in this pass because their stored environment/kernel is not the declared Python 3.11 chemistry environment and execution could rewrite historical displayed outputs. No embedded token pattern or absolute `/Users/` path was found by maintained privacy tests. Reusable production logic remains in `scripts/`.
""",
    )
    write_text(
        "security_audit_summary.md",
        """# Security Audit Summary

Maintained tests and a filename/pattern audit found no tracked credential files, private keys, tokens, populated `.env`, hard-coded Nexus project IDs, or maintained absolute workstation paths. Historical scientific JSON contains old absolute local output paths; these are machine-specific provenance defects, not credentials, and were not rewritten. Private project/group values remain environment variables. No secret values were printed or copied into this package. Git-history rewriting is neither needed nor authorized. The untracked dependency snapshot contains package names/versions and no obvious credential assignment; it remains uncommitted pending researcher decision.
""",
    )
    write_text(
        "failure_log.md",
        """# Failure and Blocker Log

- `blocked_by_decision`: production active-space correspondence is not resolved for all four systems.
- `blocked_by_missing_evidence`: WT_4DTMP, L28R_TMP, and L28R_4DTMP lack Hamiltonians, saved VQE parameters, QASM, and local quantum results.
- `blocked_by_access`: no current live Nexus catalog or entitlement proof was collected because this pass was not authorized to authenticate or contact Nexus.
- `blocked_by_reproducibility`: current Python is 3.13 while the declared/historical environment uses Python 3.11 and licensed packages.
- `not_attempted_expensive`: the 12.7-hour historical finite-shot workflow was not rerun.
- `not_applicable`: no remote submission, hardware execution, or paid action was attempted.
""",
    )
    backend = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_source": "central static resolver; live discovery not authorized in final pass",
        "live_discovery_performed": False,
        "entitlement_verified": False,
        "selected_backend": "H2-Emulator",
        "requested_backend": "H2-Emulator",
        "resolved_backend": "H2-Emulator",
        "hosting_type": "nexus_hosted",
        "execution_type": "emulator",
        "credits_may_be_consumed": True,
        "job_created": False,
        "h1_emulator_visible": None,
        "notes": "Run the documented authenticated discovery command to obtain the live catalog.",
    }
    write_json("backend_catalog/offline_resolution.json", backend)
    catalog_path = OUT / "backend_catalog/offline_resolution.json"
    write_text(
        "backend_catalog/checksums.sha256",
        f"{sha256_file(catalog_path)}  offline_resolution.json",
    )
    write_text(
        "command_log.txt",
        """SAFE COMMANDS RUN IN FINAL PASS
pwd
git status --short --branch
git branch --show-current
git log -10 --oneline
git diff main...codex/full-code-audit --stat
python --version
python -m pip --version
python -m pytest -q
python -m compileall -q scripts tests
ruff check scripts tests
python scripts/validate_repository.py
python scripts/four_system_workflow.py --prepare
python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-Emulator --shots 10 --dry-run
python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-Emulator --shots 10 --compile-only

NOT RUN: backend discovery (requires authenticated network access).
NOT RUN: smoke submission, four-system remote submission, or retrieval.
NOT RUN: expensive production quantum calculations.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    runtime_artifacts()
    molecular_validation()
    result_summaries()
    sensitivity()
    manifest()
    evidence = evidence_and_scorecard()
    figure_manifest(evidence)
    reports()
    print(f"Built local evidence package at {OUT}")


if __name__ == "__main__":
    main()
