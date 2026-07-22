#!/usr/bin/env python3
"""Plot objective WT_TMP local finite-shot convergence evidence."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "artifacts/final_public_release/molecular/WT_TMP/local_finite_shot_replicates.csv"
)
OUT = ROOT / "artifacts/final_public_release/figures"
IDEAL = -2587.912001526413


def main() -> None:
    grouped = defaultdict(list)
    with SOURCE.open(newline="") as handle:
        for row in csv.DictReader(handle):
            grouped[int(row["shots_per_circuit"])].append(row)
    levels = sorted(grouped)
    means = [np.mean([float(r["energy_hartree"]) for r in grouped[n]]) for n in levels]
    replicate_sd = [
        np.std([float(r["energy_hartree"]) for r in grouped[n]], ddof=1) for n in levels
    ]
    propagated = [
        np.mean([float(r["uncertainty_hartree"]) for r in grouped[n]]) for n in levels
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].errorbar(levels, means, yerr=propagated, marker="o", capsize=4)
    axes[0].axhline(IDEAL, color="black", linestyle="--", label="protected ideal")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Shots per measurement circuit")
    axes[0].set_ylabel("WT_TMP energy (Hartree)")
    axes[0].set_title("Local finite-shot convergence")
    axes[0].legend()
    axes[1].plot(levels, propagated, marker="o", label="propagated uncertainty")
    axes[1].plot(levels, replicate_sd, marker="s", label="replicate SD")
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Shots per measurement circuit")
    axes[1].set_ylabel("Hartree")
    axes[1].set_title("Uncertainty and replicate variation")
    axes[1].legend()
    fig.suptitle("OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED")
    fig.tight_layout()
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"wt_tmp_local_convergence.{suffix}", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
