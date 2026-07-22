# Open Decisions

## NEEDS_RESEARCHER_DECISION: historical endpoint interval

`results/tables/endpoint.json` and classical plotting inputs predate the new
independent-replicate guard. Decide whether the source rows represent genuine
independent geometries/calculations. If they do, document that design and
replicate IDs. If they do not, retire the bootstrap interval from scientific
interpretation and report deterministic sensitivity ranges instead. The audit
preserved the historical file.

## NEEDS_RESEARCHER_DECISION: active-space production definition

The verified WT_TMP benchmark used contiguous orbitals for reproducibility.
Current configuration contains system-specific ligand-character candidates.
Choose and validate one chemically corresponding production active space for
all four systems before matched quantum comparisons. Do not overwrite the
historical WT_TMP benchmark.

## NEEDS_RESEARCHER_DECISION: untracked dependency snapshot

`requirements_before_qnexus_update.txt` existed untracked before the audit.
Decide whether it should be committed as historical environment provenance or
kept outside Git. The audit did not alter it.

## NEEDS_RESEARCHER_DECISION: legacy preparation entry points

`01_fix_ligand_parameterization.py`, `prepare_structure.py`, `extract_ligand.py`,
and `model_4dtmp.py` overlap parts of the newer four-system preparation flow.
They were preserved because each contains historical or focused functionality.
After reproducing old artifacts, decide whether to mark them formally
deprecated.

## Pending evidence

No verified quantum energies exist for WT_4DTMP, L28R_TMP, or L28R_4DTMP. No
completed molecular Nexus or physical-hardware result exists. No code decision
can replace those missing runs and their provenance.

