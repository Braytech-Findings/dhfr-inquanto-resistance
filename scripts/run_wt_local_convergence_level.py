#!/usr/bin/env python3
"""Run three independent Aer streams for one complete WT_TMP shot level."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time

from pytket.circuit import Circuit
from pytket.extensions.qiskit import AerBackend

from run_wt_local_finite_shots import (
    OUT,
    PROTECTED_IDEAL,
    WT,
    _coefficients,
    _group_sample,
    _load_groups,
)


def run_level(shots: int, master_seed: int) -> list[dict[str, object]]:
    groups = _load_groups()
    coefficients = _coefficients()
    backend = AerBackend()
    started = time.time()
    replica_count = 3
    group_means = [[] for _ in range(replica_count)]
    variances = [0.0] * replica_count
    covariance_rows = [[] for _ in range(replica_count)]
    group_ids = sorted(groups)
    for group_number, group_id in enumerate(group_ids, start=1):
        circuit = Circuit.from_dict(
            json.loads((WT / "regenerated_circuits" / f"{group_id}.json").read_text())
        )
        compiled = backend.get_compiled_circuit(circuit, optimisation_level=0)
        results = backend.run_circuits(
            [compiled] * replica_count,
            n_shots=[shots] * replica_count,
            seed=master_seed * 1000 + group_number,
        )
        for index, result in enumerate(results):
            mean, sample_variance = _group_sample(
                result, groups[group_id], coefficients, shots
            )
            group_means[index].append(mean)
            variances[index] += sample_variance / shots
            covariance_rows[index].append(
                {
                    "group_id": group_id,
                    "observable_count": len(groups[group_id]),
                    "shots": shots,
                    "seed": master_seed + index,
                    "replicate": index + 1,
                    "aer_master_seed": master_seed,
                    "aer_experiment_index": index,
                    "coefficient_weighted_group_mean_hartree": mean,
                    "c_transpose_covariance_c_hartree_squared": sample_variance,
                    "variance_of_group_mean_hartree_squared": sample_variance / shots,
                }
            )
    OUT.mkdir(parents=True, exist_ok=True)
    covariance_dir = WT / "group_covariance"
    covariance_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for index in range(replica_count):
        seed_identifier = master_seed + index
        with (covariance_dir / f"shots_{shots}_seed_{seed_identifier}.csv").open(
            "w", newline=""
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(covariance_rows[index][0]),
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(covariance_rows[index])
        energy = coefficients[""] + sum(group_means[index])
        summary = {
            "evidence_label": "LOCAL_FINITE_SHOT_SIMULATION",
            "interpretation_label": "RESEARCHER_INTERPRETATION_REQUIRED",
            "protocol": "REGENERATED_PYTKET_MEASUREMENT_PROTOCOL",
            "system": "WT_TMP",
            "backend": "AerBackend",
            "shots_per_circuit": shots,
            "circuit_count": len(groups),
            "total_circuit_shots": shots * len(groups),
            "seed": seed_identifier,
            "seed_strategy": "Aer master seed with distinct experiment stream",
            "aer_master_seed": master_seed,
            "aer_experiment_index": index,
            "replicate": index + 1,
            "energy_hartree": energy,
            "uncertainty_hartree": math.sqrt(variances[index]),
            "deviation_from_protected_ideal_hartree": energy - PROTECTED_IDEAL,
            "protected_ideal_energy_hartree": PROTECTED_IDEAL,
            "covariance_method": "sum of independent group c^T sample-Covariance c / shots",
            "finite_sample_correction": "Bessel ddof=1 within each group",
            "group_independence_assumption": True,
            "replicate_streams_independent": True,
            "runtime_seconds_for_level": time.time() - started,
            "status": "complete",
        }
        (OUT / f"shots_{shots}_seed_{seed_identifier}.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        summaries.append(summary)
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shots", type=int, required=True)
    parser.add_argument("--master-seed", type=int, required=True)
    args = parser.parse_args()
    if args.shots < 2:
        parser.error("--shots must be at least 2")
    print(json.dumps(run_level(args.shots, args.master_seed), indent=2))


if __name__ == "__main__":
    main()
