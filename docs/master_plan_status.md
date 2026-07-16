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
| Classical interaction-energy screening | In progress | frozen counterpoise definition; all four HF compact-primary calculations converge at STO-3G, 3-21G, and def2-SVP with embedding and a STO-3G embedding sensitivity; PBE0/def2-SVP primary and structural sensitivities remain |
| Active-space screening | Candidate pass | one fixed ligand-frontier map passes four-system localization, singlet, and occupation-trace checks; each CASCI output is checksum-linked to its exact selection file |
| Hamiltonian/VQE | Not started | gated behind production-level orbital recheck and Hamiltonian export validation |
| Nexus execution | Prohibited | no credits until ideal and finite-shot validation pass |
| Statistics/manuscript/archive | Not started | downstream gates |

## First 72 hours audit

- Day 1: complete (repository, structure, research question, core four, exclusions, initial commit).
- Day 2: complete (environment/imports, converged H2 RHF smoke test, Nexus/InQuanto access, credential exclusions).
- Day 3: substantially complete (scripted PDB download/checksums, exact external repository commits, deposited-structure audit, weekly log). Manual side-by-side inspection of the original PDB alternate conformers/NADPH remains an explicit human sign-off item.

## Immediate authority

Gate A passed. Gate B has an automated provisional pass; independent human sign-off of ligand depictions and structural reports remains explicitly required. The counterpoise interaction-energy definition is frozen. Continue Gate C with the PBE0/def2-SVP primary calculation and prespecified structural sensitivities. The active-space candidate is authorized only for ideal-state Hamiltonian benchmarking after its production-level orbital recheck; emulator execution remains prohibited.
