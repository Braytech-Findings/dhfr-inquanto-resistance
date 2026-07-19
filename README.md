# DHFR InQuanto Resistance

> **Plain-English summary:** DHFR is a tiny protein machine. Trimethoprim is a drug that can slow it down. This project uses quantum-chemistry tools to study one small, carefully selected part of a DHFR–drug model. Think of the full molecule as a huge school and the selected active space as one classroom: this is a useful simplification, not a literal description of electrons.

## What is verified now

For one `WT_TMP` active-space model, the repository contains an ideal saved-parameter VQE result and a completed 57,600-shot result from the **Quantinuum H2-1LE local noiseless emulator**. It is not physical quantum hardware, a noisy-emulator result, a mutation comparison, a binding-free-energy calculation, or a drug-resistance prediction.

The finite-shot result is `-2587.917118821447 ± 0.007647045141 Hartree`; the ideal saved-parameter reference is `-2587.912001526413 Hartree`. The uncertainty is too large for strong chemical or biological conclusions. Read [docs/RESULTS.md](docs/RESULTS.md), [docs/LIMITATIONS.md](docs/LIMITATIONS.md), and the fifth-grade guide in [docs/EXPLAINED_FOR_EVERYONE.md](docs/EXPLAINED_FOR_EVERYONE.md).

## Publication assets

Regenerate verified tables and figures with:

```bash
conda activate dhfr-inquanto
python scripts/build_publication_assets.py
```

Outputs are under `results/publication/`; each figure has a PNG, PDF, source CSV, and accessibility manifest. See [docs/GLOSSARY.md](docs/GLOSSARY.md) for definitions and [docs/FUTURE_WORK.md](docs/FUTURE_WORK.md) for the research roadmap.

Reproducible scaffold for testing whether mutation-specific electronic interaction signatures explain divergent resistance trajectories for trimethoprim (TMP) and 4′-desmethyltrimethoprim (4-DTMP).

## Research question

Can mutation-specific electronic interaction signatures calculated with InQuanto explain, and help predict, why TMP and 4-DTMP steer bacterial DHFR resistance along different evolutionary paths?

## Claims this project does not make

- Cluster interaction energies are not binding free energies.
- Emulator execution is not physical quantum-hardware execution.
- The study does not claim clinical efficacy, resistance prevention, a new antibiotic, or quantum advantage.
- Variant panels, active spaces, pose models, and optimizer settings must not be selected using favorable downstream quantum results.

## Prespecified systems and endpoint

| System | Protein | Ligand | Structural source |
|---|---|---|---|
| `WT_TMP` | WT | TMP | 6XG5 |
| `WT_4DTMP` | WT | 4-DTMP | modeled from 6XG5 |
| `L28R_TMP` | L28R | TMP | 6XG4 |
| `L28R_4DTMP` | L28R | 4-DTMP | modeled from 6XG4 |

The primary contrast is

`D = [E(L28R, 4-DTMP) − E(WT, 4-DTMP)] − [E(L28R, TMP) − E(WT, TMP)]`.

Do not interpret raw total energies from systems containing different atom counts as interaction energies. Use one consistent interaction-energy definition (for example, counterpoise-corrected cluster interaction energy) for all four systems.

## Installation

```bash
conda env create -f environment.yml
conda activate dhfr-qc
python -m pytest
```

InQuanto, `inquanto-pyscf`, `inquanto-nexus`, and `qnexus` are licensed/separately distributed and intentionally absent from the public environment file. Install the versions provided through your Quantinuum organization into `dhfr-qc`. Never commit tokens.

## Nexus safety boundary

The completed finite-shot result is local H2-1LE only: `-2587.917118821447 ± 0.007647045141 Ha` from 576 circuits × 100 shots. It is neither a Nexus-hosted nor physical-hardware result. A state-preparation circuit alone cannot calculate molecular energy. The guarded Nexus Bell test is `python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1SC --shots 10 --confirm-submit --max-hqc 1 --wait`; use `--dry-run` first. H2-1SC is artificial syntax checking, while H2-Emulator requires simulation quota. Backend visibility/“online” status does not establish execution entitlement; access code 14/default-group problems require organization or Quantinuum support.

## Publication-ready files

This repository now includes:

- [LICENSE](LICENSE)
- [CITATION.cff](CITATION.cff)
- [data/README.md](data/README.md)
- [notebooks/01_exploratory_analysis.ipynb](notebooks/01_exploratory_analysis.ipynb)
- [results/tables/final_results.csv](results/tables/final_results.csv) and [results/tables/final_results.json](results/tables/final_results.json)
- [results/reports/manuscript_draft.md](results/reports/manuscript_draft.md)
- [analysis/figures.R](analysis/figures.R)

