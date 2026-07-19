#!/usr/bin/env python3
"""Rank canonical orbitals by ligand character for transparent active-space review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyscf import scf


def atom_ao_indices(molecule, atom_indices: list[int]) -> np.ndarray:
    slices = molecule.aoslice_by_atom()
    return np.concatenate(
        [np.arange(slices[index, 2], slices[index, 3]) for index in atom_indices]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("atom_map", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    parser.add_argument("--occupied-window", type=int, default=16)
    parser.add_argument("--virtual-window", type=int, default=12)
    args = parser.parse_args()
    molecule, data = scf.chkfile.load_scf(str(args.checkpoint))
    coefficients = np.asarray(data["mo_coeff"])
    energies = np.asarray(data["mo_energy"])
    occupations = np.asarray(data["mo_occ"])
    atom_map = pd.read_csv(args.atom_map)
    ligand_atoms = atom_map.loc[atom_map.fragment.eq("ligand"), "atom_index"].to_list()
    ligand_ao = atom_ao_indices(molecule, ligand_atoms)
    overlap = molecule.intor_symmetric("int1e_ovlp")
    ligand_population = np.einsum(
        "pi,pq,qi->i",
        coefficients[ligand_ao],
        overlap[ligand_ao, :],
        coefficients,
        optimize=True,
    )
    table = pd.DataFrame(
        {
            "orbital": np.arange(len(energies)),
            "energy_hartree": energies,
            "occupation": occupations,
            "ligand_population": ligand_population,
        }
    )
    occupied = table.index[table.occupation > 0].max()
    virtual = occupied + 1
    occupied_window = table.iloc[
        max(0, occupied - args.occupied_window + 1) : occupied + 1
    ]
    virtual_window = table.iloc[virtual : virtual + args.virtual_window]
    selected_occupied = occupied_window.nlargest(3, "ligand_population")
    selected_virtual = virtual_window.nlargest(3, "ligand_population")
    selection = pd.concat([selected_occupied, selected_virtual]).sort_values("orbital")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output.with_suffix(".csv"), index=False)
    result = {
        "checkpoint": str(args.checkpoint),
        "ligand_atoms": ligand_atoms,
        "homo": int(occupied),
        "lumo": int(virtual),
        "selection_rule": (
            "three highest ligand-population occupied and virtual canonical orbitals "
            f"in fixed {args.occupied_window}-orbital occupied and "
            f"{args.virtual_window}-orbital virtual frontier windows"
        ),
        "candidate_orbitals": selection.to_dict(orient="records"),
        "candidate_active_space": {
            "electrons": int(selected_occupied.occupation.sum()),
            "orbitals": 6,
        },
        "status": "candidate only; inspect orbitals and correspondence across all systems before freezing",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    fig, axis = plt.subplots(figsize=(7, 5))
    shown = table.iloc[
        max(0, occupied - args.occupied_window + 1) : virtual + args.virtual_window
    ]
    axis.scatter(
        shown.ligand_population,
        shown.energy_hartree,
        c=np.where(shown.occupation > 0, "#2166ac", "#b2182b"),
    )
    for index, row in enumerate(selection.itertuples(index=False)):
        vertical_offset = 3 + 12 * (index % 3)
        axis.annotate(
            str(row.orbital),
            (row.ligand_population, row.energy_hartree),
            xytext=(4, vertical_offset),
            textcoords="offset points",
        )
    axis.axhline(energies[occupied], color="black", linestyle="--", linewidth=0.7)
    axis.set_xlabel("Ligand Mulliken population")
    axis.set_ylabel("Canonical orbital energy (Eh)")
    axis.set_title("Frontier orbital ligand character")
    fig.tight_layout()
    args.figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.figure, dpi=200)
    plt.close(fig)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
