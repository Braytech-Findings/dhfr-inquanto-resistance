# Active-space validation

## Result

The proposed CAS(6,6) space passes the frozen-geometry screening criterion across the four-system panel.

## Frozen screening protocol

- Compact primary QM cluster with the N1-protonated ligand and fixed NADPH point-charge embedding.
- Restricted HF/STO-3G orbitals were ranked by ligand Mulliken population in fixed 16-orbital occupied and 12-orbital virtual frontier windows.
- The three most ligand-localized occupied and virtual orbitals form the 6-electron, 6-orbital candidate space.
- CASCI in that explicit orbital set verifies the electron count and reports active-space natural occupations.
- Screening CASCI calculations use density fitting and are labeled accordingly.

## Results

| System | Explicit canonical orbital indices | Minimum ligand population | CASCI method | ⟨S²⟩ | Occupation sum | Status |
| --- | --- | ---: | --- | ---: | ---: | --- |
| WT_TMP | 195,206,207,211,215,217 | 0.994 | DF-CASCI | 6.89e-32 | 6.000000 | pass |
| WT_4DTMP | 192,202,203,207,212,213 | 0.913 | DF-CASCI | 2.01e-30 | 6.000000 | pass |
| L28R_TMP | 207,214,215,225,226,229 | 0.734 | DF-CASCI | 2.94e-39 | 6.000000 | pass |
| L28R_4DTMP | 206,211,213,219,221,224 | 0.866 | DF-CASCI | 1.95e-40 | 6.000000 | pass |

## Scope and limitation

This registers an explicit, ligand-centered *candidate* active space for ideal-state benchmarking. The orbital indices are system-specific and must be mapped explicitly when generating each Hamiltonian; they are not a contiguous HOMO/LUMO block. Before a production energy claim, repeat the localization check at the production classical level and review orbital shapes.
