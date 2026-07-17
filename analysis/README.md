# Figure generation with R

Run the publication-quality figure script from the repository root:

```bash
Rscript analysis/figures.R
```

The script reads the result tables in `results/tables/` and the classical JSON files in `results/classical/`, then writes high-resolution PNG and PDF figures to `results/figures/`.

## Figures produced

1. `results/figures/publication_summary.png` and `.pdf` – a multi-panel publication summary figure.
2. `results/figures/figure_1.png` / `.pdf` – the D contrast bar plot with 95% CI.
3. `results/figures/figure_2.png` / `.pdf` – the HF energy comparison across the four systems.
4. `results/figures/figure_3.png` / `.pdf` – a robustness plot of the D contrast across sensitivity rows.
