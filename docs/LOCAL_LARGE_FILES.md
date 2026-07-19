# Local large files

Large generated quantum artefacts stay on the workstation and are intentionally not committed. The largest current files are the 1.0 GB built protocol checkpoint, 1.5 GB compiled checkpoint, 1.5 GB completed checkpoint, and a 2.3 GB expanded Pauli-partitioning CSV.

They are reproducibility evidence, not convenient source code. Their sizes make normal GitHub storage and cloning inappropriate. The public repository retains hashes, small numerical summaries, scripts, environment instructions, and a manifest so another researcher can inspect the methodology and recreate the artefacts in a licensed `dhfr-inquanto` environment.

See `results/quantum/results_manifest.json` for checked file identities and `results/quantum/README.md` for regeneration instructions.
