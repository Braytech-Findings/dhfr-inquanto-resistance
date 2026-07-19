#!/usr/bin/env python3
"""Create the classical calculation manifest from the processed structures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
OUTPUT = ROOT / "results/tables/classical_inputs.csv"


def main() -> None:
    rows = []
    for pdb in sorted(PROCESSED.glob("*_minimized*.pdb")):
        stem = pdb.stem
        if stem.endswith("_minimized"):
            system = stem[:-10]
            suffix = "neutral"
        else:
            prefix = stem.removesuffix("_minimized")
            system, suffix = (
                prefix.rsplit("_", 1)
                if "_" in prefix
                and prefix.rsplit("_", 1)[1] in {"dry", "expanded6A", "protonatedN1"}
                else (prefix, "neutral")
            )
            if suffix == "neutral":
                system = prefix
        rows.append(
            {
                "system": system,
                "structure_suffix": suffix,
                "pdb_path": str(pdb),
                "json_path": str(PROCESSED / f"{pdb.stem}.json"),
            }
        )
    df = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
