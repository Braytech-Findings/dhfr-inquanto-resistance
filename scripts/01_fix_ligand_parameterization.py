#!/usr/bin/env python3
"""Generate GAFF-style ligand parameterization files for TMP and 4-DTMP."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem

ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data/processed"


def generate_gaff_params(smiles: str, ligand_name: str, charge: int = 0) -> None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Could not parse SMILES for {ligand_name}")
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, randomSeed=0xC0FFEE)
    AllChem.UFFOptimizeMolecule(mol)
    with tempfile.TemporaryDirectory(dir=str(DATA_PROCESSED)) as tmpdir:
        mol2_path = Path(tmpdir) / f"{ligand_name}.mol2"
        Chem.MolToMolFile(mol, str(mol2_path))
        antechamber_out = Path(tmpdir) / f"{ligand_name}_gaff.mol2"
        frcmod_path = Path(tmpdir) / f"{ligand_name}.frcmod"
        subprocess.run(
            [
                "antechamber",
                "-i",
                str(mol2_path),
                "-fi",
                "mol2",
                "-o",
                str(antechamber_out),
                "-fo",
                "mol2",
                "-c",
                "bcc",
                "-nc",
                str(charge),
                "-rn",
                ligand_name,
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "parmchk2",
                "-i",
                str(antechamber_out),
                "-o",
                str(frcmod_path),
                "-f",
                "mol2",
            ],
            check=True,
            capture_output=True,
        )
        shutil.copy(str(antechamber_out), DATA_PROCESSED / f"{ligand_name}.mol2")
        shutil.copy(str(frcmod_path), DATA_PROCESSED / f"{ligand_name}.frcmod")
    print(f"✅ Generated GAFF params for {ligand_name}")


def main() -> None:
    tmp_smiles = "COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC"
    generate_gaff_params(tmp_smiles, "TMP", charge=0)
    four_dtmp_smiles = "COc1cc(Cc2cnc(N)nc2N)cc(O)c1OC"
    generate_gaff_params(four_dtmp_smiles, "4DTMP", charge=0)


if __name__ == "__main__":
    main()
