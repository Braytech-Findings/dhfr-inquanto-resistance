#!/usr/bin/env python3
"""Select and report an AVAS active space from a converged PySCF checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyscf import scf
from pyscf.mcscf import avas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--ao-label", action="append", default=["N", "O"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    mol, scf_data = scf.chkfile.load_scf(str(args.checkpoint))
    mf = scf.RHF(mol)
    mf.__dict__.update(scf_data)
    ncas, nelecas, mo = avas.avas(mf, args.ao_label)
    result = {
        "method": "AVAS",
        "ao_labels": args.ao_label,
        "active_orbitals": int(ncas),
        "active_electrons": int(nelecas),
        "requested_model_space": "Review and reduce to (6e,6o) only after orbital inspection",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
