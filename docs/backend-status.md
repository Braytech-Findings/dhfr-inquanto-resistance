# Backend status and evidence boundary

| Environment | Purpose | Project status | Evidence | Scientific interpretation |
|---|---|---|---|---|
| PySCF classical workflow | Mean-field/electronic-structure setup | Used locally | `results/quantum/WT_TMP_saved_params_exact.json` (local only) | Supports the active-space workflow; not a binding free energy. |
| Ideal saved-parameter VQE | Deterministic reference expectation | Completed locally | `results/publication/data/verified_summary.json` | Reference for the fixed ansatz and Hamiltonian. |
| `H2-1LE` local noiseless emulator | Finite-shot Pauli measurements | Completed locally | `results/publication/data/verified_quantum_provenance.json` | A 57,600-shot local emulator result, not a Nexus-hosted job or hardware run. |
| `H2-Emulator` Nexus-hosted emulator | Primary remote access and noisy-emulation target | SCSU access confirmed by Quantinuum support on 2026-07-21; project Bell test not yet recorded as completed | `scripts/test_quantinuum_access.py` and `docs/QUANTINUUM_ACCESS_TROUBLESHOOTING.md` | Nexus-hosted, costed in simulation seconds, and not physical hardware. |
| `H1-Emulator` Nexus-hosted emulator | Supported fallback remote target | SCSU access confirmed by Quantinuum support on 2026-07-21; project Bell test not yet recorded as completed | `scripts/test_quantinuum_access.py` | Nexus-hosted, costed in simulation seconds, and not physical hardware. |
| Hardware-tier emulators ending in `E` | Machine-instance emulation | Not available through the current SCSU organization access | Quantinuum support clarification dated 2026-07-21 | These are distinct from Nexus-hosted emulators and are costed in HQCs. They are intentionally rejected by the guarded script. |
| Quantinuum physical hardware | Future selected validation | Not yet completed | None | Requires separate entitlement, explicit cost review, and a validated molecular-energy workflow. |

Endpoint suffixes matter. `H2-Emulator` and `H1-Emulator` are Nexus-hosted endpoints. Hardware-tier emulator names ending in `E` are a different product tier. A device being visible or online does not by itself prove execution entitlement.
