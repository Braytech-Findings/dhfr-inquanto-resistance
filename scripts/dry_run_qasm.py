#!/usr/bin/env python3
"""
Dry-run script to load a QASM circuit directly from disk,
upload it to Nexus, compile it, and exit cleanly on timeout.
"""

import pathlib
import sys
import time
import argparse
import qnexus as qnx
from qnexus import QuantinuumConfig
from pytket.qasm import circuit_from_qasm

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Write a simple Bell-state QASM circuit to disk if it doesn't exist
QASM_PATH = DATA_PROCESSED / "dry_run_circuit.qasm"
QASM_CONTENT = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
"""

def main():
    parser = argparse.ArgumentParser(description="Dry-run QASM compile via qnexus")
    parser.add_argument("--backend", default="H2-Emulator", help="Quantinuum backend")
    args = parser.parse_args()

    # Create the QASM file
    with open(QASM_PATH, "w") as f:
        f.write(QASM_CONTENT)
    print(f"✅ Generated mock QASM circuit at {QASM_PATH}")

    # 1. Login and get Project
    qnx.login()
    project = qnx.projects.get_or_create("dhfr-h2-hardware")
    print(f"✅ Using project: {project.annotations.name} (ID: {project.id})")

    # 2. Load the QASM file directly from disk
    print(f"🔧 Loading QASM circuit from {QASM_PATH}...")
    try:
        circuit = circuit_from_qasm(str(QASM_PATH))
        print("✅ Circuit loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load QASM from disk: {e}")
        sys.exit(1)

    # 3. Upload the circuit to Nexus
    print("🔧 Uploading circuit to Nexus...")
    try:
        circuit_ref = qnx.circuits.upload(
            circuit=circuit,
            project=project,
            name="dry_run_qasm_upload"
        )
        print("✅ Circuit uploaded.")
    except Exception as e:
        print(f"❌ Failed to upload circuit to Nexus: {e}")
        sys.exit(1)

    # 4. Compile with Nexus and enforce a 60-second timeout
    print(f"🔧 Compiling for {args.backend} (timeout: 60s)...")
    backend_config = QuantinuumConfig(device_name=args.backend)
    
    start_time = time.time()
    try:
        compiled = qnx.compile(
            programs=circuit_ref,
            backend_config=backend_config,
            project=project,
            name="dry_run_qasm_compile",
            timeout=60.0
        )
        elapsed = time.time() - start_time
        print(f"✅ Compilation successful in {elapsed:.2f} seconds.")
        
        # Download and print compiled circuit details
        compiled_circuit = compiled[0].download_circuit()
        print(f"   Depth: {compiled_circuit.depth()}, Gates: {compiled_circuit.n_gates}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Compilation failed or timed out after {elapsed:.2f} seconds.")
        print(f"   Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
