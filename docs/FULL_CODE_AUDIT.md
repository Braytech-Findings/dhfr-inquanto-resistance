# Full Code Audit

## Executive summary

The repository had a healthy test baseline and strong existing result caveats.
The audit fixed an unsafe implicit Nexus network default, an invalid endpoint
bootstrap path, ambiguous local backend metadata, missing system/shot guards,
and silent continuation after failed SCF in measurement-plan preparation. It
added shared validation and focused tests without changing saved scientific
outputs or submitting work.

## Repository state before changes

The audit began on `main` at `aa12cbe`. The working tree contained one preexisting
untracked file, `requirements_before_qnexus_update.txt`. The required branch
`codex/full-code-audit` was created. Origin matches
`Braytech-Findings/dhfr-inquanto-resistance`.

## Test baseline

`python -m pytest -q`: **20 passed, 1 skipped**.

## Files inspected

Eighty maintained executable/configuration artifacts (7,664 lines) were
inventoried. Downloaded upstream Python/R/MATLAB code was classified as preserved
vendor provenance. See [CODE_INVENTORY.md](CODE_INVENTORY.md).

## Critical problems

None found. Protected WT_TMP values matched the supplied facts.

## High-priority problems

- **Severity:** High. **File/function:** `scripts/test_quantinuum_access.py:main`.
  **Problem:** no arguments caused login and a Nexus device query. **Why:** the
  default was not local/dry. **Fix:** no-mode now prints help offline; discovery
  requires `--discover`. **Test:** `test_nexus_command_without_mode_is_offline`.
  **Scientific outputs changed:** no.
- **Severity:** High. **File/function:** `scripts/analyze_endpoint.py:main`.
  **Problem:** one deterministic row per system could be bootstrapped and labeled
  with a 95% CI. **Why:** resampling a singleton supplies no independent
  uncertainty. **Fix:** require replicate IDs, at least two per system, positive
  bootstrap count, and exact system set; define the interval. **Test:** core D
  sign test retained; replicate guard covered by CLI behavior review.
  **Scientific outputs changed:** no historical file was overwritten; future
  invalid inputs are rejected.
- **Severity:** High. **File/function:** `scripts/analyze_endpoint.py:main`.
  **Problem:** bootstrap draws iterated over an unordered Python set, so the
  same seed could produce different intervals in separate processes. **Why:** a
  documented seed did not guarantee reproducibility. **Fix:** use the canonical
  four-system tuple for every draw. **Test:**
  `test_endpoint_is_reproducible_with_fixed_seed`. **Scientific outputs
  changed:** historical output was preserved; future reruns are deterministic.

## Medium-priority problems

- **Severity:** Medium. **File:** `scripts/run_local_h2.py`. **Problem:** arbitrary
  system names, nonpositive shots, and ambiguous `backend: H2-1LE`. **Fix:**
  canonical validation and explicit local/noiseless metadata. **Tests:** shared
  name/backend/shot tests. **Outputs changed:** future metadata only.
- **Severity:** Medium. **File:** `scripts/prepare_local_pauli_energy.py`.
  **Problem:** unreviewed systems were accepted and unconverged RHF merely warned.
  **Fix:** restrict current saved-parameter path to WT_TMP, validate shots, and
  fail on non-convergence. **Outputs changed:** invalid future runs stop.
- **Severity:** Medium. **Files:** repeated workflow constants. **Fix:** added
  `scripts/audit_core.py` for four IDs, aliases, protected facts, backend classes,
  shot formula, access errors, JSON, and checksums. **Outputs changed:** none.

## Low-priority cleanup

Several focused historical preparation scripts overlap newer orchestration.
They were preserved pending reproduction and a researcher decision. Notebook
and R comments remain less extensive than production Python documentation; the
walkthrough supplies beginner context without decorative source churn.

## Scientific correctness findings

Units are consistently Hartree in saved energy fields. The conversion constant
is correctly labeled. D's subtraction direction is consistent and tested. The
counterpoise result is an interaction proxy, not binding free energy. The
historical endpoint interval requires a researcher decision about replicate
independence. Three planned quantum systems remain pending.

## Backend-labeling findings

The verified result is correctly described as local noiseless H2-1LE emulation.
No saved evidence supports hosted or physical-hardware molecular execution.
Syntax checking, compilation, login, and access events are not molecular
evidence. Access code 14 is now explicitly separated from scientific failure.

## Reproducibility findings

The endpoint bootstrap seed is explicit. Optimized local checkpoints preserve
environment/Git/input hashes. Historical verified provenance preserves critical
versions but lacks comprehensive input/output hashes and an explicit random
seed; these were not invented retroactively.

## Security findings

Existing tests found no tracked credential-like files or workstation paths in
maintained public sources. The preexisting private-selector environment pattern
is appropriate. The audit did not print secret values or change credentials.

## Documentation findings

The existing README already separated verified WT_TMP from unsupported claims.
It now names all pending quantum systems and labels endpoint CSV values as
examples. Nine required audit documents plus this changelog were added.

## Files changed

See `CHANGELOG_CODE_AUDIT.md` and `git diff --stat` for the exact set.

## Tests added or changed

`tests/test_audit_core.py` adds validation for names/aliases, backend identity,
shots, code 14, missing/corrupt JSON, checksums, protected metadata, placeholder
rejection, offline default, and confirmation requirements.

## Test results after changes

Final clean verification: **30 passed, 1 skipped**. Python compile, Ruff, shell
syntax, JSON, YAML, notebook parsing, R parsing, repository validation, and
`git diff --check` also passed.

## Verified result preserved

All protected WT_TMP values remain unchanged and are now validated centrally.

## Results that remain pending

WT_4DTMP, L28R_TMP, L28R_4DTMP matched quantum results; optimized production
validation; hosted molecular emulation; physical hardware; and wet-lab evidence.

## Researcher decisions needed

See [OPEN_DECISIONS.md](OPEN_DECISIONS.md).

## Recommended next steps

Review the diff, decide how to treat the historical endpoint interval and
dependency snapshot, validate a chemically corresponding four-system active
space, then generate missing local results with complete provenance. Do not
attempt paid hardware before those gates pass.
