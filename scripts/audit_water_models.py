#!/usr/bin/env python3
"""Run the standard structural QC checks over dry and expanded-water models."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from inspect_structures import SYSTEMS, inspect

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = []
    for system in SYSTEMS:
        for model, suffix in (("dry", "dry"), ("expanded6A", "expanded6A")):
            path = ROOT / "data/processed" / f"{system}_minimized_{suffix}.pdb"
            row = inspect(system, path)
            row["water_model"] = model
            rows.append(row)
    frame = pd.DataFrame(rows)
    output = ROOT / "results/tables/water_model_qc.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(frame.to_string(index=False))
    if frame["status"].isin(["FAIL", "MISSING"]).any():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
