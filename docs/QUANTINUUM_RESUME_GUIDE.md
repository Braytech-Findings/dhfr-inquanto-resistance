# Quantinuum Resume Guide

1. Set the exact authorized `QNEXUS_PROJECT_NAME` and `QNEXUS_USER_GROUP`.
2. Verify a numeric non-cash balance and disabled paid overage in Nexus.
3. Repeat discovery and archive sanitized metadata.
4. Run compile-only and dry-run.
5. Run the ten-shot smoke test only with `--confirm-submit --wait`.
6. Save its job identifier immediately.
7. Resume an existing job with `--retrieve-job EXISTING_JOB_ID`; never submit
   a replacement because polling or the local session ended.

Molecular work must also wait for the active-space decision and complete QASM
preflight for all intended systems.

