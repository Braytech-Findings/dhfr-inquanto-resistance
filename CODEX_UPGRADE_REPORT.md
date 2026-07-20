# Codex Upgrade Report

Verified on 2026-07-20 without provider credentials or remote submissions.

## Files created

- Consolidated installation, running, troubleshooting, societal-impact, and beginner-walkthrough documentation
- Credit-safe `scripts/validate_repository.py`
- macOS/Linux and PowerShell setup helpers, plus test and figure shell helpers

## Files modified

- `README.md`: expanded navigation and an evidence-bounded societal-impact section
- `Makefile`: added safe setup and validation targets
- Publication PDF assets were regenerated from committed data by the existing figure builder

## Figures

`python scripts/build_publication_assets.py` completed successfully. Existing publication PNG/PDF figures, source tables, and manifests remain the authoritative assets; no scientific values were invented.

## Verification

- `python -m pytest -q`: 20 passed, 1 optional molecular-stack test skipped
- Python compilation: passed
- Configured Ruff checks: passed
- `python scripts/build_publication_assets.py`: passed
- `python scripts/validate_repository.py`: passed
- No Nexus, emulator-quota, or physical-QPU job was submitted

The shell runtime was Python 3.13.5. The reproducible Conda environment remains pinned to Python 3.11 and CI tests Python 3.11; these environments are reported separately.

## Problems found and fixed

- Missing consolidated cross-platform setup and exact environment command matrix
- Missing standalone societal-impact, troubleshooting, and beginner documents
- No single public validation command
- The first validator draft looked for shot count in the wrong summary schema; it was corrected to cross-check the provenance equation `576 × 100 = 57,600`

## Remaining limitations

- Only the WT_TMP quantum-energy case is verified.
- No matched mutant quantum result, noisy hosted chemistry result, or physical-hardware chemistry result exists.
- Licensed InQuanto components cannot be installed or exercised in public CI.
- The minimal basis, finite cluster, and active-space selection limit biological inference.

## Recommended next steps

Complete the prespecified matched systems and sensitivity analyses before biological interpretation. Review all remote plans and quota/cost estimates before any explicitly authorized Nexus submission.
