#!/usr/bin/env python3
"""Run the complete regenerated WT_TMP estimator on local Aer sampling."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from pytket.circuit import Bit, Circuit
from pytket.extensions.qiskit import AerBackend


ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts" / "max_shot_production" / "WT_TMP"
OUT = WT / "local_finite_shots"
PROTECTED_IDEAL = -2587.912001526413


def _load_groups() -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    with (WT / "regenerated_measurement_map.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups[row["group_id"]].append(row)
    return groups


def _coefficients() -> dict[str, float]:
    terms = json.loads(
        (ROOT / "data" / "processed" / "WT_TMP_qubit_hamiltonian.json").read_text()
    )["terms"]
    return {term["pauli_string"]: float(term["coefficient"]["real"]) for term in terms}


def _group_sample(
    result,
    mappings: list[dict[str, str]],
    coefficients: dict[str, float],
    shots: int,
) -> tuple[float, float]:
    contribution = _group_contributions(result, mappings, coefficients, shots)
    return float(np.mean(contribution)), float(np.var(contribution, ddof=1))


def _group_contributions(
    result,
    mappings: list[dict[str, str]],
    coefficients: dict[str, float],
    shots: int,
) -> np.ndarray:
    """Return coefficient-weighted per-shot values for covariance propagation."""
    bit_count = (
        max(
            int(bit)
            for mapping in mappings
            for bit in mapping["bits"].split(";")
            if bit
        )
        + 1
    )
    readouts = np.asarray(
        result.get_shots(cbits=[Bit(index) for index in range(bit_count)]),
        dtype=np.int8,
    )
    if readouts.shape != (shots, bit_count):
        raise RuntimeError(
            f"Unexpected readout shape {readouts.shape}; expected {(shots, bit_count)}"
        )
    contribution = np.zeros(shots, dtype=float)
    for mapping in mappings:
        bits = [int(value) for value in mapping["bits"].split(";") if value]
        parity = np.prod(1 - 2 * readouts[:, bits], axis=1)
        if mapping["invert"] == "true":
            parity *= -1
        contribution += coefficients[mapping["pauli_string"]] * parity
    # Var(this vector) is exactly c^T Cov(X_group) c and retains covariance.
    return contribution


def run_replicate(shots: int, seed: int, replicate: int) -> dict[str, object]:
    groups = _load_groups()
    coefficients = _coefficients()
    backend = AerBackend()
    started = time.time()
    covariance_rows = []
    group_means = []
    variance_of_mean = 0.0
    for group_number, group_id in enumerate(sorted(groups), start=1):
        circuit = Circuit.from_dict(
            json.loads((WT / "regenerated_circuits" / f"{group_id}.json").read_text())
        )
        compiled = backend.get_compiled_circuit(circuit, optimisation_level=0)
        result = backend.run_circuit(
            compiled,
            n_shots=shots,
            seed=seed * 1000 + group_number,
        )
        mean, sample_variance = _group_sample(
            result, groups[group_id], coefficients, shots
        )
        group_means.append(mean)
        variance_of_mean += sample_variance / shots
        covariance_rows.append(
            {
                "group_id": group_id,
                "observable_count": len(groups[group_id]),
                "shots": shots,
                "seed": seed,
                "replicate": replicate,
                "coefficient_weighted_group_mean_hartree": mean,
                "c_transpose_covariance_c_hartree_squared": sample_variance,
                "variance_of_group_mean_hartree_squared": sample_variance / shots,
            }
        )
    energy = coefficients[""] + sum(group_means)
    uncertainty = math.sqrt(variance_of_mean)
    OUT.mkdir(parents=True, exist_ok=True)
    covariance_dir = WT / "group_covariance"
    covariance_dir.mkdir(parents=True, exist_ok=True)
    covariance_path = covariance_dir / f"shots_{shots}_seed_{seed}.csv"
    with covariance_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(covariance_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(covariance_rows)
    summary = {
        "evidence_label": "LOCAL_FINITE_SHOT_SIMULATION",
        "interpretation_label": "RESEARCHER_INTERPRETATION_REQUIRED",
        "protocol": "REGENERATED_PYTKET_MEASUREMENT_PROTOCOL",
        "system": "WT_TMP",
        "backend": "AerBackend",
        "shots_per_circuit": shots,
        "circuit_count": len(groups),
        "total_circuit_shots": shots * len(groups),
        "seed": seed,
        "replicate": replicate,
        "energy_hartree": energy,
        "uncertainty_hartree": uncertainty,
        "deviation_from_protected_ideal_hartree": energy - PROTECTED_IDEAL,
        "protected_ideal_energy_hartree": PROTECTED_IDEAL,
        "covariance_method": "sum of independent group c^T sample-Covariance c / shots",
        "finite_sample_correction": "Bessel ddof=1 within each group",
        "group_independence_assumption": True,
        "runtime_seconds": time.time() - started,
        "status": "complete",
    }
    (OUT / f"shots_{shots}_seed_{seed}.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--replicate", type=int, default=1)
    args = parser.parse_args()
    if args.shots < 2:
        parser.error("--shots must be at least 2 for sample covariance")
    print(json.dumps(run_replicate(args.shots, args.seed, args.replicate), indent=2))


if __name__ == "__main__":
    main()
