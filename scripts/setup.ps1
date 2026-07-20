$ErrorActionPreference = "Stop"
conda env create -f environment.yml
Write-Output "Run: conda activate dhfr-qc"
