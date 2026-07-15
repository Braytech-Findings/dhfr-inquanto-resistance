#!/usr/bin/env python3
"""Run structural QC over the four N1-protonated ligand models."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from inspect_structures import SYSTEMS, inspect

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = []
    for system in SYSTEMS:
        path = ROOT / "data/processed" / f"{system}_minimized_protonatedN1.pdb"
        rows.append(inspect(system, path))
    frame = pd.DataFrame(rows)
    output = ROOT / "results/tables/protonated_structure_qc.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(frame.to_string(index=False))
    if frame["status"].isin(["FAIL", "MISSING"]).any():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
