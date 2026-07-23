# Quantinuum Nexus Recovery

## What failed

Earlier hosted attempts authenticated successfully but did not establish usable
execution entitlement. The saved record says H2-Emulator compilation was
possible while execution lacked simulation quota, and an H2-1E attempt returned
access code 14. A later H2-1SC Bell job also ended in an access/entitlement
failure. None is a chemistry, Hamiltonian, VQE, or DHFR result.

Login still worked because identity authentication is separate from project
membership, user-group selection, backend entitlement, and quota. A visible or
online backend is discoverable; it is not necessarily executable by the selected
organization context.

## Endpoint-name differences

- `H2-Emulator` and `H1-Emulator` are Nexus-hosted emulators. They use hosted
  simulation allocation and are not physical hardware.
- `H2-1E` and `H2-2E` are Quantinuum-hosted physical-hardware endpoints.
- `H2-1SC` and `H2-2SC` are syntax checkers whose artificial output is not
  molecular evidence.
- `H2-1LE` is the repository's local noiseless emulator. It is neither Nexus
  hosted nor physical hardware.

No alias or fallback connects these names. In particular, `H2-Emulator` must
never become `H2-1E` or silently fall back to `H1-Emulator`.

## Exact defect found and correction

The old Bell helper passed the raw CLI string to both Nexus configuration calls,
so no literal `H2-Emulator` to `H2-1E` rewrite was found. However, it classified
the name by uppercasing it while later comparing the mixed-case value against
uppercase sets. It also let `--nexus-emulator` accept syntax checker and hardware
names, defaulted that mode's backend to the old `H2-1SC` endpoint, kept retrieval
inside the just-submitted-job path, and had no immutable compile/execute
resolution record or four-system state.

`scripts/nexus_backend.py` now resolves only exact catalog names. Its immutable
record contains requested/resolved names, hosting and backend types, local/remote
location, sanitized project/group selection, credit risk, and entitlement state.
`require_nexus_emulator` rejects syntax checkers, hardware, local targets, and
unknown values. Both compilation and execution receive the same configuration
object constructed from `resolution.resolved_backend`. No fallback exists.

Backend trace for the smoke test:

1. `--backend H2-Emulator` enters `argparse` unchanged.
2. `hosted_bell()` calls `resolve_backend(args.backend, ...)`.
3. The resolver returns requested and resolved values both equal to
   `H2-Emulator`.
4. `require_nexus_emulator()` confirms `nexus_hosted` plus `emulator`.
5. `QuantinuumConfig(device_name=resolution.resolved_backend)` creates one
   configuration.
6. `qnx.compile(... backend_config=config ...)` uses it.
7. `qnx.start_execute_job(... backend_config=config ...)` reuses that exact
   object. There is no second resolution, alias, retry, or fallback.

## Safe commands

### Live result from 2026-07-22

Read-only discovery authenticated successfully and returned `H1-Emulator` and
`H2-Emulator` as visible maintained targets. It created no submission and used
no credits. No project was supplied and Nexus used its default group, so
entitlement was not verified. The quota API reported `No quota set for user`;
because that does not prove a numeric non-cash allocation or disabled overage,
remote submission stopped with `NEEDS_RESEARCHER_BILLING_DECISION`.

A subsequent explicit execution authorization selected the repository-matching
`dhfr-h2-hardware` project and used the existing Nexus default group. Separate
ten-shot H2-Emulator and H1-Emulator smoke jobs completed and were retrieved.
They are access-path evidence only, not DHFR evidence. Molecular submission
remains blocked by incomplete quantum chains and unresolved matched active-space
correspondence.

Set the authorized project and group privately through command flags or the
documented environment variables. Do not commit their values.

Backend discovery authenticates and saves sanitized visibility metadata. It
does not upload, compile, execute, or consume credits:

```bash
python scripts/test_quantinuum_access.py --discover \
  --project-name "$QNEXUS_PROJECT_NAME" \
  --user-group "$QNEXUS_USER_GROUP" \
  --metadata-output results/quantinuum_access/backend_discovery.json
```

Compile-only validates and records the exact requested circuit/backend locally.
It deliberately creates no Nexus compile or execution job:

```bash
python scripts/test_quantinuum_access.py --nexus-emulator \
  --backend H2-Emulator --shots 10 --compile-only
```

Dry-run is also completely offline:

```bash
python scripts/test_quantinuum_access.py --nexus-emulator \
  --backend H2-Emulator --shots 10 --dry-run
```

Only after discovery and dry-run review, the researcher may intentionally run
the ten-shot Bell smoke test:

```bash
python scripts/test_quantinuum_access.py --nexus-emulator \
  --backend H2-Emulator --shots 10 \
  --project-name "$QNEXUS_PROJECT_NAME" \
  --user-group "$QNEXUS_USER_GROUP" \
  --confirm-submit --wait
```

