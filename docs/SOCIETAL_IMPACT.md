# Societal Impact

## The problem

**Simple explanation:** DHFR is a tiny machine that cells use to make building blocks for DNA. Some medicines slow that machine down. A mutation can change its shape, so a medicine may stop working as well.

**Technical explanation:** Dihydrofolate reductase supports folate metabolism and nucleotide biosynthesis. DHFR inhibitors are relevant to infectious disease and cancer, while target mutations can alter molecular recognition and contribute to resistance. Resistance is multiscale: molecular energetics alone cannot establish organism-level or clinical outcomes.

## What this project contributes

This repository makes a small DHFR–trimethoprim electronic-structure workflow inspectable and reproducible. It records structure provenance, classical preparation stages, active-space choices, a 12-qubit circuit workflow, finite-shot local-emulator evidence, uncertainty, and limitations. Its strongest current contribution is methodological transparency—not a treatment or resistance prediction.

## Who could benefit

Students can learn how biology, chemistry, and quantum circuits connect. Computational researchers can audit assumptions and reuse the guarded workflow. In the longer term, better validated molecular models could help drug-discovery teams prioritize laboratory experiments and reduce wasted computation, but that benefit has not been demonstrated here.

## What remains uncertain

Only one WT_TMP active-space quantum-energy case is verified. The minimal basis, finite QM cluster, active-space choice, missing matched mutant calculation, and absence of noisy hosted or physical-hardware chemistry results limit inference. An emulator result is not proof of quantum advantage, drug efficacy, or a biological mechanism.

## Research needed next

Future evidence would require matched wild-type/mutant systems, consistent interaction-energy definitions, basis and QM-region sensitivity analysis, validated orbital correspondence, emulator and hardware uncertainty studies, comparison with stronger classical references, and laboratory validation. Clinical conclusions would require a much larger chain of biological and medical evidence.

> This is exploratory computational research. It is not a clinical test, medical advice, or proof of a new treatment.
