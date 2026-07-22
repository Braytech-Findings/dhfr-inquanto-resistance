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

A local H2/STO-3G PySCF RHF calculation converged successfully. A later retry
using the absolute historical interpreter confirmed that InQuanto imports,
reports version 6.1.0 through package metadata, and exposes
`PauliAveraging.load`. The earlier diagnosis of a license blocker was therefore
incorrect and is superseded by this result.

Loading the 1.06-GB built checkpoint still terminated before returning an
object or writing a report, while system memory was nearly exhausted. The
remaining blocker is checkpoint-deserialization resource use, not installation
or license availability. A streaming recovery of the partition CSV found 576
group records but only one unique serialized circuit: the bound state
preparation. The measurement-basis suffixes remain internal to the checkpoint.
The maximum-shot execution plan requires those suffixes before production.

Resume on a machine/process with enough memory to deserialize the checkpoint:

```bash
conda activate dhfr-inquanto
python -c "from importlib.metadata import version; import inquanto; print(version('inquanto'))"
python -c "from inquanto.protocols import PauliAveraging; print('protocol loader available')"
```

Do not place license keys, private index credentials, or tokens in repository
files. No environment was created, upgraded, or downgraded in this pass.
