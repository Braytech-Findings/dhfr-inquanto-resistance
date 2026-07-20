#!/usr/bin/env sh
set -eu
python -m compileall -q scripts
python -m pytest -q
