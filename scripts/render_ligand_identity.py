#!/usr/bin/env python3
"""Render the frozen ligand and protonation identities for visual sign-off."""

from __future__ import annotations

from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
OUTPUT = ROOT / "results/reports/ligand_identity.png"


def load(path: Path) -> Chem.Mol:
    molecule = next((mol for mol in Chem.SDMolSupplier(str(path), removeHs=False) if mol), None)
    if molecule is None:
        raise ValueError(f"Cannot parse {path}")
    molecule = Chem.RemoveHs(molecule)
    rdDepictor.Compute2DCoords(molecule)
    return molecule


def main() -> None:
    molecules = [
        load(PROCESSED / "WT_TMP.sdf"),
        load(PROCESSED / "WT_4DTMP.sdf"),
        load(PROCESSED / "protonation_models/WT_TMP_protonatedN1.sdf"),
        load(PROCESSED / "protonation_models/WT_4DTMP_protonatedN1.sdf"),
    ]
    legends = ["TMP, neutral", "4-DTMP, neutral", "TMP, N1-protonated (+1)", "4-DTMP, N1-protonated (+1)"]
    image = Draw.MolsToGridImage(molecules, legends=legends, molsPerRow=2, subImgSize=(520, 360))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
