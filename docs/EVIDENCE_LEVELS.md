# Evidence Levels

| Level | Definition |
|---:|---|
| 0 | Placeholder, example, draft, or unverified |
| 1 | File exists but provenance or validation is incomplete |
| 2 | Locally reproducible computational result with validated inputs |
| 3 | Matched multi-system result with uncertainty and sensitivity checks |
| 4 | Externally executed emulator result with complete provenance/retrieval |
| 5 | Physical-hardware result with complete provenance |
| 6 | Independent biological or experimental validation |

WT_TMP is Level 2: it has protected metadata, checksums, an ideal saved-parameter
result, and a local finite-shot result, but lacks a complete historical seed,
commit, optimizer record, and matched systems. Each other system is Level 1:
prepared/classical files exist, but its production Hamiltonian, parameters, and
quantum results do not. No result is Level 3–6.

