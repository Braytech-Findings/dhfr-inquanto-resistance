# Data provenance

The prepared WT_TMP structure is `data/processed/WT_TMP_minimized.pdb`; its programmatic rendering identifies protein chain `A` and ligand residue `TOP` on chain `X`. The compact QM cluster is `data/processed/qm_clusters/WT_TMP_compact_primary.xyz`. They are derived research inputs; the public visualization manifest records SHA-256 digests and does not assert atom-by-atom correspondence between the two files.

The numerical publication summaries are derived from ignored local quantum result JSON and measurement-plan JSON by `scripts/build_publication_assets.py`. `results/publication/data/verified_summary.json` is the lightweight public record. See `docs/LOCAL_LARGE_FILES.md` for excluded checkpoints and regeneration instructions.
