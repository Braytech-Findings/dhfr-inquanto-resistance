#!/usr/bin/env python3
"""Reproduce all public DHFR figures, tables, molecular renders, and checks.

The runner is intentionally local and public-data-only. It does not authenticate to
Nexus, submit a Quantinuum job, spend HQCs, or claim to recreate the licensed InQuanto
finite-shot calculation. That calculation has a separate, explicit workflow documented
in docs/REPRODUCIBILITY.md.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PUBLIC_OUTPUTS = (
    ROOT / "results/publication/figures/energy_comparison.png",
    ROOT / "results/publication/figures/statistical_uncertainty.png",
    ROOT / "results/publication/figures/hamiltonian_compression.png",
    ROOT / "results/publication/figures/parameter_distribution.png",
    ROOT / "results/publication/figures/workflow_technical.png",
    ROOT / "results/publication/figures/molecular/wt_tmp_complex_overview.png",
    ROOT / "results/publication/data/energy_results.csv",
    ROOT / "results/publication/data/verified_quantum_provenance.json",
)


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]


def run(step: Step, *, dry_run: bool) -> float:
    print(f"\n{'=' * 78}\n{step.name}\n$ {' '.join(step.command)}\n{'=' * 78}")
    if dry_run:
        return 0.0
    started = time.perf_counter()
    subprocess.run(step.command, cwd=ROOT, check=True)
    elapsed = time.perf_counter() - started
    print(f"✓ {step.name} completed in {elapsed:.1f} seconds")
    return elapsed


def build_steps(args: argparse.Namespace) -> list[Step]:
    python = sys.executable
    steps: list[Step] = []

    if not args.skip_tests:
        steps.extend(
            [
                Step("Compile public Python scripts", (python, "-m", "compileall", "-q", "scripts")),
                Step("Run public lint checks", (python, "-m", "ruff", "check", ".")),
                Step("Run public automated tests", (python, "-m", "pytest", "-q")),
            ]
        )

    if not args.skip_figures:
        steps.append(
            Step(
                "Regenerate publication tables, figures, and accessibility manifests",
                (python, "scripts/build_publication_assets.py"),
            )
        )

    if not args.skip_molecular:
        steps.append(
            Step(
                "Regenerate the reproducible WT_TMP molecular render",
                (python, "scripts/render_molecular_3d.py"),
            )
        )

    if args.include_r:
        rscript = shutil.which("Rscript")
        if rscript is None and not args.dry_run:
            raise SystemExit(
                "Rscript was not found. Install R and the packages documented in "
                "docs/REPRODUCIBILITY.md, or rerun without --include-r."
            )
        steps.append(
            Step(
                "Regenerate the optional R publication figures",
                ((rscript or "Rscript"), "analysis/R/make_publication_figures.R"),
            )
        )

    if args.include_manuscript:
        bash = shutil.which("bash")
        if bash is None and not args.dry_run:
            raise SystemExit("bash was not found; the manuscript build uses manuscript/build.sh.")
        steps.append(
            Step(
                "Build the optional manuscript PDF",
                ((bash or "bash"), "manuscript/build.sh"),
            )
        )

    return steps


def check_outputs(*, dry_run: bool) -> list[Path]:
    if dry_run:
        return []
    missing = [path for path in EXPECTED_PUBLIC_OUTPUTS if not path.exists()]
    if missing:
        formatted = "\n".join(f"- {path.relative_to(ROOT)}" for path in missing)
        raise RuntimeError(f"Expected public outputs are missing:\n{formatted}")
    return list(EXPECTED_PUBLIC_OUTPUTS)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Safely reproduce all public DHFR publication assets and checks."
    )
    command.add_argument("--skip-tests", action="store_true")
    command.add_argument("--skip-figures", action="store_true")
    command.add_argument("--skip-molecular", action="store_true")
    command.add_argument(
        "--include-r",
        action="store_true",
        help="Also run analysis/R/make_publication_figures.R.",
    )
    command.add_argument(
        "--include-manuscript",
        action="store_true",
        help="Also build the manuscript; requires the local LaTeX toolchain.",
    )
    command.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the complete command sequence without running it.",
    )
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required.")

    print("DHFR InQuanto Resistance — public reproduction runner")
    print(f"Repository: {ROOT}")
    print("Safety boundary: local public assets only; no Nexus or physical-hardware submission.")

    steps = build_steps(args)
    total = 0.0
    completed: list[str] = []
    try:
        for step in steps:
            total += run(step, dry_run=args.dry_run)
            completed.append(step.name)
        outputs = check_outputs(dry_run=args.dry_run)
    except subprocess.CalledProcessError as error:
        print(f"\n✗ Reproduction stopped during: {step.name}", file=sys.stderr)
        print(f"  Exit code: {error.returncode}", file=sys.stderr)
        return error.returncode or 1
    except RuntimeError as error:
        print(f"\n✗ {error}", file=sys.stderr)
        return 1

    print("\n" + "=" * 78)
    print("PUBLIC REPRODUCTION COMPLETE" if not args.dry_run else "DRY RUN COMPLETE")
    print("=" * 78)
    for name in completed:
        print(f"✓ {name}")
    if outputs:
        print(f"✓ Verified {len(outputs)} expected public output files")
    if not args.dry_run:
        print(f"Total command time: {total:.1f} seconds")
    print("Licensed InQuanto/H2-1LE execution is documented separately and is never run here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
