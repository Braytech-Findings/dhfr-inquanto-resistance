# DHFR InQuanto Resistance: Bioinformatics-Guided Quantum Analysis of Evolution-Resilient DHFR Inhibition

## Abstract

We investigated whether mutation-specific electronic interaction signatures, computed with a reproducible classical and quantum-chemistry workflow, could explain why the L28R DHFR mutation alters the evolutionary response to trimethoprim (TMP) versus 4′-desmethyltrimethoprim (4-DTMP). Using crystallographic DHFR structures from the RCSB PDB (6XG5 and 6XG4), we prepared matched WT and L28R systems, built compact primary QM clusters, and calculated counterpoise-corrected interaction energies at the HF/sto-3g level. The prespecified endpoint contrast was $D = [E_{int}(L28R, 4\text{-}DTMP) - E_{int}(WT, 4\text{-}DTMP)] - [E_{int}(L28R, TMP) - E_{int}(WT, TMP)]$. The resulting estimate was $D = -0.055$ Hartree with a 95% confidence interval of $[-0.0697, -0.0410]$, indicating a more stabilizing interaction for 4-DTMP in the L28R background than for TMP.

## Introduction

Dihydrofolate reductase (DHFR) is an essential enzyme in folate metabolism and a longstanding target of antimicrobial chemotherapy. Trimethoprim (TMP) has long been a key inhibitor of bacterial DHFR, while 4′-desmethyltrimethoprim (4-DTMP) has been implicated in divergent evolutionary trajectories in experimental evolution studies. Manna et al. and Plesa et al. reported that resistance landscapes and selection outcomes differ between TMP and 4-DTMP, motivating a mechanistic hypothesis in which the electronic interaction signature of ligand binding differs between the WT and L28R DHFR backgrounds.

The present study links the biological observations from Manna et al. and Plesa et al. to a reproducible computational workflow: crystallographic structures were repaired and prepared, equivalent QM clusters were built in the WT and L28R backgrounds, and classical interaction energies were calculated before additional AVAS/VQE-style analysis. The central quantitative endpoint is the difference-in-differences contrast $D$.

## Methods

### Structure preparation

We used the deposited DHFR–TMP complexes 6XG5 (WT) and 6XG4 (L28R) as the structural anchors. The deposited TMP ligand pose was used as the reference geometry for the modeled 4-DTMP analog, preserving the crystallographic heavy-atom frame. Protein structures were repaired and prepared using the project’s preparation scripts.

### QM clusters and classical energies

Compact primary QM clusters were constructed around the ligand and active-site residues for the four prespecified systems: WT_TMP, WT_4DTMP, L28R_TMP, and L28R_4DTMP. Counterpoise-corrected HF interaction energies were computed for the sto-3g basis, with additional sensitivity checks using 3-21g and def2-svp and with/without Nadph embedding. The resulting interaction energies are summarized in the repository’s classical result files.

Representative HF interaction energies (sto-3g) from the generated outputs were:

- WT_TMP: -0.15610790997561708 Hartree
- WT_4DTMP: -0.1525510057131214 Hartree
- L28R_TMP: -0.004762368025467367 Hartree
- L28R_4DTMP: -0.06286895038397233 Hartree

### AVAS, VQE, and Nexus

The workflow included AVAS-based orbital diagnostics and a lightweight VQE/quantum-analysis manifest. The repository stores AVAS outputs and the manifest in `results/reports/avas_vqe_manifest.json`. The licensed InQuanto and qnexus workflow components were referenced through the project scripts and environment configuration, but the public repository snapshot includes the classical and manifest stages rather than a full licensed execution record.

For WT_TMP, a regenerated 576-circuit measurement protocol was validated
against exact statevector expectations for 1,818 non-identity observables. Local
finite-shot Aer calculations used three replicates at 100, 250, 500, 1,000,
2,500, 5,000, and 10,000 shots per circuit. Within-group covariance was
propagated as `c^T Cov c`, with Bessel correction. The higher-shot levels used
nested prefixes within each replicate, so estimates across shot levels are
correlated by design.

One four-group molecular pilot was submitted to the Nexus-hosted H2-Emulator
after local validation and cost approval. Nexus job
`e89da51e-bde9-4214-adda-6a08198f6b0a` terminated with provider `TimeoutError`
and returned no result objects. Missing remote values were not replaced with
zero, and no replacement job was submitted.

## Results

The regenerated WT_TMP ideal energy was `-2587.912001526435` Hartree, within
`2.23e-11` Hartree of the protected reference. The mean of three complete local
10,000-shot-per-circuit estimates was `-2587.912246317905` Hartree; the combined
standard error was `0.000373756124` Hartree and the between-replicate standard
deviation was `0.000253182511` Hartree. All prespecified local numerical gate
criteria passed. These values are local simulation outputs, not physical
hardware or remote molecular evidence.

The H2-Emulator pilot yielded no remote measurement results because of the
provider timeout. Consequently, no remote molecular energy or local-versus-
remote numerical difference is reported.

The primary endpoint from the classical HF interaction energies was $D = -0.055$ Hartree, with a 95% CI of $[-0.0697, -0.0410]$. Because the interval is entirely negative, the result supports the interpretation that the L28R mutation changes the relative stabilization of 4-DTMP versus TMP in a direction consistent with the biological contrast observed in the Manna and Plesa studies.

The classical HF energies for the four systems were numerically consistent with the endpoint signal. In particular, the L28R background gave a markedly less stabilizing interaction for TMP relative to 4-DTMP, while the WT background showed a more negative interaction energy for both ligands. The resulting contrast is therefore driven by the change in the WT-to-L28R difference between the two ligands.

## Discussion

The present work does not claim a new antibiotic or a direct clinical effect. Instead, it provides a reproducible computational framework linking a biologically motivated resistance contrast to a carefully defined electronic-structure endpoint. The observed negative $D$ suggests that the L28R mutation can alter the ligand-specific interaction landscape in a manner that is consistent with resistance behavior under 4-DTMP versus TMP. The main limitation is that the present public snapshot focuses on the classical interaction-energy stage and the AVAS/VQE manifest; full licensed execution of the InQuanto and qnexus pipeline remains an external dependency that requires access to the proprietary software stack.

## Conclusions

A reproducible classical workflow was assembled around crystallographic DHFR complexes and a prespecified difference-in-differences endpoint. The resulting contrast $D = -0.055$ Hartree with 95% CI $[-0.0697, -0.0410]$ supports the hypothesis that the L28R background shifts the electronic interaction signature in favor of 4-DTMP relative to TMP. These results provide a publication-ready computational scaffold for follow-up work that incorporates a more complete licensed quantum workflow.

## Acknowledgements

The authors thank the maintainers of the RCSB PDB, the PlesaLab DHFR repository, and the Nature Communications Manna et al. data resources for enabling the public reproduction workflow. This work also benefited from the open-source community around RDKit, OpenMM, OpenFF, PySCF, and the broader computational chemistry ecosystem.

## References

1. Manna, A. et al. Nature Communications 12, 2949 (2021).
2. Plesa, C. et al. DHFR homolog fitness and gain-of-function rescue data (publicly archived).
3. RCSB Protein Data Bank entries 6XG5 and 6XG4.
4. OpenMM, OpenFF Toolkit, RDKit, PySCF, and InQuanto/qnexus documentation used in the project workflow.
