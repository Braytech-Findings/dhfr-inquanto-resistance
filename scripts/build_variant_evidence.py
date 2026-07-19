#!/usr/bin/env python3
"""Build the phenotype-only evidence table for the frozen variant panel."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/external/NatureCommunication2021_Manna"
CONFIG = ROOT / "configs/variant_panel.yaml"
OUTPUT = ROOT / "results/tables/variant_panel_evidence.csv"


def expands_group(label: str) -> list[str]:
    """Expand labels such as P21L/S/Q into P21L, P21S, and P21Q."""
    parts = label.split("/")
    if len(parts) == 1:
        return parts
    prefix = parts[0][:-1]
    return [parts[0], *(prefix + part for part in parts[1:])]


def main() -> None:
    panel = yaml.safe_load(CONFIG.read_text())
    selected = {entry["variant"]: entry for entry in panel["systems"]}
    trajectories = pd.read_csv(
        RAW / "Figure_4/FIgure_4d_4f/Cultures_MutationFrequencies.csv"
    )
    major = pd.read_csv(RAW / "Figure_4/Figure_4e/Day21_MajorMutations.csv")
    rows = []
    for variant, metadata in selected.items():
        row: dict[str, object] = {"variant": variant, **metadata}
        exact = trajectories[trajectories["Mutation"].eq(variant)]
        for drug in ("TMP", "V041"):
            drug_rows = exact[exact["Drug"].eq(drug)]
            row[f"{drug}_n_cultures"] = int(drug_rows["Replica"].nunique())
            row[f"{drug}_mean_day0_percent"] = drug_rows["0.0"].mean()
            row[f"{drug}_mean_day21_percent"] = drug_rows["21.0"].mean()
        grouped = major[
            major["Mutation"].apply(lambda label: variant in expands_group(label))
        ]
        if not grouped.empty:
            row["grouped_day21_TMP_percent"] = float(grouped.iloc[0]["TMP"])
            row["grouped_day21_V041_percent"] = float(grouped.iloc[0]["V041"])
        rows.append(row)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
