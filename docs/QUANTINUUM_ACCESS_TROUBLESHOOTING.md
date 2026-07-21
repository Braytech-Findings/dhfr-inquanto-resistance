# Quantinuum access troubleshooting

## Confirmed endpoint policy

On July 21, 2026, Quantinuum support confirmed that Southern Connecticut State University still has access to Nexus and the Nexus-hosted emulators. The failed jobs were sent to hardware-tier Quantinuum emulator endpoints that the organization no longer has access to.

Use these exact Nexus-hosted endpoint names:

- `H2-Emulator` — default target for this project
- `H1-Emulator` — supported fallback

Do not substitute hardware-tier emulator names such as `H2-1E`, `H2-2E`, or `H1-1E`. Quantinuum documentation distinguishes the endpoint families by suffix: names ending in `Emulator` are Nexus-hosted and costed in simulation seconds, while names ending in `E` are hardware-tier emulators costed in Hardware Quantum Credits (HQCs).

Official reference: <https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/introduction.html>

## Safe test commands

Preview the default target without logging in or submitting anything:

```bash
python scripts/test_quantinuum_access.py \
  --nexus-emulator \
  --backend H2-Emulator \
  --shots 10 \
  --dry-run
```

Use the H1 Nexus-hosted emulator instead:

```bash
python scripts/test_quantinuum_access.py \
  --nexus-emulator \
  --backend H1-Emulator \
  --shots 10 \
  --dry-run
```

After the dry run is correct, a deliberate remote Bell-circuit test adds `--confirm-submit` and may add `--wait`. The authorized Nexus project must be supplied privately through `--project-id`, `--project-name`, `QNEXUS_PROJECT_ID`, or `QNEXUS_PROJECT_NAME`. Use `--user-group` or `QNEXUS_USER_GROUP` only when the organization requires an exact quota-bearing group.

## What the earlier failures mean

Earlier `H2-1E` or `H2-2E` failures do not show that the SCSU Nexus account is broken. They show that the job targeted the wrong endpoint family for the organization's current access. A visible balance, visible device, or online status does not by itself grant entitlement to a hardware-tier endpoint.

A failure on `H2-Emulator` or `H1-Emulator` should be investigated separately for project selection, user-group assignment, authentication, queue state, or simulation-time quota. The script now rejects hardware-tier emulator names before login or submission so the same endpoint mistake is not repeated.

## Scientific evidence boundary

The verified molecular-energy result in this repository used the local `H2-1LE` noiseless emulator. That local result is separate from the Nexus-hosted `H2-Emulator` and `H1-Emulator` access test. A successful Bell-circuit test confirms remote endpoint access only; it is not a completed DHFR molecular-energy result and must not be reported as physical quantum hardware.
