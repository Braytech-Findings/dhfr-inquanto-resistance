# Reproduce Everything

This repository has two deliberately separate reproducibility levels:

1. **Public reproduction** regenerates the committed figures, tables, molecular render, accessibility records, and automated checks from public repository data.
2. **Licensed local reproduction** reruns the saved-parameter 576-circuit finite-shot calculation using InQuanto and the Quantinuum H2-1LE **local noiseless emulator**. It requires licensed software and several gigabytes of local checkpoints that are not stored on GitHub.

Neither level requires physical quantum hardware. Public reproduction does not require Nexus authentication, tokens, or cloud access.

> [!IMPORTANT]
> The verified finite-shot result is a local-emulator result, not a Nexus-hosted result and not a physical H2 QPU result. Reproducing figures from the verified summary does not independently rerun the licensed quantum calculation.

## Visual workflow

<p align="center"><img src="assets/reproducibility_dashboard.svg" alt="Four-stage DHFR reproducibility workflow from biological model through classical chemistry and local quantum measurement to verified public assets" width="100%"></p>

## Reproducibility matrix

| Level | Who can run it | What it regenerates | Cloud or hardware use |
|---|---|---|---|
| Public tests | Anyone with Python 3.11 | Integrity, safety, parsing, and publication-asset tests | None |
| Public publication assets | Anyone with `environment.yml` | PNG/PDF figures, source CSVs, manifests, provenance summaries, molecular render | None |
| Optional R figures | Anyone with R and documented packages | Independent R figure outputs | None |
| Optional manuscript | Anyone with the required LaTeX toolchain | Manuscript PDF from committed source | None |
| Licensed local finite-shot calculation | Authorized InQuanto user with excluded local artifacts | 576 circuits × 100 shots on local H2-1LE, energy, uncertainty, checkpoints | Local emulator only |
| Nexus diagnostics or Bell dry run | Authorized Nexus user | Access checks or a non-submitting plan | Authentication may be required; default commands do not submit |
| Physical H2 QPU | Not part of the verified study | Nothing in the current evidence record | Not reproduced or claimed |

## Fastest public route

### 1. Create the public environment

```bash
conda env create -f environment.yml
conda activate dhfr-qc
```

When the environment already exists:

```bash
conda env update -f environment.yml --prune
conda activate dhfr-qc
```

### 2. Preview the complete workflow

```bash
python scripts/reproduce_everything.py --dry-run --include-r --include-manuscript
```

### 3. Regenerate all standard public assets

```bash
python scripts/reproduce_everything.py
```

This runs:

1. Python byte-code compilation for repository scripts;
2. Ruff checks;
3. the public pytest suite;
4. publication table, figure, and accessibility-manifest generation;
5. the reproducible WT_TMP molecular render; and
6. a final check that expected public output files exist.

### 4. Include optional R figures

```bash
python scripts/reproduce_everything.py --include-r
```

### 5. Include the manuscript build

```bash
python scripts/reproduce_everything.py --include-manuscript
```

The manuscript option requires the LaTeX tools used by `manuscript/build.sh`.

## Makefile route

The repository also provides short Make targets:

| Goal | Command |
|---|---|
| Show available safe targets | `make help` |
| Run public tests | `make test-public` |
| Regenerate Python figures and tables | `make figures` |
| Regenerate R figures | `make figures-r` |
| Regenerate the molecular render | `make molecular` |
| Regenerate publication assets | `make publication` |
| Regenerate public assets and run tests | `make all-public` |
| Run local access diagnostics | `make access-diagnostics` |
| Preview the guarded Nexus Bell path | `make nexus-bell-dry-run` |

For a standard full public reproduction:

```bash
make all-public
```

## Manual public route

Run commands from the repository root.

### Validate code and documentation assumptions

```bash
python -m compileall -q scripts
ruff check .
pytest -q
```

### Regenerate publication assets

```bash
python scripts/build_publication_assets.py
```

The main output tree is:

```text
results/publication/
├── data/       Source CSV and JSON summaries
├── figures/    PNG and PDF figures
└── ...         Accessibility and provenance manifests
```

Each major figure is paired with source data or a machine-readable record. See [FIGURE_GALLERY.md](FIGURE_GALLERY.md), [FIGURE_ALT_TEXT.md](FIGURE_ALT_TEXT.md), and [FIGURE_GUIDE.md](FIGURE_GUIDE.md).

### Regenerate the molecular render

```bash
python scripts/render_molecular_3d.py
```

Expected primary output:

```text
results/publication/figures/molecular/wt_tmp_complex_overview.png
```

This is a deterministic programmatic rendering of the prepared structure, not an experimental image.

### Regenerate optional R figures

```bash
Rscript analysis/R/make_publication_figures.R
```

### Build the manuscript

```bash
cd manuscript
./build.sh
cd ..
```

## Expected public outputs

A successful standard run should preserve or regenerate at least:

```text
results/publication/figures/energy_comparison.png
results/publication/figures/statistical_uncertainty.png
results/publication/figures/hamiltonian_compression.png
results/publication/figures/parameter_distribution.png
results/publication/figures/workflow_technical.png
results/publication/figures/molecular/wt_tmp_complex_overview.png
results/publication/data/energy_results.csv
results/publication/data/verified_quantum_provenance.json
```

