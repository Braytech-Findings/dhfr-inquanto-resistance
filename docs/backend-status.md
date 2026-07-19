# Backend status and evidence boundary

| Environment | Purpose | Project status | Evidence | Scientific interpretation |
|---|---|---|---|---|
| PySCF classical workflow | Mean-field/electronic-structure setup | Used locally | `results/quantum/WT_TMP_saved_params_exact.json` (local only) | Supports the active-space workflow; not a binding free energy. |
| Ideal saved-parameter VQE | Deterministic reference expectation | Completed locally | `results/publication/data/verified_summary.json` | Reference for the fixed ansatz and Hamiltonian. |
| H2-1LE local noiseless emulator | Finite-shot Pauli measurements | Completed locally | `results/publication/data/verified_quantum_provenance.json` | A 57,600-shot local emulator result, not a hosted job or hardware run. |
| Aer/QASM artifacts | Circuit development/export | Generated where files exist | `data/processed/` is local/ignored | A generated circuit is not an executed molecular result. |
| H2-1SC syntax checker | Access/circuit validation | Authorized Bell submission attempted 2026-07-19; ended in access/entitlement error | `scripts/test_quantinuum_access.py` | No counts were retrieved. Any successful syntax-checker counts would be artificial and scientifically unusable. |
| Nexus-hosted emulator | Remote execution validation | Not yet completed | `docs/QUANTINUUM_ACCESS_TROUBLESHOOTING.md` | Requires simulation quota and entitlement. |
| Quantinuum hardware | Future selected validation | Not yet completed | None | Requires explicit confirmation, cost ceiling, entitlement, and a validated workflow. |

“Online” or visible in Nexus describes service availability, not a user’s quota, user-group membership, or entitlement.
