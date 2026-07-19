#!/usr/bin/env python3
"""Materialize the frozen dry and expanded-water structural sensitivity models."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts/01_prepare_complexes.py"
SYSTEM_IDS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")


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
    parser.add_argument("--restraint", type=float, default=10.0)
    args = parser.parse_args()
    prepare = load_prepare()
    models = (("dry", None), ("expanded6A", 6.0))
    rows = []
    for system in SYSTEM_IDS:
        for label, cutoff in models:
            rows.append(prepare(system, args.iterations, args.restraint, cutoff, label))
    table = pd.DataFrame(rows)
    output = ROOT / "results/tables/water_model_manifest.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    frozen = {
        "status": "FROZEN",
        "frozen_on": "2026-07-15",
        "selection_distance": "minimum water-oxygen to ligand-heavy-atom distance",
        "models": {
            "dry": {"cutoff_angstrom": None, "role": "sensitivity"},
            "primary5A": {"cutoff_angstrom": 5.0, "role": "primary"},
            "expanded6A": {"cutoff_angstrom": 6.0, "role": "sensitivity"},
        },
        "preparation": {
            "iterations": args.iterations,
            "restraint_k_kcal_mol_angstrom2": args.restraint,
        },
    }
    (ROOT / "configs/water_models.yaml").write_text(
        yaml.safe_dump(frozen, sort_keys=False)
    )
    print(json.dumps(frozen, indent=2))
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
