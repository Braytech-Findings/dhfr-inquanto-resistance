#!/usr/bin/env python3
"""Extract the first named ligand residue from a PDB as an RDKit SDF."""

from __future__ import annotations

import argparse
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdb", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--resname", default="TOP", help="PDB residue name (TOP in 6XG4/6XG5)"
    )
    args = parser.parse_args()
    lines = [
        line
        for line in args.pdb.read_text().splitlines()
        if line.startswith(("ATOM  ", "HETATM")) and line[17:20].strip() == args.resname
    ]
    if not lines:
        raise ValueError(f"Residue {args.resname!r} not found in {args.pdb}")
    block = "\n".join(lines + ["END"]) + "\n"
    mol = Chem.MolFromPDBBlock(block, removeHs=False, sanitize=False)
    if mol is None:
        raise ValueError(
            "RDKit could not infer ligand bonding; use an RCSB chemical-component SDF instead"
        )
    if args.resname == "TOP":
        # PDB coordinates do not encode bond order. Restore the deposited TMP
        # chemistry while retaining the crystallographic atom coordinates.
        template = Chem.MolFromSmiles("COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC")
        mol = AllChem.AssignBondOrdersFromTemplate(template, mol)
    Chem.SanitizeMol(mol)
    mol = Chem.AddHs(mol, addCoords=True)
    if AllChem.MMFFHasAllMoleculeParams(mol):
        AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    mol.SetProp("_Name", args.resname)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(args.output))
    writer.write(mol)
    writer.close()


if __name__ == "__main__":
    main()
