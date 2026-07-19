#!/usr/bin/env python3
"""Build union-defined QM clusters with explicit peptide-boundary link atoms."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from openmm import app, unit
from openmm.app.element import Element

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
CONFIG = ROOT / "configs/cluster_models.yaml"
SYSTEMS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")
PROTEIN = {
    "ALA",
    "ARG",
    "ASN",
    "ASP",
    "CYS",
    "GLN",
    "GLU",
    "GLY",
    "HIS",
    "ILE",
    "LEU",
    "LYS",
    "MET",
    "PHE",
    "PRO",
    "SER",
    "THR",
    "TRP",
    "TYR",
    "VAL",
}
SIDECHAIN_CHARGE = {"ARG": 1, "LYS": 1, "ASP": -1, "GLU": -1}


def xyz(pdb: app.PDBFile) -> np.ndarray:
    return np.asarray(
        [position.value_in_unit(unit.angstrom) for position in pdb.positions]
    )


def source_path(system: str, suffix: str | None) -> Path:
    label = f"_{suffix}" if suffix else ""
    return PROCESSED / f"{system}_minimized{label}.pdb"


def selected_union(cutoff: float, suffix: str | None) -> list[int]:
    selected: set[int] = set()
    for system in SYSTEMS:
        pdb = app.PDBFile(str(source_path(system, suffix)))
        positions = xyz(pdb)
        ligand = [
            atom.index
            for atom in pdb.topology.atoms()
            if atom.residue.name in {"TOP", "DTM"} and atom.element.symbol != "H"
        ]
        for residue in pdb.topology.residues():
            if residue.name not in PROTEIN:
                continue
            heavy = [
                atom.index for atom in residue.atoms() if atom.element.symbol != "H"
            ]
            distance = np.linalg.norm(
                positions[heavy, None, :] - positions[ligand][None, :, :], axis=2
            ).min()
            if distance <= cutoff:
                selected.add(int(residue.id))
    return sorted(selected)


def link_position(
    anchor: np.ndarray, excluded: np.ndarray, length: float
) -> np.ndarray:
    direction = excluded - anchor
    return anchor + direction / np.linalg.norm(direction) * length


def build(
    system: str,
    tier: str,
    residues: list[int],
    water_cutoff: float | None,
    structure_suffix: str | None,
    ligand_formal_charge: int,
) -> dict[str, object]:
    pdb = app.PDBFile(str(source_path(system, structure_suffix)))
    positions = xyz(pdb)
    protein_residues = [
        residue for residue in pdb.topology.residues() if residue.name in PROTEIN
    ]
    by_number = {int(residue.id): residue for residue in protein_residues}
    selected = set(residues)
    ligand_residue = next(
        residue for residue in pdb.topology.residues() if residue.name in {"TOP", "DTM"}
    )
    ligand_heavy = [
        atom.index for atom in ligand_residue.atoms() if atom.element.symbol != "H"
    ]
    atoms: list[dict[str, object]] = []

    def append_atom(
        element: str, position: np.ndarray, fragment: str, label: str
    ) -> None:
        atoms.append(
            {"element": element, "xyz": position, "fragment": fragment, "label": label}
        )

    for number in residues:
        residue = by_number[number]
        for atom in residue.atoms():
            append_atom(
                atom.element.symbol,
                positions[atom.index],
                "environment",
                f"{residue.name}{number}:{atom.name}",
            )
    for atom in ligand_residue.atoms():
        append_atom(
            atom.element.symbol,
            positions[atom.index],
            "ligand",
            f"{ligand_residue.name}:{atom.name}",
        )

    retained_waters = 0
    if water_cutoff is not None:
        for residue in pdb.topology.residues():
            if residue.name not in {"HOH", "WAT"}:
                continue
            oxygen = next(
                atom for atom in residue.atoms() if atom.element.symbol == "O"
            )
            distance = np.linalg.norm(
                positions[oxygen.index] - positions[ligand_heavy], axis=1
            ).min()
            if distance <= water_cutoff:
                retained_waters += 1
                for atom in residue.atoms():
                    append_atom(
                        atom.element.symbol,
                        positions[atom.index],
                        "environment",
                        f"water{residue.id}:{atom.name}",
                    )

    link_count = 0
    for index, residue in enumerate(protein_residues):
        number = int(residue.id)
        if number not in selected:
            continue
        atom_by_name = {atom.name: atom for atom in residue.atoms()}
        if index > 0 and int(protein_residues[index - 1].id) not in selected:
            previous = {atom.name: atom for atom in protein_residues[index - 1].atoms()}
            if "N" in atom_by_name and "C" in previous:
                append_atom(
                    "H",
                    link_position(
                        positions[atom_by_name["N"].index],
                        positions[previous["C"].index],
                        1.01,
                    ),
                    "environment",
                    f"link:N{number}",
                )
                link_count += 1
        if (
            index + 1 < len(protein_residues)
            and int(protein_residues[index + 1].id) not in selected
        ):
            following = {
                atom.name: atom for atom in protein_residues[index + 1].atoms()
            }
            if "C" in atom_by_name and "N" in following:
                append_atom(
                    "H",
                    link_position(
                        positions[atom_by_name["C"].index],
                        positions[following["N"].index],
                        1.09,
                    ),
                    "environment",
                    f"link:C{number}",
                )
                link_count += 1

    environment_charge = sum(
        SIDECHAIN_CHARGE.get(by_number[number].name, 0) for number in residues
    )
    charge = environment_charge + ligand_formal_charge
    electron_count = (
        sum(Element.getBySymbol(str(atom["element"])).atomic_number for atom in atoms)
        - charge
    )
    if electron_count % 2:
        raise ValueError(
            f"{system}/{tier}: odd electron count {electron_count} is incompatible with multiplicity 1"
        )
    output_dir = PROCESSED / "qm_clusters"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{system}_{tier}"
    with (output_dir / f"{stem}.xyz").open("w") as handle:
        handle.write(
            f"{len(atoms)}\ncharge={charge} multiplicity=1 system={system} tier={tier}\n"
        )
        for atom in atoms:
            x, y, z = atom["xyz"]
            handle.write(f"{atom['element']:<2} {x: .10f} {y: .10f} {z: .10f}\n")
    pd.DataFrame(
        [
            {
                "atom_index": i,
                "element": atom["element"],
                "fragment": atom["fragment"],
                "label": atom["label"],
            }
            for i, atom in enumerate(atoms)
        ]
    ).to_csv(output_dir / f"{stem}_atoms.csv", index=False)
    metadata = {
        "system": system,
        "tier": tier,
        "structure_suffix": structure_suffix or "neutral",
        "residue_numbers": residues,
        "atom_count": len(atoms),
        "link_atoms": link_count,
        "waters": retained_waters,
        "charge": charge,
        "ligand_charge": ligand_formal_charge,
        "environment_charge": environment_charge,
        "electron_count": electron_count,
        "multiplicity": 1,
        "ligand_fragment_atoms": sum(atom["fragment"] == "ligand" for atom in atoms),
        "environment_fragment_atoms": sum(
            atom["fragment"] == "environment" for atom in atoms
        ),
    }
    (output_dir / f"{stem}.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text())
    rows = []
    for tier, definition in config["tiers"].items():
        suffix = definition.get("structure_suffix")
        residues = definition.get("protein_residue_numbers")
        if residues is None:
            residues = selected_union(
                float(definition["protein_cutoff_angstrom"]), suffix
            )
        for system in SYSTEMS:
            rows.append(
                build(
                    system,
                    tier,
                    residues,
                    definition["water_cutoff_angstrom"],
                    suffix,
                    int(definition["ligand_formal_charge"]),
                )
            )
    table = pd.DataFrame(rows)
    output = ROOT / "results/tables/qm_cluster_manifest.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
