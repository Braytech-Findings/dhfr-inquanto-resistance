#!/usr/bin/env python3
"""Build fixed CHARMM36 NADPH point-charge embeddings at deposited coordinates."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from openmm import app, unit

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/pdbs"
OUTPUT = ROOT / "data/processed/embedding"
FORCEFIELD_PATH = Path(app.__file__).resolve().parent / "data/charmm36.xml"


def ndp_template() -> tuple[dict[str, float], list[tuple[str, str]]]:
    root = ET.parse(FORCEFIELD_PATH).getroot()
    residue = next(
        node
        for node in root.findall("./Residues/Residue")
        if node.attrib["name"] == "NDP"
    )
    charges = {
        atom.attrib["name"]: float(atom.attrib["charge"])
        for atom in residue.findall("Atom")
    }
    bonds = [
        (bond.attrib["atomName1"], bond.attrib["atomName2"])
        for bond in residue.findall("Bond")
    ]
    return charges, bonds


def main() -> None:
    charges, bonds = ndp_template()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for background, pdb_id in (("WT", "6XG5"), ("L28R", "6XG4")):
        pdb = app.PDBFile(str(RAW / f"{pdb_id}.pdb"))
        ndp = next(
            residue for residue in pdb.topology.residues() if residue.name == "NDP"
        )
        deposited_names = {atom.name for atom in ndp.atoms()}
        collapsed = {name: charges[name] for name in deposited_names}
        for name, charge in charges.items():
            if name in deposited_names:
                continue
            parent = next(
                (
                    right if left == name else left
                    for left, right in bonds
                    if (left == name and right in deposited_names)
                    or (right == name and left in deposited_names)
                ),
                None,
            )
            if parent is None:
                raise ValueError(
                    f"{background}: cannot collapse missing atom {name} onto a deposited heavy atom"
                )
            collapsed[parent] += charge
        records = []
        for atom in ndp.atoms():
            if atom.name not in collapsed:
                raise ValueError(
                    f"{background}: no CHARMM36 charge for NDP atom {atom.name}"
                )
            position = pdb.positions[atom.index].value_in_unit(unit.angstrom)
            records.append(
                {
                    "atom_name": atom.name,
                    "element": atom.element.symbol,
                    "x_A": position.x,
                    "y_A": position.y,
                    "z_A": position.z,
                    "charge_e": collapsed[atom.name],
                }
            )
        frame = pd.DataFrame(records)
        total = float(frame["charge_e"].sum())
        if not np.isclose(total, -3.0, atol=1e-8):
            raise ValueError(
                f"{background}: expected CHARMM36 NDP charge -3, obtained {total}"
            )
        frame.to_csv(OUTPUT / f"{background}_nadph_charmm36.csv", index=False)
        rows.append(
            {
                "background": background,
                "pdb": pdb_id,
                "atoms": len(frame),
                "total_charge_e": total,
                "charge_source": "OpenMM charmm36.xml NDP template; H charges collapsed to bonded heavy atoms",
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(ROOT / "results/tables/nadph_embedding_manifest.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
