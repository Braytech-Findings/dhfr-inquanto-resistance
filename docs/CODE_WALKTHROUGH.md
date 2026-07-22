# Code Walkthrough

This guide follows repository order. The detailed status, inputs, outputs,
services, and action for every logic file are in [CODE_INVENTORY.md](CODE_INVENTORY.md).
All commands start at the repository root. “Success” means the expected artifact
or message appears; it never means the biological hypothesis is proven.

## `Makefile`

### What this file does

It gives short names to common local commands. `make test` compiles, lints, and
tests; `make figures` rebuilds saved-data plots. The Nexus target is dry-run.

### Why the project needs it

It reduces typing and keeps safe public checks consistent.

### Inputs

The repository, Python environment, and the selected Make target.

### Outputs

Test messages or artifacts made by the called script.

### Step-by-step explanation

The first block declares targets. Each later block runs one documented command.
No target submits a remote job.

### Important functions

Make has targets instead of functions. Failure means the called tool is missing
or returned a nonzero status.

### Example command

```bash
make test
```

### What success looks like

Compile, lint, and test checks finish with no failure.

### Scientific meaning

Passing checks supports reproducibility; it is not molecular evidence.

## `analysis/`

### What these files do

- `analysis/R/make_publication_figures.R` reads the verified energy CSV and
  writes R PNG/PDF versions.
- `analysis/R/validate_publication_data.R` checks three finite numeric rows and
  records the R session.
- `analysis/figures.R` plots classical interaction proxies, endpoint values,
  and sensitivity rows.

### Why the project needs them

They provide independent plotting and classical-analysis views. Their inputs
must already be scientifically valid; plotting does not validate them.

### Inputs and outputs

Inputs are saved CSV/JSON under `results/`; outputs are figures and
`analysis/R/sessionInfo.txt`. They are local and cost no credits.

### Step-by-step explanation

Each script finds the root, reads tables, checks or reshapes columns, labels
axes in Hartree/millihartree, then saves files. `analysis/figures.R` must not be
used to interpret the historical bootstrap CI until the open replicate decision
is resolved.

### Important functions and failure cases

These scripts are linear. Missing R packages, missing columns, missing files, or
non-numeric data stop execution (the compact publication plot treats absent
`ggplot2` as an optional skip).

### Example command and success

```bash
Rscript analysis/R/validate_publication_data.R
Rscript analysis/R/make_publication_figures.R
```

Success reports three validated rows and writes two figure formats. It does not
prove a hardware run or a four-system comparison.

## `configs/`

### What these files do

Eight YAML files freeze system identities, structures, poses, hydration,
clusters, active spaces, classical methods, broader variants, and source
provenance. `core_systems.yaml` defines the endpoint sign. These files keep
research choices visible instead of hiding them in scripts.

### Inputs and outputs

They are human-written inputs and create nothing alone. Builders read them to
create structures, calculations, and tables. Bad YAML or inconsistent IDs cause
validation failures.

### Example command and success

```bash
python -c "import yaml, pathlib; [yaml.safe_load(p.read_text()) for p in pathlib.Path('configs').glob('*.yaml')]; print('configs parse')"
```

Success only means valid YAML. Scientific choices still need researcher review.

## Saved parameters, environment, manuscript, and notebooks

### What these files do

`data/params/WT_TMP_params.json` stores the 117 reviewed WT_TMP parameters.
`environment.yml` defines the public Python 3.11 environment. `manuscript/build.sh`
builds existing TeX without changing its prose. The exploratory notebook shows
analysis; the publication-validation notebook is a minimal support artifact.
`requirements_before_qnexus_update.txt` is an untracked user-owned historical
snapshot, not the installer.

### Inputs, outputs, and warnings

The parameter JSON is historical scientific input and must not be reformatted
casually. Environment creation downloads packages but uses no quantum credits.
Notebook output can become stale and is not evidence without traceable inputs.

### Example commands

```bash
conda env create -f environment.yml
jupyter nbconvert --to notebook --execute notebooks/01_exploratory_analysis.ipynb --stdout >/dev/null
```

The notebook command is only appropriate after reviewing its cost and inputs.

