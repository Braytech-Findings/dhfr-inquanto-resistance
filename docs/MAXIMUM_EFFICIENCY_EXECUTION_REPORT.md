# Maximum-Efficiency Execution Report

OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED

- Largest verified circuit batch: 4 circuits in one execute job.
- Largest verified payload: four two-qubit pytket circuits.
- Shots per circuit: 10.
- Submission concurrency: one batch.
- Total new batch-pilot circuits: 4.
- Total new batch-pilot shots: 40.
- Batch-pilot jobs: 1 completed, 0 failed, 0 retried.
- Avoided duplicates: 1; retrieval resumed the persisted job ID.
- Queue/execution timing: not exposed separately by the returned status.
- Retrieval reliability: all four results retrieved in original order.
- Compiler configuration: optimisation level 0, selected to minimize pilot
  transformation rather than claim production optimality.
- Cost: Nexus returned `None`; numeric non-cash usage is unavailable.

Molecular efficiency remains unmeasured. The active Python environment lacks
InQuanto and PySCF, and the historical WT circuit/group mapping is retained in
an InQuanto checkpoint plus a nonportable 2.5-GB CSV. No scientifically valid
molecular batch can be assembled until those dependencies and mappings are
restored.

