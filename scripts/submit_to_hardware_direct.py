#!/usr/bin/env python3
"""
Submit a pre‑optimized VQE circuit to Quantinuum H2‑1 hardware using qnexus directly.
This script does NOT require inquanto.extensions.nexus.

If no saved parameters are found, it runs a quick local noiseless VQE to generate them.
"""

import pathlib
import json
import sys
import time
import argparse
import numpy as np
import pandas as pd
import qnexus as qnx
from qnexus import QuantinuumConfig
from pyscf import gto, scf
from inquanto.spaces import FermionSpace
from inquanto.states import FermionState
from inquanto.extensions.pyscf import ChemistryDriverPySCFMolecularRHF
from inquanto.ansatzes import FermionSpaceAnsatzUCCSD
from inquanto.express import run_vqe
from pytket.extensions.qiskit import AerStateBackend
from pytket.qasm import circuit_to_qasm

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RESULTS = PROJECT_ROOT / "results" / "tables"
PARAM_DIR = PROJECT_ROOT / "data" / "params"
PARAM_DIR.mkdir(parents=True, exist_ok=True)

def get_optimized_params(system_id: str, basis: str = "sto-3g", force_recompute: bool = False):
    """
    Load saved parameters from JSON, or run a quick local VQE if missing.
    Returns: (ansatz, params)
    """
    param_path = PARAM_DIR / f"{system_id}_params.json"
    xyz_file = DATA_PROCESSED / "qm_clusters" / f"{system_id}_compact_primary.xyz"

    if not xyz_file.exists():
        raise FileNotFoundError(f"Missing pocket geometry file: {xyz_file}")

    # 1. Run a quick PySCF RHF to get the number of occupied orbitals and total orbitals
    # so we can define the active space and frozen list.
    mol = gto.M(atom=str(xyz_file), basis=basis, charge=0, spin=0)
    mf = scf.RHF(mol)
    mf.conv_tol = 1e-5 # Speed up local optimization setup
    mf.kernel()
    if not mf.converged:
        print("⚠️ Warning: PySCF RHF did not converge, proceeding anyway.")

    n_occ = int(np.sum(mf.mo_occ // 2))
    n_mo = len(mf.mo_energy)
    active_indices = list(range(n_occ - 3, n_occ + 3))
    frozen_indices = [i for i in range(n_mo) if i not in active_indices]

    # 2. Build the Chemistry Driver and get the system
    driver = ChemistryDriverPySCFMolecularRHF(
        geometry=str(xyz_file),
        basis=basis,
        charge=0,
        frozen=frozen_indices,
        df=True # Enable density fitting for significant speedup
    )
    ham, space, state = driver.get_system()
    ansatz = FermionSpaceAnsatzUCCSD(space, state)

    # Try to load existing parameters
    if not force_recompute and param_path.exists():
        with open(param_path, "r") as f:
            data = json.load(f)
        symbol_map = {sym.name: sym for sym in ansatz.state_circuit.free_symbols()}
        params = {symbol_map[name]: value for name, value in data["params"].items() if name in symbol_map}
        print(f"✅ Loaded saved parameters for {system_id}")
        return ansatz, params

    # If not found, run a quick local VQE
    print(f"🔧 No saved parameters for {system_id}. Running local noiseless VQE (this may take a few minutes)...")
    q_ham = ham.qubit_encode()
    vqe_result = run_vqe(ansatz, q_ham, AerStateBackend())
    
    params = vqe_result.final_parameters
    # Save parameters for future use
    serialized_params = {str(k): float(v) for k, v in params.items()}
    with open(param_path, "w") as f:
        json.dump({"params": serialized_params}, f, indent=2)
    print(f"✅ Local VQE finished. Parameters saved to {param_path}")
    return ansatz, params

def main():
    parser = argparse.ArgumentParser(description="Submit VQE circuit to Quantinuum hardware")
    parser.add_argument("--system", default="WT_TMP", help="System ID (e.g., WT_TMP)")
    parser.add_argument("--basis", default="sto-3g", help="Molecular basis set (e.g. sto-3g, def2-SVP)")
    parser.add_argument("--shots", type=int, default=10000, help="Number of shots")
    parser.add_argument("--backend", default="H2-1", help="Quantinuum backend (H2-1, H2-Emulator, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Only compile and estimate cost, do not submit")
    parser.add_argument("--force-recompute", action="store_true", help="Force re‑optimization even if parameters exist")
    parser.add_argument("--generate-qasm-only", action="store_true", help="Only write out the QASM circuit file, then exit")
    parser.add_argument("--skip-compile", action="store_true", help="Skip client-side compilation and submit directly (compiles on remote backend)")
    args = parser.parse_args()

    # 1. Login and get Nexus project
    qnx.login()
    project = qnx.projects.get_or_create("dhfr-h2-hardware")
    print(f"✅ Using project: {project.annotations.name} (ID: {project.id})")

    # 2. Load or compute optimized parameters
    ansatz, params = get_optimized_params(args.system, basis=args.basis, force_recompute=args.force_recompute)

    # 3. Build the circuit and substitute the symbolic parameters
    circuit = ansatz.state_circuit.copy()
    circuit.symbol_substitution(params)
    
    qasm_path = DATA_PROCESSED / f"{args.system}_circuit.qasm"
    circuit_to_qasm(circuit, str(qasm_path))
    print(f"✅ Circuit written to {qasm_path}")

    if args.generate_qasm_only:
        print("ℹ️ --generate-qasm-only specified. Exiting.")
        return

    # 4. Upload the circuit to Nexus
    print(f"🔧 Uploading circuit to Nexus...")
    circuit_ref = qnx.circuits.upload(
        circuit=circuit,
        project=project,
        name=f"{args.system}_hardware_submission"
    )
    print(f"✅ Circuit uploaded.")

    # 5. Compile or prepare submission programs
    backend_config = QuantinuumConfig(device_name=args.backend)
    
    if args.skip_compile:
        print("ℹ️ Skipping client-side compilation (--skip-compile). Submitting circuit directly...")
        submit_programs = circuit_ref
    else:
        print(f"🔧 Compiling for {args.backend}...")
        compiled = qnx.compile(
            programs=circuit_ref,
            backend_config=backend_config,
            project=project,
            name=f"{args.system}_hardware_submission"
        )
        print(f"✅ Compilation successful.")
        
        # Download compiled circuit to view resources
        compiled_circuit = compiled[0].download_circuit()
        print(f"   Depth: {compiled_circuit.depth()}, Gates: {compiled_circuit.n_gates}")
        
        # Cost estimate
        cost = qnx.circuits.cost(
            circuit_ref=compiled[0],
            n_shots=args.shots,
            backend_config=backend_config,
            project=project
        )
        print(f"   Estimated cost: {cost} HQC")
        submit_programs = compiled

    if args.dry_run:
        print("ℹ️  Dry-run mode — not submitting. Remove --dry-run to actually submit.")
        return

    # 6. Submit the job
    print(f"🚀 Submitting job to {args.backend}...")
    job = qnx.start_execute_job(
        programs=submit_programs,
        n_shots=args.shots,
        backend_config=backend_config,
        project=project,
        name=f"{args.system}_hardware_submission"
    )
    print(f"✅ Job submitted! Job ID: {job.id}")
    status = qnx.jobs.status(job)
    print(f"   Status: {status.status.value}")
    print(f"   Check progress at: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}")

if __name__ == "__main__":
    main()
