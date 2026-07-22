# Scientific Validation

## Systems and result status

The canonical IDs are `WT_TMP`, `WT_4DTMP`, `L28R_TMP`, and `L28R_4DTMP`.
Only WT_TMP has a verified quantum benchmark. The other three have preparation
and classical artifacts but no equivalent verified quantum energy.

## Energies and units

Saved electronic energies and interaction proxies use Hartree (`Ha`). The
publication builder uses `1 Ha = 627.509474 kcal/mol`. It does not relabel one
unit as another. Total energies from systems with unequal atom counts must not
be compared as though they were binding or interaction energies.

The frozen counterpoise proxy is
`E(complex) - E(ligand in complex basis) - E(environment in complex basis)`.
It is not a binding free energy.

## Directions of comparisons

The repository defines the mutation effect at each ligand as L28R minus WT.
Its difference-in-differences endpoint is:

`D = (L28R_4DTMP - WT_4DTMP) - (L28R_TMP - WT_TMP)`.

This is algebraically equal to
`(L28R_4DTMP - L28R_TMP) - (WT_4DTMP - WT_TMP)`. The implementation and test
fix the sign. The scientific interpretation still depends on using the same
validated interaction-energy definition for all four systems.

## Shots, uncertainty, and replicates

`total shots = measurement circuits × shots per circuit × job replicates`.
For verified WT_TMP, `576 × 100 × 1 = 57,600`.

The reported `0.007647045141 Ha` quantity is a **standard error** from finite
shots. The approximate 95% interval in publication assets is `estimate ± 1.96
× standard error`; it is not a hardware confidence statement. Shots inside one
job are not independent scientific replicates. `analyze_endpoint.py` now
requires at least two labeled independent replicates per system before it will
bootstrap a percentile interval.

## Protected verified benchmark

- Ideal saved-parameter VQE: `-2587.912001526413 Ha`
- Finite-shot estimate: `-2587.917118821447 Ha`
- Standard error: `0.007647045141 Ha`
- Backend: Quantinuum H2-1LE local noiseless emulator
- Circuits/shots: 576 circuits, 100 shots each, 57,600 total

Tests reject changed protected fields, placeholder flags, hardware labels, and
inconsistent shot arithmetic. Historical result files were not recalculated.

## Provenance assessment

The saved provenance records system, date, basis, active-space description,
software versions, backend class, circuit/shot counts, energies, and
limitations. Optimized runner checkpoints additionally record Git state,
platform, hashes, circuit resources, and timing. Missing from the historical
verified record are comprehensive input/output checksums and an explicit random
seed. Those cannot be invented after the fact.

