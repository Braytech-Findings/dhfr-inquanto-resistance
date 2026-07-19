#!/usr/bin/env python3
"""Render one-page annotated visual QC reports for the core four structures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openmm import app, unit

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
QC = ROOT / "results/tables/structure_qc.csv"
OUTPUT = ROOT / "results/reports/structures"


def coordinates(pdb: app.PDBFile) -> np.ndarray:
    return np.asarray(
        [position.value_in_unit(unit.angstrom) for position in pdb.positions]
    )


def set_equal_3d(ax: plt.Axes, points: np.ndarray) -> None:
    center = points.mean(axis=0)
    radius = max(np.ptp(points, axis=0).max() / 2, 1.0)
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)


def main() -> None:
    qc = pd.read_csv(QC).set_index("system")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for system, metrics in qc.iterrows():
        pdb = app.PDBFile(str(PROCESSED / f"{system}_minimized.pdb"))
        xyz = coordinates(pdb)
        ligand = []
        res28 = []
        waters = []
        backbone = []
        for residue in pdb.topology.residues():
            indices = [atom.index for atom in residue.atoms()]
            if residue.name in {"TOP", "DTM"}:
                ligand.extend(indices)
            elif residue.id == "28":
                res28.extend(indices)
            elif residue.name in {"HOH", "WAT"}:
                waters.extend(indices)
            else:
                backbone.extend(
                    atom.index for atom in residue.atoms() if atom.name == "CA"
                )
        focus_indices = ligand + res28 + waters
        focus = xyz[focus_indices]
        fig = plt.figure(figsize=(11, 8.5), facecolor="white")
        grid = fig.add_gridspec(2, 2, height_ratios=[0.18, 0.82], hspace=0.03)
        title_ax = fig.add_subplot(grid[0, :])
        title_ax.axis("off")
        title_ax.text(0, 0.8, f"{system} — structural QC", fontsize=20, weight="bold")
        summary = (
            f"Ligand {metrics.ligand_resname} ({int(metrics.ligand_heavy_atoms)} heavy atoms)  |  "
            f"Residue 28 {metrics.residue_28}  |  closest contact {metrics.ligand_res28_min_A:.2f} Å\n"
            f"Protein–ligand minimum {metrics.min_protein_ligand_A:.2f} Å  |  "
            f"<1.2 Å clashes {int(metrics.severe_clashes_lt_1_2A)}  |  retained waters {int(metrics.waters)}"
        )
        title_ax.text(0, 0.18, summary, fontsize=11, linespacing=1.5)
        for column, (elev, azim, label) in enumerate(
            ((20, -55, "Pocket overview"), (5, 35, "Orthogonal view"))
        ):
            ax = fig.add_subplot(grid[1, column], projection="3d")
            ax.plot(*xyz[backbone].T, color="#c5c9ce", linewidth=1, alpha=0.55)
            ax.scatter(
                *xyz[ligand].T, color="#129e9a", s=42, label="ligand", depthshade=False
            )
            ax.scatter(
                *xyz[res28].T,
                color="#b8324a",
                s=42,
                label="residue 28",
                depthshade=False,
            )
            if waters:
                ax.scatter(
                    *xyz[waters].T,
                    color="#3b82c4",
                    s=20,
                    label="retained water O/H",
                    alpha=0.65,
                )
            set_equal_3d(ax, focus)
            ax.view_init(elev=elev, azim=azim)
            ax.set_title(label, fontsize=13)
            ax.set_xlabel("x (Å)")
            ax.set_ylabel("y (Å)")
            ax.set_zlabel("z (Å)")
            if column == 0:
                ax.legend(loc="upper left", fontsize=9)
        fig.savefig(OUTPUT / f"{system}_qc.png", dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(OUTPUT / f"{system}_qc.png")


if __name__ == "__main__":
    main()