Retrieve an already-created job without uploading or creating a replacement:

```bash
python scripts/test_quantinuum_access.py \
  --retrieve-job EXISTING_JOB_ID \
  --project-name "$QNEXUS_PROJECT_NAME" \
  --user-group "$QNEXUS_USER_GROUP"
```

## Four-system resumable workflow

Prepare or refresh per-system status without running calculations:

```bash
python scripts/four_system_workflow.py --prepare
```

The JSON tracks molecular input, classical reference, Hamiltonian, VQE
parameters, QASM, compilation, local result, Nexus-emulator result, uncertainty,
validation, and figures separately for WT_TMP, WT_4DTMP, L28R_TMP, and
L28R_4DTMP. Missing artifacts are `missing` with a null value, never zero.

After every required reviewed artifact exists, the later researcher submission
command is:

```bash
python scripts/four_system_workflow.py --submit-all \
  --backend H2-Emulator --shots 10 \
  --project-name "$QNEXUS_PROJECT_NAME" \
  --user-group "$QNEXUS_USER_GROUP" \
  --confirm-submit
```

The orchestrator preflights all four systems before the first submission. If any
required QASM, Hamiltonian, parameter, molecular input, or validation file is
missing, it stops before submitting any system. It never substitutes H1,
hardware, or a zero result. A single reviewed QASM can be dry-run separately
with `scripts/run_nexus_qasm.py`; QASM counts are not automatically an energy.

The corresponding later all-system local QASM command is:

```bash
python scripts/four_system_workflow.py --local-all --shots 100
```

It also uses an all-or-nothing QASM preflight and currently stops before local
execution because three systems are incomplete.

## Timeout-resistant WT_TMP pilot

The original pilot placed four deep circuits into one provider execution job at
compilation optimization level 0. A provider timeout therefore made all four
results unavailable together. Retrying that same Nexus job repeats the same
execution shape.

The replacement runner uses one group per job, optimization level 2, and one
saved job ID per group. A completed group remains usable if another group times
out. Retrieval never submits, and a failed group is never replaced
automatically.

Preview one shard without a remote call:

```bash
python scripts/run_wt_remote_molecular_pilot_sharded.py \
  --project-name dhfr-h2-hardware --group WT_TMP_G0001 --dry-run
```

Future researcher-authorized submission of that one shard:

```bash
python scripts/run_wt_remote_molecular_pilot_sharded.py \
  --project-name dhfr-h2-hardware --group WT_TMP_G0001 \
  --confirm-submit --confirm-partnership-access
```

Retrieve that exact saved shard without submitting another job:

```bash
python scripts/run_wt_remote_molecular_pilot_sharded.py \
  --project-name dhfr-h2-hardware --group WT_TMP_G0001 \
  --retrieve-job SAVED_JOB_ID
```

Do not use the sharded submission command while the researcher-started retry of
the original batch remains active. First retrieve or record that retry's final
state and job ID.

When Nexus shows the manually retried job's full ID, adopt and retrieve that
exact job without submitting anything new:

```bash
python scripts/run_wt_remote_molecular_pilot.py \
  --project-name dhfr-h2-hardware \
  --adopt-manual-retry-job NEW_RETRY_JOB_ID \
  --replaces-job e89da51e-bde9-4214-adda-6a08198f6b0a
```

The old failed job is retained in `job_history`; the tool records that the
retry was created manually in Nexus and then retrieves only the supplied job.

## Failure guide

| Observation | Classification | Action |
|---|---|---|
| Login works, backend visible | Authentication/visibility only | Check project, group, quota, and entitlement |
| Access code 14 | `access_or_entitlement` | Stop; ask the organization administrator or provider support |
| Simulation quota absent | `access_or_entitlement` | Stop; do not retry repeatedly |
| QASM missing or invalid | Circuit input/preflight failure | Correct locally; do not change backend |
| Molecular inputs/parameters missing | Incomplete scientific workflow | Leave status missing; do not submit |
| Job incomplete | Remote job state | Retrieve the same job later; do not create a replacement |

Code-14 metadata records requested/resolved backend, whether project and group
were selected, no retry, and no fallback. It never switches to hardware.

## What the smoke test proves

A completed smoke test proves that one tiny Bell circuit could be uploaded,
compiled, executed, and retrieved for the exact saved Nexus context at that
time. It can help diagnose authentication, project, group, endpoint, and quota
plumbing.

It does **not** prove a DHFR energy, validate a Hamiltonian or VQE, establish
physical-hardware access, demonstrate quantum advantage, complete any of the
four molecular systems, or show that future quota/entitlement will remain
available.
