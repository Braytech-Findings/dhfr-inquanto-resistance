#!/usr/bin/env python3
"""Collect converged counterpoise calculations and calculate labeled contrasts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from analyze_endpoint import contrast

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results/classical"
OUTPUT = ROOT / "results/tables/classical_interaction_energies.csv"
CONTRASTS = ROOT / "results/tables/classical_contrasts.csv"


def main() -> None:
    rows = []
    for path in sorted(INPUT.glob("*.json")):
        result = json.loads(path.read_text())
        rows.append(
            {
                "system_id": result["system"],
                "tier": result["tier"],
                "method": result["method"],
                "basis": result["basis"],
                "nadph_embedding": result["nadph_embedding"],
                "interaction_energy_hartree": result["interaction_energy_hartree"],
                "converged": result["converged"],
                "source_file": str(path.relative_to(ROOT)),
            }
        )
    frame = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT, index=False)
    contrast_rows = []
    group_columns = ["tier", "method", "basis", "nadph_embedding"]
    for keys, group in frame.groupby(group_columns):
        values = dict(zip(group["system_id"], group["interaction_energy_hartree"], strict=True))
        if len(values) == 4:
            contrast_rows.append(
                {**dict(zip(group_columns, keys, strict=True)), "D_hartree": contrast(values),
                 "status": "pilot_only" if keys[1:] == ("HF", "sto-3g", True) else "sensitivity"}
            )
    contrasts = pd.DataFrame(contrast_rows)
    contrasts.to_csv(CONTRASTS, index=False)
    print(frame.to_string(index=False))
    print("\nContrasts (not automatically interpretable):")
    print(contrasts.to_string(index=False))


if __name__ == "__main__":
    main()

