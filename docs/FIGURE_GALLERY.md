# Figure gallery

All figures below are generated from repository data by `scripts/build_publication_assets.py` or `scripts/render_molecular_3d.py`. They describe one WT_TMP model unless otherwise noted. They do not show physical-hardware or clinical results.

## Verified energy and uncertainty

<a href="../results/publication/figures/energy_comparison.png"><img src="../results/publication/figures/energy_comparison.png" alt="Bar chart comparing Hartree–Fock, ideal saved-parameter VQE, and finite-shot local H2-1LE energy estimates relative to SCF." width="760"></a>

**WT_TMP energy comparison.** The finite-shot result is from the local noiseless H2-1LE emulator, with one-standard-error uncertainty. [PNG](../results/publication/figures/energy_comparison.png) · [PDF](../results/publication/figures/energy_comparison.pdf) · [source table](../results/publication/data/energy_results.csv). It is not a binding free energy.

<a href="../results/publication/figures/statistical_uncertainty.png"><img src="../results/publication/figures/statistical_uncertainty.png" alt="Finite-shot estimate shown with one-standard-error bar and approximate 95 percent interval relative to the exact saved-parameter energy." width="760"></a>

**Sampling uncertainty.** Repeated finite-shot measurements create statistical uncertainty; this interval does not include model, basis, or biological uncertainty. [PNG](../results/publication/figures/statistical_uncertainty.png) · [PDF](../results/publication/figures/statistical_uncertainty.pdf).

## Quantum measurement workload

<a href="../results/publication/figures/hamiltonian_compression.png"><img src="../results/publication/figures/hamiltonian_compression.png" alt="Bar chart showing 1819 Hamiltonian terms grouped into 576 measurement circuits." width="760"></a>

**Pauli grouping.** The Hamiltonian’s 1,819 Pauli terms were grouped into 576 measurement circuits; grouping reduces circuit count but does not change the Hamiltonian. [PNG](../results/publication/figures/hamiltonian_compression.png) · [PDF](../results/publication/figures/hamiltonian_compression.pdf).

<a href="../results/publication/figures/parameter_distribution.png"><img src="../results/publication/figures/parameter_distribution.png" alt="Histogram of 117 saved UCCSD parameter values." width="760"></a>

**UCCSD parameters.** These 117 values define the fixed trial state used for the saved-parameter reference. A large parameter is not automatically biologically important. [PNG](../results/publication/figures/parameter_distribution.png) · [PDF](../results/publication/figures/parameter_distribution.pdf).

## Structure and workflow

<a href="../results/publication/figures/molecular/wt_tmp_complex_overview.png"><img src="../results/publication/figures/molecular/wt_tmp_complex_overview.png" alt="Programmatic rendering of prepared WT DHFR protein trace with TOP ligand." width="620"></a>

**Prepared WT_TMP complex.** Protein chain `A` is shown with TMP residue `TOP` on chain `X`. This is a reproducible PDB rendering, not an experimental image. [PNG](../results/publication/figures/molecular/wt_tmp_complex_overview.png) · [PDF](../results/publication/figures/molecular/wt_tmp_complex_overview.pdf).

<a href="../results/publication/figures/workflow_technical.png"><img src="../results/publication/figures/workflow_technical.png" alt="Technical workflow from DHFR–TMP structure through active space and qubits to finite-shot energy." width="760"></a>

**Workflow overview.** This diagram explains the implemented local workflow from structure to energy and uncertainty. [PNG](../results/publication/figures/workflow_technical.png) · [PDF](../results/publication/figures/workflow_technical.pdf).

See [FIGURE_CAPTIONS.md](FIGURE_CAPTIONS.md), [FIGURE_ALT_TEXT.md](FIGURE_ALT_TEXT.md), and [FIGURE_GUIDE.md](FIGURE_GUIDE.md) for sources and interpretation limits.
