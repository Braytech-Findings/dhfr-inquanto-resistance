# Quantinuum All-Backend Plan

The screenshot-derived historical catalog is broader than the live API result.
Live read-only discovery on 2026-07-22 returned only `H1-Emulator` and
`H2-Emulator` through the maintained target filter. Neither was submitted to.

The execution order is discovery, project/group verification, billing gate,
offline compile-only, offline dry-run, H2 smoke test, retrieval, WT_TMP pilot,
then four-system work. H1 is a cross-generation sensitivity target only when
the identical model fits. Aer, Qulacs, local LE targets, Helios, and Selene
require separate capability discovery; they must not be inferred from the
filtered Nexus list or treated as equivalent endpoints.

Production molecular execution is blocked by unresolved matched active-space
selection and three missing QASM/Hamiltonian/VQE chains. Backend exploration
must not bypass those scientific gates.

