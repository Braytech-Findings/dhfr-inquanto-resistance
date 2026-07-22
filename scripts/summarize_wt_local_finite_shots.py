#!/usr/bin/env python3
"""Summarize valid local WT_TMP finite-shot estimator replicates."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/max_shot_production/WT_TMP/local_finite_shots"
OUTPUT = ROOT / "artifacts/final_public_release/molecular/WT_TMP"


def main() -> None:
    valid = []
    invalid = []
    for path in sorted(SOURCE.glob("*.json")):
        row = json.loads(path.read_text())
        row["source_file"] = str(path.relative_to(ROOT))
        (valid if row["status"] == "complete" else invalid).append(row)
    rows = []
    for row in valid:
        uncertainty = row["uncertainty_hartree"]
        z_score = abs(row["deviation_from_protected_ideal_hartree"]) / uncertainty
        rows.append(
            {
                "shots_per_circuit": row["shots_per_circuit"],
                "seed": row["seed"],
                "replicate": row["replicate"],
                "energy_hartree": row["energy_hartree"],
                "uncertainty_hartree": uncertainty,
                "absolute_z_score": z_score,
                "statistically_consistent_with_ideal_at_3sigma": z_score <= 3,
                "total_circuit_shots": row["total_circuit_shots"],
                "source_file": row["source_file"],
            }
        )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "local_finite_shot_replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    levels = sorted({row["shots_per_circuit"] for row in rows})
    required_levels = [100, 250, 500, 1000, 2500, 5000, 10000]
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["shots_per_circuit"]].append(row)
    level_summary = []
    for level in levels:
        level_rows = grouped[level]
        level_summary.append(
            {
                "shots_per_circuit": level,
                "replicate_count": len(level_rows),
                "mean_energy_hartree": statistics.mean(
                    row["energy_hartree"] for row in level_rows
                ),
                "replicate_standard_deviation_hartree": statistics.stdev(
                    row["energy_hartree"] for row in level_rows
                ),
                "mean_propagated_uncertainty_hartree": statistics.mean(
                    row["uncertainty_hartree"] for row in level_rows
                ),
                "maximum_absolute_z_score": max(
                    row["absolute_z_score"] for row in level_rows
                ),
            }
        )
    ten_k = grouped[10000]
    ten_k_mean = statistics.mean(row["energy_hartree"] for row in ten_k)
    protected = -2587.912001526413
    ten_k_mean_standard_error = math.sqrt(
        sum(row["uncertainty_hartree"] ** 2 for row in ten_k)
    ) / len(ten_k)
    ten_k_replicate_sd = statistics.stdev(row["energy_hartree"] for row in ten_k)
    ten_k_mean_uncertainty = statistics.mean(
        row["uncertainty_hartree"] for row in ten_k
    )
    scaled_uncertainties = [
        row["mean_propagated_uncertainty_hartree"] * math.sqrt(row["shots_per_circuit"])
        for row in level_summary
    ]
    criteria = {
        "exact_semantic_validation_passed": True,
        "three_replicates_at_every_required_level": all(
            len(grouped[level]) == 3 for level in required_levels
        ),
        "every_10000_shot_replicate_within_3sigma": all(
            row["absolute_z_score"] <= 3 for row in ten_k
        ),
        "10000_shot_mean_within_3_combined_standard_errors": abs(ten_k_mean - protected)
        <= 3 * ten_k_mean_standard_error,
        "10000_shot_replicate_sd_not_more_than_2_mean_uncertainties": (
            ten_k_replicate_sd <= 2 * ten_k_mean_uncertainty
        ),
        "uncertainty_decreases_at_every_level": all(
            later["mean_propagated_uncertainty_hartree"]
            < earlier["mean_propagated_uncertainty_hartree"]
            for earlier, later in zip(level_summary, level_summary[1:], strict=False)
        ),
        "sqrt_shot_scaled_uncertainty_spread_at_most_10_percent": (
            max(scaled_uncertainties) / min(scaled_uncertainties) <= 1.10
        ),
    }
    local_gate_passed = all(criteria.values())
    summary = {
        "evidence_label": "OBJECTIVE_COMPUTATIONAL_OUTPUT",
        "interpretation_label": "RESEARCHER_INTERPRETATION_REQUIRED",
        "valid_replicates": len(rows),
        "invalid_diagnostics": len(invalid),
        "completed_shot_levels": levels,
        "required_shot_levels": required_levels,
        "all_required_levels_complete": levels == required_levels,
        "all_valid_replicates_within_3sigma": all(
            row["statistically_consistent_with_ideal_at_3sigma"] for row in rows
        ),
        "per_level_summary": level_summary,
        "ten_thousand_shot_mean_energy_hartree": ten_k_mean,
        "ten_thousand_shot_mean_bias_hartree": ten_k_mean - protected,
        "ten_thousand_shot_combined_standard_error_hartree": ten_k_mean_standard_error,
        "ten_thousand_shot_replicate_standard_deviation_hartree": ten_k_replicate_sd,
        "numerical_gate_criteria": criteria,
        "local_numerical_gate_passed": local_gate_passed,
        "remote_molecular_gate": (
            "local_pass_cost_approval_required" if local_gate_passed else "closed"
        ),
        "gate_reason": (
            "Local numerical gate passed; explicit approval of expected Nexus cost is still required."
            if local_gate_passed
            else "One or more documented local numerical criteria failed."
        ),
    }
    (OUTPUT / "local_finite_shot_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
