# Master plan status audit

Audit date: 2026-07-15. Governing document: `DHFR_InQuanto_Master_Plan_2026-2027.pdf`, operating protocol v1.0.

| Area | Status | Evidence / remaining gate |
|---|---|---|
| Repository skeleton and environment | Complete | README, environment.yml, configs, scripts, tests, CI |
| Credentials exclusion | Complete | .gitignore; no credentials tracked |
| Core PDB acquisition/checksums | Complete | scripted download and `data/raw/pdbs/manifest.csv` (raw files ignored) |
| InQuanto/Nexus setup | Complete | InQuanto 6.1, inquanto-pyscf 2.2, authenticated qnexus 0.46; H2 emulators visible |
| Core four construction | Provisional pass | four restrained 50-step validation structures; Amber14SB/OpenFF Sage; retained waters |
| Automated structure QC | Provisional pass | correct ligand counts, residue 28 contacts, no <1.2 A clashes |
| Bioinformatics reproduction | Complete | three Manna headline results plus PlesaLab homolog-fitness and GOF summaries reproduced from pinned public data |
| Variant panel freeze | Complete | 10-member phenotype-only panel frozen in `configs/variant_panel.yaml`; evidence table and numbering convention recorded |
| Ligand identity evidence | Provisional pass | published identity, formula, charge, exact atom mapping and coordinate inheritance documented; human 2D sign-off remains |
| Pose sensitivity | Complete | inherited and ±30° local torsion candidates geometry-scored; primary and alternate frozen without energies |
| Protonation sensitivity | Complete | N1-protonated primary and neutral sensitivity structures generated and QC-passed |
| Structure visual reports | Complete | four one-page annotated PNG reports rendered and visually checked |
| Compact/expanded QM clusters | Provisional pass | focused, neutral, hydrated, and 4.5 Å tiers exported with link atoms, charges, even electron counts, fragments, and frozen NADPH embedding |
| Classical/AVAS/Hamiltonian/VQE | Not started | correctly gated behind Gate B |
| Nexus execution | Prohibited | no credits until ideal and finite-shot validation pass |
| Statistics/manuscript/archive | Not started | downstream gates |

## First 72 hours audit

- Day 1: complete (repository, structure, research question, core four, exclusions, initial commit).
- Day 2: complete (environment/imports, converged H2 RHF smoke test, Nexus/InQuanto access, credential exclusions).
- Day 3: substantially complete (scripted PDB download/checksums, exact external repository commits, deposited-structure audit, weekly log). Manual side-by-side inspection of the original PDB alternate conformers/NADPH remains an explicit human sign-off item.

## Immediate authority

Gate A passed. Gate B has an automated provisional pass; independent human sign-off of ligand depictions and structural reports remains explicitly required. Resume at Gate C with resource estimates and a minimal classical pilot only. Do not interpret the primary endpoint until the counterpoise interaction-energy definition and uncertainty plan are frozen.
