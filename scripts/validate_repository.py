#!/usr/bin/env python3
"""Run credit-safe integrity checks for the public repository."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "environment.yml",
    ".env.example",
    "docs/FIGURE_GUIDE.md",
    "docs/GLOSSARY.md",
    "docs/INSTALLATION.md",
    "docs/RUNNING_THE_PROJECT.md",
    "docs/SOCIETAL_IMPACT.md",
    "results/publication/data/verified_summary.json",
    "scripts/build_publication_assets.py",
    "scripts/test_quantinuum_access.py",
)
FORBIDDEN_TRACKED_NAMES = {".env", "credentials.json", "quantinuum_token.txt"}


def run(*command: str) -> str:
    completed = subprocess.run(
        command, cwd=ROOT, check=True, text=True, capture_output=True
    )
    return completed.stdout.strip()


def main() -> int:
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("Missing required files: " + ", ".join(missing))

    summary = json.loads(
        (ROOT / "results/publication/data/verified_summary.json").read_text()
    )
    for field in ("backend", "finite_shot_energy_hartree", "standard_error_hartree"):
        if field not in summary:
            raise SystemExit(f"Verified summary lacks required field: {field}")

    provenance = json.loads(
        (ROOT / "results/publication/data/verified_quantum_provenance.json").read_text()
    )
    if provenance.get("total_shots") != (
        provenance.get("measurement_circuits", 0)
        * provenance.get("shots_per_circuit", 0)
    ):
        raise SystemExit("Quantum provenance contains inconsistent shot totals")

    tracked = set(run("git", "ls-files").splitlines())
    unsafe = sorted(
        name for name in tracked if Path(name).name in FORBIDDEN_TRACKED_NAMES
    )
    if unsafe:
        raise SystemExit("Credential-like files are tracked: " + ", ".join(unsafe))

    guard = (ROOT / "scripts/test_quantinuum_access.py").read_text()
    for flag in ("--dry-run", "--confirm-submit", "--confirm-hardware", "--max-hqc"):
        if flag not in guard:
            raise SystemExit(f"Hardware guard is missing {flag}")

    print(run(sys.executable, "-m", "pytest", "-q"))
    print("Repository validation passed (no remote jobs were submitted).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
