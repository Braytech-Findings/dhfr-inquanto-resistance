#!/usr/bin/env python3
"""Audit prepared DHFR complexes before QM-region construction."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from openmm import unit
from openmm.app import PDBFile

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")
PROTEIN_NAMES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}


def coords_angstrom(pdb: PDBFile) -> np.ndarray:
    return np.asarray([p.value_in_unit(unit.angstrom) for p in pdb.positions], dtype=float)


def inspect(system_id: str, path: Path) -> dict[str, object]:
    pdb = PDBFile(str(path))
    xyz = coords_angstrom(pdb)
    residues = list(pdb.topology.residues())
    ligand_residues = [r for r in residues if r.name in {"TOP", "DTM", "4DT", "UNK"}]
    if len(ligand_residues) != 1:
        raise ValueError(f"{path}: expected exactly one ligand residue, found {len(ligand_residues)}")
    ligand = ligand_residues[0]
    ligand_atoms = list(ligand.atoms())
    ligand_heavy = [a.index for a in ligand_atoms if a.element.symbol != "H"]
    expected = 20 if "4DTMP" in system_id else 21

    res28_candidates = [r for r in residues if r.id == "28" and r.name in PROTEIN_NAMES]
    if not res28_candidates:
        raise ValueError(f"{path}: protein residue number 28 not found")
    # Prefer the chain closest to the ligand if crystallographic copies exist.
    lig_center = xyz[ligand_heavy].mean(axis=0)
    res28 = min(res28_candidates, key=lambda r: np.linalg.norm(
        xyz[[a.index for a in r.atoms() if a.element.symbol != "H"]].mean(axis=0) - lig_center
    ))
    res28_heavy = [a.index for a in res28.atoms() if a.element.symbol != "H"]
    res28_center = xyz[res28_heavy].mean(axis=0)
    pair = np.linalg.norm(xyz[ligand_heavy, None, :] - xyz[res28_heavy][None, :, :], axis=2)

    protein_heavy = [a.index for a in pdb.topology.atoms()
                     if a.residue.name in PROTEIN_NAMES and a.element.symbol != "H"]
    contacts = np.linalg.norm(xyz[ligand_heavy, None, :] - xyz[protein_heavy][None, :, :], axis=2)
    min_contact = float(contacts.min())
    severe_clashes = int(np.count_nonzero(contacts < 1.2))
    waters = sum(1 for r in residues if r.name in {"HOH", "WAT"})

    status = "PASS"
    notes: list[str] = []
    if len(ligand_heavy) != expected:
        status = "FAIL"
        notes.append(f"heavy atoms {len(ligand_heavy)} != {expected}")
    if severe_clashes:
        status = "FAIL"
        notes.append(f"{severe_clashes} protein-ligand distances below 1.2 A")
    if float(pair.min()) > 6.0:
        status = "REVIEW" if status == "PASS" else status
        notes.append("residue 28 is more than 6 A from ligand")
    if waters == 0:
        notes.append("waters intentionally absent from current preparation")

    return {
        "system": system_id,
        "file": str(path),
        "status": status,
        "ligand_resname": ligand.name,
        "ligand_heavy_atoms": len(ligand_heavy),
        "residue_28": f"{res28.chain.id}:{res28.name}{res28.id}",
        "ligand_res28_min_A": float(pair.min()),
        "ligand_res28_centroid_A": float(np.linalg.norm(lig_center - res28_center)),
        "min_protein_ligand_A": min_contact,
        "severe_clashes_lt_1_2A": severe_clashes,
        "waters": waters,
        "notes": "; ".join(notes),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--csv", type=Path, default=ROOT / "results/tables/structure_qc.csv")
    parser.add_argument("--report", type=Path, default=ROOT / "results/reports/structure_qc.md")
    args = parser.parse_args()
    rows = []
    for system_id in SYSTEMS:
        path = args.processed / f"{system_id}_minimized.pdb"
        if not path.exists():
            rows.append({"system": system_id, "file": str(path), "status": "MISSING", "notes": "file not found"})
            continue
        rows.append(inspect(system_id, path))
    frame = pd.DataFrame(rows)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.csv, index=False)
    columns = ["system", "status", "ligand_heavy_atoms", "residue_28", "ligand_res28_min_A", "min_protein_ligand_A", "severe_clashes_lt_1_2A", "notes"]
    report = "# Prepared-structure quality control\n\n"
    report += "| " + " | ".join(columns) + " |\n"
    report += "| " + " | ".join("---" for _ in columns) + " |\n"
    for row in frame.to_dict(orient="records"):
        report += "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |\n"
    report += "\n"
    report += "Distances are geometric screening metrics, not evidence of binding affinity. "
    report += "The current protocol removed crystallographic waters; water sensitivity must be assessed before production QM calculations.\n"
    args.report.write_text(report)
    print(frame.to_string(index=False))
    print(f"\nSaved {args.csv} and {args.report}")
    if any(frame.status.isin(["FAIL", "MISSING"])):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
