# Contributing

Contributions via pull requests are welcome. The most useful contributions are repro-oriented fixes, notebook improvements, documentation updates, and additional validation around the classical interaction energies and endpoint calculation.

## Reproducing the workflow

1. Create the environment from the repository root:

   ```bash
   conda env create -f environment.yml
   conda activate dhfr-qc
   ```

2. Acquire the required external data:

   ```bash
   python scripts/download_pdbs.py --outdir data/raw/pdbs
   git clone https://github.com/PlesaLab/DHFR.git data/raw/external/PlesaLab_DHFR
   git clone https://github.com/erdaltoprak-zz/NatureCommunication2021_Manna.git data/raw/external/NatureCommunication2021_Manna
   ```

3. Run the pipeline from the repository root:

   ```bash
   python scripts/01_prepare_complexes.py
   python scripts/build_qm_clusters.py
   python scripts/02_prepare_classical_inputs.py
   python scripts/03_run_classical_calculations.py
   python scripts/04_run_avas_and_vqe.py
   python scripts/05_collect_results.py
   python scripts/analyze_endpoint.py results/tables/classical_interaction_energies.csv --output results/tables/endpoint.json
   ```

4. Inspect the generated tables and reports under `results/tables` and `results/reports`.

## Reporting changes

When you modify the workflow or results, please update the relevant docs, tests, and generated tables where appropriate. Keep the scientific interpretation aligned with the prespecified endpoint definition and do not overstate the claims of the work.
