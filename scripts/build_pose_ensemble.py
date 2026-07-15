#!/usr/bin/env python3
"""Build and geometry-score a prespecified local 4-DTMP pose ensemble."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from rdkit import Chem
from rdkit.Chem import rdMolTransforms

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
CONFIG = ROOT / "configs/pose_models.yaml"


def load_sdf(path: Path) -> Chem.Mol:
    molecule = next((mol for mol in Chem.SDMolSupplier(str(path), removeHs=False) if mol), None)
    if molecule is None:
        raise ValueError(f"Cannot parse {path}")
    return molecule


def linker_dihedral(molecule: Chem.Mol) -> tuple[int, int, int, int]:
    """Find pyrimidine-C / methylene / phenyl-C / phenyl-neighbor indices."""
    for atom in molecule.GetAtoms():
        if atom.GetAtomicNum() != 6 or atom.GetIsAromatic():
            continue
        heavy_neighbors = [neighbor for neighbor in atom.GetNeighbors() if neighbor.GetAtomicNum() > 1]
        aromatic = [neighbor for neighbor in heavy_neighbors if neighbor.GetIsAromatic()]
        if len(aromatic) != 2:
            continue
        phenyl = next(
            (candidate for candidate in aromatic if all(n.GetAtomicNum() == 6 for n in candidate.GetNeighbors())),
            None,
        )
        if phenyl is None:
            continue
        pyrimidine = next(candidate for candidate in aromatic if candidate.GetIdx() != phenyl.GetIdx())
        phenyl_neighbor = next(
            neighbor for neighbor in phenyl.GetNeighbors()
            if neighbor.GetIdx() != atom.GetIdx() and neighbor.GetIsAromatic()
        )
        return pyrimidine.GetIdx(), atom.GetIdx(), phenyl.GetIdx(), phenyl_neighbor.GetIdx()
    raise ValueError("Could not identify the TMP pyrimidine-methylene-phenyl linker")


def protein_coordinates(path: Path) -> tuple[np.ndarray, np.ndarray]:
    pdb = Chem.MolFromPDBFile(str(path), removeHs=False, sanitize=False)
    if pdb is None:
        raise ValueError(f"Cannot parse {path}")
    conformer = pdb.GetConformer()
    xyz = []
    polar = []
    for atom in pdb.GetAtoms():
        info = atom.GetPDBResidueInfo()
        if atom.GetAtomicNum() <= 1 or (info and info.GetResidueName().strip() in {"TOP", "DTM"}):
            continue
        point = np.asarray(conformer.GetAtomPosition(atom.GetIdx()))
        xyz.append(point)
        if atom.GetAtomicNum() in {7, 8, 16}:
            polar.append(point)
    return np.asarray(xyz), np.asarray(polar)


def score(molecule: Chem.Mol, protein: np.ndarray, polar: np.ndarray) -> dict[str, float | int]:
    conformer = molecule.GetConformer()
    ligand_indices = [atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomicNum() > 1]
    ligand = np.asarray([conformer.GetAtomPosition(index) for index in ligand_indices])
    distances = np.linalg.norm(ligand[:, None, :] - protein[None, :, :], axis=2)
    ligand_polar = np.asarray(
        [conformer.GetAtomPosition(atom.GetIdx()) for atom in molecule.GetAtoms() if atom.GetAtomicNum() in {7, 8}]
    )
    polar_distances = np.linalg.norm(ligand_polar[:, None, :] - polar[None, :, :], axis=2)
    return {
        "min_protein_distance_A": float(distances.min()),
        "clashes_lt_1_8A": int((distances < 1.8).sum()),
        "polar_pairs_2_4_to_3_5A": int(((polar_distances >= 2.4) & (polar_distances <= 3.5)).sum()),
    }


def main() -> None:
    rows = []
    frozen: dict[str, object] = {
        "status": "FROZEN",
        "frozen_on": "2026-07-15",
        "selection_basis": "geometry-only; no classical or quantum energies",
        "models": {},
    }
    out_dir = PROCESSED / "pose_candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    for background in ("WT", "L28R"):
        source = load_sdf(PROCESSED / f"{background}_4DTMP.sdf")
        protein, polar = protein_coordinates(PROCESSED / f"{background}_4DTMP_minimized.pdb")
        dihedral = linker_dihedral(source)
        base = rdMolTransforms.GetDihedralDeg(source.GetConformer(), *dihedral)
        candidates = []
        for label, offset in (("inherited", 0.0), ("torsion_minus30", -30.0), ("torsion_plus30", 30.0)):
            candidate = Chem.Mol(source)
            rdMolTransforms.SetDihedralDeg(candidate.GetConformer(), *dihedral, base + offset)
            candidate.SetProp("_Name", f"{background}_4DTMP_{label}")
            path = out_dir / f"{background}_4DTMP_{label}.sdf"
            writer = Chem.SDWriter(str(path))
            writer.write(candidate)
            writer.close()
            metrics = score(candidate, protein, polar)
            row = {"background": background, "model": label, "torsion_offset_deg": offset, **metrics}
            rows.append(row)
            candidates.append(row)
        alternatives = sorted(
            (row for row in candidates if row["model"] != "inherited"),
            key=lambda row: (row["clashes_lt_1_8A"], -row["polar_pairs_2_4_to_3_5A"], abs(row["torsion_offset_deg"])),
        )
        frozen["models"][background] = {
            "primary": "inherited",
            "alternate": alternatives[0]["model"],
            "alternate_rule": "fewest <1.8 A clashes, then most 2.4-3.5 A polar pairs",
        }
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(TABLES / "pose_ensemble_qc.csv", index=False)
    CONFIG.write_text(yaml.safe_dump(frozen, sort_keys=False))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
