#!/usr/bin/env python3
"""Create coordinate-preserving N1-protonated TMP and 4-DTMP sensitivity inputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
OUTPUT = PROCESSED / "protonation_models"
TABLE = ROOT / "results/tables/ligand_protonation_models.csv"
N1_PATTERN = Chem.MolFromSmarts("[c]1[cH][n:1][c]([NH2])[n][c]1[NH2]")


def protonate_n1(molecule: Chem.Mol) -> Chem.Mol:
    match = molecule.GetSubstructMatch(N1_PATTERN)
    if not match:
        raise ValueError("Could not identify diaminopyrimidine N1")
    n1 = next(
        matched
        for query, matched in enumerate(match)
        if N1_PATTERN.GetAtomWithIdx(query).GetAtomMapNum() == 1
    )
    editable = Chem.RWMol(molecule)
    atom = editable.GetAtomWithIdx(n1)
    atom.SetFormalCharge(1)
    atom.SetNumExplicitHs(1)
    atom.SetNoImplicit(True)
    product = editable.GetMol()
    Chem.SanitizeMol(product)
    return Chem.AddHs(product, addCoords=True)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for background in ("WT", "L28R"):
        for ligand in ("TMP", "4DTMP"):
            source = PROCESSED / f"{background}_{ligand}.sdf"
            molecule = next(
                (mol for mol in Chem.SDMolSupplier(str(source), removeHs=False) if mol),
                None,
            )
            if molecule is None:
                raise ValueError(f"Cannot parse {source}")
            product = protonate_n1(molecule)
            product.SetProp("_Name", f"{background}_{ligand}_N1H+")
            output = OUTPUT / f"{background}_{ligand}_protonatedN1.sdf"
            writer = Chem.SDWriter(str(output))
            writer.write(product)
            writer.close()
            rows.append(
                {
                    "background": background,
                    "ligand": ligand,
                    "state": "N1-protonated",
                    "formal_charge": Chem.GetFormalCharge(product),
                    "formula": rdMolDescriptors.CalcMolFormula(product),
                    "canonical_smiles": Chem.MolToSmiles(
                        Chem.RemoveHs(product), canonical=True
                    ),
                    "coordinate_rule": "all heavy coordinates inherited",
                }
            )
    frame = pd.DataFrame(rows)
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(TABLE, index=False)
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
