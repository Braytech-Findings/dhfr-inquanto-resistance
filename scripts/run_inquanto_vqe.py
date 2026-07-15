#!/usr/bin/env python3
"""Run an ideal-statevector InQuanto UCCSD VQE from an InQuanto HDF5 system.

Generate the HDF5 Hamiltonian with the licensed inquanto-pyscf extension after
selecting the active orbitals. This boundary is intentional: an orbital NPZ is
not a quantum-chemistry Hamiltonian and cannot safely be substituted for one.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("system_h5", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    try:
        from inquanto.ansatzes import FermionSpaceAnsatzUCCSD
        from inquanto.express import get_system, run_vqe
        from pytket.extensions.qiskit import AerStateBackend
    except ImportError as exc:
        raise SystemExit("Install licensed InQuanto plus pytket-qiskit in the dhfr-qc environment") from exc

    fermion_hamiltonian, fermion_space, hf_state = get_system(str(args.system_h5))
    ansatz = FermionSpaceAnsatzUCCSD(fermion_space, hf_state)
    qubit_hamiltonian = fermion_hamiltonian.qubit_encode()
    calculation = run_vqe(ansatz, qubit_hamiltonian, AerStateBackend())
    result = {
        "system": str(args.system_h5),
        "algorithm": "UCCSD-VQE",
        "backend": "AerStateBackend (ideal statevector)",
        "energy_hartree": float(calculation.final_value),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

