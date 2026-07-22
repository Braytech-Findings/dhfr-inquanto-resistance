# Results status

`OBJECTIVE_COMPUTATIONAL_OUTPUT` — `RESEARCHER_INTERPRETATION_REQUIRED`

## WT_TMP

- Exact regenerated estimator: passed for all 1,818 mapped non-identity
  observables and all 576 measurement circuits.
- Reconstructed ideal energy: `-2587.912001526435 Ha`, differing from the
  protected value by `2.23e-11 Ha`.
- Local finite-shot convergence: three replicates at 100, 250, 500, 1,000,
  2,500, 5,000, and 10,000 shots per circuit.
- 10,000-shot local mean: `-2587.912246317905 Ha`.
- 10,000-shot combined standard error: `0.000373756124 Ha`.
- Local numerical remote-submission gate: passed.

## Nexus molecular pilot

The approved four-circuit H2-Emulator pilot used job
`e89da51e-bde9-4214-adda-6a08198f6b0a`. Nexus terminated it with provider
`TimeoutError`. It returned zero result objects and reported no monetary or HQC
cost. Simulation quota usage did not increase; compilation usage and database
storage did increase. No automatic resubmission occurred.

Remote molecular values are therefore **missing**, not zero. This operational
failure is not classified as a chemistry, Hamiltonian, VQE, or estimator
failure. The pilot is partial-estimator validation only and is not a molecular
energy or physical-hardware result.

## Other systems

`WT_4DTMP`, `L28R_TMP`, and `L28R_4DTMP` do not yet have complete matched,
validated quantum molecular estimators. No four-system quantum contrast is
reported.
