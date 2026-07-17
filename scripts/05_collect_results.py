#!/usr/bin/env python3
"""Collect outputs produced by the earlier stages into a summary report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> None:
    rows = []
    for path in sorted((RESULTS / "classical").glob("*.json")):
        data = json.loads(path.read_text())
        rows.append({"source": path.name, "interaction_energy_hartree": data.get("interaction_energy_hartree", None)})
    df = pd.DataFrame(rows)
    (RESULTS / "tables").mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS / "tables" / "classical_summary.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
