# Quantinuum access troubleshooting

The July 18, 2026 discovery diagnostic authenticated through the normal browser session and listed 16 visible targets. This does not authorize execution. The account dashboard showed 20,000 HQCs for H2-1E/H2-2E, but no default group; the API phrase “No quota set for user” means no individual override, not unlimited organization quota.

Evidence boundaries: the H2-1LE local noiseless emulator completed the finite-shot WT_TMP calculation. H2-Emulator compilation completed but its execution was blocked by monthly simulation quota. An H2-1E execution attempt returned access code 14. No physical-hardware molecular energy was submitted or completed.

On 2026-07-19, the guarded H2-1SC Bell test authenticated normally and created a job, but Nexus returned an access/entitlement error. No job identifier, account identifier, or result is published. This confirms that authentication alone does not resolve target/user-group authorization.

Use `python scripts/diagnose_quantinuum_access.py --login` for safe discovery. `scripts/test_quantinuum_access.py` refuses hosted submission without explicit flags. Keep reports in ignored `results/quantinuum_access/`; they may contain account-specific operational metadata.

`H2-1SC` is a syntax checker: its output is artificial and scientifically unusable. `H2-Emulator` requires simulation quota. “Online” and visible only mean the backend service is operational and discoverable; they do not grant quota, a default user group, or machine entitlement. Nexus Lab is optional: the documented local `qnexus` API is supported. Access code 14 must be resolved by the organization administrator or Quantinuum support.

`scripts/test_quantinuum_access.py` is the sole maintained Nexus Bell-circuit access tool. A parameterized UCCSD state-preparation circuit does not calculate molecular energy; the complete result requires the exact 576 grouped Hamiltonian measurement circuits and Pauli reconstruction. `scripts/submit_hosted_pauli_energy.py` intentionally refuses submission until that mapping has been independently validated.

Before any hosted test, confirm target visibility, user-group entitlement, cost, project association, and quota allocation with the organization administrator or Quantinuum support. Do not change group settings through this repository.
