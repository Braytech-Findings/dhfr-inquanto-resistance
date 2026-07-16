#!/usr/bin/env python3
"""Run a frozen-geometry Boys-Bernardi counterpoise interaction calculation."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
from pyscf import dft, gto, qmmm, scf

ROOT = Path(__file__).resolve().parents[1]
CLUSTERS = ROOT / "data/processed/qm_clusters"
EMBEDDING = ROOT / "data/processed/embedding"


def geometry(stem: str, real_fragment: str | None = None) -> list[tuple[str, tuple[float, float, float]]]:
    lines = (CLUSTERS / f"{stem}.xyz").read_text().splitlines()[2:]
    atom_map = pd.read_csv(CLUSTERS / f"{stem}_atoms.csv")
    atoms = []
    for line, row in zip(lines, atom_map.itertuples(index=False), strict=True):
        fields = line.split()
        symbol = fields[0]
        if real_fragment is not None and row.fragment != real_fragment:
            symbol = f"ghost-{symbol}"
        atoms.append((symbol, tuple(float(value) for value in fields[1:4])))
    return atoms


def run_scf(
    atoms: list[tuple[str, tuple[float, float, float]]],
    charge: int,
    method: str,
    basis: str,
    memory: int,
    embedding: pd.DataFrame | None,
    conv_tol: float,
) -> tuple[float, bool, int, float]:
    molecule = gto.M(atom=atoms, basis=basis, charge=charge, spin=0, unit="Angstrom", verbose=3, max_memory=memory)
    if method == "HF":
        mean_field = scf.RHF(molecule).density_fit()
    else:
        mean_field = dft.RKS(molecule).density_fit()
        mean_field.xc = method.lower()
        mean_field.grids.level = 2
    if embedding is not None:
        mean_field = qmmm.mm_charge(
            mean_field,
            embedding[["x_A", "y_A", "z_A"]].to_numpy(float),
            embedding["charge_e"].to_numpy(float),
            unit="Angstrom",
        )
    mean_field.conv_tol = conv_tol
    mean_field.max_cycle = 100
    start = time.monotonic()
    energy = float(mean_field.kernel())
    elapsed = time.monotonic() - start
    return energy, bool(mean_field.converged), int(mean_field.cycles), elapsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", required=True)
    parser.add_argument("--tier", default="compact_primary")
    parser.add_argument("--method", choices=("HF", "B3LYP", "PBE0"), default="HF")
    parser.add_argument("--basis", default="sto-3g")
    parser.add_argument("--memory", type=int, default=4000)
    parser.add_argument("--conv-tol", type=float, default=1e-7)
    parser.add_argument("--no-embedding", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    stem = f"{args.system}_{args.tier}"
    metadata = json.loads((CLUSTERS / f"{stem}.json").read_text())
    background = "L28R" if args.system.startswith("L28R") else "WT"
    embedding = None if args.no_embedding else pd.read_csv(EMBEDDING / f"{background}_nadph_charmm36.csv")
    embedding_label = "noembed" if args.no_embedding else "embed"
    output = args.output or ROOT / "results/classical" / f"{stem}_{args.method}_{args.basis.replace('*', 's')}_{embedding_label}.json"
    partial = output.with_suffix(".partial.json")
    signature = {
        "system": args.system,
        "tier": args.tier,
        "method": args.method,
        "basis": args.basis,
        "nadph_embedding": not args.no_embedding,
        "conv_tol": args.conv_tol,
    }
    definitions = {
        "complex": (None, int(metadata["charge"])),
        "ligand": ("ligand", int(metadata["ligand_charge"])),
        "environment": ("environment", int(metadata["environment_charge"])),
    }
    components = {}
    if partial.exists():
        cached = json.loads(partial.read_text())
        if cached.get("signature") == signature:
            components = cached.get("components", {})
            print(f"Resuming {len(components)} cached counterpoise component(s) from {partial}")
    for name, (fragment, charge) in definitions.items():
        if name in components:
            continue
        energy, converged, cycles, elapsed = run_scf(
            geometry(stem, fragment), charge, args.method, args.basis, args.memory,
            embedding, args.conv_tol,
        )
        if not converged:
            raise RuntimeError(f"{name} SCF failed to converge")
        components[name] = {"energy_hartree": energy, "charge": charge, "cycles": cycles, "elapsed_seconds": elapsed}
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_text(json.dumps({"signature": signature, "components": components}, indent=2) + "\n")
    interaction = (
        components["complex"]["energy_hartree"]
        - components["ligand"]["energy_hartree"]
        - components["environment"]["energy_hartree"]
    )
    result = {
        "system": args.system,
        "tier": args.tier,
        "method": args.method,
        "basis": args.basis,
        "counterpoise": "Boys-Bernardi full cluster basis with ghost functions",
        "nadph_embedding": not args.no_embedding,
        "components": components,
        "interaction_energy_hartree": interaction,
        "converged": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    partial.unlink(missing_ok=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
