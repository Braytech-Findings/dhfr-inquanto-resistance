# Source-data reproduction notes

The Manna et al. (2021) public repository is pinned in `configs/source_manifest.yaml`. Run:

```bash
python scripts/reproduce_manna.py
```

The script reproduces three prespecified biological directions from source figure data: L28R-specific TMP resistance relative to 4-DTMP, suppression of L28R frequency under 4-DTMP evolution, and lower final fitted resistance under 4-DTMP. Exact results are written to `results/tables/manna_headline_results.csv`; the figure is generated from code.

The PlesaLab processed archive is pinned by DOI, size, and MD5 in `configs/source_manifest.yaml`. Run:

```bash
python scripts/reproduce_plesa.py
```

This reproduces the distribution of 797 designed-homolog fitness measurements across the TMP gradient and the source notebook's prespecified gain-of-function definition. A parent is a complementation dropout at `fitD05D03 < -1`; a measured one-amino-acid mutant is a rescue when it reaches `fitD05D03 >= -1`. Summary tables, the complete threshold-crossing rescue set, and a figure are generated under `results/`.

Reproduced values on 2026-07-15:

- L28R median IC95: TMP 2.5 versus 4-DTMP 0.0926 ug/mL (27-fold).
- L28R day-21 mutation frequency: TMP 81.83% versus 4-DTMP 12.29% (6.66-fold).
- Mean day-21 fitted IC50: TMP 1768.8 versus 4-DTMP 152.3 ug/mL (11.61-fold).

PlesaLab reproduction on 2026-07-15:

- 794/797 homologs had finite complementation fitness; 52.39% were at or above -1.
- The median homolog fitness decreased from -1.26 at 0.058 ug/mL TMP to -7.42 at 200 ug/mL TMP.
- Among 317 dropout parents with measured single mutants, 476 unique single mutants rescued 196 parent homologs across the -1 complementation threshold.
