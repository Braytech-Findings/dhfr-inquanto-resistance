#!/usr/bin/env sh
set -eu
conda env create -f environment.yml
printf '%s\n' 'Run: conda activate dhfr-qc'
