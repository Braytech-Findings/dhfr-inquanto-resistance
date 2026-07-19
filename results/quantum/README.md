# Local quantum-result artefacts

The numerical summaries used by the public repository are reproduced in `results/publication/data/verified_summary.json` and the publication tables/figures.

The files listed in `results_manifest.json` remain local because they are generated checkpoints or measurement-plan artefacts totaling about 6.3 GB. They are excluded to keep GitHub cloning practical. Do not delete them: they support local audit and resumption.

To regenerate a baseline local finite-shot result in the licensed `dhfr-inquanto` environment:

```bash
python scripts/run_local_pauli_energy.py --system WT_TMP --basis sto-3g --shots-per-circuit 100
```

This recreates the 576-circuit, 57,600-shot workflow on the Quantinuum H2-1LE local noiseless emulator. It is not physical-hardware execution. The optimized workflow must first pass its three-circuit equivalence validation before a full rerun is justified.
