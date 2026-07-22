# WT_TMP Partition Strategy Recovery

OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED

Repository source proves that InQuanto `PauliAveraging.build_from` created the
historical partition, but no saved enum records its graph-colouring method or
CX configuration. The strategy must not be inferred from the count of 576.

An exhaustive pairwise audit of the preserved groups found:

- 576 qubit-wise-commuting groups;
- 0 general-commuting-only groups;
- 0 invalid/noncommuting groups;
- 1,818 unique non-identity observables with complete Hamiltonian coverage.

Because every preserved group is QWC, regeneration uses
`PauliPartitionStrat.NonConflictingSets` separately on each existing group. It
does not globally repartition the Hamiltonian. `GraphColourMethod.Lazy` is used
only within a group that is already fixed; each group is required to yield one
verified measurement circuit. No entangling `CXConfigType` is needed for QWC
basis rotations.

The result is labeled `REGENERATED_PYTKET_MEASUREMENT_PROTOCOL`, not a
byte-for-byte historical export.
