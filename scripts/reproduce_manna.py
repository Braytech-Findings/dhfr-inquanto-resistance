#!/usr/bin/env python3
"""Reproduce three headline results from the Manna et al. public data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/external/NatureCommunication2021_Manna"
TABLES = ROOT / "results/tables"
FIGURES = ROOT / "results/figures"


def replicate_values(row: pd.Series) -> np.ndarray:
    return row.filter(like="mic_values_").dropna().to_numpy(float)


def main() -> None:
    if not RAW.exists():
        raise SystemExit("Missing raw source. Clone the repository recorded in configs/source_manifest.yaml")
    ic95 = pd.read_csv(RAW / "Figure_2/Figure_2b_2c/IC95.csv")
    mutations = pd.read_csv(RAW / "Figure_4/Figure_4e/Day21_MajorMutations.csv")
    evolution = pd.read_csv(RAW / "Figure_4/Figure_4a_4b_4c/DataWithHillFitParameters.csv")

    l28r = ic95[ic95.strain.eq("L28R")].set_index("drug")
    l28r_tmp = float(np.median(replicate_values(l28r.loc["TMP"])))
    l28r_dtmp = float(np.median(replicate_values(l28r.loc["V-041"])))

    l28r_frequency = mutations[mutations.Mutation.eq("L28R")].iloc[0]
    final = evolution[evolution["Day#"].eq(21)].groupby(["EvolvedIn", "Culture#"])["fIC50-A"].mean()
    final_tmp = final.loc["TMP"].to_numpy(float)
    final_dtmp = final.loc["V041"].to_numpy(float)

    rows = [
        {"metric": "L28R median IC95", "tmp_value": l28r_tmp, "dtmp_value": l28r_dtmp,
         "ratio_tmp_to_dtmp": l28r_tmp / l28r_dtmp, "unit": "ug/mL", "source_figure": "2b-2c"},
        {"metric": "L28R day-21 mutation frequency", "tmp_value": float(l28r_frequency.TMP),
         "dtmp_value": float(l28r_frequency.V041), "ratio_tmp_to_dtmp": float(l28r_frequency.TMP / l28r_frequency.V041),
         "unit": "percent", "source_figure": "4e"},
        {"metric": "Mean day-21 fitted IC50", "tmp_value": float(final_tmp.mean()),
         "dtmp_value": float(final_dtmp.mean()), "ratio_tmp_to_dtmp": float(final_tmp.mean() / final_dtmp.mean()),
         "unit": "ug/mL", "source_figure": "4a-4c"},
    ]
    result = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    result.to_csv(TABLES / "manna_headline_results.csv", index=False)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    labels = ["TMP", "4-DTMP"]
    axes[0].bar(labels, [l28r_tmp, l28r_dtmp], color=["#777777", "#159d9a"])
    axes[0].set_title("L28R median IC95")
    axes[0].set_ylabel("ug/mL")
    axes[1].bar(labels, [l28r_frequency.TMP, l28r_frequency.V041], color=["#777777", "#159d9a"])
    axes[1].set_title("L28R frequency, day 21")
    axes[1].set_ylabel("percent")
    axes[2].boxplot([final_tmp, final_dtmp], tick_labels=labels)
    axes[2].set_title("Final fitted IC50")
    axes[2].set_ylabel("ug/mL")
    fig.tight_layout()
    fig.savefig(FIGURES / "manna_reproduction.png", dpi=200)
    plt.close(fig)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

