#!/usr/bin/env python3
"""Build a public-safe backend catalog from read-only Nexus discovery output."""

from __future__ import annotations

import ast
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "quantinuum_access" / "available_targets.csv"
REPORT = ROOT / "results" / "quantinuum_access" / "access_report.json"
OUT = ROOT / "artifacts" / "final_public_release"


ROLE = {
    "Aer": ("simulator", "shots", "standardized_and_local_control"),
    "AerState": ("simulator", "statevector", "exact_reference"),
    "AerUnitary": ("simulator", "unitary", "tiny_measurement_free_only"),
    "Braket": ("simulator", "statevector", "standardized_first"),
    "Qulacs": ("simulator", "statevector", "exact_cross_check"),
    "H1-1LE": ("ideal_emulator", "shots", "molecular_if_identical_model_fits"),
    "H2-1LE": ("ideal_emulator", "shots", "molecular_reference"),
    "H1-Emulator": ("noisy_emulator", "shots", "molecular_if_identical_model_fits"),
    "H2-Emulator": ("noisy_emulator", "shots", "primary_molecular_backend"),
    "Helios-1E-lite": ("emulator", "specialized", "standardized_first"),
    "Selene": ("simulator", "guppy_hugr", "standardized_first"),
    "SelenePlus": ("simulator", "guppy_hugr", "standardized_first"),
}


def _qubit_count(raw: str) -> int | None:
    try:
        info = ast.literal_eval(raw)
        return len(info.get("architecture", {}).get("nodes", [])) or None
    except (SyntaxError, ValueError, TypeError):
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = json.loads(REPORT.read_text())
    rows = []
    with SOURCE.open(newline="") as handle:
        for source in csv.DictReader(handle):
            catalog_name = source["device_name"] or source["backend_name"]
            kind, model, compatibility = ROLE.get(
                catalog_name,
                ROLE.get(
                    source["backend_name"], ("unknown", "unknown", "review_required")
                ),
            )
            rows.append(
                {
                    "exact_name": catalog_name,
                    "provider": source["backend_name"],
                    "type": kind,
                    "qubit_count": _qubit_count(source["backend_info"]),
                    "status": "visible",
                    "programming_model": model,
                    "nexus_hosted": source["nexus_hosted"].lower() == "true",
                    "project": "dhfr-h2-hardware",
                    "authentication_source": "existing qnexus session",
                    "entitlement_verified": False,
                    "standardized_compatibility": compatibility,
                    "molecular_compatibility": compatibility,
                    "notes": "Visibility is not entitlement; no job was submitted by discovery.",
                }
            )
    catalog = {
        "schema_version": 1,
        "generated_utc": report["generated_utc"],
        "packaged_utc": datetime.now(timezone.utc).isoformat(),
        "authenticated": report["authenticated"],
        "discovery_only": True,
        "submission_count": 0,
        "project": "dhfr-h2-hardware",
        "project_listing_error": next(
            (e for e in report.get("errors", []) if e.startswith("projects:")), None
        ),
        "backends": rows,
        "evidence_labels": [
            "OBJECTIVE_COMPUTATIONAL_OUTPUT",
            "RESEARCHER_INTERPRETATION_REQUIRED",
        ],
    }
    (OUT / "backend_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    columns = list(rows[0])
    with (OUT / "backend_capability_matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} visible backends; submitted 0 jobs.")


if __name__ == "__main__":
    main()
