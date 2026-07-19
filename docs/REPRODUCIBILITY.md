# Reproducibility

Use the pinned conda environment in `environment.yml`, then run `make publication` to rebuild lightweight figures and molecular renders. Run `make test-public` for code checks. The finite-shot result requires licensed InQuanto and local large inputs described in `results/quantum/README.md`; it does not require a cloud or hardware submission.

All paths in committed documentation are repository-relative. No credential, token, cookie, or Nexus session is required for public tests.
