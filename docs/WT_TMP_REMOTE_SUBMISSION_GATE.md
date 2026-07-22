# WT_TMP remote-submission gate

This gate applies only to the regenerated 576-circuit WT_TMP estimator. Passing
it does not authorize a Nexus submission and does not establish biological or
physical-hardware evidence.

Evidence labels: `OBJECTIVE_COMPUTATIONAL_OUTPUT`,
`RESEARCHER_INTERPRETATION_REQUIRED`, and `LOCAL_FINITE_SHOT_SIMULATION`.

## Numerical criteria

All criteria must pass:

1. Exact semantic validation covers 1,818 observables with no failures and the
   reconstructed ideal energy agrees within `1e-10` Hartree.
2. Exactly three valid replicates exist at 100, 250, 500, 1,000, 2,500, 5,000,
   and 10,000 shots per each of 576 circuits.
3. Every 10,000-shot replicate is within three of its propagated standard
   errors of the protected ideal energy.
4. The mean 10,000-shot energy is within three combined standard errors of the
   protected ideal.
5. The 10,000-shot between-replicate standard deviation is no more than twice
   the mean propagated uncertainty.
6. Mean propagated uncertainty decreases at every increasing shot level.
7. The spread of `uncertainty * sqrt(shots)` is at most 10%, testing the
   expected inverse-square-root convergence law.

Within each group, uncertainty uses the complete coefficient-weighted
`c^T Cov c` contribution with Bessel's finite-sample correction. Measurement
groups are treated as independent because they are sampled by separate
circuits. The 500-through-10,000-shot levels use nested prefixes of three
independent 10,000-shot Aer streams; estimates across shot levels are therefore
correlated by design, while the three replicates within each level are
independent.

The machine-readable decision is in
`artifacts/final_public_release/molecular/WT_TMP/local_finite_shot_summary.json`.

## Authorization gate

Even when every numerical criterion passes, remote submission remains disabled
until the exact workload, expected Nexus quota or monetary cost, backend,
project, and batch plan are shown to the researcher and explicitly approved.
An unavailable cost estimate is not equivalent to zero cost. No personal cash
charge or paid overage may be accepted.
