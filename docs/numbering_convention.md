# DHFR numbering convention

All protein variants use the 159-residue *E. coli* `folA`/DHFR reference sequence (RefSeq NP_414590.1). Residue numbers map directly to chain A in deposited structures 6XG5 and 6XG4; no signal peptide, insertion code, or mature-protein offset is applied. Mutation labels are `reference amino acid` + `one-based residue number` + `alternate amino acid`.

The core deposited structures independently verify LEU28 in 6XG5 and ARG28 in 6XG4. Before generating each expanded variant, the modeling code must assert that the input residue matches the mutation label; a mismatch is a hard error rather than an automatic renumbering.

Ligands are not part of this protein numbering system. TMP is residue `TOP` and 4-DTMP is residue `DTM` in generated structures.
