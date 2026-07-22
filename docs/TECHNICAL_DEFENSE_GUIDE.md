# Technical Defense Guide

The researcher should answer these independently rather than memorize generated
competition prose.

| Question | Source to study |
|---|---|
| Why DHFR, TMP, L28R, and 4′-DTMP? | `docs/scientific-background.md`, `configs/core_systems.yaml` |
| Why these four matched systems and what is the hypothesis? | `README.md`, `docs/COMPARISON_DEFINITIONS.md` |
| What is a Hamiltonian and active space? | `docs/GLOSSARY.md`, `docs/ACTIVE_SPACE_DECISION.md` |
| What are VQE, qubits, circuits, and shots? | `docs/BEGINNER_WALKTHROUGH.md` |
| Why 576 circuits and 100 shots? | `results/quantum/measurement_plans/WT_TMP_H2-1LE_100shots_plan.json` |
| What does the uncertainty mean? | `docs/STATISTICAL_ANALYSIS_PLAN.md` |
| What is the classical reference? | `configs/classical_protocol.yaml`, final-validation classical table |
| Why use an emulator? | `docs/BACKEND_CLASSIFICATION.md` |
| What do H2-1LE and H2-Emulator mean? | `docs/QUANTINUUM_RECOVERY.md` |
| Why is emulator evidence not hardware evidence? | `docs/EVIDENCE_LEVELS.md` |
| What failed in Nexus and what was fixed? | `docs/QUANTINUUM_RECOVERY.md`, `scripts/nexus_backend.py` |
| What did software automate and what needs researcher judgment? | `docs/CODE_WALKTHROUGH.md`, `docs/OPEN_DECISIONS.md` |
| What are the largest limitations? | `docs/RED_TEAM_REVIEW.md` |
| What would falsify the hypothesis? | A matched validated contrast near zero, opposite in sign, below uncertainty, or unstable across prespecified models; see sensitivity plan |
| What is the strongest claim and what is unproven? | `docs/WHAT_THE_PROJECT_PROVES.md` |
| What should happen next? | `artifacts/final_validation/final_validation_summary.md` |

