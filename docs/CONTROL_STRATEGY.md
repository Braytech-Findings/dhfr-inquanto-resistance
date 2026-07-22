# Control Strategy

Controls already present or run locally include:

- Protected WT_TMP exact-versus-finite-shot comparison.
- PySCF H2 smoke calculation, which tests software rather than DHFR science.
- Bell circuit dry-run/compile-only tests, which test Nexus routing only.
- Invalid system, alias, corrupt JSON, missing-file, placeholder, and shot-total
  tests.
- Cross-process fixed-seed endpoint repeat.
- Mocked access-code-14, no-confirmation, no-network, and retrieval-without-
  resubmission tests.
- Hamiltonian coefficient-imaginary-part inspection for saved WT_TMP
  Hermiticity.

Still needed are an independently regenerated WT_TMP objective, exact
diagonalization for the chosen production active space, QASM semantic round
trip for all four systems, and at least one defensible active-space sensitivity.
A Bell state is never molecular evidence.

