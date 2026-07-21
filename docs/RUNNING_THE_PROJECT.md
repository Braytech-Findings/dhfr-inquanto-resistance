# Running the Project

Run all commands from the repository root. The commands below correspond to files in this repository.

## Safe command matrix

| Environment | Purpose | Cost risk | Credentials | Command | Result or success check |
|---|---|---:|---|---|---|
| Public local validation | Check files, imports, tests, secrets, and guards | None | No | `python scripts/validate_repository.py` | Ends with `Repository validation passed` |
| Local publication workflow | Rebuild verified tables and figures | None | No | `python scripts/build_publication_assets.py` | Files appear in `results/publication/` |
| Local `H2-1LE` emulator | Reproduce the saved finite-shot chemistry method | None | Licensed InQuanto stack | `python scripts/run_local_pauli_energy.py --help` first; see `results/quantum/README.md` | A JSON result plus measurement data; no network job |
| Nexus `H2-Emulator` | Primary SCSU remote Bell test and noisy-emulation target | Nexus simulation seconds | Nexus account and authorized project | `python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-Emulator --shots 10 --dry-run` | Preview only until `--confirm-submit` is deliberately added |
| Nexus `H1-Emulator` | Supported fallback remote target | Nexus simulation seconds | Nexus account and authorized project | `python scripts/test_quantinuum_access.py --nexus-emulator --backend H1-Emulator --shots 10 --dry-run` | Preview only until `--confirm-submit` is deliberately added |
| Hardware-tier emulator ending in `E` | Different Quantinuum endpoint tier | HQCs | Not available through current SCSU organization access | No supported command in this repository | The guarded script rejects these endpoint names before login or submission |
| Quantinuum physical hardware | Future selected validation | HQCs may be spent | Separate approved entitlement | Not implemented by the guarded emulator test | Requires a separate reviewed workflow |
| IBM / qBraid | Not implemented in this repository | — | — | No verified command | This DHFR repository contains no IBM or qBraid execution path |

## Correct Nexus-hosted emulator workflow

Use `H2-Emulator` first:

```bash
python scripts/test_quantinuum_access.py \
  --nexus-emulator \
  --backend H2-Emulator \
  --shots 10 \
  --dry-run
```

The dry run does not import `qnexus`, log in, compile, use quota, or submit a job. After checking the output, a deliberate remote Bell test is:

```bash
python scripts/test_quantinuum_access.py \
  --nexus-emulator \
  --backend H2-Emulator \
  --shots 10 \
  --confirm-submit \
  --wait
```

The authorized project must be supplied privately with `--project-id`, `--project-name`, `QNEXUS_PROJECT_ID`, or `QNEXUS_PROJECT_NAME`. Add `--user-group` or `QNEXUS_USER_GROUP` only when an exact quota-bearing group is required.

`H1-Emulator` is the supported fallback. Do not replace either Nexus-hosted name with a hardware-tier emulator name ending in `E`. Quantinuum support confirmed on July 21, 2026 that SCSU retains access to Nexus-hosted emulators but no longer has access to the hardware-tier emulator endpoints used by the failed jobs.

## Beginner path

```bash
make test
make figures
```

On Windows, use:

```powershell
python -m compileall -q scripts
python -m pytest -q
python scripts/build_publication_assets.py
```

The main human-readable results are [RESULTS.md](RESULTS.md), while machine-readable values are in `results/publication/data/` and plots are in `results/publication/figures/`.

## Scientific workflow boundaries

Structure download and preparation, PySCF calculations, active-space selection, and InQuanto execution have distinct dependencies and scientific review gates. The exact stepwise commands and caveats are retained in the main [README](../README.md#workflow). Do not treat example input names as completed evidence. The only currently verified quantum-energy result is the saved `WT_TMP` local `H2-1LE` emulator result. A successful Nexus Bell test proves endpoint access only; it is not a completed DHFR molecular-energy result.
