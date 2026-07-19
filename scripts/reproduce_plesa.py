#!/usr/bin/env python3
"""Reproduce homolog-fitness and gain-of-function summaries from PlesaLab data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/external/PlesaLab_processed"
TABLES = ROOT / "results/tables"
FIGURES = ROOT / "results/figures"

FITNESS_COLUMNS = {
    "fitD05D03": "Complementation",
    "fitD06D03": "0.058 ug/mL TMP",
    "fitD07D03": "0.5 ug/mL TMP (MIC)",
    "fitD08D03": "1 ug/mL TMP",
    "fitD09D03": "10 ug/mL TMP",
    "fitD10D03": "50 ug/mL TMP",
    "fitD11D03": "200 ug/mL TMP",
}


def finite(series: pd.Series) -> pd.Series:
    """Return numeric finite values only."""
    values = pd.to_numeric(series, errors="coerce")
    return values[np.isfinite(values)]


def main() -> None:
    perfect_path = RAW / "perfects15_5BCs.csv"
    mutant_path = RAW / "mutIDinfo15.csv"
    if not perfect_path.exists() or not mutant_path.exists():
        raise SystemExit(
            "Missing processed PlesaLab data. See configs/source_manifest.yaml for the pinned archive."
        )

    perfects = pd.read_csv(perfect_path)
    mutants = pd.read_csv(mutant_path)
    distribution_rows: list[dict[str, object]] = []
    for column, condition in FITNESS_COLUMNS.items():
        values = finite(perfects[column])
        distribution_rows.append(
            {
                "condition": condition,
                "column": column,
                "n_homologs": int(values.size),
                "median_logfc": float(values.median()),
                "q25_logfc": float(values.quantile(0.25)),
                "q75_logfc": float(values.quantile(0.75)),
                "fraction_fit_ge_minus1": float((values >= -1).mean()),
            }
        )
    distributions = pd.DataFrame(distribution_rows)

    parent = perfects[["ID", "fitD05D03"]].rename(
        columns={"fitD05D03": "parent_fitness"}
    )
    single = mutants.loc[mutants["mutations"].eq(1), ["IDalign", "mutID", "fitD05D03"]]
    single = single.rename(columns={"fitD05D03": "mutant_fitness"})
    joined = single.merge(parent, left_on="IDalign", right_on="ID", how="inner")
    joined = joined.dropna(subset=["parent_fitness", "mutant_fitness"])
    dropout = joined[joined["parent_fitness"] < -1].copy()
    rescues = dropout[dropout["mutant_fitness"] >= -1].copy()
    rescue_summary = pd.DataFrame(
        [
            {
                "metric": "dropout parent homologs with measured single mutants",
                "value": int(dropout["IDalign"].nunique()),
            },
            {
                "metric": "unique single-mutant GOF rescues",
                "value": int(rescues["mutID"].nunique()),
            },
            {
                "metric": "dropout parent homologs with >=1 GOF rescue",
                "value": int(rescues["IDalign"].nunique()),
            },
        ]
    )

    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    distributions.to_csv(TABLES / "plesa_homolog_fitness_summary.csv", index=False)
    rescue_summary.to_csv(TABLES / "plesa_gof_summary.csv", index=False)
    rescues.assign(
        delta_fitness=rescues["mutant_fitness"] - rescues["parent_fitness"]
    ).to_csv(TABLES / "plesa_single_mutant_gof_rescues.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    plot_columns = list(FITNESS_COLUMNS)
    axes[0].boxplot(
        [finite(perfects[column]).to_numpy() for column in plot_columns],
        tick_labels=[
            FITNESS_COLUMNS[column].replace(" ug/mL TMP", "") for column in plot_columns
        ],
        showfliers=False,
    )
    axes[0].axhline(-1, color="#b33a3a", linestyle="--", linewidth=1)
    axes[0].tick_params(axis="x", rotation=55)
    axes[0].set_ylabel("Median fitness (log fold-change)")
    axes[0].set_title("DHFR homolog fitness across TMP selection")
    if not rescues.empty:
        axes[1].scatter(
            rescues["parent_fitness"], rescues["mutant_fitness"], s=12, alpha=0.55
        )
    axes[1].axvline(-1, color="#b33a3a", linestyle="--", linewidth=1)
    axes[1].axhline(-1, color="#b33a3a", linestyle="--", linewidth=1)
    axes[1].set_xlabel("Parent complementation fitness")
    axes[1].set_ylabel("Single-mutant complementation fitness")
    axes[1].set_title("Threshold-crossing GOF rescues")
    fig.tight_layout()
    fig.savefig(FIGURES / "plesa_reproduction.png", dpi=200)
    plt.close(fig)

    print(distributions.to_string(index=False))
    print(rescue_summary.to_string(index=False))


if __name__ == "__main__":
    main()
