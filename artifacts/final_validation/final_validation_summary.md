# Final Validation Summary

## Repository and branch

Repository: `Braytech-Findings/dhfr-inquanto-resistance`  
Branch: `codex/final-research-validation`, created from audit commit `9b957e1`.

## Environment

Final shell: Python 3.13.5, ARM64 macOS. Declared/historical target: Python
3.11. `pip check` reports a Qiskit conflict in an unrelated installed package;
therefore the current base shell is not a production lock environment.

## Prior audit verification

Bootstrap replicate guards, cross-process seed determinism, approved system
names, shot arithmetic, protected WT_TMP metadata, offline no-argument Nexus
behavior, exact backend routing, and non-resubmitting retrieval all pass
behavioral tests.

## Tests before changes

`40 passed, 1 skipped` in 2.64 seconds.

## Tests after changes

`48 passed, 1 skipped` in 3.98 seconds. Repository validation independently
reran the suite with `48 passed, 1 skipped`. Ruff lint/format, compilation,
shell syntax, configuration parsing, and notebook execution passed. An
unconfigured whole-tree MyPy attempt did not pass; see the failure log.

## Files inspected

The maintained logic inventory covers 80 earlier files plus the final-pass
configuration, generator, orchestration, resolver, QASM runner, and tests.
Vendored sources remain third-party provenance.

## Files changed

See the final branch commits and `git diff --stat`.

## Four-system status

All four compact molecular inputs, pilot HF/STO-3G interaction artifacts,
candidate active-space validations, and orbital-character figures exist. Only
WT_TMP has the saved Hamiltonian, parameters, QASM, compilation, ideal result,
finite-shot result, and uncertainty. The other systems remain missing, not zero.

## Molecular input status

Four XYZ cluster files are readable, have recorded atom counts/charges, finite
Angstrom coordinates, and no duplicate atoms closer than 0.1 Å. This is basic
file/geometry validation, not a proof of biological equivalence.

## Classical reference status

Pilot counterpoise-corrected HF/STO-3G cluster interaction proxies exist for all
four systems. They are not production binding free energies. A PBE0/def2-SVP
primary result is incomplete across the matched panel.

## Hamiltonian status

Only WT_TMP has a serialized 12-qubit, 1,819-term Hamiltonian. Its saved
coefficients pass the Hermiticity check. One-/two-body source counts and the
exact fermion-to-qubit mapping were not recorded in the compact artifact.

## VQE status

Only WT_TMP has 117 saved UCCSD parameters. The exact objective is preserved,
but optimizer, starting point, iteration history, seed, and exact Git commit are
incomplete. No parameters were copied between systems.

## Local ideal simulation status

WT_TMP saved ideal result verified. Other systems: not started.

## Local finite-shot status

WT_TMP protected result verified: 576 circuits × 100 shots = 57,600 local
H2-1LE shots. Other systems: not started. The 12.7-hour historical run was not
repeated without a resolved production active space.

## Quantinuum recovery status

Exact resolver and tests prove `H2-Emulator` remains unchanged and compile and
execute use one immutable configuration. No fallback exists. Access code 14 is
`access_or_entitlement`, not scientific failure.

## Live backend-discovery status

Read-only live discovery completed on 2026-07-22. The sanitized catalog lists
`H1-Emulator` and `H2-Emulator`. Authentication succeeded, but no project or
explicit user group was selected and entitlement remains unverified. The quota
API reported `No quota set for user`, which is not a verified non-cash balance.
Discovery itself created no job and consumed no credits. A later explicitly
authorized execution pass selected the matching project and ran two smoke tests.

## Dry-run status

H2-Emulator ten-shot dry-run and compile-only metadata paths passed offline and
created no job.

## Remote submission status

Two remote Bell smoke-test jobs were submitted and retrieved under
`dhfr-h2-hardware`: H2 job `3d554c78-945d-4c66-b6cf-7f622c02186c` and H1 job
`250413ef-f0f1-4acc-b527-2d96a9c82ab9`. Both completed and are labeled
`SMOKE_TEST_ONLY`. No molecular job or paid call occurred. Nexus reported cost
as `None`; numeric allocation use is unknown. Molecular execution stopped at
`STOPPED_BY_SCIENTIFIC_BLOCKER` because three quantum chains are missing and
matched active-space correspondence is unresolved.

## Reproducibility status

Fixed-seed endpoint output matches across processes. Protected checksums pass.
Full numerical four-system reproducibility is blocked by missing artifacts and
the unresolved active space.

## Sensitivity status

Classical pilot/model-sensitivity rows exist. Matched quantum sensitivity is not
possible yet.

## Statistical status

WT_TMP uncertainty is a finite-shot standard error from one job. There are
insufficient independent replicates for a matched confidence interval.

## Figures and tables

Existing WT_TMP figures have checksums and source paths. A categorical
four-system evidence-status figure was added; it does not plot missing energies
as zero. Final-validation tables define their columns and units in headers.

## Evidence levels

WT_TMP: Level 2. Other systems: Level 1. No Level 3–6 evidence exists.

## Strongest supported claim

**DRAFT TECHNICAL INTERPRETATION FOR RESEARCHER REVIEW:** one WT_TMP active-space
UCCSD workflow produced a locally reproducible saved ideal expectation and
finite-shot local-emulator estimate under documented model limitations.

## Claims not supported

Matched four-system quantum effect, resistance prediction, ligand superiority,
binding free energy, clinical relevance, hosted molecular result, hardware
validation, quantum advantage, or independent experimental confirmation.

## Critical limitations

Unresolved matched orbital identity; three missing Hamiltonians/parameter sets;
one finite-shot job without seed/independent replicates; minimal basis and
truncated static clusters; incomplete optimizer provenance; current environment
drift; no live entitlement proof.

## Researcher decisions needed

Production active-space correspondence, historical dependency snapshot
retention, endpoint biological meaning, and whether/when to authorize live Nexus
discovery after reviewing privacy and organizational context.

## Exact next commands

```bash
conda env create -f environment.yml
conda activate dhfr-qc
python -m pip check
python scripts/validate_repository.py
python scripts/four_system_workflow.py --prepare
python scripts/build_final_validation.py
```

See `docs/QUANTINUUM_RECOVERY.md` for separately gated discovery and smoke-test
commands.

## Remote-job confirmation

Exactly two authorized smoke-test jobs were submitted and retrieved. No
molecular job was submitted.

## Confirmation that nothing was pushed

Confirmed at package creation time. The final Git status is reported after
local commits.
