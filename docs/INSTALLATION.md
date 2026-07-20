# Installation

The supported reproducible environment uses **Python 3.11** through Conda. Public tests and figure generation do not require credentials and never submit remote jobs.

## macOS and Linux

1. Install [Git](https://git-scm.com/downloads) and [Miniforge](https://github.com/conda-forge/miniforge).
2. In a terminal, run:

   ```bash
   git clone https://github.com/Braytech-Findings/dhfr-inquanto-resistance.git
   cd dhfr-inquanto-resistance
   conda env create -f environment.yml
   conda activate dhfr-qc
   cp .env.example .env
   python -m pytest -q
   ```

## Windows PowerShell

1. Install [Git for Windows](https://git-scm.com/download/win) and [Miniforge](https://github.com/conda-forge/miniforge).
2. In Miniforge Prompt or a Conda-enabled PowerShell, run:

   ```powershell
   git clone https://github.com/Braytech-Findings/dhfr-inquanto-resistance.git
   Set-Location dhfr-inquanto-resistance
   conda env create -f environment.yml
   conda activate dhfr-qc
   Copy-Item .env.example .env
   python -m pytest -q
   ```

The `.env` copy contains placeholders only. Add an authorized Nexus project selection only if you intend to use authenticated remote features. Never commit `.env`.

## Licensed components

The public environment installs `qnexus`, but InQuanto and its extensions require separate Quantinuum licensing and the provider's private package index. The safe public validation, tests, and publication-figure workflow do not require those packages. Follow your institution's current Quantinuum instructions rather than placing credentials in a command or file tracked by Git.

## Confirm the installation

```bash
python scripts/validate_repository.py
```

Expected outputs include `20 passed` (the exact count can grow) and `Repository validation passed`. An optional molecular-modeling test can be skipped when its larger dependency stack is unavailable.
