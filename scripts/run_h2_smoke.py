#!/usr/bin/env python3
"""Two-atom PySCF Hartree-Fock competency smoke test."""

from __future__ import annotations

import json
from pathlib import Path

from pyscf import gto, scf

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    mol = gto.M(atom="H 0 0 0; H 0 0 0.74", basis="sto-3g", unit="Angstrom", verbose=0)
    mf = scf.RHF(mol)
    energy = float(mf.kernel())
    result = {
        "system": "H2",
        "distance_angstrom": 0.74,
        "method": "RHF",
        "basis": "STO-3G",
        "energy_hartree": energy,
        "converged": bool(mf.converged),
    }
    if not mf.converged:
        raise RuntimeError("H2 RHF did not converge")
    output = ROOT / "results/tables/h2_smoke.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
