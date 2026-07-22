# Quantinuum Execution Log

## 2026-07-22

- Read-only discovery: completed.
- Visible maintained targets: `H1-Emulator`, `H2-Emulator`.
- Project selected: no.
- User group selected: no; Nexus default group reported.
- Entitlement verified: no.
- Compilation/simulation quota guards: true.
- Numeric allocated credit balance: unavailable; API reported no user quota.
- Offline H2 compile-only: passed, no Nexus import or job.
- Offline H2 dry-run: passed, no Nexus import or job.
- Selected project: `dhfr-h2-hardware` (the unique repository-matching live
  project).
- Selected group: existing Nexus default group; qnexus exposes no documented
  group-list API.
- H2-Emulator smoke job `3d554c78-945d-4c66-b6cf-7f622c02186c`:
  `COMPLETED`, retrieved, counts 00=5 and 11=5.
- H1-Emulator smoke job `250413ef-f0f1-4acc-b527-2d96a9c82ab9`:
  `COMPLETED`, retrieved, counts 00=4 and 11=6.
- Both results are `SMOKE_TEST_ONLY`, not molecular evidence.
- Reported job cost: unavailable (`None`); numeric allocation use remains
  unknown and no cash confirmation was presented or accepted.
- Molecular jobs: none.
- H2 multi-circuit pilot job `4961b3c8-b875-4709-bc61-c45202b97b0e`:
  `COMPLETED`, four circuits and 40 total shots retrieved in submission order.
- Largest verified Nexus batch: four circuits in one execute job.
- H2 maximum-shot backend-validation job
  `333914f2-7128-49b9-a03d-7cc1e6261870`: `COMPLETED`, four circuits returned
  10,000 shots each, 40,000 combined. This is not molecular evidence.
- Stopping reason: `STOPPED_BY_SCIENTIFIC_BLOCKER`; three systems lack their
  Hamiltonian/VQE/QASM chains, matched orbital correspondence is unresolved,
  and the active environment lacks InQuanto and PySCF. The portable 576-circuit
  WT measurement map cannot be safely extracted without the original stack.
