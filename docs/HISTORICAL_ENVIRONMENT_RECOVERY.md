# Historical Environment Recovery

OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED

The original environment was found intact at
`/opt/anaconda3/envs/dhfr-inquanto`. It was inspected without modification.

| Component | Version/status |
|---|---|
| Python | 3.11.15 |
| InQuanto | 6.1.0 installed |
| PySCF | 2.13.1 |
| pytket | 2.18.1 |
| qnexus | 0.46.0 |
| pytket-quantinuum | 0.57.0 |
| NumPy | 2.4.6 |
| SciPy | 1.17.1 |
| `pip check` | passed |

A local H2/STO-3G PySCF RHF calculation converged successfully. InQuanto import
attempted its supported online licensing/authentication initialization. With
restricted networking it raised a connection error. With network access the
process terminated during import before user code could report a version or
write a sanitized checkpoint-load result. No InQuanto credential or license
environment variable was present, inspected, copied, or bypassed.

Consequently the installed package is present but not usable in this
noninteractive session. The WT protocol checkpoint cannot be loaded, so its 576
measurement circuits and exact group mapping cannot be exported safely. The
maximum-shot execution plan requires this export before any shot-limit or
production experiment; those phases were not run.

Resume only after normal InQuanto license access is restored:

```bash
conda activate dhfr-inquanto
python -c "import inquanto; print('InQuanto import succeeded')"
python -c "from inquanto.protocols import PauliAveraging; print('protocol loader available')"
```

Do not place license keys, private index credentials, or tokens in repository
files. No environment was created, upgraded, or downgraded in this pass.

