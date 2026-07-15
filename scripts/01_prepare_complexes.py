#!/usr/bin/env python3
"""Prepare four DHFR complexes with Amber14SB + OpenFF Sage.

This stage preserves the deposited ligand frame, repairs protein heavy atoms,
adds pH-dependent hydrogens, and performs a restrained implicit-solvent
relaxation. It is a reproducible starting geometry, not a binding-pose proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from openff.toolkit import Molecule
from openff.toolkit.utils import AmberToolsToolkitWrapper
from openmm import CustomExternalForce, LangevinMiddleIntegrator, Platform, unit
from openmm.app import HBonds, Modeller, NoCutoff, PDBFile, Simulation
from openmmforcefields.generators import SystemGenerator
from pdbfixer import PDBFixer
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = {
    "WT_TMP": ("6XG5", "WT_TMP.sdf"),
    "WT_4DTMP": ("6XG5", "WT_4DTMP.sdf"),
    "L28R_TMP": ("6XG4", "L28R_TMP.sdf"),
    "L28R_4DTMP": ("6XG4", "L28R_4DTMP.sdf"),
}


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
    off.assign_partial_charges("am1bcc", toolkit_registry=AmberToolsToolkitWrapper())
    conformer = off.conformers[0].to_openmm()
    return off, conformer


def prepare(system_id: str, iterations: int, restraint_k: float, water_cutoff: float | None) -> dict:
    pdb_id, sdf_name = SYSTEMS[system_id]
    raw = ROOT / "data/raw/pdbs" / f"{pdb_id}.pdb"
    sdf = ROOT / "data/processed" / sdf_name
    out = ROOT / "data/processed" / f"{system_id}_minimized.pdb"

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

    print(f"[{system_id}] assigning Amber/OpenFF parameters", flush=True)
    protein_forcefields = ["amber14/protein.ff14SB.xml"]
    if retained_waters:
        protein_forcefields.append("amber14/tip3p.xml")
    generator = SystemGenerator(
        forcefields=protein_forcefields,
        small_molecule_forcefield="openff-2.0.0.offxml",
        molecules=[ligand],
        forcefield_kwargs={"constraints": HBonds},
        nonperiodic_forcefield_kwargs={"nonbondedMethod": NoCutoff},
    )
    system = generator.create_system(modeller.topology, molecules=[ligand])
    print(f"[{system_id}] parameterization complete", flush=True)

    # Restrain backbone and ligand heavy atoms to avoid interpreting a vacuum-like
    # local relaxation as a new binding-pose prediction.
    restraint = CustomExternalForce("k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    restraint.addGlobalParameter("k", restraint_k * 4.184 * 100.0)  # kcal/mol/A^2 -> kJ/mol/nm^2
    for name in ("x0", "y0", "z0"):
        restraint.addPerParticleParameter(name)
    positions = modeller.positions
    for atom in modeller.topology.atoms():
        is_backbone = atom.index < protein_atoms and atom.name in {"N", "CA", "C", "O"}
        is_ligand_heavy = atom.index >= protein_atoms and atom.element.symbol != "H"
        if is_backbone or is_ligand_heavy:
            xyz = positions[atom.index].value_in_unit(unit.nanometer)
            restraint.addParticle(atom.index, list(xyz))
    system.addForce(restraint)

    integrator = LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 0.002 * unit.picoseconds)
    print(f"[{system_id}] minimizing", flush=True)
    simulation = Simulation(modeller.topology, system, integrator, Platform.getPlatformByName("Reference"))
    simulation.context.setPositions(positions)
    initial = simulation.context.getState(getEnergy=True).getPotentialEnergy()
    simulation.minimizeEnergy(maxIterations=iterations)
    state = simulation.context.getState(getPositions=True, getEnergy=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        PDBFile.writeFile(modeller.topology, state.getPositions(), handle, keepIds=True)
    result = {"system": system_id, "output": str(out), "protein_atoms": protein_atoms,
              "total_atoms": modeller.topology.getNumAtoms(), "retained_waters": retained_waters,
              "water_cutoff_angstrom": water_cutoff, "iterations": iterations,
              "initial_kj_mol": initial.value_in_unit(unit.kilojoule_per_mole),
              "final_kj_mol": state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)}
    (out.with_suffix(".json")).write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=SYSTEMS)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--restraint", type=float, default=10.0, help="kcal/mol/A^2")
    parser.add_argument("--water-cutoff", type=float, default=5.0, help="retain crystallographic water O atoms within this ligand-centroid distance (A)")
    parser.add_argument("--no-waters", action="store_true")
    args = parser.parse_args()
    if not args.all and not args.system:
        parser.error("choose --all or --system")
    for system_id in SYSTEMS if args.all else [args.system]:
        cutoff = None if args.no_waters else args.water_cutoff
        print(json.dumps(prepare(system_id, args.iterations, args.restraint, cutoff), indent=2))


if __name__ == "__main__":
    main()
