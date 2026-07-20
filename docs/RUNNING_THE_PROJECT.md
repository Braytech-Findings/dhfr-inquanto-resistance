# Running the Project

Run all commands from the repository root. The commands below correspond to files in this repository.

## Safe command matrix

| Environment | Purpose | Cost risk | Credentials | Command | Result or success check |
|---|---|---:|---|---|---|
| Public local validation | Check files, imports, tests, secrets, and guards | None | No | `python scripts/validate_repository.py` | Ends with `Repository validation passed` |
| Local publication workflow | Rebuild verified tables and figures | None | No | `python scripts/build_publication_assets.py` | Files appear in `results/publication/` |
| Local H2-1LE emulator | Reproduce the saved finite-shot chemistry method | None | Licensed InQuanto stack | `python scripts/run_local_pauli_energy.py --help` first; see `results/quantum/README.md` | A JSON result plus measurement data; no network job |
| Nexus syntax checker | Validate a small Bell circuit | Usually none; provider policy applies | Nexus account/project | `python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1SC --dry-run` | Prints backend, width, shots, group source, and no submission |
| Nexus H-Series emulator | Hosted noisy emulation | Quota may apply | Nexus account/project and simulation quota | `python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-Emulator --shots 10 --dry-run` | Preview only until `--confirm-submit` is deliberately added |
| Quantinuum H-Series hardware | Physical QPU | **HQCs may be spent** | Approved Nexus access | `python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1E --shots 10 --max-hqc LIMIT --dry-run` | Preview only; submission additionally requires both confirmation flags |
| IBM / qBraid | Not implemented in this repository | — | — | No verified command | This DHFR repository contains no IBM or qBraid execution path |

**Paid/limited-credit warning:** no setup, test, validation, figure, or Make target submits a remote job. Physical H-Series execution requires `--confirm-hardware`, `--confirm-submit`, and a positive `--max-hqc`. Always run the same command with `--dry-run` first.

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

Structure download and preparation, PySCF calculations, active-space selection, and InQuanto execution have distinct dependencies and scientific review gates. The exact stepwise commands and caveats are retained in the main [README](../README.md#workflow). Do not treat example input names as completed evidence. The only currently verified quantum-energy result is the saved `WT_TMP` local H2-1LE emulator result.
