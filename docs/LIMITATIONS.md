# Limitations

This repository intentionally does not overstate its evidence.

| Limitation | Why it matters | Next step |
|---|---|---|
| One WT_TMP model | Cannot compare resistance mutations | Build matching mutant calculations |
| STO-3G basis | Small basis can bias energies | Test larger bases |
| Contiguous orbitals 208–213 | Reproducible, but not yet chemically localized | Compare AVAS/localized choices |
| Total energy | Not a binding free energy | Use matched interaction/free-energy protocols |
| 100 shots/group | Large sampling uncertainty | Increase shots and repeat seeds |
| Local noiseless emulator | Does not test hardware noise | Run noise studies, then selected hardware validation |
| No experiments | No biological or clinical conclusion | Compare against structural and wet-lab evidence |

The optimized measurement workflow is not yet validated by its required three-circuit exact-equivalence test. The completed baseline result remains the authoritative finite-shot result.
