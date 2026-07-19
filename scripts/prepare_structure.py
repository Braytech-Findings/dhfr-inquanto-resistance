#!/usr/bin/env python3
"""Repair a protein PDB, add hydrogens, and minimize it with OpenMM.

The ligand is deliberately excluded: standard Amber force fields do not
parameterize TMP/4-DTMP. Ligand parameterization and complex minimization must
use an explicit small-molecule force field (OpenFF/GAFF) before production use.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openmm import LangevinMiddleIntegrator, unit
from openmm.app import ForceField, HBonds, NoCutoff, PDBFile, Simulation
from pdbfixer import PDBFixer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ph", type=float, default=7.4)
    parser.add_argument("--keep-water", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=500)
    args = parser.parse_args()

    fixer = PDBFixer(filename=str(args.input))
    fixer.removeHeterogens(keepWater=args.keep_water)
    fixer.findMissingResidues()
    # Do not invent unresolved terminal loops; these can distort the pocket.
    fixer.missingResidues = {}
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(args.ph)

    forcefield = ForceField("amber14-all.xml", "implicit/gbn2.xml")
    system = forcefield.createSystem(
        fixer.topology, nonbondedMethod=NoCutoff, constraints=HBonds
    )
    integrator = LangevinMiddleIntegrator(
        300 * unit.kelvin, 1 / unit.picosecond, 0.002 * unit.picoseconds
    )
    simulation = Simulation(fixer.topology, system, integrator)
    simulation.context.setPositions(fixer.positions)
    simulation.minimizeEnergy(maxIterations=args.max_iterations)
    state = simulation.context.getState(getPositions=True, getEnergy=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as handle:
        PDBFile.writeFile(fixer.topology, state.getPositions(), handle, keepIds=True)
    print(f"Wrote {args.output}; potential energy = {state.getPotentialEnergy()}")


if __name__ == "__main__":
    main()
