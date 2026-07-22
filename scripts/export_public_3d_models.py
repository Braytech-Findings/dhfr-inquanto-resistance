#!/usr/bin/env python3
"""Export compact public-safe PDB views from the verified prepared structures."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed"
OUT = ROOT / "visualization/public_structures"
SYSTEMS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")
ALLOWED = ("ATOM  ", "HETATM", "TER   ", "CONECT", "END   ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for system in SYSTEMS:
        source = SOURCE / f"{system}_minimized.pdb"
        target = OUT / f"{system}.pdb"
        lines = [
            line.rstrip()
            for line in source.read_text().splitlines()
            if line.startswith(ALLOWED)
        ]
        target.write_text("\n".join(lines) + "\n")
        records.append(
            {
                "system": system,
                "source_file": str(source.relative_to(ROOT)),
                "source_sha256": sha256(source),
                "public_file": str(target.relative_to(ROOT)),
                "public_sha256": sha256(target),
                "representation": "prepared protein-ligand PDB coordinates",
                "rendering": "3Dmol.js cartoon plus ligand sticks",
                "creation_date": date.today().isoformat(),
                "scientific_boundary": "static prepared structure; not molecular dynamics",
            }
        )
    (OUT / "provenance.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"Exported {len(records)} public 3D models")


if __name__ == "__main__":
    main()
