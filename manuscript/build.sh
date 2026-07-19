#!/usr/bin/env sh
set -eu
command -v pdflatex >/dev/null || { echo "pdflatex is not installed"; exit 0; }
pdflatex -interaction=nonstopmode main.tex
