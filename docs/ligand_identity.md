# Ligand identity and transformation record

## Authoritative identities

The deposited ligand `TOP` is trimethoprim, formula C14H18N4O3, in both 6XG5 and 6XG4. The Manna et al. study identifies the comparison compound as 4′-desmethyltrimethoprim (4′-DTMP): the para aryl methoxy group of TMP is converted to a phenol while the 2,4-diaminopyrimidine pharmacophore is retained.

Sources:

- Manna et al., *Nature Communications* 12, 2949 (2021): https://doi.org/10.1038/s41467-021-23191-z
- RCSB chemical component `TOP`: https://www.rcsb.org/ligand/TOP
- Deposited structures: https://doi.org/10.2210/pdb6XG5/pdb and https://doi.org/10.2210/pdb6XG4/pdb

## Computational representation

| Ligand | Formula | Formal charge | Heavy atoms | Canonical SMILES |
|---|---:|---:|---:|---|
| TMP | C14H18N4O3 | 0 | 21 | `COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC` |
| 4-DTMP | C13H16N4O3 | 0 | 20 | `COc1cc(Cc2cnc(N)nc2N)cc(OC)c1O` |

`scripts/model_4dtmp.py` removes the methyl carbon attached to the para methoxy oxygen and adds the phenolic hydrogen. It does not optimize the isolated product. `scripts/audit_ligands.py` proves that 4-DTMP is an exact heavy-atom substructure of TMP and writes the complete atom map. All 20 retained heavy atoms inherit the deposited TMP coordinates exactly (direct RMSD 0.000 Å) in both backgrounds.

AM1-BCC partial charges are assigned consistently by the OpenFF toolkit during preparation. Those partial charges are model parameters and are not confused with the formal charge of zero.

## Review state

Automated identity, formula, formal-charge, atom-count, substructure, and coordinate-mapping checks pass. A human should still inspect the 2D structures side by side before Gate B is signed off; this is intentionally recorded as a review item rather than silently treated as automated evidence.
