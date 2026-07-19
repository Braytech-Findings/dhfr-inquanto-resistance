#!/usr/bin/env python3
"""Validate a selected CAS(6,6) space with exact CASCI natural occupations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyscf import fci, mcscf, qmmm, scf

ROOT = Path(__file__).resolve().parents[1]
EMBEDDING = ROOT / "data/processed/embedding"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("selection", type=Path)
    parser.add_argument("--system", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--density-fit",
        action="store_true",
        help="Use density-fitted CASCI for tractable active-space screening.",
    )
    args = parser.parse_args()
    molecule, data = scf.chkfile.load_scf(str(args.checkpoint))
    mean_field = scf.RHF(molecule)
    background = "L28R" if args.system.startswith("L28R") else "WT"
    embedding = pd.read_csv(EMBEDDING / f"{background}_nadph_charmm36.csv")
    mean_field = qmmm.mm_charge(
        mean_field,
        embedding[["x_A", "y_A", "z_A"]].to_numpy(),
        embedding["charge_e"].to_numpy(),
        unit="Angstrom",
    )
    mean_field.__dict__.update(data)
    selection_bytes = args.selection.read_bytes()
    selection = json.loads(selection_bytes)
    orbitals = [int(row["orbital"]) for row in selection["candidate_orbitals"]]
    if len(orbitals) != 6 or selection["candidate_active_space"] != {
        "electrons": 6,
        "orbitals": 6,
    }:
        raise ValueError("Expected exactly a 6e,6o candidate selection")
    casci = (
        mcscf.DFCASCI(mean_field, 6, 6)
        if args.density_fit
        else mcscf.CASCI(mean_field, 6, 6)
    )
    casci.fcisolver = fci.direct_spin0.FCI(molecule)
    sorted_orbitals = mcscf.addons.sort_mo(casci, mean_field.mo_coeff, caslst=orbitals)
    energy, _, ci, _, _ = casci.kernel(sorted_orbitals)
    active_rdm = casci.fcisolver.make_rdm1(ci, casci.ncas, casci.nelecas)
    occupations = np.linalg.eigvalsh(active_rdm)[::-1]
    spin_square, multiplicity = casci.fcisolver.spin_square(
        ci, casci.ncas, casci.nelecas
    )
    result = {
        "system": args.system,
        "method": "DF-CASCI" if args.density_fit else "CASCI",
        "active_electrons": 6,
        "active_orbitals": 6,
        "selected_canonical_orbitals": orbitals,
        "selection_sha256": hashlib.sha256(selection_bytes).hexdigest(),
        "energy_hartree": float(energy),
        "natural_occupations": occupations.tolist(),
        "occupation_sum": float(occupations.sum()),
        "spin_square": float(spin_square),
        "multiplicity": float(multiplicity),
        "status": "pass" if np.isclose(occupations.sum(), 6.0, atol=1e-6) else "fail",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
