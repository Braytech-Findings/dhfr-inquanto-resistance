# Nexus Batch Capability Audit

OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED

The installed qnexus API accepts a list of `CircuitRef` objects in both
`qnx.compile` and `qnx.start_execute_job`. Per-circuit shot counts may be passed
as a list. One H2-Emulator execute job containing four compiled two-qubit
circuits completed and returned four result references in submission order.

- SDK: qnexus installed in the recorded environment snapshot.
- Verified batch size: 4 circuits.
- Verified shots: 10 per circuit, 40 total.
- Backend: exact `H2-Emulator`.
- Project: `dhfr-h2-hardware`.
- Job: `4961b3c8-b875-4709-bc61-c45202b97b0e`.
- Result order and names: preserved by the persisted positional mapping.
- Reported cost: `None`.
- Retrieval: successful through an explicit retrieval-only resume path.
- Duplicate avoided: the initial process ended after persistence; retrieval
  resumed the same job rather than submitting another.

No larger batch, payload ceiling, concurrency limit, or 576-circuit submission
has been verified. Four circuits is therefore the largest supported batch proven
by this repository, not the provider maximum.