## How to Cite

If you use this repository or its generated results, cite the metadata in [CITATION.cff](CITATION.cff) and reference the DHFR InQuanto Resistance project repository at https://github.com/Braytech-Findings/dhfr-inquanto-resistance.

## Workflow

Run commands from the repository root.

1. Download and checksum the experimental structures:

   ```bash
   python scripts/download_pdbs.py
   ```

2. Extract TMP and construct a pose-preserving 4-DTMP starting geometry:

   ```bash
   python scripts/extract_ligand.py data/raw/pdbs/6XG5.pdb data/processed/WT_TMP.sdf --resname TOP
   python scripts/model_4dtmp.py data/processed/WT_TMP.sdf data/processed/WT_4DTMP.sdf
   python scripts/extract_ligand.py data/raw/pdbs/6XG4.pdb data/processed/L28R_TMP.sdf --resname TOP
   python scripts/model_4dtmp.py data/processed/L28R_TMP.sdf data/processed/L28R_4DTMP.sdf
   ```

   Inspect atom mapping, protonation, stereochemistry, and the changed torsion visually. The transformation removes the para O-methyl group; it is not a validated bound-pose prediction.

3. Repair and minimize protein-only structures:

   ```bash
   python scripts/prepare_structure.py data/raw/pdbs/6XG5.pdb data/processed/WT_protein.pdb
   python scripts/prepare_structure.py data/raw/pdbs/6XG4.pdb data/processed/L28R_protein.pdb
   ```

   Before minimizing complexes, parameterize both ligands consistently with OpenFF or GAFF and validate protonation. The script refuses to imply that Amber protein parameters cover either ligand.

4. Build charge-balanced QM cluster XYZ files containing the ligand and the same pocket residue definitions in all systems. Cap severed peptide bonds, document retained waters, and converge the radius. Then run classical references:

   ```bash
   python scripts/run_pyscf.py cluster.xyz --method HF --basis def2-SVP \
     --output results/tables/WT_TMP_hf.json --save-orbitals results/WT_TMP_orbitals.npz \
     --checkpoint results/WT_TMP.chk
   ```

   Repeat for isolated fragments in their complex geometries and compute `E_complex − E_protein_fragment − E_ligand_fragment`; use ghost atoms for counterpoise correction. A production result should also include at least one DFT method and basis/QM-region sensitivity analyses.

5. Select an active space using chemically localized orbital diagnostics. `(6e,6o)` is a hypothesis, not a justified default. Generate and inspect cube files, track orbitals across all four systems, and retain the same chemical subspace. The supplied AVAS utility provides a first diagnostic:

   ```bash
   python scripts/select_active_space.py results/WT_TMP.chk \
     --ao-label N --ao-label O --output results/tables/WT_TMP_active_space.json
   ```

6. Export active-space Hamiltonians with the licensed `inquanto-pyscf` extension, then run ideal VQE before any noisy backend:

   ```bash
   python scripts/run_inquanto_vqe.py system.h5 --output results/tables/WT_TMP_vqe.json
   python scripts/check_nexus_backend.py --login --device H2-Emulator
   ```

   Use `H2-Emulator` for early remote tests. `H2-1E` consumes HQCs; submit only after checking circuit width/depth, shot count, queue status, and cost. The backend check does not submit a job.

7. Assemble replicate interaction energies and compute the endpoint:

   ```csv
   system_id,replicate,interaction_energy_hartree
   WT_TMP,1,-0.010
   WT_4DTMP,1,-0.009
   L28R_TMP,1,-0.008
   L28R_4DTMP,1,-0.011
   ```

   ```bash
   python scripts/analyze_endpoint.py results/tables/interaction_energies.csv
   ```

## Four-week decision gates

- Week 1: immutable inputs, ligand identity/protonation, prepared structures, and pocket definition pass visual and chemical review.
- Week 2: all four classical calculations converge; basis, cluster size, and orbital correspondence are documented.
- Week 3: ideal VQE agrees with exact active-space diagonalization to the chosen tolerance; noisy-emulator resources are estimated before submission.
- Week 4: prespecified contrast, uncertainty/sensitivity analyses, figures, and manuscript methods are generated from frozen tables.

See [docs/methods.md](docs/methods.md) for reporting requirements and scientific caveats.
