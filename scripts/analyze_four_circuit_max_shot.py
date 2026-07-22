#!/usr/bin/env python3
"""Normalize and validate the 40,000-total-shot Nexus backend run."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/max_shot_production/nexus/four_circuit_40000_total"
RAW = RUN / "raw_result.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_counts(counts: dict[str, int]) -> dict[str, int]:
    result = {"00": 0, "01": 0, "10": 0, "11": 0}
    for key, value in counts.items():
        bits = key.replace("(", "").replace(")", "").replace(",", "").replace(" ", "")
        if bits not in result:
            raise ValueError(f"Unexpected two-bit outcome: {key}")
        result[bits] += int(value)
    return result


def main() -> None:
    raw = json.loads(RAW.read_text())
    if raw["state"] != "COMPLETED" or not raw["retrieval_complete"]:
        raise SystemExit("Raw Nexus result is not complete and retrieved")
    expected_names = ["bell_z", "bell_x", "bell_y", "product_01"]
    if [item["circuit_name"] for item in raw["results"]] != expected_names:
        raise SystemExit("Nexus result order or circuit identity changed")
    normalized = []
    summaries = []
    for item in raw["results"]:
        counts = normalized_counts(item["counts"])
        shots = sum(counts.values())
        if shots != 10_000 or item["returned_shots"] != 10_000:
            raise SystemExit(f"Shot total mismatch for {item['circuit_name']}")
        normalized.append(
            {
                "position": item["position"],
                "circuit_name": item["circuit_name"],
                "counts": counts,
                "shots": shots,
            }
        )
        if item["circuit_name"].startswith("bell_"):
            parity = (counts["00"] + counts["11"] - counts["01"] - counts["10"]) / shots
            expected_parity = -1.0 if item["circuit_name"] == "bell_y" else 1.0
            forbidden = (
                counts["00"] + counts["11"]
                if expected_parity < 0
                else counts["01"] + counts["10"]
            )
            summaries.append(
                {
                    "circuit_name": item["circuit_name"],
                    "shots": shots,
                    "parity_expectation": parity,
                    "expected_parity": expected_parity,
                    "parity_standard_error": math.sqrt(
                        max(0.0, 1.0 - parity * parity) / shots
                    ),
                    "forbidden_outcomes": forbidden,
                    "forbidden_frequency": forbidden / shots,
                }
            )
        else:
            expected = counts["10"]
            summaries.append(
                {
                    "circuit_name": item["circuit_name"],
                    "shots": shots,
                    "expected_outcome": "10",
                    "expected_outcome_count": expected,
                    "expected_outcome_probability": expected / shots,
                    "unexpected_outcome_count": shots - expected,
                }
            )
    combined = sum(item["shots"] for item in normalized)
    if combined != 40_000:
        raise SystemExit(f"Combined shot total is {combined}, expected 40000")
    normalized_payload = {
        "label": "MAX_SHOT_BACKEND_VALIDATION - NOT_MOLECULAR_EVIDENCE - NOT_HARDWARE_EVIDENCE",
        "job_id": raw["job_id"],
        "backend": raw["resolved_backend"],
        "project": raw["project"],
        "requested_shots_per_circuit": raw["shots_per_circuit"],
        "results": normalized,
        "combined_returned_shots": combined,
    }
    normalized_path = RUN / "normalized_result.json"
    normalized_path.write_text(json.dumps(normalized_payload, indent=2) + "\n")
    summary_path = RUN / "statistical_summary.json"
    summary_path.write_text(json.dumps({"circuits": summaries}, indent=2) + "\n")
    validation = {
        "classification": [
            "MAX_SHOT_BACKEND_VALIDATION",
            "40000_TOTAL_CIRCUIT_SHOTS",
            "NOT_MOLECULAR_EVIDENCE",
            "NOT_HARDWARE_EVIDENCE",
        ],
        "job_id": raw["job_id"],
        "final_state": raw["state"],
        "result_count": len(normalized),
        "per_circuit_returned_shots": [item["shots"] for item in normalized],
        "combined_returned_shots": combined,
        "shot_semantics": "n_shots list value applied independently to each circuit",
        "order_preserved": True,
        "identity_preserved": True,
        "truncation_detected": False,
        "reported_cost": raw.get("reported_cost"),
        "raw_sha256": sha256(RAW),
        "normalized_sha256": sha256(normalized_path),
        "summary_sha256": sha256(summary_path),
        "validation_status": "pass",
    }
    (RUN / "validation_report.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
