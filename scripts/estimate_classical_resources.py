#!/usr/bin/env python3
"""Estimate AO counts and dense-storage scales before launching cluster SCF jobs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pyscf import gto

ROOT = Path(__file__).resolve().parents[1]
CLUSTERS = ROOT / "data/processed/qm_clusters"
OUTPUT = ROOT / "results/tables/classical_resource_estimates.csv"
BASES = ("sto-3g", "3-21g", "def2-svp")


def main() -> None:
    rows = []
    for metadata_path in sorted(CLUSTERS.glob("*.json")):
        metadata = json.loads(metadata_path.read_text())
        if metadata["tier"] not in {"compact_primary", "expanded_primary"}:
            continue
        xyz = metadata_path.with_suffix(".xyz")
        for basis in BASES:
            molecule = gto.M(
                atom=str(xyz),
                basis=basis,
                charge=int(metadata["charge"]),
                spin=0,
                unit="Angstrom",
                verbose=0,
            )
            nao = molecule.nao_nr()
            rows.append(
                {
                    "system": metadata["system"],
                    "tier": metadata["tier"],
                    "basis": basis,
                    "atoms": molecule.natm,
                    "electrons": molecule.nelectron,
                    "ao_functions": nao,
                    "one_dense_matrix_mb": 8 * nao**2 / 1e6,
                    "in_core_eri_tb": 8 * nao**4 / 1e12,
                    "recommendation": "direct/density-fitted SCF required"
                    if 8 * nao**4 / 1e12 > 0.01
                    else "in-core may fit",
                }
            )
    frame = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT, index=False)
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
