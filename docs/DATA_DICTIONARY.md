# Data dictionary

`results/publication/data/energy_results.csv`: `method` (string), `energy_hartree` (float, Hartree), `standard_error_hartree` (float, Hartree; zero for deterministic entries), `relative_to_scf_millihartree` (float, mHartree).

`results/publication/data/verified_summary.json`: exact and finite-shot energies (Hartree), standard error (Hartree and derived kcal/mol), signed/absolute error metrics, and backend label.

`results/publication/data/uccsd_parameters.csv`: `parameter` (string identifier), `value` (float amplitude), `class` (derived coarse label).

`results/publication/data/molecular_structure_summary.csv`: selected structural metadata. `qm_cluster_mapping_verified=false` is deliberate missing-proof behavior, not a negative scientific finding.
