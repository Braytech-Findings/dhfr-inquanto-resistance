#!/usr/bin/env python3
"""Guardrail for a future complete Nexus-hosted Pauli-energy workload.

No submission is implemented here deliberately. The local InQuanto PauliAveraging
checkpoint contains protocol-specific measurement mappings and evaluator state;
uploading a state circuit alone cannot reproduce the 576-term energy. A hosted
implementation must first validate every reconstructed measurement circuit
against the ignored local checkpoint, estimate the aggregate cost, and provide
batch/resume semantics. This command checks prerequisites only and never uploads
or submits work.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="WT_TMP")
    parser.add_argument("--shots-per-circuit", type=int, default=100)
    parser.add_argument("--confirm-full-submit", action="store_true")
    args = parser.parse_args()
    checkpoint = (
        ROOT
        / "results/quantum/protocol_checkpoints"
        / f"{args.system}_H2-1LE_{args.shots_per_circuit}shots_built.pkl"
    )
    plan = (
        ROOT
        / "results/quantum/measurement_plans"
        / f"{args.system}_H2-1LE_{args.shots_per_circuit}shots_plan.json"
    )
    missing = [
        str(path.relative_to(ROOT)) for path in (checkpoint, plan) if not path.exists()
    ]
    if missing:
        raise SystemExit(
            "Required ignored local artifacts are missing: " + ", ".join(missing)
        )
    print(
        "Prerequisites found, but no hosted molecular-energy submission path is enabled."
    )
    print(
        "Reason: the repository has not yet validated an exact, checkpoint-preserving mapping of all PauliAveraging circuits to Nexus batches."
    )
    print("No circuit was uploaded and no HQC was consumed.")


if __name__ == "__main__":
    main()
