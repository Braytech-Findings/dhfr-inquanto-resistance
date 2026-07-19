#!/usr/bin/env python3
"""Render lightweight, reproducible WT_TMP structural figures without PyMOL.

The script reads repository-relative PDB/XYZ inputs and writes PNG/PDF figures plus
a manifest.  It deliberately does not claim that the independent QM-cluster atom
ordering maps one-to-one onto the prepared PDB unless that test passes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PDB = ROOT / "data/processed/WT_TMP_minimized.pdb"
XYZ = ROOT / "data/processed/qm_clusters/WT_TMP_compact_primary.xyz"
OUT = ROOT / "results/publication/figures/molecular"
DATA = ROOT / "results/publication/data"
COLORS = {
    "C": "#505050",
    "N": "#2878b5",
    "O": "#d53e4f",
    "S": "#d99a00",
    "H": "#d9d9d9",
}


def atoms(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            rows.append(
                {
                    "name": line[12:16].strip(),
                    "res": line[17:20].strip(),
                    "chain": line[21].strip(),
                    "resi": int(line[22:26]),
                    "element": (line[76:78].strip() or line[12:16].strip()[0]).upper(),
                    "xyz": np.array(
                        [float(line[30:38]), float(line[38:46]), float(line[46:54])]
                    ),
                }
            )
    return rows


def xyz_atoms(path: Path) -> list[dict]:
    lines = path.read_text().splitlines()[2:]
    return [
        {"element": p[0].upper(), "xyz": np.array(list(map(float, p[1:4])))}
        for p in (line.split() for line in lines)
        if len(p) >= 4
    ]


def draw(ax, selection, title, bonds=True):
    for atom in selection:
        ax.scatter(
            *atom["xyz"],
            s=16 if atom["element"] == "H" else 32,
            c=COLORS.get(atom["element"], "#8b5a2b"),
            alpha=0.82,
            edgecolors="none",
        )
    if bonds:
        heavy = [a for a in selection if a["element"] != "H"]
        for i, left in enumerate(heavy):
            for right in heavy[i + 1 :]:
                d = np.linalg.norm(left["xyz"] - right["xyz"])
                if 0.65 < d < 1.85:
                    ax.plot(
                        *np.vstack((left["xyz"], right["xyz"])).T,
                        color="#777",
                        lw=0.7,
                        alpha=0.55,
                    )
    ax.set_title(title)
    ax.set_axis_off()
    ax.view_init(elev=22, azim=-58)
    ax.set_box_aspect((1, 1, 0.75))


def save(selection, name, title):
    fig = plt.figure(figsize=(6.2, 5.2))
    ax = fig.add_subplot(111, projection="3d")
    draw(ax, selection, title)
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{suffix}", dpi=250, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    pdb = atoms(PDB)
    ligand = [a for a in pdb if a["res"] == "TOP"]
    protein_ca = [a for a in pdb if a["chain"] == "A" and a["name"] == "CA"]
    centre = np.mean([a["xyz"] for a in ligand], axis=0)
    pocket = [
        a for a in pdb if a["chain"] == "A" and np.linalg.norm(a["xyz"] - centre) <= 5.0
    ]
    # A full-complex view uses CA trace plus ligand, which is readable and avoids a false bond network.
    save(
        protein_ca + ligand,
        "wt_tmp_complex_overview",
        "WT DHFR–TMP prepared complex (protein Cα trace + TOP ligand)",
    )
    save(
        pocket + ligand,
        "wt_tmp_binding_pocket",
        "WT_TMP binding pocket: atoms within 5 Å of TOP",
    )
    cluster = xyz_atoms(XYZ)
    save(
        cluster,
        "wt_tmp_qm_cluster",
        "WT_TMP compact primary QM cluster (XYZ rendering)",
    )
    # Exact coordinate equality is intentionally stringent; cluster construction can transform/order atoms.
    mapping_verified = False
    manifest = {
        "system": "WT_TMP",
        "pdb": str(PDB.relative_to(ROOT)),
        "ligand_residue": "TOP",
        "protein_chain": "A",
        "ligand_atoms": len(ligand),
        "pocket_radius_angstrom": 5.0,
        "pocket_atoms": len(pocket),
        "qm_xyz": str(XYZ.relative_to(ROOT)),
        "qm_cluster_atoms": len(cluster),
        "qm_cluster_mapping_verified": mapping_verified,
        "mapping_note": "No PDB-overlaid QM selection is shown because atom-level correspondence was not independently verified.",
        "inputs_sha256": {
            str(PDB.relative_to(ROOT)): hashlib.sha256(PDB.read_bytes()).hexdigest(),
            str(XYZ.relative_to(ROOT)): hashlib.sha256(XYZ.read_bytes()).hexdigest(),
        },
    }
    (ROOT / "visualization/molecular_assets_manifest.json").parent.mkdir(exist_ok=True)
    (ROOT / "visualization/molecular_assets_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    with (DATA / "molecular_structure_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["field", "value"])
        writer.writeheader()
        writer.writerows(
            {"field": k, "value": v}
            for k, v in manifest.items()
            if not isinstance(v, dict)
        )


if __name__ == "__main__":
    main()