## Numbered workflow scripts

### What these files do

`01_prepare_complexes.py` creates four consistent structures;
`02_prepare_classical_inputs.py` prepares classical jobs;
`03_run_classical_calculations.py` dispatches local calculations;
`04_run_avas_and_vqe.py` dispatches active-space/VQE steps; and
`05_collect_results.py` gathers outputs. `01_fix_ligand_parameterization.py` is
an overlapping historical helper retained pending a researcher decision.

### Inputs and outputs

They read PDB/SDF/YAML and prior-stage files, then write processed structures,
calculation JSON, checkpoints, or tables. They run locally. Chemistry stages may
be slow but do not submit cloud jobs.

### Important functions and failure cases

Each `main()` checks or dispatches one stage. Preparation helpers preserve the
retained ligand coordinates. Missing chemistry dependencies, invalid structures,
failed subprocesses, or unconverged calculations mean the stage is incomplete.

### Example command and success

```bash
python scripts/01_prepare_complexes.py --help
```

Success from a real run means expected files and QC metadata exist, not that the
pose or resistance hypothesis is experimentally validated.

## Analysis, audit, and collection scripts

### What these files do

- `analyze_endpoint.py` calculates the fixed D contrast and, only with genuine
  replicates, a seeded percentile bootstrap interval.
- `analyze_orbital_character.py` scores ligand population in candidate orbitals.
- `audit_ligands.py`, `audit_pdb_sources.py`, `audit_protonated_models.py`, and
  `audit_water_models.py` check identity, provenance, and structural variants.
- `collect_classical_results.py` assembles converged local result JSON and fixed
  D contrasts.
- `summarize_active_space.py` checks selection hashes and combines four-system
  orbital/CASCI data.

### Inputs and outputs

They read saved structures/checkpoints/CSV/JSON and write local tables, JSON,
plots, or reports. They contact no service and consume no credits.

### Important functions

`contrast(values)` fixes the subtraction direction. Orbital functions map atom
and orbital indices. `load()`/`inspect()` functions reject missing or malformed
inputs. Failures indicate incomplete or inconsistent inputs, not a negative
biological finding.

### Example command

```bash
python scripts/analyze_endpoint.py --help
python scripts/summarize_active_space.py --help
```

## Molecular builders and renderers

### What these files do

`build_nadph_embedding.py`, `build_pose_ensemble.py`,
`build_protonation_models.py`, `build_qm_clusters.py`, `build_water_models.py`,
and `prepare_protonated_models.py` create controlled model variants.
`extract_ligand.py`, `model_4dtmp.py`, and `prepare_structure.py` are focused
older helpers. `inspect_structures.py`, `render_ligand_identity.py`,
`render_molecular_3d.py`, and `render_structure_reports.py` create local QC and
visual evidence.

### Inputs and outputs

PDB/SDF/config inputs become PDB/SDF/XYZ/CSV/JSON and PNG/PDF outputs. The
scripts use local chemistry packages. `render_molecular_3d.py` explicitly keeps
the unverified QM-to-PDB mapping separate.

### Important functions and failure cases

Builders select residues, add link atoms or a proton, preserve coordinates, and
record counts/charges. Renderers calculate selections before drawing. Missing
atoms, inconsistent residue names, force-field failures, or implausible charges
must stop interpretation.

### Example command

```bash
python scripts/inspect_structures.py --help
python scripts/render_molecular_3d.py
```

## Classical and active-space calculations

### What these files do

`run_pyscf.py`, `run_scf_checkpoint.py`, and `run_counterpoise.py` run local
electronic-structure calculations. `select_active_space.py` performs diagnostic
AVAS selection; `validate_active_space.py` runs CASCI checks;
`estimate_classical_resources.py` labels estimates rather than measured cost.
`run_h2_smoke.py` tests PySCF on H2 and is not DHFR evidence.

### Inputs and outputs

They read XYZ, point charges, checkpoints, and CLI settings, then write JSON,
NPZ, checkpoint, or table files in Hartree. No cloud backend is used.

### Important functions and failure cases

