# Comparison Definitions

All quantities below must use comparable interaction-energy definitions,
geometries, basis, active space, charge, and units. Current classical values are
pilot/model-sensitivity proxies; current quantum total energies do not form a
four-system matched set.

| Comparison | Formula | Meaning of sign |
|---|---|---|
| TMP mutation effect | `L28R_TMP - WT_TMP` | Positive: L28R is less stabilizing under a consistently defined interaction proxy; negative: more stabilizing |
| 4′-DTMP mutation effect | `L28R_4DTMP - WT_4DTMP` | Same convention for 4′-DTMP |
| WT ligand effect | `WT_4DTMP - WT_TMP` | Positive: 4′-DTMP is less stabilizing than TMP in WT; negative: more stabilizing |
| L28R ligand effect | `L28R_4DTMP - L28R_TMP` | Same convention in L28R |
| Difference-in-differences | `(L28R_4DTMP - L28R_TMP) - (WT_4DTMP - WT_TMP)` | Positive: the 4′-DTMP-minus-TMP change is more positive in L28R; negative: more negative; zero: no interaction on this model scale |

Units are Hartree unless explicitly converted. The difference-in-differences is
algebraically identical to the mutation-effect form implemented in
`analyze_endpoint.py`. Whether it is the final biological resistance metric is
**NEEDS_RESEARCHER_DECISION**. It omits kinetics, protein flexibility, solvent
free energy, entropy, concentration, fitness, and clinical response.

Uncertainty propagation is valid only when covariance and independent units are
known. That condition is not met for a matched quantum contrast today.

