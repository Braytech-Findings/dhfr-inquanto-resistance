# Methods and reporting checklist

## Structural model

Record PDB checksums, chains, alternate conformers, missing residues/atoms, retained crystallographic waters, ligand protonation/tautomer states, and every manual intervention. Align modeled 4-DTMP to the crystallographic TMP heavy atoms and report the local relaxation protocol and RMSD.

## Energy definition

The primary quantity must be defined before calculation. For a cluster supermolecule protocol, report charge, multiplicity, caps, embedding, geometry constraints, method, basis, grids, SCF thresholds, counterpoise correction, and fragment definitions. Total electronic energies from unlike atom sets are not comparable.

## Active-space validation

For each system report orbital plots, occupation numbers, entanglement/selection diagnostic, active electrons and orbitals, frozen-core convention, qubit mapping, tapering, and exact diagonalization energy. Demonstrate orbital correspondence across the four systems. Report sensitivity to plausible neighboring active spaces.

## Quantum algorithm

Report InQuanto/pytket/qnexus versions, ansatz/pool, optimizer, initialization, convergence criteria, random seeds, mapping, circuit compilation, two-qubit gate counts, shots, emulator, mitigation, and uncertainty. Compare HF, exact active-space, ideal VQE, and noisy-emulator energies.

## Statistical analysis

The estimand is a difference-in-differences. Technical repeats from a deterministic calculation do not create biological replication. Bootstrap intervals are meaningful only when the rows represent defensible independent uncertainty draws (structures, conformers, or stochastic measurements). Report Hartree and kJ/mol, show all four cell estimates, and include method/basis/QM-region/conformer sensitivity analyses.

## Manuscript skeleton

1. Introduction: evolutionary hypothesis and prespecified contrast.
2. Methods: structures, chemical preparation, electronic structure, active space, quantum workflow, and statistics.
3. Results: model validation, classical references, active-space convergence, ideal/noisy comparison, and endpoint.
4. Discussion: mechanistic interpretation, limits of four structures, force-field/QM-region uncertainty, and predictive validation needs.
5. Data/code availability: immutable inputs, manifests, environment, seeds, and generated result tables.

