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
from inquanto.protocols import PauliAveraging

from pytket.extensions.quantinuum import (
    QuantinuumAPIOffline,
    QuantinuumBackend,
)


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="WT_TMP")
    parser.add_argument("--basis", default="sto-3g")
    parser.add_argument("--shots-per-circuit", type=int, default=100)
    args = parser.parse_args()

    xyz_path = (
        ROOT
        / "data"
        / "processed"
        / "qm_clusters"
        / f"{args.system}_compact_primary.xyz"
    )

    parameter_path = (
        ROOT
        / "data"
        / "params"
        / f"{args.system}_params.json"
    )

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
        print("⚠️ RHF did not converge.", flush=True)

    n_occ = int(np.sum(mean_field.mo_occ // 2))
    n_mo = len(mean_field.mo_energy)

    active_indices = list(range(n_occ - 3, n_occ + 3))
    frozen_indices = [
        index
        for index in range(n_mo)
        if index not in active_indices
    ]

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

    saved_parameters = json.loads(
        parameter_path.read_text()
    )["params"]

    symbols = {
        symbol.name: symbol
        for symbol in ansatz.state_circuit.free_symbols()
    }

    parameters = {
        symbols[name]: float(value)
        for name, value in saved_parameters.items()
        if name in symbols
    }

    missing = sorted(set(symbols) - set(saved_parameters))

    if missing:
        raise SystemExit(
            "❌ Missing parameter values: "
            + ", ".join(missing)
        )

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
    total_shots = number_of_circuits * args.shots_per_circuit

    checkpoint_dir = (
        ROOT
        / "results"
        / "quantum"
        / "protocol_checkpoints"
    )
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    built_checkpoint = (
        checkpoint_dir
        / (
            f"{args.system}_H2-1LE_"
            f"{args.shots_per_circuit}shots_built.pkl"
        )
    )

    compiled_checkpoint = (
        checkpoint_dir
        / (
            f"{args.system}_H2-1LE_"
            f"{args.shots_per_circuit}shots_compiled.pkl"
        )
    )

    completed_checkpoint = (
        checkpoint_dir
        / (
            f"{args.system}_H2-1LE_"
            f"{args.shots_per_circuit}shots_completed.pkl"
        )
    )

    protocol.dump(str(built_checkpoint))

    print("", flush=True)
    print("✅ Logical measurement circuits built.", flush=True)
    print(f"   Grouped circuits: {number_of_circuits}", flush=True)
    print(f"   Shots per circuit: {args.shots_per_circuit}", flush=True)
    print(f"   Total shots: {total_shots}", flush=True)
    print(f"💾 Built checkpoint: {built_checkpoint}", flush=True)

    print("", flush=True)
    print(
        "🔧 Compiling all measurement circuits for H2-1LE...",
        flush=True,
    )

    compile_start = time.time()

    protocol.compile_circuits(
        optimization_level=0,
    )

    compile_seconds = time.time() - compile_start

    compiled_resources = protocol.dataframe_circuit_shot()

    compiled_resource_path = (
        output_dir
        / (
            f"{args.system}_H2-1LE_"
            f"{args.shots_per_circuit}shots_"
            "compiled_resources.csv"
        )
    )

    compiled_resources.to_csv(
        compiled_resource_path,
        index=True,
    )

    protocol.dump(str(compiled_checkpoint))

    print(
        f"✅ Compilation finished in "
        f"{compile_seconds:.1f} seconds.",
        flush=True,
    )
    print(
        f"💾 Compiled checkpoint: {compiled_checkpoint}",
        flush=True,
    )
    print(
        f"💾 Compiled resources: {compiled_resource_path}",
        flush=True,
    )

    print("", flush=True)
    print(
        f"🚀 Executing {number_of_circuits} circuits "
        f"with {args.shots_per_circuit} shots each...",
        flush=True,
    )

    run_start = time.time()

    protocol.run()

    run_seconds = time.time() - run_start

    print(
        f"✅ All local measurements completed in "
        f"{run_seconds:.1f} seconds.",
        flush=True,
    )

    print("⚛️ Reconstructing the molecular energy...", flush=True)

    measured_energy = complex(
        energy.evaluate(
            protocol.get_evaluator()
        )
    )

    energy_uvalue = protocol.evaluate_expectation_uvalue(
        ansatz,
        qubit_hamiltonian,
    )

    nominal_energy = float(
        getattr(
            energy_uvalue,
            "nominal_value",
            getattr(
                energy_uvalue,
                "n",
                measured_energy.real,
            ),
        )
    )

    standard_error = float(
        getattr(
            energy_uvalue,
            "std_dev",
            getattr(
                energy_uvalue,
                "s",
                float("nan"),
            ),
        )
    )

    exact_path = (
        ROOT
        / "results"
        / "quantum"
        / f"{args.system}_saved_params_exact.json"
    )

    exact_energy = None

    if exact_path.exists():
        exact_energy = float(
            json.loads(
                exact_path.read_text()
            )["vqe_energy_hartree"]
        )

    difference_from_exact = (
        nominal_energy - exact_energy
        if exact_energy is not None
        else None
    )

    measurement_table = protocol.dataframe_measurements()

    measurement_path = (
        ROOT
        / "results"
        / "quantum"
        / (
            f"{args.system}_H2-1LE_"
            f"{args.shots_per_circuit}shots_"
            "pauli_measurements.csv"
        )
    )

    measurement_table.to_csv(
        measurement_path,
        index=False,
    )

    result_path = (
        ROOT
        / "results"
        / "quantum"
        / (
            f"{args.system}_H2-1LE_"
            f"{args.shots_per_circuit}shots_energy.json"
        )
    )

    result = {
        "system": args.system,
        "basis": args.basis,
        "backend": "H2-1LE",
        "backend_type": "local noiseless H2 emulator",
        "method": "UCCSD PauliAveraging",
        "n_qubits": ansatz.state_circuit.n_qubits,
        "n_hamiltonian_terms": len(qubit_hamiltonian),
        "n_measurement_circuits": number_of_circuits,
        "shots_per_circuit": args.shots_per_circuit,
        "total_shots": total_shots,
        "shot_based_energy_hartree": nominal_energy,
        "standard_error_hartree": standard_error,
        "exact_energy_hartree": exact_energy,
        "difference_from_exact_hartree": difference_from_exact,
        "compile_seconds": compile_seconds,
        "execution_seconds": run_seconds,
        "total_seconds": time.time() - start,
        "measurement_table": str(measurement_path),
        "compiled_resources": str(compiled_resource_path),
    }

    result_path.write_text(
        json.dumps(result, indent=2)
    )

    protocol.dump(str(completed_checkpoint))

    print("", flush=True)
    print("======================================")
    print("✅ SHOT-BASED VQE ENERGY COMPLETE")
    print("======================================")
    print(
        f"Shot-based energy: "
        f"{nominal_energy:.12f} Hartree"
    )
    print(
        f"Standard error:    "
        f"{standard_error:.12f} Hartree"
    )

    if exact_energy is not None:
        print(
            f"Exact reference:   "
            f"{exact_energy:.12f} Hartree"
        )
        print(
            f"Difference:        "
            f"{difference_from_exact:+.12f} Hartree"
        )

    print(f"Measurement circuits: {number_of_circuits}")
    print(f"Total shots: {total_shots}")
    print(f"💾 Result: {result_path}")
    print(f"💾 Measurements: {measurement_path}")
    print(f"💾 Completed checkpoint: {completed_checkpoint}")


if __name__ == "__main__":
    main()
