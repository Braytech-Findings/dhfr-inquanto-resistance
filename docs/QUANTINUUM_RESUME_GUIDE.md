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

Completed smoke jobs can be re-retrieved without replacement submission:

```bash
python scripts/test_quantinuum_access.py --retrieve-job \
  3d554c78-945d-4c66-b6cf-7f622c02186c \
  --project-name dhfr-h2-hardware
python scripts/test_quantinuum_access.py --retrieve-job \
  250413ef-f0f1-4acc-b527-2d96a9c82ab9 \
  --project-name dhfr-h2-hardware
```
