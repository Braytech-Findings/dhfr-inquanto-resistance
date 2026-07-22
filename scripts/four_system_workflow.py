#!/usr/bin/env python3
"""Build and inspect resumable status for the four planned molecular systems.

Preparation only inspects existing files and writes status JSON. It never runs
chemistry or contacts Nexus. Submission mode performs a complete four-system
preflight before invoking the guarded QASM runner; no partial batch starts when
any required QASM or provenance stage is missing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

try:
    from .audit_core import SYSTEMS
except ImportError:
    from audit_core import SYSTEMS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results" / "workflow_status" / "four_system_status.json"
PROJECT_STATUS_OUTPUT = ROOT / "data" / "project_status.json"


def stage_path(system: str, stage: str) -> Path | None:
    """Return the canonical artifact path for a stage, when one is defined."""
    paths = {
        "molecular_input": ROOT
        / "data/processed/qm_clusters"
        / f"{system}_compact_primary.xyz",
        "classical_reference": ROOT
        / "results/classical"
        / f"{system}_compact_primary_HF_sto-3g.json",
        "hamiltonian": ROOT / "data/processed" / f"{system}_qubit_hamiltonian.json",
        "vqe_parameters": ROOT / "data/params" / f"{system}_params.json",
        "qasm": ROOT / "data/processed" / f"{system}_circuit.qasm",
        "compilation": ROOT / "data/processed" / f"{system}_H2-1LE_compiled.json",
        "local_result": ROOT
        / "results/quantum"
        / f"{system}_H2-1LE_100shots_energy.json",
        "nexus_emulator_result": ROOT
        / "results/quantum/nexus"
        / f"{system}_H2-Emulator.json",
        "uncertainty": ROOT
        / "results/quantum"
        / f"{system}_H2-1LE_100shots_energy.json",
        "validation": ROOT / "results/tables" / f"{system}_casci_active_space.json",
        "figures": ROOT / "results/figures" / f"{system}_orbital_character.png",
    }
    return paths.get(stage)


def build_status() -> dict[str, Any]:
    """Return per-system stages; missing values stay null and never become zero."""
    stages = (
        "molecular_input",
        "classical_reference",
        "hamiltonian",
        "vqe_parameters",
        "qasm",
        "compilation",
        "local_result",
        "nexus_emulator_result",
        "uncertainty",
        "validation",
        "figures",
    )
    systems: dict[str, Any] = {}
    for system in SYSTEMS:
        entries = {}
        for stage in stages:
            path = stage_path(system, stage)
            present = bool(path and path.is_file())
            # A submission receipt is not a result. Require retrieval metadata.
            if present and stage == "nexus_emulator_result":
                try:
                    present = (
                        json.loads(path.read_text()).get("result_retrieved") is True
                    )
                except (OSError, json.JSONDecodeError, AttributeError):
                    present = False
            entries[stage] = {
                "status": "present" if present else "missing",
                "path": str(path.relative_to(ROOT)) if path else None,
                "value": None,
            }
        systems[system] = entries
    return {
        "schema_version": 1,
        "systems": systems,
        "remote_submission_performed": False,
        "missing_values_are_zero": False,
    }


def write_status(path: Path) -> dict[str, Any]:
    payload = build_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def build_project_status() -> dict[str, Any]:
    """Return the required resumable stage state using only allowed values."""
    evidence = build_status()["systems"]
    mapping = {
        "molecular_input": "molecular_input",
        "classical_reference": "classical_reference",
        "active_space": "validation",
        "hamiltonian": "hamiltonian",
        "vqe_parameters": "vqe_parameters",
        "ansatz": "vqe_parameters",
        "measurement_circuits": "qasm",
        "qasm": "qasm",
        "local_compilation": "compilation",
        "nexus_compilation": None,
        "local_ideal_result": "local_result",
        "local_finite_shot_result": "local_result",
        "nexus_emulator_result": "nexus_emulator_result",
        "uncertainty": "uncertainty",
        "validation": "validation",
        "figures": "figures",
    }
    systems = {}
    for system in SYSTEMS:
        stages = {}
        for target, source in mapping.items():
            if target == "active_space":
                value = "needs_researcher_decision"
            elif source and evidence[system][source]["status"] == "present":
                value = "complete"
            else:
                value = "not_started"
            stages[target] = {"status": value, "value": None}
        stages["final_evidence_status"] = {
            "status": "complete" if system == "WT_TMP" else "pending",
            "value": "LEVEL 2" if system == "WT_TMP" else "LEVEL 1",
        }
        systems[system] = stages
    return {
        "schema_version": 1,
        "allowed_statuses": [
            "not_started",
            "pending",
            "running",
            "complete",
            "failed",
            "blocked_by_access",
            "blocked_by_dependency",
            "needs_researcher_decision",
            "not_applicable",
        ],
        "systems": systems,
        "remote_submission_performed": False,
    }


def write_project_status(path: Path = PROJECT_STATUS_OUTPUT) -> dict[str, Any]:
    payload = build_project_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def submit_all(args: argparse.Namespace) -> None:
    """Preflight all systems, then call the guarded runner with no fallback."""
    if not args.confirm_submit:
        raise SystemExit("Four-system remote execution requires --confirm-submit.")
    status = build_status()
    required = (
        "molecular_input",
        "hamiltonian",
        "vqe_parameters",
        "qasm",
        "validation",
    )
    missing = [
        f"{system}:{stage}"
        for system in SYSTEMS
        for stage in required
        if status["systems"][system][stage]["status"] != "present"
    ]
    if missing:
        raise SystemExit(
            "Preflight failed before any submission; missing: " + ", ".join(missing)
        )
    for system in SYSTEMS:
        command = [
            sys.executable,
            "scripts/run_nexus_qasm.py",
            "--system",
            system,
            "--qasm",
            str(stage_path(system, "qasm")),
            "--backend",
            args.backend,
            "--shots",
            str(args.shots),
            "--confirm-submit",
        ]
        if args.project_id:
            command.extend(["--project-id", args.project_id])
        if args.project_name:
            command.extend(["--project-name", args.project_name])
        if args.user_group:
            command.extend(["--user-group", args.user_group])
        command.extend(
            [
                "--metadata-output",
                str(ROOT / "results/quantum/nexus" / f"{system}-{args.backend}.json"),
            ]
        )
        subprocess.run(command, cwd=ROOT, check=True)


def run_local_all(args: argparse.Namespace) -> None:
    """Run each reviewed QASM locally only after an all-system preflight."""
    status = build_status()
    missing = [
        f"{system}:qasm"
        for system in SYSTEMS
        if status["systems"][system]["qasm"]["status"] != "present"
    ]
    if missing:
        raise SystemExit(
            "Local preflight failed before any execution; missing: "
            + ", ".join(missing)
        )
    for system in SYSTEMS:
        subprocess.run(
            [
                sys.executable,
                "scripts/run_local_h2.py",
                "--system",
                system,
                "--shots",
                str(args.shots),
            ],
            cwd=ROOT,
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare", action="store_true", help="Write resumable status only."
    )
    parser.add_argument(
        "--submit-all",
        action="store_true",
        help="Submit all four only after full preflight.",
    )
    parser.add_argument(
        "--local-all",
        action="store_true",
        help="Run all four reviewed QASM files locally after preflight.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--backend", default="H2-Emulator")
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--project-id")
    parser.add_argument("--project-name")
    parser.add_argument("--user-group")
    parser.add_argument("--confirm-submit", action="store_true")
    args = parser.parse_args()
    if args.submit_all:
        submit_all(args)
        return
    if args.local_all:
        run_local_all(args)
        return
    payload = write_status(args.output)
    write_project_status()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
