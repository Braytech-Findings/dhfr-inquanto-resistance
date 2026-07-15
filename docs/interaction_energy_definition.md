# Frozen electronic interaction-energy proxy

Frozen 2026-07-15, before any production-basis or quantum-algorithm result.

For ligand fragment A and capped protein environment B at the frozen complex geometry:

`E_int^CP(q) = E_AB^(AB basis,q) - E_A^(AB basis,q) - E_B^(AB basis,q)`

All three terms use the full cluster basis; atoms absent from a fragment are represented by ghost basis functions. The same frozen NADPH point-charge field `q` is applied to all terms. This is the Boys–Bernardi counterpoise-corrected electronic cluster interaction proxy. It includes nonadditive polarization in the external cofactor field but no thermal, entropic, bulk-solvent, standard-state, or full-protein free-energy contribution.

The primary structural model is the N1-protonated compact cluster with residues 27, 28, 31, and 94, explicit peptide-boundary hydrogen link atoms, no explicit water, and deposited-coordinate CHARMM36 NADPH embedding. The exact charge of each whole cluster and both fragments is stored in the cluster JSON manifest and checked for closed-shell electron parity.

STO-3G/HF calculations are labeled pipeline pilots only. Primary interpretation requires the frozen PBE0/def2-SVP calculation plus the prespecified method, basis, cluster, protonation, water, and embedding sensitivities in `configs/classical_protocol.yaml`.
