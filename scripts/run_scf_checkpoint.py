#!/usr/bin/env python3
"""Run one converged cluster SCF and save a checkpoint for AVAS/orbital review."""

from __future__ import annotations

import argparse
from pathlib import Path

from pyscf import dft, gto, qmmm, scf
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLUSTERS = ROOT / "data/processed/qm_clusters"
EMBEDDING = ROOT / "data/processed/embedding"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", required=True)
    parser.add_argument("--tier", default="compact_primary")
    parser.add_argument("--method", choices=("HF", "PBE0"), default="HF")
    parser.add_argument("--basis", default="sto-3g")
    parser.add_argument("--memory", type=int, default=4000)
    parser.add_argument("--conv-tol", type=float, default=1e-8)
    parser.add_argument("--no-embedding", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stem = f"{args.system}_{args.tier}"
    metadata = __import__("json").loads((CLUSTERS / f"{stem}.json").read_text())
    lines = (CLUSTERS / f"{stem}.xyz").read_text().splitlines()[2:]
    atoms = [(fields[0], tuple(float(value) for value in fields[1:4])) for fields in (line.split() for line in lines)]
    molecule = gto.M(atom=atoms, basis=args.basis, charge=int(metadata["charge"]), spin=0, unit="Angstrom", verbose=3, max_memory=args.memory)
    mean_field = scf.RHF(molecule) if args.method == "HF" else dft.RKS(molecule)
    if args.method == "PBE0":
        mean_field.xc = "pbe0"
        mean_field = mean_field.density_fit()
    if not args.no_embedding:
        background = "L28R" if args.system.startswith("L28R") else "WT"
        embedding = pd.read_csv(EMBEDDING / f"{background}_nadph_charmm36.csv")
        mean_field = qmmm.mm_charge(mean_field, embedding[["x_A", "y_A", "z_A"]].to_numpy(), embedding["charge_e"].to_numpy(), unit="Angstrom")
    mean_field.conv_tol = args.conv_tol
    mean_field.chkfile = str(args.output)
    energy = float(mean_field.kernel())
    if not mean_field.converged:
        raise RuntimeError("SCF did not converge")
    print({"checkpoint": str(args.output), "energy_hartree": energy, "converged": bool(mean_field.converged)})


if __name__ == "__main__":
    main()
