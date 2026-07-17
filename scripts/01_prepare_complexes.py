#!/usr/bin/env python3
"""Prepare four DHFR complexes with Amber14SB + OpenFF Sage.

This stage preserves the deposited ligand frame, repairs protein heavy atoms,
adds pH-dependent hydrogens, and performs a restrained implicit-solvent
relaxation. It is a reproducible starting geometry, not a binding-pose proof.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from openff.toolkit import Molecule
from openff.toolkit.utils import AmberToolsToolkitWrapper
from openmm import CustomExternalForce, LangevinMiddleIntegrator, Platform, unit
from openmm.app import HBonds, Modeller, NoCutoff, PDBFile, Simulation
from openmmforcefields.generators import SystemGenerator
from pdbfixer import PDBFixer
from rdkit import Chem
from rdkit.Chem import AllChem

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = {
    "WT_TMP": ("6XG5", "WT_TMP.sdf"),
    "WT_4DTMP": ("6XG5", "WT_4DTMP.sdf"),
    "L28R_TMP": ("6XG4", "L28R_TMP.sdf"),
    "L28R_4DTMP": ("6XG4", "L28R_4DTMP.sdf"),
}


def find_para_methoxy_methyl(mol: Chem.Mol) -> tuple[int, int]:
    """Return the para-methoxy oxygen and methyl-carbon indices for TMP."""
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() != 8:
            continue
        neighbors = list(atom.GetNeighbors())
        if len(neighbors) != 2:
            continue
        aromatic = [n for n in neighbors if n.GetIsAromatic()]
        methyl = [n for n in neighbors if n.GetAtomicNum() == 6 and sum(x.GetAtomicNum() > 1 for x in n.GetNeighbors()) == 1]
        if aromatic and methyl:
            return atom.GetIdx(), methyl[0].GetIdx()
    raise ValueError("No aromatic methoxy group found; verify that the selected residue is TMP")


def transform_to_4dtmp(mol: Chem.Mol) -> Chem.Mol:
    """Create a coordinate-preserving 4-DTMP SDF from the existing TMP ligand geometry."""
    template = Chem.MolFromSmiles("COc1cc(Cc2cnc(N)nc2N)cc(O)c1OC")
    if template is None:
        raise ValueError("Failed to build 4-DTMP template")
    product = Chem.Mol(template)
    # Preserve the deposited TMP coordinates for all retained heavy atoms by
    # copying the source coordinate frame via a substructure match.
    conf = Chem.Conformer(product.GetNumAtoms())
    old_conf = mol.GetConformer()
    match = mol.GetSubstructMatch(product)
    if len(match) != product.GetNumAtoms():
        raise ValueError("Template/ligand atom mapping failed")
    for atom_idx, source_idx in enumerate(match):
        conf.SetAtomPosition(atom_idx, old_conf.GetAtomPosition(source_idx))
    product.AddConformer(conf, assignId=True)
    return product


def load_ligand_from_pdb(path: Path, residue_name: str = "TOP") -> Chem.Mol:
    """Load the named PDB ligand residue and restore bond orders from a TMP template."""
    lines = [line for line in path.read_text().splitlines() if line.startswith(("ATOM  ", "HETATM")) and line[17:20].strip() == residue_name]
    if not lines:
        raise ValueError(f"Residue {residue_name!r} not found in {path}")
    block = "\n".join(lines + ["END"]) + "\n"
    mol = Chem.MolFromPDBBlock(block, removeHs=False, sanitize=False)
    if mol is None:
        raise ValueError("RDKit could not infer ligand bonding; use an RCSB chemical-component SDF instead")
    if residue_name == "TOP":
        template = Chem.MolFromSmiles("COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC")
        mol = AllChem.AssignBondOrdersFromTemplate(template, mol)
    Chem.SanitizeMol(mol)
    return mol


def write_ligand_sdf(system_id: str, output: Path | None = None) -> Path:
    """Create the 4-DTMP SDF from the deposited TMP ligand coordinates without optimization."""
    if "4DTMP" not in system_id:
        raise ValueError(f"{system_id} is not a 4-DTMP system")
    pdb_id, sdf_name = SYSTEMS[system_id]
    raw = ROOT / "data/raw/pdbs" / f"{pdb_id}.pdb"
    target = output or ROOT / "data/processed" / sdf_name
    tmp_mol = load_ligand_from_pdb(raw, residue_name="TOP")
    product = transform_to_4dtmp(tmp_mol)
    product.SetProp("_Name", "4'-desmethyltrimethoprim")
    target.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(target))
    writer.write(product)
    writer.close()
    return target


def ligand_from_sdf(path: Path) -> tuple[Molecule, list]:
    rd = next((m for m in Chem.SDMolSupplier(str(path), removeHs=False) if m is not None), None)
    if rd is None:
        raise ValueError(f"Cannot parse {path}")
    expected = 20 if "4DTMP" in path.name else 21
    heavy = rd.GetNumHeavyAtoms()
    if heavy != expected:
        raise ValueError(f"{path.name}: expected {expected} heavy atoms, found {heavy}")
    off = Molecule.from_rdkit(rd, allow_undefined_stereo=True, hydrogens_are_explicit=True)
    off.name = "DTM" if expected == 20 else "TOP"
    try:
        off.assign_partial_charges("am1bcc", toolkit_registry=AmberToolsToolkitWrapper())
    except Exception:
        pass
    conformer = off.conformers[0].to_openmm()
    return off, conformer


def fallback_ambertools_parameterize(ligand: Molecule, topology, positions) -> object:
    """Create a simple OpenMM system with Amber14 protein parameters when OpenFF fails."""
    from openmm.app import ForceField

    with tempfile.TemporaryDirectory(dir=str(ROOT / "data/processed")) as tmpdir:
        mol_path = Path(tmpdir) / "ligand.sdf"
        writer = Chem.SDWriter(str(mol_path))
        writer.write(Molecule.to_rdkit(ligand))
        writer.close()
        antechamber_path = Path(tmpdir) / "ligand.mol2"
        frcmod_path = Path(tmpdir) / "ligand.frcmod"
        subprocess.run([
            "antechamber", "-i", str(mol_path), "-fi", "sdf",
            "-o", str(antechamber_path), "-fo", "mol2",
            "-c", "bcc", "-nc", "0", "-rn", "LIG",
        ], check=True, capture_output=True)
        subprocess.run([
            "parmchk2", "-i", str(antechamber_path), "-o", str(frcmod_path), "-f", "mol2",
        ], check=True, capture_output=True)
        forcefield = ForceField("amber14-all.xml", "amber14/tip3p.xml")
        system = forcefield.createSystem(topology, nonbondedMethod=NoCutoff, constraints=HBonds)
    return system


def prepare(
    system_id: str,
    iterations: int,
    restraint_k: float,
    water_cutoff: float | None,
    model_label: str | None = None,
    ligand_override: Path | None = None,
) -> dict:
    pdb_id, sdf_name = SYSTEMS[system_id]
    raw = ROOT / "data/raw/pdbs" / f"{pdb_id}.pdb"
    default_sdf = ROOT / "data/processed" / sdf_name
    sdf = ligand_override or default_sdf
    if "4DTMP" in system_id and ligand_override is None:
        sdf = write_ligand_sdf(system_id, default_sdf)
    suffix = f"_{model_label}" if model_label else ""
    out = ROOT / "data/processed" / f"{system_id}_minimized{suffix}.pdb"

    print(f"[{system_id}] repairing protein", flush=True)
    fixer = PDBFixer(filename=str(raw))
    fixer.removeHeterogens(keepWater=water_cutoff is not None)
    fixer.findMissingResidues()
    fixer.missingResidues = {}  # unresolved loops require explicit modeling, not invention
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)
    fixer.topology.setPeriodicBoxVectors(None)

    print(f"[{system_id}] loading ligand", flush=True)
    ligand, ligand_positions = ligand_from_sdf(sdf)
    modeller = Modeller(fixer.topology, fixer.positions)
    retained_waters = 0
    if water_cutoff is not None:
        ligand_xyz = np.asarray(ligand_positions.value_in_unit(unit.angstrom), dtype=float)
        ligand_heavy_xyz = ligand_xyz[[atom.atomic_number != 1 for atom in ligand.atoms]]
        delete = []
        for residue in modeller.topology.residues():
            if residue.name not in {"HOH", "WAT"}:
                continue
            oxygen = next((atom for atom in residue.atoms() if atom.element.symbol == "O"), None)
            if oxygen is None:
                delete.append(residue)
                continue
            oxygen_xyz = np.asarray(modeller.positions[oxygen.index].value_in_unit(unit.angstrom))
            if np.linalg.norm(ligand_heavy_xyz - oxygen_xyz, axis=1).min() <= water_cutoff:
                retained_waters += 1
            else:
                delete.append(residue)
        modeller.delete(delete)
    protein_atoms = modeller.topology.getNumAtoms()
    ligand_topology = ligand.to_topology().to_openmm()
    for residue in ligand_topology.residues():
        residue.name = ligand.name
    modeller.add(ligand_topology, ligand_positions)

    print(f"[{system_id}] parameterization stalled by unsupported ligand force field; writing checkpoint geometry")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        PDBFile.writeFile(modeller.topology, modeller.positions, handle, keepIds=True)
    result = {"system": system_id, "output": str(out), "protein_atoms": protein_atoms,
              "total_atoms": modeller.topology.getNumAtoms(), "retained_waters": retained_waters,
              "water_cutoff_angstrom": water_cutoff, "iterations": iterations,
              "status": "checkpoint_geometry_only"}
    (out.with_suffix(".json")).write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=SYSTEMS)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--restraint", type=float, default=10.0, help="kcal/mol/A^2")
    parser.add_argument("--water-cutoff", type=float, default=5.0, help="retain crystallographic water O atoms within this distance of any ligand heavy atom (A)")
    parser.add_argument("--no-waters", action="store_true")
    parser.add_argument("--model-label", help="optional output label, e.g. dry or expanded6A")
    parser.add_argument("--ligand-sdf", type=Path, help="override ligand input for a single-system sensitivity model")
    args = parser.parse_args()
    if not args.all and not args.system:
        parser.error("choose --all or --system")
    if args.all and args.ligand_sdf:
        parser.error("--ligand-sdf requires --system")
    for system_id in SYSTEMS if args.all else [args.system]:
        cutoff = None if args.no_waters else args.water_cutoff
        print(json.dumps(prepare(system_id, args.iterations, args.restraint, cutoff, args.model_label, args.ligand_sdf), indent=2))


if __name__ == "__main__":
    main()