`main()` functions build molecules, run SCF/DFT/CASCI, check convergence, and
serialize results. Non-convergence, bad charge/spin, absent orbitals, and missing
files are calculation failures. They do not establish a biological conclusion.

### Example command

```bash
python scripts/run_pyscf.py --help
python scripts/validate_active_space.py --help
```

## Local quantum workflow

### What these files do

`evaluate_saved_vqe_energy.py` evaluates ideal WT_TMP saved parameters.
`prepare_local_pauli_energy.py` groups Hamiltonian terms into circuits.
`run_local_pauli_energy.py` is the historical local finite-shot workflow.
`run_local_pauli_energy_optimized.py` is a resumable partial-compilation
implementation with equivalence tests and hashes. `run_local_h2.py` samples
saved QASM locally. `run_inquanto_vqe.py` is a small/local VQE entry point.

### Inputs and outputs

They read WT_TMP XYZ, Hamiltonian, parameters, QASM, and checkpoints. They write
local JSON/CSV/QASM/pickle/checkpoint files. `QuantinuumAPIOffline` means no
Nexus login and no credits. Only the preserved WT_TMP result is verified.

### Important functions

`audit_core.canonical_system` rejects misleading names;
`total_shots` includes circuits, per-circuit shots, and job replicates;
optimized-runner hash, suffix, placement, batching, and exact-state functions
fail closed when circuit equivalence is not established.

### Example command and success

```bash
python scripts/run_local_h2.py --help
python scripts/prepare_local_pauli_energy.py --help
```

A successful local count file is circuit-path evidence. A successful energy
workflow needs the full saved protocol and provenance; neither is hardware.

## Remote access helpers

### What these files do

`diagnose_quantinuum_access.py` records sanitized account/device metadata.
`test_quantinuum_access.py` provides offline dry-run, explicit discovery, and a
guarded Bell test. `submit_hosted_pauli_energy.py` deliberately refuses to
implement molecular submission because circuit mapping is unvalidated.

### Inputs and outputs

Explicit remote modes can use Nexus credentials from the normal client and
private environment selectors. Reports are sanitized local files. Submission
requires confirmation flags and may consume quota/credits.

### Important functions and failure cases

`resolve_project_selection` prevents ambiguous selectors; `estimate_hqc` checks
hardware limits; `hosted_bell` refuses missing confirmation; `explain_error`
labels code 14 as access/entitlement. Authentication, compilation, and job
creation do not mean completion.

### Example command and success

```bash
python scripts/test_quantinuum_access.py
python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1SC --dry-run
```

Both are offline. Success means guards and arguments worked, not entitlement or
molecular evidence.

## Publication, reproduction, setup, and validation utilities

### What these files do

`build_publication_assets.py` creates traceable WT_TMP figures/tables;
`reproduce_manna.py` and `reproduce_plesa.py` summarize preserved upstream
biology; `download_pdbs.py` fetches/checksums public structures;
`generate_figures.sh`, `setup.sh`, `setup.ps1`, and `run_tests.sh` are wrappers;
`validate_repository.py` checks protected metadata and safety.

### Inputs, outputs, and failure cases

All are local except explicit PDB download and access diagnostics. Missing
sources, changed protected facts, checksum mismatches, test failures, or absent
dependencies stop the relevant task. Upstream reproductions are not quantum
results.

### Example command

```bash
python scripts/validate_repository.py
```

## Tests

`test_endpoint.py` fixes D's sign. `test_prepare_complexes.py` checks retained
4-DTMP coordinates and skips without the optional chemistry stack.
`test_publication_assets.py` checks figures, provenance, privacy, and mocked
Nexus guards. `test_audit_core.py` checks names, aliases, backend classes, shot
arithmetic, JSON/checksums, protected WT_TMP evidence, and offline defaults.

```bash
python -m pytest -q
```

## Visualization controls

The two visualization JSON files select relative WT_TMP inputs and record
hashes. Three PyMOL `.pml` files show the complex, pocket, or separate QM
cluster. They create views, not energies. Run, for example, `pymol
visualization/pymol/render_dhfr_tmp.pml` in a separately installed PyMOL.

