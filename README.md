<p align="center"><img src="docs/assets/dhfr_quantum_hero.svg" alt="Molecular network flowing into a quantum circuit, representing the DHFR quantum-chemistry workflow." width="100%"></p>

<h1 align="center">Quantum-Enabled Analysis of DHFR-Mediated Drug Resistance</h1>

<p align="center">A reproducible workflow connecting DHFR structural models, electronic-structure calculations, and finite-shot quantum-circuit measurements.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&amp;logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/Research-reproducible%20workflow-0B7285" alt="Research workflow">
  <img src="https://img.shields.io/badge/Domain-quantum%20chemistry-5C4B8A" alt="Quantum chemistry">
  <img src="https://img.shields.io/badge/Focus-DHFR%20and%20TMP-167C80" alt="DHFR and TMP">
  <img src="https://img.shields.io/badge/License-MIT-2EA44F" alt="MIT license">
</p>

> **In one sentence:** this project evaluates one small, reproducible DHFR–trimethoprim electronic model with classical and local quantum-emulator methods; it does not claim a drug-resistance prediction or a hardware result.

**Explore:** [Start here](#start-here-what-is-this-project) · [Research question](#research-question) · [Verified result](#what-is-verified-now) · [Figures](docs/FIGURE_GALLERY.md) · [Methods](docs/methods.md) · [Reproduction](docs/REPRODUCIBILITY.md) · [Backend status](docs/backend-status.md) · [Limitations](docs/LIMITATIONS.md) · [Manuscript](manuscript/README.md)

## Start Here: What Is This Project?

### Beginner explanation

Proteins are tiny biological machines. DHFR is a protein that helps cells make molecules needed for growth. Some medicines, including trimethoprim (TMP), interfere with DHFR. Changes in the genetic instructions for DHFR can change the protein and may contribute to drug resistance. Computational chemistry lets researchers study simplified molecular models on computers. Quantum computing may eventually help with selected electronic-structure problems; it does not replace laboratory experiments or automatically make calculations better.

This repository combines biology, molecular modeling, chemistry, and quantum computing to study a small selected part of one DHFR–TMP model. The active-space analogy is like studying one classroom in a large school: helpful for focus, but not a literal description of electrons.

### Technical explanation

The completed calculation uses a `WT_TMP` compact QM-cluster model, STO-3G basis, six selected spatial orbitals, a 12-qubit UCCSD ansatz, and Pauli-grouped finite-shot expectation estimation. Quantinuum InQuanto is the specialized quantum-chemistry software used to formulate this workflow. See [scientific background](docs/scientific-background.md) and the [glossary](docs/GLOSSARY.md).

## Research question

Can reproducible, mutation-specific electronic interaction descriptors help frame future studies of why TMP and 4-DTMP can follow different DHFR resistance trajectories? The present repository establishes workflow components and one WT_TMP local-emulator benchmark; it does **not** answer that biological question yet. Drug resistance matters because it can limit treatment options and raises the cost and difficulty of drug development, but molecular energy alone does not demonstrate clinical resistance.

## Project pipeline

```mermaid
flowchart LR
  A[Biological question] --> B[DHFR system selection]
  B --> C[Structure and QM-cluster preparation]
  C --> D[Classical electronic structure]
  D --> E[Active-space Hamiltonian]
  E --> F[UCCSD circuit and Pauli grouping]
  F --> G[Local H2-1LE finite-shot measurements]
  G --> H[Energy and uncertainty analysis]
  H --> I[Careful interpretation]
  classDef bio fill:#d9f1e8,stroke:#167c80,color:#102a43;
  classDef quantum fill:#eee6ff,stroke:#5c4b8a,color:#102a43;
  class A,B,C bio;
  class D,E,F,G,H,I quantum;
```

Stages `A–C` connect biology and molecular modeling; `D` is classical computation; `E–G` are quantum-chemistry/circuit stages; `H–I` are data analysis and visualization. The actual workflow is also shown in [workflow_technical.png](results/publication/figures/workflow_technical.png).

## What is verified now

| Item | Verified value | Evidence and meaning |
|---|---:|---|
| System | `WT_TMP` | One wild-type DHFR–TMP active-space model. |
| Method | UCCSD / Pauli averaging | 12 qubits; 117 saved parameters; 1,819 Pauli terms grouped into 576 circuits. |
| Basis | STO-3G | Minimal basis; a methodological limitation. |
| Ideal reference | `-2587.912001526413 Ha` | Saved-parameter expectation value. |
| Finite-shot result | `-2587.917118821447 ± 0.007647045141 Ha` | 57,600-shot local H2-1LE noiseless-emulator result. |
| Execution environment | Local emulator | Not Nexus-hosted, noisy hardware, or physical quantum hardware. |

The finite-shot value differs from the ideal reference by `-0.005117295034 Ha`; its standard error is larger than that difference. Read the [result details](docs/RESULTS.md), [machine-readable provenance](results/publication/data/verified_quantum_provenance.json), and [backend-status table](docs/backend-status.md).

## Publication assets

Regenerate verified tables and figures with:

```bash
conda activate dhfr-qc
python scripts/build_publication_assets.py
```

Outputs are under `results/publication/`; each figure has a PNG, PDF, source CSV, and accessibility manifest. See [docs/GLOSSARY.md](docs/GLOSSARY.md) for definitions and [docs/FUTURE_WORK.md](docs/FUTURE_WORK.md) for the research roadmap.

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

`qnexus==0.46.0` is installed from PyPI through `environment.yml`; it is public client software but needs an authenticated account for remote operations. InQuanto and its extensions are proprietary/separately distributed and must be installed from the organization-provided index into `dhfr-qc`. Public CI does not install either chemistry stack or perform Nexus access. Never commit tokens.

## Nexus safety boundary

The completed finite-shot result is local H2-1LE only: `-2587.917118821447 ± 0.007647045141 Ha` from 576 circuits × 100 shots. It is neither a Nexus-hosted nor physical-hardware result. A state-preparation circuit alone cannot calculate molecular energy. The guarded Nexus Bell test is `python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1SC --shots 10 --confirm-submit --wait`; H2-1SC is artificial syntax checking, while H2-Emulator requires simulation quota. Backend visibility/“online” status does not establish execution entitlement; teams and organization display names are not necessarily quota-bearing Nexus user groups. Access code 14/default-group problems require organization or Quantinuum support.

## Publication-ready files

This repository now includes:

- [LICENSE](LICENSE)
- [CITATION.cff](CITATION.cff)
- [data/README.md](data/README.md)
- [notebooks/publication_figure_validation.ipynb](notebooks/publication_figure_validation.ipynb)
- [results/tables/final_results.csv](results/tables/final_results.csv) and [results/tables/final_results.json](results/tables/final_results.json)
- [results/reports/manuscript_draft.md](results/reports/manuscript_draft.md)
- [analysis/figures.R](analysis/figures.R)

## How to Cite

If you use this repository or its generated results, cite the metadata in [CITATION.cff](CITATION.cff) and reference the DHFR InQuanto Resistance project repository at https://github.com/Braytech-Findings/dhfr-inquanto-resistance.

## Project status and structure

| Status | Scope |
|---|---|
| Completed locally | WT_TMP ideal expectation and finite-shot local H2-1LE estimate. |
| Circuit generated | Active-space/UCCSD workflow and local measurement plan. |
| Not yet completed | Matched mutant comparison, noisy hosted emulation, physical-hardware energy, wet-lab validation. |

```text
configs/                Prespecified systems, models, and protocol settings
data/                   Small public parameters and data documentation
scripts/                Reproducible preparation, analysis, plotting, and guarded access tools
results/publication/    Lightweight verified summaries, figures, and provenance
docs/                   Beginner, methods, results, limitations, and backend explanations
manuscript/             LaTeX source for the draft report
tests/                  Public lightweight integrity and safety tests
visualization/          Molecular rendering recipes and interactive viewer assets
```

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
   python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-Emulator --shots 10 --dry-run
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
