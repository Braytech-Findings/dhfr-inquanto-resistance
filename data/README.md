# Data acquisition and external sources

This repository is designed for reproducible structure preparation and quantum-chemistry analysis, but several inputs are external to the public GitHub snapshot and must be acquired separately before the full workflow can be rerun.

## 1. Experimental PDB structures

The crystallographic starting structures used in the workflow are the DHFR–TMP complexes with PDB IDs 6XG5 and 6XG4 from the RCSB Protein Data Bank. The repository’s download helper script fetches them directly from the RCSB public file service:

```bash
python scripts/download_pdbs.py --outdir data/raw/pdbs
```

This writes the files to:

- data/raw/pdbs/6XG5.pdb
- data/raw/pdbs/6XG4.pdb

## 2. External biology repositories

The reproduction workflow also depends on external public repositories referenced in [configs/source_manifest.yaml](../configs/source_manifest.yaml):

```bash
git clone https://github.com/PlesaLab/DHFR.git data/raw/external/PlesaLab_DHFR
git -C data/raw/external/PlesaLab_DHFR checkout 5e35d28bfa37caac2db9463809efd17b18b45f78

git clone https://github.com/erdaltoprak-zz/NatureCommunication2021_Manna.git data/raw/external/NatureCommunication2021_Manna
git -C data/raw/external/NatureCommunication2021_Manna checkout 3869a92642062847590203b8f536f85ea20aacaa
```

The processed PlesaLab fitness archive referenced in the manifest should be downloaded from DOI 10.6084/m9.figshare.30470525.v1 and unpacked into `data/raw/external/PlesaLab_processed` before running the reproduction scripts.

## 3. Expected data layout

After acquisition, the repository expects the following layout:

```text
data/
  raw/
    pdbs/6XG5.pdb
    pdbs/6XG4.pdb
    external/PlesaLab_DHFR/
    external/NatureCommunication2021_Manna/
    external/PlesaLab_processed/
```

Once these sources are present, the downstream structure preparation, cluster building, classical counterpoise calculations, and report generation scripts can be rerun from the repository root.
