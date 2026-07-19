#!/usr/bin/env python3

import argparse
import json
import time
from pathlib import Path

import numpy as np
from pyscf import gto, scf

from inquanto.ansatzes import FermionSpaceAnsatzUCCSD
from inquanto.computables import ExpectationValue
from inquanto.extensions.pyscf import ChemistryDriverPySCFMolecularRHF


ROOT = Path(__file__).resolve().parents[1]


def serialize_number(value):
    number = complex(value)
    return {
        "real": float(number.real),
        "imag": float(number.imag),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="WT_TMP")
    parser.add_argument("--basis", default="sto-3g")
    args = parser.parse_args()

    xyz_path = (
        ROOT
        / "data"
        / "processed"
        / "qm_clusters"
        / f"{args.system}_compact_primary.xyz"
    )

    param_path = (
        ROOT
        / "data"
        / "params"
        / f"{args.system}_params.json"
    )

    if not xyz_path.exists():
        raise SystemExit(f"❌ Missing geometry: {xyz_path}")

    if not param_path.exists():
        raise SystemExit(f"❌ Missing parameters: {param_path}")

    print(f"📥 Geometry: {xyz_path}", flush=True)
    print(f"📥 Parameters: {param_path}", flush=True)

    print("🔧 Rebuilding the same RHF active space...", flush=True)

    start = time.time()

    molecule = gto.M(
        atom=str(xyz_path),
        basis=args.basis,
        charge=0,
        spin=0,
    )

    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-5
    scf_energy = float(mean_field.kernel())

    if not mean_field.converged:
        print("⚠️ RHF did not converge.", flush=True)

    n_occ = int(np.sum(mean_field.mo_occ // 2))
    n_mo = len(mean_field.mo_energy)

    active_indices = list(range(n_occ - 3, n_occ + 3))
    frozen_indices = [
        index
        for index in range(n_mo)
        if index not in active_indices
    ]

    print(f"   Occupied orbitals: {n_occ}", flush=True)
    print(f"   Total orbitals: {n_mo}", flush=True)
    print(f"   Active orbitals: {active_indices}", flush=True)

    print("🔧 Generating the fermionic Hamiltonian...", flush=True)

    driver = ChemistryDriverPySCFMolecularRHF(
        geometry=str(xyz_path),
        basis=args.basis,
        charge=0,
        frozen=frozen_indices,
        df=True,
    )

    fermion_hamiltonian, fermion_space, hf_state = driver.get_system()

    print("🔧 Encoding the Hamiltonian to qubits...", flush=True)

    qubit_hamiltonian = fermion_hamiltonian.qubit_encode()
    ansatz = FermionSpaceAnsatzUCCSD(
        fermion_space,
        hf_state,
    )

    saved = json.loads(param_path.read_text())["params"]

    symbol_map = {
        symbol.name: symbol
        for symbol in ansatz.state_circuit.free_symbols()
    }

    parameters = {
        symbol_map[name]: float(value)
        for name, value in saved.items()
        if name in symbol_map
    }

    missing = sorted(set(symbol_map) - set(saved))

    if missing:
        raise SystemExit(
            "❌ Missing saved parameters: "
            + ", ".join(missing)
        )

    print(f"   Qubits: {ansatz.state_circuit.n_qubits}", flush=True)
    print(f"   Hamiltonian terms: {len(qubit_hamiltonian)}", flush=True)
    print(f"   Loaded parameters: {len(parameters)}", flush=True)

    print(
        "⚛️ Evaluating exact saved-parameter energy "
        "with an ideal statevector...",
        flush=True,
    )

    energy_expression = ExpectationValue(
        ansatz,
        qubit_hamiltonian,
    )

    energy_value = complex(
        energy_expression.default_evaluate(parameters)
    )

    elapsed = time.time() - start

    if abs(energy_value.imag) > 1e-8:
        print(
            f"⚠️ Non-negligible imaginary component: "
            f"{energy_value.imag}",
            flush=True,
        )

    output_dir = ROOT / "results" / "quantum"
    output_dir.mkdir(parents=True, exist_ok=True)

    result_path = (
        output_dir
        / f"{args.system}_saved_params_exact.json"
    )

    hamiltonian_path = (
        ROOT
        / "data"
        / "processed"
        / f"{args.system}_qubit_hamiltonian.json"
    )

    hamiltonian_terms = []

    for pauli_string, coefficient in zip(
        qubit_hamiltonian.pauli_strings,
        qubit_hamiltonian.coefficients,
    ):
        hamiltonian_terms.append(
            {
                "pauli_string": str(pauli_string),
                "coefficient": serialize_number(coefficient),
            }
        )

    hamiltonian_payload = {
        "system": args.system,
        "basis": args.basis,
        "n_qubits": ansatz.state_circuit.n_qubits,
        "n_terms": len(qubit_hamiltonian),
        "active_orbitals": active_indices,
        "terms": hamiltonian_terms,
    }

    hamiltonian_path.write_text(
        json.dumps(hamiltonian_payload, indent=2)
    )

    result = {
        "system": args.system,
        "basis": args.basis,
        "method": "UCCSD saved-parameter exact expectation",
        "backend": "ideal statevector",
        "scf_energy_hartree": scf_energy,
        "vqe_energy_hartree": float(energy_value.real),
        "imaginary_component": float(energy_value.imag),
        "correlation_relative_to_scf_hartree": float(
            energy_value.real - scf_energy
        ),
        "n_qubits": ansatz.state_circuit.n_qubits,
        "n_hamiltonian_terms": len(qubit_hamiltonian),
        "n_parameters": len(parameters),
        "active_orbitals": active_indices,
        "elapsed_seconds": elapsed,
        "hamiltonian_file": str(hamiltonian_path),
    }

    result_path.write_text(
        json.dumps(result, indent=2)
    )

    print("", flush=True)
    print("✅ Exact saved-parameter evaluation finished.", flush=True)
    print(f"   SCF energy: {scf_energy:.12f} Hartree", flush=True)
    print(
        f"   VQE energy: {energy_value.real:.12f} Hartree",
        flush=True,
    )
    print(
        f"   VQE − SCF: "
        f"{energy_value.real - scf_energy:.12f} Hartree",
        flush=True,
    )
    print(f"   Runtime: {elapsed:.1f} seconds", flush=True)
    print(f"💾 Result: {result_path}", flush=True)
    print(f"💾 Hamiltonian: {hamiltonian_path}", flush=True)


if __name__ == "__main__":
    main()
