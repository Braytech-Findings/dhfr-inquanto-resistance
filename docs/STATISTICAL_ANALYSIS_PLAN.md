# Statistical Analysis Plan

## Definitions

- A shot is one circuit measurement. Shots within one job estimate measurement
  probabilities; they are not independent molecular replicates.
- Standard deviation describes spread among observations.
- Standard error describes uncertainty in an estimator. The protected WT_TMP
  value `0.007647045141 Ha` is a finite-shot standard error.
- A confidence interval needs a stated sampling model. The approximate normal
  interval in saved plots is not an independent-replicate interval.
- A bootstrap interval is allowed only when each system has at least two genuine
  independent replicate-level units.
- Model sensitivity is variation across basis, embedding, geometry, active
  space, or related scientific choices; it is not random replicate noise.

For every matched comparison, report the number of independent replicates,
shots, estimator, seed, confidence level, and assumptions. Use seed 2026 for
repository bootstrap analysis unless a prespecified alternative is recorded.
Fixed-seed output must match across processes.

Current status: **INSUFFICIENT_INDEPENDENT_REPLICATES** for a four-system
confidence interval. WT_TMP has one saved finite-shot job. The other systems
have no matched quantum result. Do not manufacture an interval.

