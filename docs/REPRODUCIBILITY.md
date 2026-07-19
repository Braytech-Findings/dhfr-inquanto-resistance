# Reproducibility

Use the pinned `dhfr-qc` conda environment in `environment.yml` for public tests and lightweight figures, then run `make publication`. The finite-shot result requires licensed InQuanto and local large inputs described in `results/quantum/README.md`; in this workspace that stack is available through `dhfr-inquanto`. It does not require a cloud or hardware submission.

All paths in committed documentation are repository-relative. No credential, token, cookie, or Nexus session is required for public tests.
