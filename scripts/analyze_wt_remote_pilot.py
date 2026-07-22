#!/usr/bin/env python3
"""Compare the WT_TMP remote pilot with local predictions without imputing failures."""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / "artifacts/max_shot_production/WT_TMP"
OUT = ROOT / "artifacts/final_public_release/molecular/WT_TMP/remote_pilot"
GROUPS = ("WT_TMP_G0001", "WT_TMP_G0002", "WT_TMP_G0003", "WT_TMP_G0013")


def main() -> None:
    manifest = json.loads((OUT / "job_manifest.json").read_text())
    exact = defaultdict(float)
    with (WT / "regenerated_measurement_validation.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["group_id"] in GROUPS:
                exact[row["group_id"]] += float(row["energy_contribution_hartree"])
    local = defaultdict(list)
    for seed in (102, 103, 104):
        path = WT / "group_covariance" / f"shots_100_seed_{seed}.csv"
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                if row["group_id"] in GROUPS:
                    local[row["group_id"]].append(
                        float(row["coefficient_weighted_group_mean_hartree"])
                    )
    remote_by_group = {row["group_id"]: row for row in manifest.get("results", [])}
    rows = []
    for group_id in GROUPS:
        remote = remote_by_group.get(group_id)
        rows.append(
            {
                "group_id": group_id,
                "exact_group_contribution_hartree": exact[group_id],
                "local_100_shot_mean_group_contribution_hartree": statistics.mean(
                    local[group_id]
                ),
                "local_100_shot_replicate_sd_hartree": statistics.stdev(
                    local[group_id]
                ),
                "remote_group_contribution_hartree": "",
                "remote_minus_exact_hartree": "",
                "returned_shots": remote["returned_shots"] if remote else "",
                "comparison_status": "missing_remote_result_provider_timeout",
            }
        )
    with (OUT / "local_remote_comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    raw = {
        "job_id": manifest["job_id"],
        "state": manifest["state"],
        "raw_results": None,
        "returned_result_count": 0,
        "missing_reason": manifest["failure"]["classification"],
        "missing_values_are_not_zero": True,
    }
    (OUT / "raw_results.json").write_text(json.dumps(raw, indent=2) + "\n")
    print(json.dumps(raw, indent=2))


if __name__ == "__main__":
    main()
