#!/usr/bin/env python3
"""Create 4'-desmethyl-TMP by O-demethylating TMP while retaining its pose."""

from __future__ import annotations

import argparse
from pathlib import Path

from rdkit import Chem


def find_para_methoxy_methyl(mol: Chem.Mol) -> tuple[int, int]:
    """Return (oxygen, methyl-carbon) for the para methoxy on TMP's phenyl ring."""
    candidates = []
    for oxygen in mol.GetAtoms():
        if oxygen.GetAtomicNum() != 8 or oxygen.GetDegree() != 2:
            continue
        aromatic = [n for n in oxygen.GetNeighbors() if n.GetIsAromatic()]
        methyl = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6 and sum(x.GetAtomicNum() > 1 for x in n.GetNeighbors()) == 1]
        if aromatic and methyl:
            # TMP has three methoxy groups. The para oxygen has greatest graph
            # distance from the phenyl carbon bonded to the pyrimidine linker.
            ring_carbon = aromatic[0]
            substituted = [a for a in mol.GetAtoms() if a.GetIsAromatic() and any(
                not n.GetIsAromatic() and n.GetAtomicNum() == 6 and
                any(x.GetIsAromatic() for x in n.GetNeighbors() if x.GetIdx() != a.GetIdx())
                for n in a.GetNeighbors()
            )]
            anchor = substituted[0] if substituted else ring_carbon
            candidates.append((len(Chem.GetShortestPath(mol, anchor.GetIdx(), ring_carbon.GetIdx())), oxygen, methyl[0]))
    if not candidates:
        raise ValueError("No aromatic methoxy group found; verify that the selected residue is TMP")
    _, oxygen, methyl = max(candidates, key=lambda item: item[0])
    return oxygen.GetIdx(), methyl.GetIdx()


def transform(mol: Chem.Mol) -> Chem.Mol:
    oxygen_idx, methyl_idx = find_para_methoxy_methyl(mol)
    editable = Chem.RWMol(mol)
    editable.RemoveBond(oxygen_idx, methyl_idx)
    attached_hydrogens = [atom.GetIdx() for atom in mol.GetAtomWithIdx(methyl_idx).GetNeighbors() if atom.GetAtomicNum() == 1]
    for atom_idx in sorted(attached_hydrogens + [methyl_idx], reverse=True):
        editable.RemoveAtom(atom_idx)
    product = editable.GetMol()
    Chem.SanitizeMol(product)
    # Add only the new phenolic hydrogen. Retained heavy-atom coordinates are
    # inherited exactly from the deposited TMP pose; isolated-ligand
    # optimization would silently turn this into a different pose hypothesis.
    product = Chem.AddHs(product, addCoords=True)
    return product


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="TMP ligand as an SDF/MOL file with 3D coordinates")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    supplier = Chem.SDMolSupplier(str(args.input), removeHs=False) if args.input.suffix.lower() == ".sdf" else [Chem.MolFromMolFile(str(args.input), removeHs=False)]
    mol = next((candidate for candidate in supplier if candidate is not None), None)
    if mol is None:
        raise ValueError(f"Could not parse {args.input}")
    product = transform(mol)
    product.SetProp("_Name", "4'-desmethyltrimethoprim")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(args.output))
    writer.write(product)
    writer.close()
    print(f"Wrote {args.output} ({Chem.MolToSmiles(Chem.RemoveHs(product))})")


if __name__ == "__main__":
    main()
