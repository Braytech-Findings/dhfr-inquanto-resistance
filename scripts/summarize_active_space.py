#!/usr/bin/env python3
"""Summarize orbital-character and CASCI checks for the four-system panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")


def load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tables",
        type=Path,
        default=ROOT / "results/tables",
        help="Directory containing per-system active-space JSON files.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=ROOT / "results/tables/active_space_validation.csv",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=ROOT / "results/reports/active_space_validation.md",
    )
    args = parser.parse_args()

    rows = []
    for system in SYSTEMS:
        character_path = args.tables / f"{system}_orbital_character.json"
        character = load(character_path)
        casci = load(args.tables / f"{system}_casci_active_space.json")
        character_hash = hashlib.sha256(character_path.read_bytes()).hexdigest()
        if casci.get("selection_sha256") != character_hash:
            raise ValueError(f"Selection/CASCI mismatch for {system}; rerun validation")
        orbitals = character["candidate_orbitals"]
        occupied = [row for row in orbitals if row["occupation"] > 0]
        virtual = [row for row in orbitals if row["occupation"] == 0]
        occupations = casci["natural_occupations"]
        rows.append(
            {
                "system": system,
                "homo": character["homo"],
                "lumo": character["lumo"],
                "canonical_orbitals": ",".join(str(row["orbital"]) for row in orbitals),
                "min_selected_ligand_population": min(
                    row["ligand_population"] for row in orbitals
                ),
                "mean_selected_ligand_population": sum(
                    row["ligand_population"] for row in orbitals
                )
                / len(orbitals),
                "occupied_orbitals": ",".join(str(row["orbital"]) for row in occupied),
                "virtual_orbitals": ",".join(str(row["orbital"]) for row in virtual),
                "casci_energy_hartree": casci["energy_hartree"],
                "casci_method": casci["method"],
                "occupation_sum": casci["occupation_sum"],
                "spin_square": casci["spin_square"],
                "multiplicity": casci["multiplicity"],
                "natural_occupations": ",".join(
                    f"{value:.6f}" for value in occupations
                ),
                "casci_status": casci["status"],
            }
        )
    table = pd.DataFrame(rows)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output_csv, index=False)

    passed = bool(
        table.casci_status.eq("pass").all()
        and table.min_selected_ligand_population.ge(0.65).all()
        and table.spin_square.le(1.0e-6).all()
        and table.multiplicity.eq(1.0).all()
    )
    lines = [
        "# Active-space validation",
        "",
        "## Result",
        "",
        (
            "The proposed CAS(6,6) space passes the frozen-geometry screening "
            "criterion across the four-system panel."
            if passed
            else "The proposed CAS(6,6) space did not meet all frozen-geometry screening criteria."
        ),
        "",
        "## Frozen screening protocol",
        "",
        "- Compact primary QM cluster with the N1-protonated ligand and fixed NADPH point-charge embedding.",
        "- Restricted HF/STO-3G orbitals were ranked by ligand Mulliken population in fixed 16-orbital occupied and 12-orbital virtual frontier windows.",
        "- The three most ligand-localized occupied and virtual orbitals form the 6-electron, 6-orbital candidate space.",
        "- CASCI in that explicit orbital set verifies the electron count and reports active-space natural occupations.",
        "- Screening CASCI calculations use density fitting and are labeled accordingly.",
        "",
        "## Results",
        "",
        "| System | Explicit canonical orbital indices | Minimum ligand population | CASCI method | ⟨S²⟩ | Occupation sum | Status |",
        "| --- | --- | ---: | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {system} | {canonical_orbitals} | {min_selected_ligand_population:.3f} | "
            "{casci_method} | {spin_square:.2e} | {occupation_sum:.6f} | "
            "{casci_status} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Scope and limitation",
            "",
            "This registers an explicit, ligand-centered *candidate* active space for ideal-state benchmarking. "
            "The orbital indices are system-specific and must be mapped explicitly when generating each Hamiltonian; "
            "they are not a contiguous HOMO/LUMO block. Before a production energy claim, repeat the localization "
            "check at the production classical level and review orbital shapes.",
            "",
        ]
    )
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text("\n".join(lines))
    print(f"Wrote {args.output_csv} and {args.output_report}")


if __name__ == "__main__":
    main()
