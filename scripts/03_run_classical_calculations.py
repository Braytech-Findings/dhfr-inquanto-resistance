#!/usr/bin/env python3
"""Dispatch classical structure evaluations for every processed system."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
CONFIG = ROOT / "configs/core_systems.yaml"
INPUTS = ROOT / "results/tables/classical_inputs.csv"


def main() -> None:
    python_exe = sys.executable or os.environ.get("CONDA_PREFIX") and os.path.join(os.environ["CONDA_PREFIX"], "bin", "python")
    if not INPUTS.exists():
        subprocess.run([python_exe, str(ROOT / "scripts/02_prepare_classical_inputs.py")], check=True)
    rows = pd.read_csv(INPUTS)
    for _, row in rows.iterrows():
        system = str(row['system'])
        suffix = str(row['structure_suffix'])
        if system.endswith("_minimized"):
            system = system[:-10]
        if suffix == "neutral":
            output_name = f"{system}.json"
        else:
            output_name = f"{system}_{suffix}.json"
        output = ROOT / "results/classical" / output_name
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            continue
        cmd = [python_exe, str(ROOT / "scripts/run_counterpoise.py"), "--system", system, "--tier", "compact_primary", "--method", "HF", "--basis", "sto-3g", "--output", str(output)]
        print("RUN", " ".join(cmd))
        subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