Open [FIGURE_GALLERY.md](FIGURE_GALLERY.md) to inspect the regenerated visual package.

## Licensed local finite-shot reproduction

The public repository records the verified result and provenance, but several large working files remain local because they total approximately **6.3 GB**. The excluded items include protocol checkpoints and a 2.3 GB measurement-partition file. Their expected locations and available checksums are recorded in `results/quantum/results_manifest.json`.

### Verified licensed environment

The stored manifest records:

| Package | Verified version |
|---|---:|
| Python | 3.11 |
| InQuanto | 6.1.0 |
| pytket | 2.18.1 |
| pytket-quantinuum | 0.57.0 |
| pytket-qiskit | 0.77.0 |
| PySCF | 2.13.1 |
| NumPy | 2.4.6 |

In the original workspace this licensed environment is named `dhfr-inquanto`.

### Baseline licensed command

After confirming that the excluded local inputs and checkpoints exist:

```bash
conda activate dhfr-inquanto
python scripts/run_local_pauli_energy.py \
  --system WT_TMP \
  --basis sto-3g \
  --shots-per-circuit 100
```

This recreates the 576-circuit, 57,600-shot workflow on the Quantinuum H2-1LE **local noiseless emulator**.

### Optimized workflow

The optimized implementation compiles the shared UCCSD preparation once and validates representative measurement groups before a full execution. First inspect its plan and prerequisites, then run only in the licensed local environment:

```bash
python scripts/run_local_pauli_energy_optimized.py \
  --system WT_TMP \
  --basis sto-3g \
  --shots-per-circuit 100 \
  --batch-size 16 \
  --validate-circuits 3
```

A full local execution requires the explicit flag:

```bash
python scripts/run_local_pauli_energy_optimized.py \
  --system WT_TMP \
  --basis sto-3g \
  --shots-per-circuit 100 \
  --batch-size 16 \
  --validate-circuits 3 \
  --execute
```

Do not run the full optimized path unless its exact-state and representative finite-shot validation passes. The script is fail-closed when circuit reconstruction or backend validity checks fail.

## Verify the result record

The public verified summary is under:

```text
results/publication/data/verified_summary.json
results/publication/data/verified_quantum_provenance.json
```

The current verified values are:

| Quantity | Value |
|---|---:|
| System | `WT_TMP` |
| Qubits | 12 |
| Saved UCCSD parameters | 117 |
| Pauli terms | 1,819 |
| Measurement circuits | 576 |
| Shots per circuit | 100 |
| Total shots | 57,600 |
| Ideal saved-parameter energy | `-2587.912001526413 Ha` |
| Finite-shot local H2-1LE energy | `-2587.917118821447 Ha` |
| Standard error | `0.007647045141 Ha` |

The difference between the finite-shot estimate and the ideal saved-parameter reference is smaller than the reported standard error. This uncertainty covers finite-shot sampling only; it does not include model, basis, active-space, structural, or biological uncertainty.

## Nexus and provider safety boundary

Public reproduction requires no credentials. The following commands are diagnostic or dry-run tools and must remain separately labeled:

```bash
python scripts/diagnose_quantinuum_access.py
python scripts/test_quantinuum_access.py \
  --nexus-emulator \
  --backend H2-1SC \
  --dry-run
```

`H2-1SC` is a syntax checker, not a simulator or QPU. Backend visibility or online status does not prove execution entitlement. Never commit tokens, cookies, populated `.env` files, project secrets, user-group identifiers, or unsanitized provider responses.

## What cannot be exactly reproduced from GitHub alone

- The excluded multi-gigabyte local checkpoints and measurement plan.
- Licensed InQuanto execution without authorized packages.
- A historical cloud queue, provider entitlement state, or calibration snapshot.
- Physical H2 QPU results, because none are part of the verified evidence record.
- A drug-resistance prediction, binding free energy, clinical result, or claim of quantum advantage.

## Troubleshooting

### `conda` is not found

Install Miniconda, Anaconda, or another compatible Conda distribution, then recreate `dhfr-qc` from `environment.yml`.

### `ModuleNotFoundError` for InQuanto

You are in the public environment. InQuanto is licensed and intentionally not installed by `environment.yml`. Public tests and publication assets do not require it.

### Molecular rendering fails

Confirm that the prepared public structure inputs exist and that the scientific Python dependencies in `environment.yml` installed successfully.

### `Rscript` is not found

R is optional. Run the standard reproduction without `--include-r`, or install R and rerun the optional step.

### Manuscript build fails

The manuscript requires a local LaTeX toolchain. This does not invalidate the Python figures, tables, or tests.

### Generated figures look different

Check package versions, source CSV/JSON files, and the accessibility/source manifests. Do not compare screenshots alone; compare the underlying data and recorded provenance.

## Final integrity checklist

- [ ] The `dhfr-qc` environment was created from `environment.yml`.
- [ ] Public tests and Ruff checks passed.
- [ ] Publication figures and source tables regenerated.
- [ ] The WT_TMP molecular render regenerated.
- [ ] Verified public summaries agree with the committed result record.
- [ ] Licensed local output, local emulator output, Nexus output, and physical hardware remain separately labeled.
- [ ] No secrets or multi-gigabyte private checkpoints were added to GitHub.
- [ ] No biological, clinical, or quantum-advantage claim was inferred from energy alone.
