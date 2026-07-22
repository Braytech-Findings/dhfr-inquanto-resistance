#!/usr/bin/env python3
"""Run nested higher-shot convergence from three independent Aer streams."""

from __future__ import annotations

import csv
import json
import math
import time

import numpy as np
from pytket.circuit import Circuit
from pytket.extensions.qiskit import AerBackend

from run_wt_local_finite_shots import (
    OUT,
    PROTECTED_IDEAL,
    WT,
    _coefficients,
    _group_contributions,
    _load_groups,
)


LEVELS = (500, 1000, 2500, 5000, 10000)
MASTER_SEED = 10001
REPLICATES = 3


def main() -> None:
    groups = _load_groups()
    coefficients = _coefficients()
    backend = AerBackend()
    started = time.time()
    means = {(level, replica): [] for level in LEVELS for replica in range(REPLICATES)}
    variances = {
        (level, replica): 0.0 for level in LEVELS for replica in range(REPLICATES)
    }
    covariance_rows = {
        (level, replica): [] for level in LEVELS for replica in range(REPLICATES)
    }
    for group_number, group_id in enumerate(sorted(groups), start=1):
        circuit = Circuit.from_dict(
            json.loads((WT / "regenerated_circuits" / f"{group_id}.json").read_text())
        )
        compiled = backend.get_compiled_circuit(circuit, optimisation_level=0)
        results = backend.run_circuits(
            [compiled] * REPLICATES,
            n_shots=[max(LEVELS)] * REPLICATES,
            seed=MASTER_SEED * 1000 + group_number,
        )
        for replica, result in enumerate(results):
            contributions = _group_contributions(
                result, groups[group_id], coefficients, max(LEVELS)
            )
            for level in LEVELS:
                prefix = contributions[:level]
                mean = float(np.mean(prefix))
                sample_variance = float(np.var(prefix, ddof=1))
                means[level, replica].append(mean)
                variances[level, replica] += sample_variance / level
                covariance_rows[level, replica].append(
                    {
                        "group_id": group_id,
                        "observable_count": len(groups[group_id]),
                        "shots": level,
                        "seed": MASTER_SEED + replica,
                        "replicate": replica + 1,
                        "aer_master_seed": MASTER_SEED,
                        "aer_experiment_index": replica,
                        "nested_prefix_of_shots": max(LEVELS),
                        "coefficient_weighted_group_mean_hartree": mean,
                        "c_transpose_covariance_c_hartree_squared": sample_variance,
                        "variance_of_group_mean_hartree_squared": sample_variance
                        / level,
                    }
                )
    covariance_dir = WT / "group_covariance"
    covariance_dir.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = []
    for level in LEVELS:
        for replica in range(REPLICATES):
            seed_identifier = MASTER_SEED + replica
            rows = covariance_rows[level, replica]
            with (covariance_dir / f"shots_{level}_seed_{seed_identifier}.csv").open(
                "w", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=list(rows[0]), lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(rows)
            energy = coefficients[""] + sum(means[level, replica])
            summary = {
                "evidence_label": "LOCAL_FINITE_SHOT_SIMULATION",
                "interpretation_label": "RESEARCHER_INTERPRETATION_REQUIRED",
                "protocol": "REGENERATED_PYTKET_MEASUREMENT_PROTOCOL",
                "system": "WT_TMP",
                "backend": "AerBackend",
                "shots_per_circuit": level,
                "circuit_count": len(groups),
                "total_circuit_shots": level * len(groups),
                "seed": seed_identifier,
                "seed_strategy": "Aer master seed with distinct experiment stream",
                "aer_master_seed": MASTER_SEED,
                "aer_experiment_index": replica,
                "replicate": replica + 1,
                "nested_convergence_design": True,
                "nested_prefix_of_shots": max(LEVELS),
                "energy_hartree": energy,
                "uncertainty_hartree": math.sqrt(variances[level, replica]),
                "deviation_from_protected_ideal_hartree": energy - PROTECTED_IDEAL,
                "protected_ideal_energy_hartree": PROTECTED_IDEAL,
                "covariance_method": "sum of independent group c^T sample-Covariance c / shots",
                "finite_sample_correction": "Bessel ddof=1 within each group",
                "group_independence_assumption": True,
                "replicate_streams_independent": True,
                "runtime_seconds_for_nested_study": time.time() - started,
                "status": "complete",
            }
            (OUT / f"shots_{level}_seed_{seed_identifier}.json").write_text(
                json.dumps(summary, indent=2) + "\n"
            )
            summaries.append(summary)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
