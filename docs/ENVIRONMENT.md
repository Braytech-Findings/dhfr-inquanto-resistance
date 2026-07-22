# Environment

## Supported setup

The public environment targets Python 3.11 through Conda. From the repository
root on macOS or Linux:

```bash
conda env create -f environment.yml
conda activate dhfr-qc
python -m compileall -q scripts tests
python -m pytest -q
```

Creating the environment downloads packages but does not contact a quantum
backend. The file includes molecular tools (RDKit, OpenMM, OpenFF), scientific
Python, PySCF, notebooks, tests, and the public `qnexus` client. InQuanto and
its PySCF extension are licensed/private dependencies and are not declared as
publicly installable packages. Local InQuanto reproduction therefore needs a
separately authorized environment.

On Apple Silicon, use a current conda-forge distribution. If OpenFF/OpenMM
solving fails, create a clean environment instead of mixing pip wheels into an
old chemistry environment. Linux uses the same commands. Windows has
`scripts/setup.ps1`, but the audit's required platform guidance is macOS/Linux.

## Dependency audit

- Imported core packages are represented in `environment.yml`.
- `json`, `pathlib`, `hashlib`, `argparse`, and similar modules are in Python's
  standard library and need no package entry.
- R publication scripts require R plus `readr`, `dplyr`, `tidyr`, `ggplot2`,
  `scales`, `cowplot`, and `jsonlite`; these are optional and not installed by
  the Python environment.
- PyMOL recipe files require a separate PyMOL installation.
- `requirements_before_qnexus_update.txt` is an untracked historical snapshot,
  not the supported installer.
- Broad unpinned scientific dependencies aid platform solving but weaken exact
  long-term reproduction. The verified result's provenance preserves critical
  observed versions; blindly upgrading them is not recommended.

Never place tokens in the environment file. Private selectors belong in shell
environment variables described by `.env.example`; a populated `.env` is
ignored by Git.

## Final-pass environment finding

The final validation shell used Python 3.13.5 on ARM64 macOS, not the declared
Python 3.11 environment. Lightweight tests passed, but `pip check` reported an
unrelated installed package, `quantum-architecture-comparison 0.1.0`, requiring
Qiskit `<2` while this shell has Qiskit 2.5.0. This is environment drift and is
recorded in `artifacts/final_validation/pip_check.txt`. It does not alter the
historical WT_TMP result, whose saved manifest records Python 3.11, InQuanto
6.1.0, pytket 2.18.1, and PySCF 2.13.1.

For numerical reproduction, create a clean Python 3.11 environment from
`environment.yml`, activate the separately authorized InQuanto packages, run
`python -m pip check`, then run `python scripts/validate_repository.py`. Do not
use the current mixed base environment as a production lock file.
