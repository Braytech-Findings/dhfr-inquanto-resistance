# Sensitivity Analysis Plan

Current classical tables vary basis and NADPH embedding and contain additional
cluster/protonation/water artifacts. These are deterministic model-sensitivity
rows, not independent replicates. They may show whether a pilot contrast changes
sign, but cannot establish uncertainty or a binding free energy.

After active-space correspondence is decided, use a small prespecified panel:

1. Primary matched compact/N1-protonated/fixed-embedding geometry.
2. One neighboring chemically matched active space.
3. STO-3G for workflow comparison and one defensible larger classical basis.
4. Fixed finite-shot seeds: repeat one seed for reproducibility and use one
   different seed to demonstrate shot-noise variability.
5. One justified boundary or protonation sensitivity, keeping other choices
   fixed.

Record the reason, changed variable, fixed variables, effect, uncertainty, and
sign stability. Do not sweep settings until a favorable result appears. Quantum
sensitivity remains blocked by missing matched Hamiltonians/parameters.

