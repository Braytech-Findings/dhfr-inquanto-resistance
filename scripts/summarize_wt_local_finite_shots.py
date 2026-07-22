#!/usr/bin/env python3
"""Summarize valid local WT_TMP finite-shot estimator replicates."""

from __future__ import annotations

import csv
import json
import statistics
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
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    levels = sorted({row["shots_per_circuit"] for row in rows})
    summary = {
        "evidence_label": "OBJECTIVE_COMPUTATIONAL_OUTPUT",
        "interpretation_label": "RESEARCHER_INTERPRETATION_REQUIRED",
        "valid_replicates": len(rows),
        "invalid_diagnostics": len(invalid),
        "completed_shot_levels": levels,
        "required_shot_levels": [100, 250, 500, 1000, 2500, 5000, 10000],
        "all_required_levels_complete": levels
        == [100, 250, 500, 1000, 2500, 5000, 10000],
        "all_valid_replicates_within_3sigma": all(
            row["statistically_consistent_with_ideal_at_3sigma"] for row in rows
        ),
        "mean_energy_hartree": statistics.mean(row["energy_hartree"] for row in rows),
        "replicate_standard_deviation_hartree": statistics.stdev(
            row["energy_hartree"] for row in rows
        ),
        "remote_molecular_gate": "closed",
        "gate_reason": "Higher-shot local convergence levels are incomplete.",
    }
    (OUTPUT / "local_finite_shot_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
