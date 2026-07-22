# Claim Audit

This is an internal technical audit, not submission prose.

| Claim family | Status | Evidence and narrower accurate statement |
|---|---|---|
| “The project proves/predicts resistance” | Unsupported | No matched four-system quantum result or biological validation. Accurate: the repository prepares a computational framework for studying a model contrast. |
| “Quantum advantage/speedup” | Unsupported | No classical resource crossover or hardware comparison. Accurate: one active-space workflow was demonstrated locally. |
| “Hardware result/validation” | Unsupported and misleading if applied to WT_TMP | WT_TMP used H2-1LE locally. No completed Nexus molecular run exists. |
| “Experimental/clinical result” | Unsupported | All project-generated energy evidence is computational. |
| “Superior ligand/drug efficacy” | Unsupported | Cluster energies do not establish efficacy, binding free energy, or clinical response. |
| “Matched four-system quantum comparison” | Pending | Three Hamiltonians/parameter sets/results are missing. |
| “Reproducible local WT_TMP benchmark” | Supported with limitations | Protected values and checksums exist; full historical optimizer/seed/commit provenance is incomplete. |
| “Production ready” | Unsupported | Active-space correspondence and environment locking remain open. |

Repository caveat language is generally disciplined. Any future promotional
statement must be checked against `artifacts/final_validation/evidence_matrix.csv`.

Exact search findings were cautionary rather than unsupported affirmative
claims. For example, `README.md:15` says the project “does not claim a
drug-resistance prediction or a hardware result,” and `README.md:83` says it
does not claim quantum advantage. `manuscript/main.tex:5` explicitly says the
calculation is not a resistance, clinical, or physical-hardware result. These
statements are supported and should remain. The old README smoke-test command
used H2-1SC under `--nexus-emulator`; the final pass corrected it to an offline
H2-Emulator dry-run because the emulator mode now correctly rejects syntax
checkers.
