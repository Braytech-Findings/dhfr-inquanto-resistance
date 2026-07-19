# Quantinuum access troubleshooting

The July 18, 2026 discovery diagnostic authenticated through the normal browser session and listed 16 visible targets. This does not authorize execution. The account dashboard showed 20,000 HQCs for H2-1E/H2-2E, but no default group; the API phrase “No quota set for user” means no individual override, not unlimited organization quota.

Evidence boundaries: the H2-1LE local noiseless emulator completed the finite-shot WT_TMP calculation. H2-Emulator compilation completed but its execution was blocked by monthly simulation quota. An H2-1E execution attempt returned access code 14. No physical-hardware molecular energy was submitted or completed.

Use `python scripts/diagnose_quantinuum_access.py --login` for safe discovery. `scripts/test_quantinuum_access.py` refuses hosted submission without explicit flags. Keep reports in ignored `results/quantinuum_access/`; they may contain account-specific operational metadata.

Before any hosted test, confirm target visibility, user-group entitlement, cost, project association, and quota allocation with the organization administrator or Quantinuum support. Do not change group settings through this repository.
