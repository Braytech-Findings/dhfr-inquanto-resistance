# Nexus Maximum-Shot Semantics

OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED

The installed qnexus signature accepts either one integer or a list of per-item
shot counts. The previous four-circuit pilot passed `[10, 10, 10, 10]` and each
returned result contained exactly ten shots. This proves per-circuit list
semantics at ten shots.

A later explicitly authorized backend-validation job passed
`[10000, 10000, 10000, 10000]`. Nexus returned exactly 10,000 shots for each
result and 40,000 combined shots. Therefore list-form `n_shots` is applied per
circuit, not divided across the batch, at this tested size.

- Backend: exact `H2-Emulator`.
- Job: `333914f2-7128-49b9-a03d-7cc1e6261870`.
- Final state: `COMPLETED` and retrieved.
- Circuits: four, in submission order.
- Truncation: none.
- Reported cost: `None`.

This proves 10,000 shots per circuit for a four-circuit batch. It does not prove
the maximum circuit count or authorize treating toy-circuit output as molecular
evidence.
