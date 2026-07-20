# Troubleshooting

| Symptom | Likely cause | Safe response |
|---|---|---|
| `conda: command not found` | Miniforge/Conda is not installed or initialized | Install Miniforge, reopen the shell, and retry. |
| Package import fails | Wrong environment is active | Run `conda activate dhfr-qc` and `python --version`; the project environment targets 3.11. |
| InQuanto import fails | Licensed packages are absent | Use public tests/figures, or install through your authorized Quantinuum channel. |
| Molecular test is skipped | Optional OpenMM/OpenFF stack is unavailable | This is expected in lightweight CI; use `environment.yml` for the full public environment. |
| Matplotlib cache warning | Default cache directory is not writable | Set `MPLCONFIGDIR` to a writable temporary directory; results are unaffected. |
| Nexus says no default group / access code 14 | Account entitlement or group selection is missing | Stop; ask the organization administrator or Quantinuum support. See [Quantinuum access troubleshooting](QUANTINUUM_ACCESS_TROUBLESHOOTING.md). |
| Backend is visible but execution fails | Visibility does not prove quota or entitlement | Run access diagnostics and confirm the authorized project/user group. Do not repeatedly submit. |
| Hardware command refuses to run | A safety flag or positive HQC cap is missing | Review the dry run and add flags only after explicit approval to spend credits. |
| Figure values look surprising | Plot inputs may have changed | Inspect `results/publication/data/` and the corresponding manifest before interpreting the image. |

Never paste a token into an issue. Sanitized diagnostics can be generated with `python scripts/diagnose_quantinuum_access.py`; its report intentionally excludes credentials and private identifiers.
