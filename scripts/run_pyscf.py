#!/usr/bin/env python3
"""Run a reproducible PySCF single point from an XYZ geometry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from pyscf import dft, gto, scf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xyz", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method", choices=("HF", "B3LYP"), default="HF")
    parser.add_argument("--basis", default="def2-SVP")
    parser.add_argument("--charge", type=int, default=0)
    parser.add_argument("--spin", type=int, default=0, help="2S = unpaired alpha minus beta electrons")
    parser.add_argument("--memory", type=int, default=4000)
    parser.add_argument("--save-orbitals", type=Path)
    parser.add_argument("--checkpoint", type=Path, help="PySCF checkpoint for AVAS/restart")
    args = parser.parse_args()

    mol = gto.M(atom=str(args.xyz), basis=args.basis, charge=args.charge, spin=args.spin, unit="Angstrom", verbose=4, max_memory=args.memory)
    mf = scf.RHF(mol) if args.method == "HF" and args.spin == 0 else scf.UHF(mol) if args.method == "HF" else dft.RKS(mol) if args.spin == 0 else dft.UKS(mol)
    if args.method == "B3LYP":
        mf.xc = "b3lyp"
    if args.checkpoint:
        args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        mf.chkfile = str(args.checkpoint)
    mf.conv_tol = 1e-9
    energy = float(mf.kernel())
    if not mf.converged:
        raise RuntimeError("SCF did not converge")
    result = {"geometry": str(args.xyz), "method": args.method, "basis": args.basis, "charge": args.charge, "spin": args.spin, "total_energy_hartree": energy, "converged": bool(mf.converged)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if args.save_orbitals:
        args.save_orbitals.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.save_orbitals, mo_coeff=mf.mo_coeff, mo_energy=mf.mo_energy, mo_occ=mf.mo_occ)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
