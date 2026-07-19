# Quantinuum Nexus support template

Subject: Minimal Bell-circuit execution rejected after successful authentication

Hello Quantinuum support,

Authentication and project discovery succeed in a local `qnexus` workflow, but execution of a minimal two-qubit Bell circuit on the selected target is rejected at the authorization stage. The circuit is a guarded access test only; it is not a molecular workload or hardware-energy claim.

Please confirm:

1. Whether the authenticated user belongs to a Nexus user group with execution entitlement for the selected project and target.
2. Whether the selected project has syntax-checker, emulator, or hardware allocation as appropriate.
3. Whether a project, user group, or region must be supplied differently through `qnexus 0.46.0`.
4. Whether a minimal H2-1SC or hosted-emulator Bell test is permitted for this account.

The repository can provide a private sanitized diagnostic report containing package versions and a stage-level error classification. It intentionally excludes tokens, cookies, project IDs, job IDs, personal paths, and browser-session details.
