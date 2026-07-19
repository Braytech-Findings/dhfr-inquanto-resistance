#!/usr/bin/env python3
"""Audit ligand identity and retained-atom mapping for the core four."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "results/tables"


def load(path: Path) -> Chem.Mol:
    molecule = next(
        (mol for mol in Chem.SDMolSupplier(str(path), removeHs=False) if mol), None
    )
    if molecule is None:
        raise ValueError(f"Cannot parse {path}")
    return molecule


def heavy(molecule: Chem.Mol) -> Chem.Mol:
    return Chem.RemoveHs(molecule)


def main() -> None:
    rows = []
    maps = []
    for background in ("WT", "L28R"):
        tmp = load(PROCESSED / f"{background}_TMP.sdf")
        dtmp = load(PROCESSED / f"{background}_4DTMP.sdf")
        tmp_h = heavy(tmp)
        dtmp_h = heavy(dtmp)
        match = tmp_h.GetSubstructMatch(dtmp_h)
        if len(match) != dtmp_h.GetNumAtoms():
            raise ValueError(
                f"{background}: 4-DTMP is not an exact heavy-atom substructure of TMP"
            )
        tmp_xyz = np.asarray(tmp_h.GetConformer().GetPositions())[list(match)]
        dtmp_xyz = np.asarray(dtmp_h.GetConformer().GetPositions())
        retained_rmsd = float(
            np.sqrt(np.mean(np.sum((tmp_xyz - dtmp_xyz) ** 2, axis=1)))
        )
        for dtmp_index, tmp_index in enumerate(match):
            maps.append(
                {
                    "background": background,
                    "dtmp_atom_index": dtmp_index,
                    "tmp_atom_index": tmp_index,
                    "element": dtmp_h.GetAtomWithIdx(dtmp_index).GetSymbol(),
                }
            )
        for ligand, molecule in (("TMP", tmp), ("4-DTMP", dtmp)):
            molecule_h = heavy(molecule)
            rows.append(
                {
                    "background": background,
                    "ligand": ligand,
                    "formula": rdMolDescriptors.CalcMolFormula(molecule),
                    "formal_charge": Chem.GetFormalCharge(molecule),
                    "heavy_atoms": molecule_h.GetNumAtoms(),
                    "canonical_smiles": Chem.MolToSmiles(molecule_h, canonical=True),
                    "retained_atom_rmsd_from_tmp_A": 0.0
                    if ligand == "TMP"
                    else retained_rmsd,
                }
            )
    TABLES.mkdir(parents=True, exist_ok=True)
    identities = pd.DataFrame(rows)
    identities.to_csv(TABLES / "ligand_identity.csv", index=False)
    pd.DataFrame(maps).to_csv(TABLES / "tmp_to_4dtmp_atom_map.csv", index=False)
    print(identities.to_string(index=False))


if __name__ == "__main__":
    main()
