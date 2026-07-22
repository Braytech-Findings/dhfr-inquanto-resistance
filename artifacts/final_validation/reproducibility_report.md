# Reproducibility Report

- Fixed-seed endpoint analysis was run twice in separate processes by `tests/test_audit_core.py`; outputs matched exactly.
- Protected WT_TMP metadata and small-result checksums passed repository validation.
- Dry-run and compile-only Nexus metadata used the exact H2-Emulator name and created no job.
- Deterministic JSON/YAML/notebook parsing and Python compilation passed.
- The historical 45,887-second finite-shot calculation was not rerun: doing so is expensive, its exact random seed is absent, and no new scientific decision justified overwriting it.
- Three systems lack current Hamiltonians and VQE parameters, so a four-system quantum reproducibility repeat is blocked.

Pass criterion for deterministic stages: exact JSON equality or matching SHA-256. Numeric chemistry tolerance was not newly exercised because no production calculation was rerun.
