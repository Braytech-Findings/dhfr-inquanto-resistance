# Visual Research Gallery

<p align="center"><img src="assets/reproducibility_dashboard.svg" alt="DHFR reproducibility dashboard from biological model to verified public assets" width="100%"></p>

All figures are generated from repository data by `scripts/build_publication_assets.py` or `scripts/render_molecular_3d.py`. They describe one `WT_TMP` model unless otherwise noted. They do **not** show a physical-hardware result, binding free energy, clinical result, or drug-resistance prediction.

<p align="center">
  <img src="https://img.shields.io/badge/Evidence-local%20emulator-2EA44F" alt="Local emulator evidence">
  <img src="https://img.shields.io/badge/Model-WT__TMP-17A589" alt="WT TMP model">
  <img src="https://img.shields.io/badge/Figures-PNG%20%2B%20PDF-7D5FFF" alt="PNG and PDF figures">
  <img src="https://img.shields.io/badge/Sources-CSV%20%2B%20JSON-F39C52" alt="CSV and JSON source records">
</p>

## Gallery at a glance

<table>
<tr>
<td width="50%" align="center">
<a href="../results/publication/figures/energy_comparison.png"><img src="../results/publication/figures/energy_comparison.png" alt="Bar chart comparing Hartree-Fock, ideal saved-parameter VQE, and finite-shot local H2-1LE energy estimates relative to SCF" width="100%"></a><br>
<strong>Figure 1 · Energy comparison</strong><br>
The finite-shot value is compared with classical and ideal saved-parameter references.<br>
<a href="../results/publication/figures/energy_comparison.png">PNG</a> · <a href="../results/publication/figures/energy_comparison.pdf">PDF</a> · <a href="../results/publication/data/energy_results.csv">source CSV</a>
</td>
<td width="50%" align="center">
<a href="../results/publication/figures/statistical_uncertainty.png"><img src="../results/publication/figures/statistical_uncertainty.png" alt="Finite-shot estimate with one-standard-error bar and approximate 95 percent interval relative to the exact saved-parameter energy" width="100%"></a><br>
<strong>Figure 2 · Sampling uncertainty</strong><br>
The interval shows finite-shot uncertainty only, not model or biological uncertainty.<br>
<a href="../results/publication/figures/statistical_uncertainty.png">PNG</a> · <a href="../results/publication/figures/statistical_uncertainty.pdf">PDF</a>
</td>
</tr>
<tr>
<td width="50%" align="center">
<a href="../results/publication/figures/hamiltonian_compression.png"><img src="../results/publication/figures/hamiltonian_compression.png" alt="Bar chart showing 1819 Hamiltonian terms grouped into 576 measurement circuits" width="100%"></a><br>
<strong>Figure 3 · Hamiltonian compression</strong><br>
1,819 Pauli terms are grouped into 576 measurement circuits to reduce workload.<br>
<a href="../results/publication/figures/hamiltonian_compression.png">PNG</a> · <a href="../results/publication/figures/hamiltonian_compression.pdf">PDF</a>
</td>
<td width="50%" align="center">
<a href="../results/publication/figures/parameter_distribution.png"><img src="../results/publication/figures/parameter_distribution.png" alt="Histogram of 117 saved UCCSD parameter values" width="100%"></a><br>
<strong>Figure 4 · UCCSD parameters</strong><br>
117 saved values define the fixed trial state; size alone is not biological importance.<br>
<a href="../results/publication/figures/parameter_distribution.png">PNG</a> · <a href="../results/publication/figures/parameter_distribution.pdf">PDF</a>
</td>
</tr>
<tr>
<td width="50%" align="center">
<a href="../results/publication/figures/molecular/wt_tmp_complex_overview.png"><img src="../results/publication/figures/molecular/wt_tmp_complex_overview.png" alt="Programmatic rendering of prepared WT DHFR protein trace with TOP ligand" width="100%"></a><br>
<strong>Figure 5 · Prepared WT_TMP complex</strong><br>
A reproducible PDB rendering of protein chain A and TMP residue TOP on chain X.<br>
<a href="../results/publication/figures/molecular/wt_tmp_complex_overview.png">PNG</a> · <a href="../results/publication/figures/molecular/wt_tmp_complex_overview.pdf">PDF</a>
</td>
<td width="50%" align="center">
<a href="../results/publication/figures/workflow_technical.png"><img src="../results/publication/figures/workflow_technical.png" alt="Technical workflow from DHFR TMP structure through active space and qubits to finite-shot energy" width="100%"></a><br>
<strong>Figure 6 · Technical workflow</strong><br>
The implemented path from prepared structure to active-space energy and uncertainty.<br>
<a href="../results/publication/figures/workflow_technical.png">PNG</a> · <a href="../results/publication/figures/workflow_technical.pdf">PDF</a>
</td>
</tr>
</table>

## Plain-language interpretation

| Figure | Main message | Do not conclude |
|---|---|---|
| Energy comparison | The finite-shot estimate is close to the ideal saved-parameter reference at the displayed scale. | That the model predicts binding or resistance. |
| Sampling uncertainty | Repeating a finite number of measurements creates statistical variation. | That this interval covers every scientific uncertainty. |
| Hamiltonian compression | Measurement grouping reduces the number of circuits required. | That the molecular Hamiltonian itself was simplified or changed. |
| Parameter distribution | The fixed UCCSD state uses 117 saved values. | That the largest values identify important mutations or residues. |
| Molecular overview | The prepared structure and ligand placement can be rendered reproducibly. | That the rendering is experimental microscopy or a validated binding pose. |
| Technical workflow | The full implemented calculation can be followed stage by stage. | That a state-preparation circuit alone computes molecular energy. |

## Recreate the gallery

Create the public environment and run the one-command workflow:

```bash
conda env create -f environment.yml
conda activate dhfr-qc
python scripts/reproduce_everything.py
```

Or regenerate only the visual assets:

```bash
python scripts/build_publication_assets.py
python scripts/render_molecular_3d.py
```

Read [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for expected output paths, optional R figures, the manuscript build, licensed local execution, and troubleshooting.

## Accessibility and source records

- [Figure captions](FIGURE_CAPTIONS.md)
- [Figure alt text](FIGURE_ALT_TEXT.md)
- [Figure interpretation guide](FIGURE_GUIDE.md)
- [Verified quantum provenance](../results/publication/data/verified_quantum_provenance.json)
- [Energy source table](../results/publication/data/energy_results.csv)

## Evidence boundary

These visuals summarize one compact `WT_TMP` model and one local H2-1LE finite-shot benchmark. The figures do not support claims of physical quantum-hardware performance, clinical efficacy, binding free energy, resistance prevention, or quantum advantage.
