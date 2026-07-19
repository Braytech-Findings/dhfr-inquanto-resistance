#!/usr/bin/env python3
"""Run local finite-shot Pauli averaging with partial circuit compilation.

This script targets the local H2-1LE emulator only.  It does not submit a
physical-hardware job or contact Nexus.

For fixed VQE parameters, every PauliAveraging circuit has the same UCCSD state
preparation followed by a different measurement basis.  The baseline workflow
compiles each complete circuit.  This implementation follows the documented
pytket partial-compilation pattern: compile the preparation once, preserve its
final placement map, then place, compile, execute, and checkpoint only each
measurement suffix.

The extraction routine is deliberately fail-closed: it verifies that every
protocol circuit begins with the exact instantiated UCCSD preparation and that
preparation plus suffix reconstructs the original logical circuit byte-for-byte
at the command level.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from pyscf import gto, scf

from inquanto.ansatzes import FermionSpaceAnsatzUCCSD
from inquanto.computables import ExpectationValue
from inquanto.extensions.pyscf import ChemistryDriverPySCFMolecularRHF
from inquanto.protocols import PauliAveraging
from pytket.circuit import Circuit, Node, OpType, Qubit
from pytket.backends.backendresult import BackendResult
from pytket.extensions.quantinuum import QuantinuumAPIOffline, QuantinuumBackend
from pytket.extensions.qiskit import AerStateBackend
from pytket.placement import Placement
from pytket.predicates import CompilationUnit


ROOT = Path(__file__).resolve().parents[1]
BACKEND_NAME = "H2-1LE"
BACKEND_LABEL = "local noiseless H2-1LE emulator (not physical hardware)"


def progress(message: str, current: int | None = None, total: int | None = None) -> None:
    prefix = time.strftime("%H:%M:%S")
    suffix = "" if current is None else f" {current}/{total}"
    print(f"[{prefix}] {message}{suffix}", flush=True)


def json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def json_read(path: Path) -> Any:
    return json.loads(path.read_text())


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def circuit_hash(circuit: Circuit) -> str:
    return payload_hash(circuit.to_dict())


def json_number(value: float | None) -> float | None:
    """Keep final JSON strictly standards-compliant (no NaN or infinity)."""
    return value if value is not None and math.isfinite(value) else None


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def environment_payload() -> dict[str, Any]:
    from importlib.metadata import PackageNotFoundError, version

    packages: dict[str, str] = {}
    for package in (
        "inquanto",
        "pytket",
        "pytket-quantinuum",
        "pytket-qiskit",
        "qnexus",
        "pyscf",
        "numpy",
    ):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = "not installed"
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unavailable",
        "packages": packages,
        "git_commit": git_value("rev-parse", "HEAD"),
        "git_status": git_value("status", "--short"),
    }


def circuit_metrics(circuit: Circuit) -> dict[str, Any]:
    commands = circuit.get_commands()
    return {
        "qubits": circuit.n_qubits,
        "classical_bits": circuit.n_bits,
        "command_count": len(commands),
        "depth": circuit.depth(),
        "two_qubit_gate_count": sum(
            len(command.qubits) == 2 and command.op.type != OpType.Measure
            for command in commands
        ),
        "measurement_count": sum(command.op.type == OpType.Measure for command in commands),
        "classical_bit_order": [str(bit) for bit in circuit.bits],
        "sha256": circuit_hash(circuit),
    }


def selected_pauli_terms(path: Path, indices: set[int]) -> dict[int, list[str]]:
    """Stream the 2.3 GB partition CSV without retaining its circuit column."""
    selected = {index: [] for index in indices}
    with path.open("r", encoding="utf-8", newline="") as handle:
        next(handle, None)
        for line in handle:
            fields = line.split(",", 2)
            if len(fields) < 2:
                continue
            try:
                index = int(fields[1])
            except ValueError:
                continue
            if index in selected:
                selected[index].append(fields[0])
    return selected


def wire_to_json(wire: Any) -> dict[str, Any]:
    """Serialise the Qubit/Node values used by a pytket final map."""
    if isinstance(wire, Node):
        kind = "node"
    elif isinstance(wire, Qubit):
        kind = "qubit"
    else:
        raise TypeError(f"Unsupported final-map unit: {wire!r}")
    return {"kind": kind, "register": wire.reg_name, "index": list(wire.index)}


def json_to_wire(payload: dict[str, Any]) -> Qubit | Node:
    index = payload["index"]
    unit_index = index[0] if len(index) == 1 else index
    if payload["kind"] == "node":
        return Node(unit_index)
    if payload["kind"] == "qubit":
        return Qubit(payload["register"], unit_index)
    raise ValueError(f"Unknown final-map unit kind: {payload['kind']!r}")


def placement_to_json(final_map: dict[Any, Any]) -> list[dict[str, Any]]:
    return [
        {"source": wire_to_json(source), "target": wire_to_json(target)}
        for source, target in final_map.items()
        if isinstance(source, Qubit) and isinstance(target, (Qubit, Node))
    ]


def placement_from_json(payload: list[dict[str, Any]]) -> dict[Qubit, Qubit | Node]:
    return {
        json_to_wire(item["source"]): json_to_wire(item["target"])
        for item in payload
    }


def command_strings(circuit: Circuit) -> list[str]:
    return [str(command) for command in circuit.get_commands()]


def matching_commands(left: Circuit, right: Circuit) -> bool:
    return command_strings(left) == command_strings(right)


def blank_circuit_like(source: Circuit) -> Circuit:
    target = Circuit()
    for register in source.q_registers:
        target.add_q_register(register.name, register.size)
    for register in source.c_registers:
        target.add_c_register(register.name, register.size)
    return target


def copy_suffix_command(target: Circuit, command: Any) -> None:
    """Copy the supported PauliAveraging measurement-ending operations."""
    if command.op.type == OpType.Measure:
        target.Measure(command.qubits[0], command.bits[0])
        return
    if command.bits:
        raise RuntimeError(
            "Unexpected classical operation in the PauliAveraging measurement "
            f"suffix: {command}"
        )
    # This documented overload deliberately copies only ordinary quantum gates.
    # If PauliAveraging ever emits a non-gate box here, reconstruction below
    # fails rather than silently changing the experiment.
    target.add_gate(command.op.type, command.op.params, command.qubits)


def append_suffix(preparation: Circuit, suffix: Circuit) -> Circuit:
    combined = preparation.copy()
    known_registers = {register.name for register in combined.c_registers}
    for register in suffix.c_registers:
        if register.name not in known_registers:
            combined.add_c_register(register.name, register.size)
    combined.append(suffix)
    return combined


def extract_suffix(full: Circuit, preparation: Circuit) -> Circuit:
    """Extract and certify the logical measurement basis ending."""
    full_commands = full.get_commands()
    prep_commands = preparation.get_commands()
    if [str(item) for item in full_commands[: len(prep_commands)]] != [
        str(item) for item in prep_commands
    ]:
        raise RuntimeError(
            "Protocol circuit does not begin with the expected instantiated "
            "UCCSD preparation; partial compilation is unsafe."
        )
    suffix = blank_circuit_like(full)
    for command in full_commands[len(prep_commands) :]:
        copy_suffix_command(suffix, command)
    if not matching_commands(append_suffix(preparation, suffix), full):
        raise RuntimeError(
            "Reconstructed preparation-plus-suffix circuit differs from the "
            "original PauliAveraging circuit."
        )
    return suffix


def make_problem(
    system: str, basis: str
) -> tuple[Any, Any, ExpectationValue, dict[Any, float], list[int]]:
    """Build the same active space, Hamiltonian, ansatz, and parameter map."""
    xyz_path = ROOT / "data" / "processed" / "qm_clusters" / f"{system}_compact_primary.xyz"
    params_path = ROOT / "data" / "params" / f"{system}_params.json"
    if not xyz_path.exists() or not params_path.exists():
        raise FileNotFoundError("Missing the required geometry or saved-parameter file.")

    progress("Reconstructing the baseline RHF active space")
    molecule = gto.M(atom=str(xyz_path), basis=basis, charge=0, spin=0)
    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-5
    mean_field.kernel()
    if not mean_field.converged:
        raise RuntimeError("RHF did not converge; refusing to alter the baseline.")
    n_occupied = int(np.sum(mean_field.mo_occ // 2))
    n_orbitals = len(mean_field.mo_energy)
    active_indices = list(range(n_occupied - 3, n_occupied + 3))
    frozen_indices = [item for item in range(n_orbitals) if item not in active_indices]

    progress("Regenerating the baseline Hamiltonian and UCCSD ansatz")
    driver = ChemistryDriverPySCFMolecularRHF(
        geometry=str(xyz_path),
        basis=basis,
        charge=0,
        frozen=frozen_indices,
        df=True,
    )
    fermion_hamiltonian, fermion_space, hf_state = driver.get_system()
    qubit_hamiltonian = fermion_hamiltonian.qubit_encode()
    ansatz = FermionSpaceAnsatzUCCSD(fermion_space, hf_state)

    saved_parameters = json_read(params_path)["params"]
    symbols = {symbol.name: symbol for symbol in ansatz.state_circuit.free_symbols()}
    missing = sorted(set(symbols) - set(saved_parameters))
    if missing:
        raise RuntimeError("Missing saved parameters: " + ", ".join(missing))
    parameter_map = {
        symbols[name]: float(value)
        for name, value in saved_parameters.items()
        if name in symbols
    }
    energy = ExpectationValue(ansatz, qubit_hamiltonian)
    return ansatz, qubit_hamiltonian, energy, parameter_map, active_indices


def build_or_load_protocol(
    path: Path,
    backend: QuantinuumBackend,
    parameters: dict[Any, float],
    energy: ExpectationValue,
    shots_per_circuit: int,
) -> PauliAveraging:
    if path.exists():
        progress(f"Loading built protocol checkpoint: {path.name}")
        return PauliAveraging.load(str(path), backend)

    progress("Building the identical PauliAveraging grouping")
    protocol = PauliAveraging(backend=backend, shots_per_circuit=shots_per_circuit)
    protocol.build_from(parameters, energy)
    protocol.dump(str(path))
    progress(f"Saved circuit-generation checkpoint: {path.name}")
    return protocol


def compile_shared_preparation(
    checkpoint: Path,
    backend: QuantinuumBackend,
    preparation: Circuit,
    optimisation_level: int,
) -> tuple[Circuit, dict[Qubit, Qubit | Node]]:
    if checkpoint.exists():
        progress("Loading compiled shared UCCSD preparation")
        payload = json_read(checkpoint)
        return Circuit.from_dict(payload["circuit"]), placement_from_json(payload["final_map"])

    progress("Compiling the shared UCCSD preparation once")
    compilation_unit = CompilationUnit(preparation.copy())
    compiler = backend.default_compilation_pass(
        optimisation_level=optimisation_level
    )
    compiler.apply(compilation_unit)
    if compilation_unit.final_map is None:
        raise RuntimeError("Compiler did not provide the required final placement map.")
    compiled = compilation_unit.circuit
    if not backend.valid_circuit(compiled):
        raise RuntimeError("Compiled UCCSD preparation is not valid for H2-1LE.")
    json_write(
        checkpoint,
        {
            "circuit": compiled.to_dict(),
            "final_map": placement_to_json(compilation_unit.final_map),
            "optimisation_level": optimisation_level,
        },
    )
    return compiled, compilation_unit.final_map


def compile_suffix(
    suffix: Circuit,
    final_map: dict[Qubit, Qubit | Node],
    backend: QuantinuumBackend,
    optimisation_level: int,
) -> Circuit:
    measured = suffix.copy()
    Placement.place_with_map(measured, final_map)
    backend.default_compilation_pass(
        optimisation_level=optimisation_level
    ).apply(measured)
    return measured


def batches(total: int, batch_size: int) -> Iterable[tuple[int, list[int]]]:
    for batch_number, start in enumerate(range(0, total, batch_size)):
        yield batch_number, list(range(start, min(total, start + batch_size)))


def batch_paths(root: Path, number: int) -> tuple[Path, Path]:
    name = f"batch_{number:03d}.json"
    return root / "compiled_batches" / name, root / "executed_batches" / name


def serialise_circuits(indices: list[int], circuits: list[Circuit]) -> dict[str, Any]:
    return {"indices": indices, "circuits": [item.to_dict() for item in circuits]}


def deserialise_circuits(payload: dict[str, Any]) -> tuple[list[int], list[Circuit]]:
    return payload["indices"], [Circuit.from_dict(item) for item in payload["circuits"]]


def measurement_basis_kind(suffix: Circuit) -> str:
    """Classify a Pauli measurement ending from its basis-change gates."""
    names = {command.op.type.name for command in suffix.get_commands()}
    if {"V", "Vdg"} & names:
        return "Y-containing or mixed-basis"
    if "H" in names:
        return "X-containing"
    return "mostly Z-type"


def representative_indices(full_circuits: list[Circuit], preparation: Circuit) -> list[int]:
    """Choose one Z, one X, and one Y/mixed suffix rather than first-three."""
    wanted = ["mostly Z-type", "X-containing", "Y-containing or mixed-basis"]
    selected: dict[str, int] = {}
    for index, circuit in enumerate(full_circuits):
        kind = measurement_basis_kind(extract_suffix(circuit, preparation))
        if kind not in selected:
            selected[kind] = index
        if len(selected) == len(wanted):
            break
    absent = [kind for kind in wanted if kind not in selected]
    if absent:
        raise RuntimeError(
            "Could not find representative Pauli groups for: " + ", ".join(absent)
        )
    return [selected[kind] for kind in wanted]


def without_measurements(source: Circuit) -> Circuit:
    """Construct the pre-measurement quantum circuit using public pytket APIs."""
    target = Circuit()
    for register in source.q_registers:
        target.add_q_register(register.name, register.size)
    for command in source.get_commands():
        if command.op.type == OpType.Measure:
            continue
        if command.bits:
            raise RuntimeError(
                "Exact state validation encountered an unsupported classical operation: "
                f"{command}"
            )
        target.add_gate(command.op.type, command.op.params, command.qubits)
    return target


def exact_state_comparison(left: Circuit, right: Circuit) -> dict[str, float]:
    """Compare compiled pre-measurement statevectors after global-phase alignment."""
    exact_backend = AerStateBackend()
    left_state = np.asarray(exact_backend.run_circuit(without_measurements(left)).get_state())
    right_state = np.asarray(exact_backend.run_circuit(without_measurements(right)).get_state())
    anchor = int(np.argmax(np.abs(left_state)))
    if abs(right_state[anchor]) > 1e-15:
        right_state = right_state * np.exp(
            1j * (np.angle(left_state[anchor]) - np.angle(right_state[anchor]))
        )
    amplitude_difference = float(np.max(np.abs(left_state - right_state)))
    probability_difference = float(
        np.max(np.abs(np.abs(left_state) ** 2 - np.abs(right_state) ** 2))
    )
    return {
        "maximum_statevector_amplitude_difference": amplitude_difference,
        "maximum_probability_difference": probability_difference,
    }


def run_test(
    full_circuits: list[Circuit],
    preparation: Circuit,
    shared_preparation: Circuit,
    final_map: dict[Qubit, Qubit | Node],
    backend: QuantinuumBackend,
    shots: int,
    optimisation_level: int,
    indices: list[int],
    pauli_terms: dict[int, list[str]],
    output: Path,
) -> None:
    """Run exact and finite-shot validation for representative measurement groups."""
    report = []
    for position, index in enumerate(indices, start=1):
        progress("[VALIDATE] Representative circuit", position, len(indices))
        original = full_circuits[index]
        baseline = backend.get_compiled_circuit(
            original, optimisation_level=optimisation_level
        )
        suffix = extract_suffix(original, preparation)
        logical_reconstruction = append_suffix(preparation, suffix)
        if not matching_commands(logical_reconstruction, original):
            raise RuntimeError(f"Logical reconstruction failed for circuit {index}.")
        optimized = append_suffix(
            shared_preparation,
            compile_suffix(suffix, final_map, backend, optimisation_level),
        )
        if not backend.valid_circuit(optimized):
            raise RuntimeError(f"Optimized circuit {index} is invalid for H2-1LE.")
        exact = exact_state_comparison(baseline, optimized)
        exact_pass = (
            exact["maximum_statevector_amplitude_difference"] <= 1e-9
            and exact["maximum_probability_difference"] <= 1e-10
        )
        if not exact_pass:
            raise RuntimeError(
                f"Exact state validation failed for circuit {index}: {exact}"
            )
        baseline_result, optimized_result = backend.run_circuits(
            [baseline, optimized], n_shots=[shots, shots]
        )
        baseline_counts = {
            str(key): int(value) for key, value in baseline_result.get_counts().items()
        }
        optimized_counts = {
            str(key): int(value) for key, value in optimized_result.get_counts().items()
        }
        keys = set(baseline_counts) | set(optimized_counts)
        variation_distance = 0.5 * sum(
            abs(baseline_counts.get(key, 0) / shots - optimized_counts.get(key, 0) / shots)
            for key in keys
        )
        report.append(
            {
                "circuit_index": index,
                "measurement_basis": measurement_basis_kind(suffix),
                "pauli_terms_measured": pauli_terms.get(index, []),
                "logical_command_equivalence": True,
                "original": circuit_metrics(original),
                "optimized": circuit_metrics(optimized),
                "prefix_command_count": len(preparation.get_commands()),
                "suffix_command_count": len(suffix.get_commands()),
                "final_qubit_placement_map": placement_to_json(final_map),
                "backend_valid_circuit": True,
                "exact_state_validation": {**exact, "passed": True},
                "baseline_counts": baseline_counts,
                "optimized_counts": optimized_counts,
                "total_variation_distance": variation_distance,
                "passed": True,
                "interpretation": (
                    "Counts are independent finite-shot samples. Scientific "
                    "equivalence is established by exact logical-command "
                    "reconstruction before compilation; the count comparison "
                    "is a diagnostic, not an equality assertion."
                ),
            }
        )
        backend.empty_cache()
        del baseline, optimized, baseline_result, optimized_result
        gc.collect()
    json_write(
        output,
        {
            "backend": BACKEND_LABEL,
            "shots_per_circuit": shots,
            "representative_indices": indices,
            "circuits": report,
            "passed": all(item["passed"] for item in report),
        },
    )


def final_energy(
    protocol: PauliAveraging,
    energy: ExpectationValue,
    ansatz: FermionSpaceAnsatzUCCSD,
    qubit_hamiltonian: Any,
    result_paths: list[Path],
) -> tuple[float, float]:
    """Evaluate with InQuanto's unchanged PauliAveraging evaluator."""
    results: list[BackendResult] = []
    expected_index = 0
    for path in result_paths:
        payload = json_read(path)
        indices = payload["indices"]
        expected = list(range(expected_index, expected_index + len(indices)))
        if indices != expected or len(payload["results"]) != len(indices):
            raise RuntimeError(f"Result ordering/checkpoint corruption in {path}")
        results.extend(BackendResult.from_dict(item) for item in payload["results"])
        expected_index += len(indices)
    protocol.retrieve(results)
    measured = complex(energy.evaluate(protocol.get_evaluator()))
    uncertainty = protocol.evaluate_expectation_uvalue(ansatz, qubit_hamiltonian)
    nominal = float(getattr(uncertainty, "nominal_value", getattr(uncertainty, "n", measured.real)))
    standard_error = float(getattr(uncertainty, "std_dev", getattr(uncertainty, "s", math.nan)))
    return nominal, standard_error


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_final_artifacts(
    root: Path,
    result_paths: list[Path],
    work: list[tuple[int, list[int]]],
    final: dict[str, Any],
) -> None:
    measurements: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []
    for (batch_number, _), result_path in zip(work, result_paths, strict=True):
        result = json_read(result_path)
        compiled_path, _ = batch_paths(root, batch_number)
        resources.append(
            {
                "batch": batch_number,
                "circuit_count": len(result["indices"]),
                "shots_per_circuit": result["shots_per_circuit"],
                "execution_seconds": result["execution_seconds"],
                "compiled_checkpoint": str(compiled_path),
                "executed_checkpoint": str(result_path),
            }
        )
        for index, result_hash in zip(result["indices"], result["result_sha256"], strict=True):
            measurements.append(
                {
                    "circuit_index": index,
                    "batch": batch_number,
                    "shots": result["shots_per_circuit"],
                    "backend_result_sha256": result_hash,
                }
            )
    write_csv(
        root / "final_measurements.csv",
        ["circuit_index", "batch", "shots", "backend_result_sha256"],
        measurements,
    )
    write_csv(
        root / "final_resources.csv",
        [
            "batch",
            "circuit_count",
            "shots_per_circuit",
            "execution_seconds",
            "compiled_checkpoint",
            "executed_checkpoint",
        ],
        resources,
    )
    report = "\n".join(
        [
            "# Optimized local finite-shot VQE result",
            "",
            f"- Backend: {BACKEND_LABEL}",
            f"- Energy: {final['energy_hartree']} Hartree",
            f"- Standard error: {final['standard_error_hartree']} Hartree",
            f"- Exact saved-parameter reference: {final['exact_saved_parameter_energy_hartree']} Hartree",
            f"- Absolute error: {final['absolute_error_hartree']} Hartree",
            "- This is a local-emulator measurement result; it is not a hardware result.",
            "- The active space remains the reproducibility definition based on contiguous HOMO/LUMO-style orbitals. Future production biological claims require system-specific orbital-localization or AVAS validation.",
            "",
        ]
    )
    (root / "final_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    workflow_started = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="WT_TMP")
    parser.add_argument("--basis", default="sto-3g")
    parser.add_argument("--shots-per-circuit", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--validate-circuits", type=int, default=3)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--optimisation-level", type=int, default=0)
    parser.add_argument("--rebuild-protocol", action="store_true")
    args = parser.parse_args()
    if args.shots_per_circuit <= 0 or args.batch_size <= 0:
        raise ValueError("shots-per-circuit and batch-size must be positive.")
    if args.validate_circuits != 3:
        raise ValueError(
            "This scientifically defined validation requires exactly three "
            "representative groups: Z-type, X-containing, and Y/mixed."
        )

    backend = QuantinuumBackend(
        device_name=BACKEND_NAME,
        api_handler=QuantinuumAPIOffline(),
    )
    ansatz, qubit_hamiltonian, energy, parameters, active_indices = make_problem(
        args.system, args.basis
    )
    preparation = ansatz.state_circuit.copy()
    preparation.symbol_substitution(parameters)
    if preparation.free_symbols:
        raise RuntimeError("UCCSD state preparation contains unresolved symbols.")

    root = (
        ROOT
        / "results"
        / "quantum"
        / "optimized_pauli_checkpoints"
        / f"{args.system}_{BACKEND_NAME}_{args.shots_per_circuit}shots"
    )
    root.mkdir(parents=True, exist_ok=True)
    source_protocol = (
        ROOT
        / "results"
        / "quantum"
        / "protocol_checkpoints"
        / f"{args.system}_{BACKEND_NAME}_{args.shots_per_circuit}shots_built.pkl"
    )
    # The baseline checkpoint is read-only input to this implementation.  If
    # it is absent, or a fresh grouping was requested, write only inside this
    # optimized workflow's own checkpoint directory.
    protocol_path = (
        source_protocol
        if source_protocol.exists() and not args.rebuild_protocol
        else root / "generated_protocol.pkl"
    )
    protocol = build_or_load_protocol(
        protocol_path,
        backend,
        parameters,
        energy,
        args.shots_per_circuit,
    )
    full_circuits = protocol.get_circuits()
    if not full_circuits:
        raise RuntimeError("No PauliAveraging circuits were built.")

    params_path = ROOT / "data" / "params" / f"{args.system}_params.json"
    xyz_path = ROOT / "data" / "processed" / "qm_clusters" / f"{args.system}_compact_primary.xyz"
    hamiltonian_path = ROOT / "data" / "processed" / f"{args.system}_qubit_hamiltonian.json"
    exact_path = ROOT / "results" / "quantum" / f"{args.system}_saved_params_exact.json"
    partitioning_path = (
        ROOT / "results" / "quantum" / "measurement_plans" / f"{args.system}_pauli_partitioning.csv"
    )
    input_paths = [
        xyz_path,
        params_path,
        hamiltonian_path,
        exact_path,
        partitioning_path,
        Path(__file__).resolve(),
    ]
    missing_inputs = [str(path) for path in input_paths if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError("Missing integrity input(s): " + ", ".join(missing_inputs))
    input_hashes = {str(path.relative_to(ROOT)): file_hash(path) for path in input_paths}
    json_write(root / "input_hashes.json", input_hashes)
    json_write(root / "environment.json", environment_payload())
    manifest_path = root / "manifest.json"
    manifest = {
        "system": args.system,
        "basis": args.basis,
        "backend": BACKEND_LABEL,
        "active_orbitals": active_indices,
        "n_qubits": ansatz.state_circuit.n_qubits,
        "n_uccsd_parameters": len(parameters),
        "n_hamiltonian_terms": len(qubit_hamiltonian),
        "n_measurement_circuits": len(full_circuits),
        "shots_per_circuit": args.shots_per_circuit,
        "total_shots": len(full_circuits) * args.shots_per_circuit,
        "input_sha256": input_hashes,
        "source_protocol_checkpoint": str(protocol_path),
        "source_protocol_identity": {
            "bytes": protocol_path.stat().st_size,
            "modified_ns": protocol_path.stat().st_mtime_ns,
        },
    }
    if manifest_path.exists() and json_read(manifest_path) != manifest:
        raise RuntimeError(
            "Checkpoint manifest does not match the current inputs. Use a new "
            "shot count or archive this optimized checkpoint directory before "
            "starting a different experiment."
        )
    json_write(manifest_path, manifest)
    json_write(
        root / "progress.json",
        {
            "stage": "built",
            "completed_compilation_batches": [],
            "completed_execution_batches": [],
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    progress("Saved circuit-generation checkpoint")
    print(
        f"Logical grouped circuits: {len(full_circuits)}; total local emulator shots: "
        f"{len(full_circuits) * args.shots_per_circuit}",
        flush=True,
    )

    shared_preparation, final_map = compile_shared_preparation(
        root / "shared_prefix_compiled.json",
        backend,
        preparation,
        args.optimisation_level,
    )
    json_write(root / "shared_prefix_logical.json", preparation.to_dict())
    json_write(root / "shared_prefix_mapping.json", placement_to_json(final_map))
    validation_path = root / "validation" / "equivalence_test.json"
    if not validation_path.exists():
        validation_indices = representative_indices(full_circuits, preparation)
        partition_terms = selected_pauli_terms(
            partitioning_path, set(validation_indices)
        )
        run_test(
            full_circuits,
            preparation,
            shared_preparation,
            final_map,
            backend,
            args.shots_per_circuit,
            args.optimisation_level,
            validation_indices,
            partition_terms,
            validation_path,
        )
    else:
        progress("Reusing equivalence-test checkpoint")

    if not args.execute:
        print(
            "Validation complete; full execution was not requested. Review "
            f"{validation_path} and rerun with --execute to measure all circuits.",
            flush=True,
        )
        return

    validation = json_read(validation_path)
    if not validation.get("passed"):
        raise RuntimeError("Validation checkpoint exists but did not pass.")

    result_paths = []
    work = list(batches(len(full_circuits), args.batch_size))
    for position, (batch_number, indices) in enumerate(work, start=1):
        compiled_path, result_path = batch_paths(root, batch_number)
        result_paths.append(result_path)
        if result_path.exists():
            progress("Reusing execution checkpoint", position, len(work))
            continue
        if compiled_path.exists():
            saved_indices, compiled_suffixes = deserialise_circuits(json_read(compiled_path))
            if saved_indices != indices:
                raise RuntimeError(f"Unexpected circuit indices in {compiled_path}")
            progress("Reusing compilation checkpoint", position, len(work))
        else:
            progress("Compiling measurement-suffix batch", position, len(work))
            compiled_suffixes = [
                compile_suffix(
                    extract_suffix(full_circuits[index], preparation),
                    final_map,
                    backend,
                    args.optimisation_level,
                )
                for index in indices
            ]
            compiled_payload = serialise_circuits(indices, compiled_suffixes)
            compiled_payload.update(
                {
                    "logical_circuit_sha256": [
                        circuit_hash(full_circuits[index]) for index in indices
                    ],
                    "compiled_circuit_sha256": [
                        circuit_hash(circuit) for circuit in compiled_suffixes
                    ],
                    "compiled_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
            json_write(compiled_path, compiled_payload)

        jobs = [append_suffix(shared_preparation, suffix) for suffix in compiled_suffixes]
        if not all(backend.valid_circuit(circuit) for circuit in jobs):
            raise RuntimeError(f"Invalid optimized circuit in batch {batch_number}.")
        progress("Executing local-emulator batch", position, len(work))
        execution_started = time.time()
        results = backend.run_circuits(jobs, n_shots=args.shots_per_circuit)
        serialised_results = [item.to_dict() for item in results]
        json_write(
            result_path,
            {
                "indices": indices,
                "shots_per_circuit": args.shots_per_circuit,
                "results": serialised_results,
                "result_sha256": [payload_hash(item) for item in serialised_results],
                "execution_seconds": time.time() - execution_started,
                "completed_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
        del jobs, compiled_suffixes, results
        backend.empty_cache()
        gc.collect()
        json_write(
            root / "progress.json",
            {
                "stage": "executing",
                "completed_compilation_batches": [
                    number for number, _ in work if batch_paths(root, number)[0].exists()
                ],
                "completed_execution_batches": [
                    number for number, _ in work if batch_paths(root, number)[1].exists()
                ],
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            },
        )

    progress("Evaluating the final energy through InQuanto")
    evaluation_started = time.time()
    nominal, standard_error = final_energy(
        protocol,
        energy,
        ansatz,
        qubit_hamiltonian,
        result_paths,
    )
    exact = float(json_read(exact_path)["vqe_energy_hartree"]) if exact_path.exists() else None
    output = root / "final_energy.json"
    absolute_error = abs(nominal - exact) if exact is not None else None
    final = {
            "system": args.system,
            "basis": args.basis,
            "backend": BACKEND_LABEL,
            "method": "UCCSD PauliAveraging with a shared compiled preparation",
            "n_measurement_circuits": len(full_circuits),
            "shots_per_circuit": args.shots_per_circuit,
            "total_shots": len(full_circuits) * args.shots_per_circuit,
            "energy_hartree": json_number(nominal),
            "standard_error_hartree": json_number(standard_error),
            "confidence_interval_95_hartree": (
                [json_number(nominal - 1.96 * standard_error), json_number(nominal + 1.96 * standard_error)]
                if math.isfinite(standard_error)
                else None
            ),
            "exact_saved_parameter_energy_hartree": exact,
            "difference_from_exact_hartree": json_number(nominal - exact) if exact is not None else None,
            "absolute_error_hartree": json_number(absolute_error),
            "absolute_error_millihartree": json_number(absolute_error * 1000) if absolute_error is not None else None,
            "absolute_error_kcal_per_mol": json_number(absolute_error * 627.509474) if absolute_error is not None else None,
            "compile_and_execution_checkpoint_directory": str(root),
            "evaluation_seconds": time.time() - evaluation_started,
            "total_wall_seconds": time.time() - workflow_started,
            "equivalence_test": str(validation_path),
            "active_space_methodology_warning": (
                "Contiguous HOMO/LUMO-style active indices are retained for "
                "reproducibility only; future production biological claims should "
                "verify orbital localization or AVAS-derived mapping."
            ),
        }
    json_write(output, final)
    write_final_artifacts(root, result_paths, work, final)
    json_write(
        root / "progress.json",
        {
            "stage": "complete",
            "completed_compilation_batches": [number for number, _ in work],
            "completed_execution_batches": [number for number, _ in work],
            "final_energy": str(output),
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(f"Final local-emulator energy: {nominal:.12f} Hartree", flush=True)
    print(f"Saved final checkpoint: {output}", flush=True)


if __name__ == "__main__":
    main()
