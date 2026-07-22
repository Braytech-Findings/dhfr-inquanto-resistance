# Credit Execution Plan

## Current gate

`NEEDS_RESEARCHER_BILLING_DECISION`

Read-only discovery on 2026-07-22 authenticated and reported that compilation
and simulation quota guards were true, but the quota table said `No quota set
for user`. No project was selected and Nexus used its default group. This is
not an allocated non-cash balance and does not establish that overage or cash
billing is impossible. No job may be submitted until the researcher supplies
the exact authorized project and user group and verifies, in Nexus billing or
allocation settings, a numeric non-cash balance and that paid overage is off.

## Spending order after the gate is cleared

1. Ten-shot Bell smoke test on exact `H2-Emulator`.
2. Retrieve and validate that same job; never replace it during retrieval.
3. Resolve the active-space decision and complete all four molecular QASMs.
4. Submit one conservative WT_TMP pilot.
5. Complete one valid result for each remaining system.
6. Add independent jobs only where uncertainty analysis justifies them.
7. Add shot or backend sensitivity only when it can change the evidence.

Before every submission, record balance, estimated cost, project, group,
backend, purpose, and whether cash overage is disabled. Stop if any is unknown.

