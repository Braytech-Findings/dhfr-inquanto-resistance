#!/usr/bin/env python3
"""Build publication tables and figures from verified WT_TMP result files."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "publication"
HARTREE_TO_KCAL_MOL = 627.509474


def save(fig: plt.Figure, stem: str, alt: str) -> None:
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"{stem}.{suffix}", dpi=300, bbox_inches="tight")
    (OUT / "manifests" / f"{stem}.json").write_text(
        json.dumps(
            {"figure": stem, "alt_text": alt, "source": "verified WT_TMP JSON outputs"},
            indent=2,
        )
        + "\n"
    )
    plt.close(fig)


def main() -> None:
    exact = json.loads(
        (ROOT / "results/quantum/WT_TMP_saved_params_exact.json").read_text()
    )
    shot = json.loads(
        (ROOT / "results/quantum/WT_TMP_H2-1LE_100shots_energy.json").read_text()
    )
    plan = json.loads(
        (
            ROOT / "results/quantum/measurement_plans/WT_TMP_H2-1LE_100shots_plan.json"
        ).read_text()
    )
    params = json.loads((ROOT / "data/params/WT_TMP_params.json").read_text())["params"]
    for folder in (
        OUT / "data",
        OUT / "figures",
        OUT / "tables",
        OUT / "manifests",
        OUT / "reports",
    ):
        folder.mkdir(parents=True, exist_ok=True)
    scf, ideal, finite, se = (
        exact["scf_energy_hartree"],
        exact["vqe_energy_hartree"],
        shot["shot_based_energy_hartree"],
        shot["standard_error_hartree"],
    )
    error = finite - ideal
    energy = pd.DataFrame(
        {
            "method": [
                "Hartree–Fock",
                "Ideal saved-parameter VQE",
                "Finite-shot H2-1LE local emulator",
            ],
            "energy_hartree": [scf, ideal, finite],
            "standard_error_hartree": [0.0, 0.0, se],
            "relative_to_scf_millihartree": [
                0.0,
                (ideal - scf) * 1000,
                (finite - scf) * 1000,
            ],
        }
    )
    energy.to_csv(OUT / "data/energy_results.csv", index=False)
    setup = pd.DataFrame(
        {
            "field": [
                "System",
                "Basis",
                "Active spatial orbitals",
                "Spatial orbitals",
                "Qubits",
                "UCCSD parameters",
                "Hamiltonian terms",
                "Grouped circuits",
                "Shots per circuit",
                "Total shots",
                "Backend",
            ],
            "value": [
                "WT_TMP",
                "STO-3G",
                "[208, 209, 210, 211, 212, 213]",
                6,
                12,
                len(params),
                plan["n_hamiltonian_terms"],
                plan["n_measurement_circuits"],
                plan["shots_per_circuit"],
                plan["total_shots"],
                "Quantinuum H2-1LE local noiseless emulator",
            ],
        }
    )
    setup.to_csv(OUT / "tables/computational_setup.csv", index=False)
    summary = {
        "hartree_to_kcal_per_mol": HARTREE_TO_KCAL_MOL,
        "scf_energy_hartree": scf,
        "ideal_vqe_energy_hartree": ideal,
        "finite_shot_energy_hartree": finite,
        "standard_error_hartree": se,
        "difference_from_exact_hartree": error,
        "absolute_error_millihartree": abs(error) * 1000,
        "absolute_error_kcal_per_mol": abs(error) * HARTREE_TO_KCAL_MOL,
        "standard_error_kcal_per_mol": se * HARTREE_TO_KCAL_MOL,
        "approximate_95_ci_hartree": [finite - 1.96 * se, finite + 1.96 * se],
        "backend": "Quantinuum H2-1LE local noiseless emulator",
    }
    (OUT / "data/verified_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(
        energy.method,
        energy.relative_to_scf_millihartree,
        color=["#6c757d", "#1976d2", "#00897b"],
    )
    ax.errorbar(
        2,
        energy.relative_to_scf_millihartree.iloc[2],
        yerr=se * 1000,
        color="black",
        capsize=5,
    )
    ax.set_ylabel("Energy relative to SCF (millihartree)")
    ax.set_title("WT_TMP energy estimates (exact vs finite-shot)")
    ax.tick_params(axis="x", rotation=18)
    save(
        fig,
        "energy_comparison",
        "Energy relative to Hartree–Fock for ideal and finite-shot VQE; finite-shot point has one-standard-error bar.",
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    values = [error, error * 1000, error * HARTREE_TO_KCAL_MOL]
    ax.bar(["Hartree", "millihartree", "kcal/mol"], values, color="#c75b39")
    ax.set_ylabel("Finite-shot minus exact energy (native unit)")
    ax.set_title("Finite-shot error relative to exact saved-parameter result")
    save(
        fig,
        "error_relative_to_exact",
        "Signed finite-shot energy error in three units.",
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(
        ["Hamiltonian Pauli terms", "Grouped measurement circuits"],
        [plan["n_hamiltonian_terms"], plan["n_measurement_circuits"]],
        color=["#6c757d", "#1976d2"],
    )
    ax.set_ylabel("Count")
    ax.set_title(
        f"Pauli grouping: {100 * (1 - plan['n_measurement_circuits'] / plan['n_hamiltonian_terms']):.1f}% fewer circuits than terms"
    )
    ax.text(
        1,
        plan["n_measurement_circuits"] + 60,
        f"{plan['total_shots']:,} total shots",
        ha="center",
    )
    save(
        fig,
        "hamiltonian_compression",
        "Hamiltonian has 1,819 Pauli terms grouped into 576 measurement circuits.",
    )
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.axvline(ideal, color="#1976d2", lw=2, label="Exact reference")
    ax.errorbar(
        finite,
        0.55,
        xerr=se,
        fmt="o",
        color="#00897b",
        capsize=6,
        label="Finite-shot ±1 SE",
    )
    ax.axvspan(
        finite - 1.96 * se,
        finite + 1.96 * se,
        color="#00897b",
        alpha=0.15,
        label="Approx. 95% interval",
    )
    ax.set_yticks([])
    ax.set_xlabel("Energy (Hartree)")
    ax.set_title("Finite sampling creates uncertainty")
    ax.legend()
    save(
        fig,
        "statistical_uncertainty",
        "Exact energy line and finite-shot estimate with one-standard-error and approximate 95 percent interval.",
    )
    fig, ax = plt.subplots(figsize=(9, 3))
    steps = [
        "DHFR–TMP\nstructure",
        "QM\ncluster",
        "6 spatial\norbitals",
        "12\nqubits",
        "UCCSD\nstate",
        "Pauli\ngroups",
        "H2-1LE\nmeasurements",
        "energy +\nuncertainty",
    ]
    ax.axis("off")
    for i, step in enumerate(steps):
        ax.text(
            i,
            0.5,
            step,
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=.45", "fc": "#e8f1fb", "ec": "#1976d2"},
        )
    for i in range(len(steps) - 1):
        ax.annotate(
            "", (i + 0.68, 0.5), (i + 0.32, 0.5), arrowprops={"arrowstyle": "->"}
        )
    ax.set_xlim(-0.7, 7.7)
    ax.set_ylim(0, 1)
    ax.set_title("Technical workflow: from structure to a finite-shot energy estimate")
    save(
        fig,
        "workflow_technical",
        "Workflow from DHFR–TMP structure through active space, qubits, measurements, and energy.",
    )
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    ax.text(
        0.5,
        0.65,
        "A huge molecule is like a big school.\nThis project studies one small classroom of important electron rooms.",
        ha="center",
        va="center",
        fontsize=14,
        bbox={"boxstyle": "round,pad=.7", "fc": "#fff4d6", "ec": "#c78b25"},
    )
    ax.text(
        0.5,
        0.15,
        "We repeat measurements (shots) to estimate energy, like repeating a science experiment.",
        ha="center",
        fontsize=11,
    )
    ax.set_title("Plain-language workflow")
    save(
        fig,
        "workflow_plain_language",
        "Simple explanation that the active space is a small selected part of a much larger molecule.",
    )
    pd.DataFrame(
        {
            "parameter": list(params),
            "value": list(params.values()),
            "class": [
                "double" if key.startswith("d") else "single/other" for key in params
            ],
        }
    ).to_csv(OUT / "data/uccsd_parameters.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(list(params.values()), bins=24, color="#7e57c2")
    ax.set_xlabel("Saved UCCSD parameter value")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of 117 saved UCCSD parameters")
    save(
        fig,
        "parameter_distribution",
        "Histogram of the 117 saved UCCSD parameter values.",
    )
    (OUT / "reports/README.md").write_text(
        "All assets are generated by `python scripts/build_publication_assets.py` from verified local JSON result files. H2-1LE is a local noiseless emulator, not physical hardware.\n"
    )


if __name__ == "__main__":
    main()
