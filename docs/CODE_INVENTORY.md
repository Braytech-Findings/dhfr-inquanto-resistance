# Code Inventory

This inventory was created before broad code changes on `codex/full-code-audit`.
It covers the 80 maintained executable, notebook, configuration, test, and
visualization-control files found on 2026-07-21. Code below
`data/raw/external/` is a preserved third-party source snapshot: it is input
provenance, is not maintained or executed by the project, and is intentionally
not rewritten. Generated result JSON is scientific data, not configuration,
except for the two visualization manifests listed below.

## Key

- **Class** uses the audit prompt's A-S classes.
- **State** is `active`, `support`, `example`, `generated`, `legacy`, or `vendor`.
- **I/O** gives the main input -> output. `CLI` includes command-line flags.
- **Service** says whether a network or paid service can be contacted.
- **Finding/action** records the initial audit decision. `Review` means retain
  while testing it; it does not mean that its scientific output is verified.

## Maintained project files

| Path | Type | Class / state / test | Purpose and scientific role | Main I/O | Service | Initial finding / recommended action |
|---|---|---|---|---|---|---|
| `Makefile` | Make | O / active / no | Safe task entry points | targets -> commands/artifacts | diagnostics can contact Nexus | Review remote wording and tested targets |
| `analysis/R/make_publication_figures.R` | R | K / active / no | Plot verified WT_TMP saved data | energy CSV -> PNG/PDF | none | Add header/help; verify root handling |
| `analysis/R/validate_publication_data.R` | R | L / active / no | Validate publication energy table | CSV -> session info | none | Add header and stronger metadata checks |
| `analysis/figures.R` | R | K / support / no | Plot classical endpoint/sensitivity | result CSV/JSON -> figures | none | Outputs are pilot/sensitivity, not matched verified evidence; label clearly |
| `configs/active_space.yaml` | YAML | D/O / active / no | Freeze candidate CAS(6,6) choices | researcher choices -> workflow settings | none | Candidate status is clear; retain |
| `configs/classical_protocol.yaml` | YAML | C/O / active / no | Freeze interaction-energy protocol | researcher choices -> workflow settings | none | Retain; primary calculations remain incomplete |
| `configs/cluster_models.yaml` | YAML | B/O / active / no | Define QM clusters and charges | model choices -> cluster builder settings | none | Retain provisional labels |
| `configs/core_systems.yaml` | YAML | O / active / no | Define systems and central endpoint formula | model choices -> multiple scripts | none | D formula differs algebraic presentation only; centralize names in Python |
| `configs/pose_models.yaml` | YAML | B/O / active / no | Freeze geometry-only poses | pose decisions -> builders | none | Retain |
| `configs/source_manifest.yaml` | YAML | O / active / no | Record external source provenance | source metadata -> audit trail | listed URLs only | Retain; validate checksums separately |
| `configs/variant_panel.yaml` | YAML | O / support / no | Freeze broader biological panel | evidence choices -> evidence table | none | Not quantum evidence; retain wording |
| `configs/water_models.yaml` | YAML | B/O / active / no | Define hydration sensitivity models | water rules -> structures | none | Retain |
| `data/params/WT_TMP_params.json` | JSON | S / generated / no | Saved optimized WT_TMP parameters | prior VQE -> parameter vector | none | Historical artifact; checksum/provenance review, never rewrite casually |
| `environment.yml` | Conda YAML | O / active / no | Reproducible environment | package channels/specs -> environment | package downloads | Audit imports, pins, platforms, optional licensed stack |
| `manuscript/build.sh` | shell | P / support / no | Build existing manuscript PDF | TeX -> PDF | none | Do not rewrite report; shell syntax only |
| `notebooks/01_exploratory_analysis.ipynb` | notebook | P / example / no | Explain exploratory workflow | repository results -> displayed analysis | none intended | Audit hidden state, labels, and execution order |
| `notebooks/publication_figure_validation.ipynb` | notebook | L/P / support / no | Validate figure assets | saved assets -> checks | none | One-line/minimal notebook; document or deprecate |
| `requirements_before_qnexus_update.txt` | pip snapshot | S / untracked historical / no | User-owned pre-update dependency snapshot | environment freeze -> package list | install would download | Preserve untouched; decide whether to track in `OPEN_DECISIONS` |
| `scripts/01_fix_ligand_parameterization.py` | Python | B/Q / legacy / no | Earlier ligand repair helper | structures -> repaired ligand files | none | Compare with current preparation; label legacy if superseded |
| `scripts/01_prepare_complexes.py` | Python | B / active / indirectly | Build four processed complexes | PDB/config -> PDB/SDF/JSON | none | Core preparation; add validation tests/docs |
| `scripts/02_prepare_classical_inputs.py` | Python | C/N / active / no | Prepare classical calculation inputs | processed structures -> inputs | none | Review path and system validation |
| `scripts/03_run_classical_calculations.py` | Python | C / active / no | Dispatch local classical jobs | prepared systems -> calculation results | none | Review subprocess failures and resource defaults |
| `scripts/04_run_avas_and_vqe.py` | Python | D/E / support / no | Dispatch active-space/VQE stages | checkpoints/config -> results | none intended | Validate stage claims and failure propagation |
| `scripts/05_collect_results.py` | Python | J / active / no | Dispatch result collection | saved results -> tables | none | Validate missing/incomplete result handling |
| `scripts/__init__.py` | Python | N / active / no | Make scripts importable for tests | imports -> package namespace | none | No change needed |
| `scripts/analyze_endpoint.py` | Python | J / active / yes | Compute prespecified difference-in-differences | interaction CSV + seed -> JSON | none | Bootstrap is invalid for deterministic single geometries unless true replicates exist; gate it |
| `scripts/analyze_orbital_character.py` | Python | D / active / no | Score ligand character of orbitals | SCF checkpoint -> JSON/CSV/plot | none | Add system and file validation |
| `scripts/audit_ligands.py` | Python | L / active / no | Check ligand identity/coordinates | SDF/PDB -> audit table | none | Retain; document pass meaning |
| `scripts/audit_pdb_sources.py` | Python | L / active / no | Check deposited PDB sources | PDB/manifest -> table | none | Retain; validate checksums |
| `scripts/audit_protonated_models.py` | Python | L / active / no | Check protonated structures | structures -> audit table | none | Imports sibling by path assumption; make root-safe |
| `scripts/audit_water_models.py` | Python | L / active / no | Check water-model structures | structures -> audit table | none | Imports sibling by path assumption; make root-safe |
| `scripts/build_nadph_embedding.py` | Python | B/C / active / no | Build fixed NADPH point charges | PDB/template -> CSV | none | Validate charge/atom correspondence |
| `scripts/build_pose_ensemble.py` | Python | B / active / no | Build 4-DTMP pose alternatives | structures/config -> SDF/QC | none | Geometry-only status must remain explicit |
| `scripts/build_protonation_models.py` | Python | B / active / no | Add ligand N1 proton model | SDF -> protonated SDF/table | none | Validate charge and coordinate preservation |
| `scripts/build_publication_assets.py` | Python | K / active / yes | Build verified WT_TMP publication assets | verified JSON -> CSV/JSON/figures | none | Protect exact facts; add schema/checksum tests |
| `scripts/build_qm_clusters.py` | Python | B/D / active / no | Cut and cap QM clusters | structures/config -> XYZ/CSV/JSON | none | High scientific impact; validate names, charges, atom counts |
| `scripts/build_variant_evidence.py` | Python | J / support / no | Summarize public variant evidence | frozen config/data -> table | none | Keep separate from quantum evidence |
| `scripts/build_water_models.py` | Python | B / active / no | Generate hydration variants | structures/config -> structures/QC | none | Dynamic import; improve error message |
| `scripts/collect_classical_results.py` | Python | J / active / no | Collect completed classical contrasts | result JSON -> CSV | none | Must reject incomplete/placeholder data and define D direction |
| `scripts/diagnose_quantinuum_access.py` | Python | H/I / active / no | Read Nexus access metadata | authenticated account -> sanitized reports | Nexus, no job submission | Network occurs by default; require explicit confirmation and sanitize errors |
| `scripts/download_pdbs.py` | Python | B/N / active / no | Download deposited PDB inputs | RCSB URLs -> PDB/checksum manifest | RCSB network, free | Add explicit network flag/checksum validation |
| `scripts/estimate_classical_resources.py` | Python | C/N / support / no | Estimate local classical resources | cluster manifests -> table | none | Estimates are not measured costs; label |
| `scripts/evaluate_saved_vqe_energy.py` | Python | G/J / active / no | Re-evaluate saved WT_TMP VQE parameters | Hamiltonian/params -> exact JSON | none | Verify dependencies, schema, and exact-result label |
| `scripts/extract_ligand.py` | Python | B / support / no | Extract ligand from structure | PDB -> ligand file | none | Compare duplication with preparation module |
| `scripts/generate_figures.sh` | shell | K/N / active / no | Wrapper for R figures | saved tables -> figures | none | Add header and root-safe execution |
| `scripts/inspect_structures.py` | Python | L / active / no | Calculate structure QC metrics | PDB -> metrics/table | none | Central system constants should be shared |
| `scripts/model_4dtmp.py` | Python | B / support / no | Remove TMP methyl to model 4-DTMP | TMP structure -> modeled ligand | none | Compare duplication; preserve coordinates |
| `scripts/prepare_local_pauli_energy.py` | Python | E/G / active / no | Build local WT_TMP measurement protocol | molecule/params -> local checkpoints/plans | none | Local only; validate resume/provenance and naming |
| `scripts/prepare_protonated_models.py` | Python | B / active / no | Prepare protonated complexes | models -> minimized structures/QC | none | Dynamic import; improve failure messages |
| `scripts/prepare_structure.py` | Python | B / support / no | Older single-structure preparation | PDB -> processed PDB | none | Likely superseded; compare and label legacy |
| `scripts/render_ligand_identity.py` | Python | K/L / active / no | Draw audited ligands | SDF -> PNG | none | Add source note/manifest |
| `scripts/render_molecular_3d.py` | Python | K / active / yes | Render WT_TMP molecular views | PDB/XYZ -> PNG/PDF/manifest | none | Mapping disclaimer is correct; add input checks |
| `scripts/render_structure_reports.py` | Python | K/L / active / no | Render four-system QC sheets | structures/metrics -> PNG/report | none | Verify units/source captions |
| `scripts/reproduce_manna.py` | Python | J/K / support / no | Reproduce selected published biology plots | vendored public data -> tables/figure | none | Third-party reproduction, not project molecular evidence |
| `scripts/reproduce_plesa.py` | Python | J/K / support / no | Reproduce selected DHFR fitness summaries | vendored public data -> tables/figure | none | Third-party reproduction, not quantum evidence |
| `scripts/run_counterpoise.py` | Python | C / active / no | Compute cluster interaction proxy | XYZ/charges/CLI -> JSON | none | Validate fragment definitions, convergence, units, overwrite behavior |
| `scripts/run_h2_smoke.py` | Python | L / active / no | Small PySCF competency test | none -> smoke JSON | none | Not molecular evidence; label in output |
| `scripts/run_inquanto_vqe.py` | Python | E/G / support / no | Run small/local InQuanto workflow | CLI -> local result | none intended | Check whether example vs DHFR and prevent misleading labels |
| `scripts/run_local_h2.py` | Python | F/G / active / no | Compile/run QASM on offline H2-1LE emulator | QASM + shots -> JSON | none | `backend: H2-1LE` is ambiguous; central classification required |
| `scripts/run_local_pauli_energy.py` | Python | G / active / no | Original local Pauli-energy workflow | molecule/params -> energy/checkpoints | none | Compare with optimized runner; mark current/legacy and validate shots |
| `scripts/run_local_pauli_energy_optimized.py` | Python | F/G/J / active / no | Resumable optimized local emulator measurement | plan/checkpoints/CLI -> energy/resources | none | Large core file; add focused tests and central metadata |
| `scripts/run_pyscf.py` | Python | C / active / no | Run local HF/DFT calculation | XYZ/CLI -> JSON | none | Add input/system/unit validation |
| `scripts/run_scf_checkpoint.py` | Python | C/D / active / no | Save converged SCF for orbital analysis | cluster/charges -> checkpoint | none | Validate convergence before saving |
| `scripts/run_tests.sh` | shell | M/N / active / yes | Run Python tests | repository -> test result | none | Add compile/lint or defer to Make target consistently |
| `scripts/select_active_space.py` | Python | D / active / no | Run AVAS candidate selection | checkpoint/CLI -> JSON | none | Broad AVAS is excluded for production; label purpose |
| `scripts/setup.ps1` | PowerShell | O/N / active / no | Create Conda environment on Windows | environment.yml -> environment | package downloads | Windows not required by prompt; retain and document |
| `scripts/setup.sh` | shell | O/N / active / no | Create Conda environment | environment.yml -> environment | package downloads | Add existing-environment guidance |
| `scripts/submit_hosted_pauli_energy.py` | Python | H / disabled / no | Refuse unvalidated hosted molecular submission | checkpoints -> prerequisite message | none | Correctly disabled; remove unused misleading confirm flag or explain it |
| `scripts/summarize_active_space.py` | Python | D/J / active / no | Combine four active-space checks | result JSON -> CSV/report | none | Validate corrupt JSON/missing systems/checksums |
| `scripts/test_quantinuum_access.py` | Python | H/I/L / active / yes | Guarded Nexus Bell access test | CLI/env -> optional Nexus job | Nexus; can consume quota/HQC | Submission requires flags; centralize classification and classify code 14 |
| `scripts/validate_active_space.py` | Python | D/L / active / no | Run CASCI validation | checkpoint/selection -> JSON | none | Validate system allowlist and convergence |
| `scripts/validate_repository.py` | Python | L/M / active / no | Run safe repository integrity checks | tracked tree/results -> status | none | Add manifests/checksums/system/backend checks |
| `tests/test_endpoint.py` | Python | M / active / yes | Test D subtraction direction | function -> assertion | none | Expand invalid/missing cases |
| `tests/test_prepare_complexes.py` | Python | M / active / yes | Test coordinate-preserving ligand model | source PDB -> temp SDF | none | Optional chemistry skip is appropriate |
| `tests/test_publication_assets.py` | Python | M / active / yes | Test verified assets and Nexus guards | tree/mocks -> assertions | mocked/none | Expand central metadata, placeholder, CLI and checksum coverage |
| `visualization/interactive/viewer_config.json` | JSON | O / active / no | Configure static molecular viewer | relative paths -> viewer selection | none | Valid relative path; generated/support status should be stated |
| `visualization/molecular_assets_manifest.json` | JSON | S/L / generated / no | Record molecular rendering inputs/checksums | renderer inputs -> provenance | none | Validate checksums automatically |
| `visualization/pymol/render_binding_pocket.pml` | PyMOL | K/P / support / no | Render binding pocket | WT_TMP PDB -> interactive view | none | Add header and verified/unverified scope |
| `visualization/pymol/render_dhfr_tmp.pml` | PyMOL | K/P / support / no | Render complex overview | WT_TMP PDB -> interactive view | none | Add header and local-use instructions |
| `visualization/pymol/render_qm_region.pml` | PyMOL | K/P / support / no | View QM cluster separately | XYZ -> interactive view | none | Existing mapping warning is correct |

## Preserved third-party code

`data/raw/external/NatureCommunication2021_Manna/` contains upstream Python and
MATLAB plotting/analysis scripts. `data/raw/external/PlesaLab_DHFR/` contains
upstream R Markdown, Python, Make, and binary helper files. These files are class
S (generated/downloaded provenance), state `vendor`, are not project tests, and
are not called by maintained automation. Their inputs and outputs belong to the
cited upstream datasets. They use no project cloud backend. Action: preserve
byte-for-byte, retain source URL/commit/checksum records, and do not apply this
project's style changes to them.

## Initial scope conclusions

- Actively maintained remote-capable code is limited to Nexus diagnostics and
  the guarded Bell test. The molecular hosted-submission helper is deliberately
  non-operational.
- Only the saved `WT_TMP` ideal and finite-shot local-emulator result is verified.
  Files for the other systems establish planned/classical preparation work, not
  equivalent verified quantum results.
- Several scripts repeat system and backend strings. A small shared validation
  module is warranted; a large framework is not.
- Historical result files and third-party sources will be preserved. Corrections
  will add validation and documentation rather than rewriting provenance.
