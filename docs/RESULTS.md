# Verified WT_TMP results

This page reports one completed electronic-structure model: wild-type DHFR with trimethoprim (WT_TMP). It is not a mutant comparison, binding-free-energy calculation, resistance prediction, or medical result.

| Quantity | Verified value |
|---|---:|
| SCF energy | -2587.906022646355 Hartree |
| Ideal saved-parameter VQE energy | -2587.912001526413 Hartree |
| Finite-shot H2-1LE local-emulator energy | -2587.917118821447 Hartree |
| Finite-shot standard error | 0.007647045141 Hartree |
| Pauli terms / groups | 1,819 / 576 |
| Shots | 100 per group; 57,600 total |

The finite-shot value differs from the ideal reference by -0.005117295034 Hartree. Its reported uncertainty is larger than that difference, so this single finite-shot estimate is statistically consistent with the ideal reference at this shot count. It is not chemical accuracy: the absolute difference is about 5.117 millihartree (about 3.21 kcal/mol).

`H2-1LE` means the **Quantinuum H2-1LE local noiseless emulator**. It is not physical quantum hardware and does not include hardware noise.
