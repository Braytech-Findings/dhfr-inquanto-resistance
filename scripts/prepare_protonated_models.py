#!/usr/bin/env python3
"""Prepare the four frozen N1-protonated structural models."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts/01_prepare_complexes.py"
SYSTEMS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")


def load_prepare():
    spec = importlib.util.spec_from_file_location("prepare_complexes", PREPARE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {PREPARE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.prepare


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=50)
    args = parser.parse_args()
    prepare = load_prepare()
    rows = []
    for system in SYSTEMS:
        background, ligand = system.split("_", 1)
        path = ROOT / "data/processed/protonation_models" / f"{background}_{ligand}_protonatedN1.sdf"
        rows.append(prepare(system, args.iterations, 10.0, 5.0, "protonatedN1", path))
    frame = pd.DataFrame(rows)
    output = ROOT / "results/tables/protonated_structure_manifest.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
