#!/usr/bin/env python3
"""Calculate the prespecified difference-in-differences endpoint.

Input rows must identify genuine independent replicates. Repeated shots within
one quantum job are not replicates. The command writes a local JSON summary and
never contacts a remote service. Its bootstrap interval is meaningful only for
the replicate population represented by the input file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYSTEM_ORDER = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")
REQUIRED = set(SYSTEM_ORDER)


def contrast(values: dict[str, float]) -> float:
    """Return (L28R_4DTMP-WT_4DTMP) - (L28R_TMP-WT_TMP), in input units."""
    return (values["L28R_4DTMP"] - values["WT_4DTMP"]) - (
        values["L28R_TMP"] - values["WT_TMP"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        type=Path,
        help="CSV columns: system_id, replicate, interaction_energy_hartree",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/tables/endpoint.json")
    )
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    missing_columns = {"system_id", "replicate", "interaction_energy_hartree"} - set(
        frame.columns
    )
    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")
    missing_systems = REQUIRED - set(frame.system_id)
    if missing_systems:
        raise ValueError(f"Missing systems: {sorted(missing_systems)}")
    unexpected_systems = set(frame.system_id) - REQUIRED
    if unexpected_systems:
        raise ValueError(f"Unexpected systems: {sorted(unexpected_systems)}")
    if args.bootstrap <= 0:
        raise ValueError("--bootstrap must be positive")
    replicate_counts = frame.groupby("system_id")["replicate"].nunique()
    too_few = sorted(replicate_counts[replicate_counts < 2].index)
    if too_few:
        raise ValueError(
            "A bootstrap confidence interval needs at least two independent "
            f"replicates per system; insufficient systems: {too_few}. Do not "
            "treat repeated shots from one job as replicates."
        )
    grouped = {
        key: group.interaction_energy_hartree.to_numpy(float)
        for key, group in frame.groupby("system_id")
    }
    # Use a fixed order so one random seed gives the same draws in every process.
    means = {key: float(np.mean(grouped[key])) for key in SYSTEM_ORDER}
    estimate = contrast(means)
    rng = np.random.default_rng(args.seed)
    samples = np.empty(args.bootstrap)
    for index in range(args.bootstrap):
        draw = {
            key: float(
                np.mean(rng.choice(grouped[key], len(grouped[key]), replace=True))
            )
            for key in SYSTEM_ORDER
        }
        samples[index] = contrast(draw)
    result = {
        "endpoint": "D",
        "estimate_hartree": estimate,
        "ci95_hartree": np.quantile(samples, [0.025, 0.975]).tolist(),
        "system_means_hartree": means,
        "bootstrap_samples": args.bootstrap,
        "seed": args.seed,
        "uncertainty_definition": (
            "percentile 95% bootstrap interval over labeled independent replicates"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
