#!/usr/bin/env python3
"""Build WT_TMP measurement circuits for local H2-1LE emulation.

This command reads a saved geometry and VQE parameters, then writes local
measurement-plan files. It does not contact Nexus or submit paid work. The
current saved parameters exist only for WT_TMP, so other systems are rejected
unless equivalent evidence is added and reviewed.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from pyscf import gto, scf

from inquanto.ansatzes import FermionSpaceAnsatzUCCSD
from inquanto.computables import ExpectationValue
from inquanto.extensions.pyscf import ChemistryDriverPySCFMolecularRHF
from inquanto.protocols import PauliAveraging

from pytket.extensions.quantinuum import (
    QuantinuumAPIOffline,
    QuantinuumBackend,
)


ROOT = Path(__file__).resolve().parents[1]

try:
    from .audit_core import backend_metadata, canonical_system, total_shots
except ImportError:
    from audit_core import backend_metadata, canonical_system, total_shots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="WT_TMP")
    parser.add_argument("--basis", default="sto-3g")
    parser.add_argument("--shots-per-circuit", type=int, default=100)
    args = parser.parse_args()
    args.system = canonical_system(args.system)
    if args.system != "WT_TMP":
        parser.error("Only WT_TMP has reviewed saved VQE parameters.")
    total_shots(0, args.shots_per_circuit)

    xyz_path = (
        ROOT
        / "data"
        / "processed"
        / "qm_clusters"
        / f"{args.system}_compact_primary.xyz"
    )

    parameter_path = ROOT / "data" / "params" / f"{args.system}_params.json"

    output_dir = ROOT / "results" / "quantum" / "measurement_plans"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not xyz_path.exists():
        raise SystemExit(f"❌ Missing geometry: {xyz_path}")

    if not parameter_path.exists():
        raise SystemExit(f"❌ Missing parameters: {parameter_path}")

    start = time.time()

    print("🔧 Reconstructing RHF active space...", flush=True)

    molecule = gto.M(
        atom=str(xyz_path),
        basis=args.basis,
        charge=0,
        spin=0,
    )

    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-5
    mean_field.kernel()

    if not mean_field.converged:
        raise RuntimeError(
            "RHF did not converge; refusing to build a measurement plan."
        )

    n_occ = int(np.sum(mean_field.mo_occ // 2))
    n_mo = len(mean_field.mo_energy)

    active_indices = list(range(n_occ - 3, n_occ + 3))
    frozen_indices = [index for index in range(n_mo) if index not in active_indices]

    print(f"   Active orbitals: {active_indices}", flush=True)

    print("🔧 Regenerating Hamiltonian and ansatz...", flush=True)

    driver = ChemistryDriverPySCFMolecularRHF(
        geometry=str(xyz_path),
        basis=args.basis,
        charge=0,
        frozen=frozen_indices,
        df=True,
    )

    fermion_hamiltonian, fermion_space, hf_state = driver.get_system()
    qubit_hamiltonian = fermion_hamiltonian.qubit_encode()

    ansatz = FermionSpaceAnsatzUCCSD(
        fermion_space,
        hf_state,
    )

    saved_parameters = json.loads(parameter_path.read_text())["params"]

    symbols = {symbol.name: symbol for symbol in ansatz.state_circuit.free_symbols()}

    parameters = {
        symbols[name]: float(value)
        for name, value in saved_parameters.items()
        if name in symbols
    }

    missing = sorted(set(symbols) - set(saved_parameters))

    if missing:
        raise SystemExit("❌ Missing parameter values: " + ", ".join(missing))

    print(f"   Qubits: {ansatz.state_circuit.n_qubits}", flush=True)
    print(f"   Hamiltonian terms: {len(qubit_hamiltonian)}", flush=True)
    print(f"   Parameters: {len(parameters)}", flush=True)

    backend = QuantinuumBackend(
        device_name="H2-1LE",
        api_handler=QuantinuumAPIOffline(),
    )

    energy = ExpectationValue(
        ansatz,
        qubit_hamiltonian,
    )

    print(
        "🧩 Grouping Pauli terms into measurement circuits...",
        flush=True,
    )

    protocol = PauliAveraging(
        backend=backend,
        shots_per_circuit=args.shots_per_circuit,
    )

    protocol.build_from(
        parameters,
        energy,
    )

    circuits = protocol.get_circuits()
    number_of_circuits = len(circuits)
    shot_total = total_shots(number_of_circuits, args.shots_per_circuit)

    resource_table = protocol.dataframe_circuit_shot()
    partition_table = protocol.dataframe_partitioning()

    resource_path = output_dir / (
        f"{args.system}_H2-1LE_{args.shots_per_circuit}shots_resources.csv"
    )

    partition_path = output_dir / f"{args.system}_pauli_partitioning.csv"

    summary_path = output_dir / (
        f"{args.system}_H2-1LE_{args.shots_per_circuit}shots_plan.json"
    )

    resource_table.to_csv(resource_path, index=True)
    partition_table.to_csv(partition_path, index=False)

    summary = {
        "system": args.system,
        "basis": args.basis,
        "backend": backend_metadata("H2-1LE")["label"],
        "backend_metadata": backend_metadata("H2-1LE"),
        "n_qubits": ansatz.state_circuit.n_qubits,
        "n_hamiltonian_terms": len(qubit_hamiltonian),
        "n_measurement_circuits": number_of_circuits,
        "shots_per_circuit": args.shots_per_circuit,
        "total_shots": shot_total,
        "active_orbitals": active_indices,
        "preparation_seconds": time.time() - start,
        "resource_table": str(resource_path),
        "partition_table": str(partition_path),
    }

    summary_path.write_text(json.dumps(summary, indent=2))

    print("", flush=True)
    print("✅ Measurement plan prepared.", flush=True)
    print(f"   Hamiltonian terms: {len(qubit_hamiltonian)}")
    print(f"   Grouped circuits: {number_of_circuits}")
    print(f"   Shots per circuit: {args.shots_per_circuit}")
    print(f"   Total local shots: {shot_total}")
    print(f"   Preparation time: {time.time() - start:.1f} seconds")
    print(f"💾 Summary: {summary_path}")
    print(f"💾 Resources: {resource_path}")
    print(f"💾 Partitioning: {partition_path}")

    print("")
    print("=== CIRCUIT RESOURCE SUMMARY ===")
    print(resource_table.to_string())


if __name__ == "__main__":
    main()
