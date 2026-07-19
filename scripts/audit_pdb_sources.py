#!/usr/bin/env python3
"""Audit deposited DHFR structures without modifying their coordinates."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from openmm import unit
from openmm.app import PDBFile

ROOT = Path(__file__).resolve().parents[1]


def audit(pdb_id: str) -> dict[str, object]:
    path = ROOT / "data/raw/pdbs" / f"{pdb_id}.pdb"
    text = path.read_text()
    pdb = PDBFile(str(path))
    xyz = np.asarray([p.value_in_unit(unit.angstrom) for p in pdb.positions])
    residues = list(pdb.topology.residues())
    ligand = next(r for r in residues if r.name == "TOP")
    ligand_heavy = [a.index for a in ligand.atoms() if a.element.symbol != "H"]
    res28 = next(r for r in residues if r.id == "28" and r.chain.id == ligand.chain.id)
    res28_heavy = [a.index for a in res28.atoms() if a.element.symbol != "H"]
    nadph = [r for r in residues if r.name == "NDP"]
    waters = [r for r in residues if r.name in {"HOH", "WAT"}]
    nearby_waters = 0
    for water in waters:
        oxygen = next(a.index for a in water.atoms() if a.element.symbol == "O")
        if np.linalg.norm(xyz[ligand_heavy] - xyz[oxygen], axis=1).min() <= 6.0:
            nearby_waters += 1
    resolution_match = re.search(r"REMARK   2 RESOLUTION\.\s+([0-9.]+) ANGSTROMS", text)
    altlocs = sorted(
        {
            line[16]
            for line in text.splitlines()
            if line.startswith(("ATOM  ", "HETATM")) and line[16].strip()
        }
    )
    missing = sum(
        1
        for line in text.splitlines()
        if line.startswith("REMARK 465")
        and re.match(r"REMARK 465\s+\w{3}\s+\w\s+\d+", line)
    )
    pair = np.linalg.norm(
        xyz[ligand_heavy, None, :] - xyz[res28_heavy][None, :, :], axis=2
    )
    return {
        "pdb_id": pdb_id,
        "resolution_angstrom": float(resolution_match.group(1))
        if resolution_match
        else np.nan,
        "chains": ",".join(sorted({r.chain.id for r in residues})),
        "ligand": ligand.name,
        "residue_28": res28.name,
        "nadph_residues": len(nadph),
        "waters_total": len(waters),
        "waters_within_6A": nearby_waters,
        "ligand_res28_min_A": float(pair.min()),
        "alternate_locations": ",".join(altlocs) or "none",
        "missing_residue_records": missing,
    }


def main() -> None:
    frame = pd.DataFrame([audit("6XG5"), audit("6XG4")])
    output = ROOT / "results/tables/pdb_source_audit.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
