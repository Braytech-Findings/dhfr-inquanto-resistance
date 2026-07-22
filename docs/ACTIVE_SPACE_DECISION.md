# Active-Space Decision

Status: **NEEDS_RESEARCHER_DECISION**

## Current definitions

The historical verified WT_TMP workflow used six electrons in six spatial
orbitals, indices 208–213, producing 12 qubits, 1,819 mapped Pauli terms, and
576 grouped measurement circuits. The current candidate configuration also
uses CAS(6,6), but selects three occupied and three virtual orbitals with high
ligand Mulliken population separately for each system:

| System | Candidate canonical orbitals |
|---|---|
| WT_TMP | 195, 206, 207, 211, 215, 217 |
| WT_4DTMP | 192, 202, 203, 207, 212, 213 |
| L28R_TMP | 207, 214, 215, 225, 226, 229 |
| L28R_4DTMP | 206, 211, 213, 219, 221, 224 |

These candidates passed occupation-trace CASCI checks and have strong ligand
character. Their strength is chemical focus at a tractable 12-qubit size. Their
weakness is that index lists alone do not prove the orbitals represent the same
chemical subspace across different structures. Orbital identities can drift,
and L28R candidates show different occupation patterns.

## Production decision

The same *size* is feasible for all systems, but matched orbital identity is not
yet demonstrated. The historical WT_TMP parameter vector is not compatible with
the new candidate WT_TMP Hamiltonian without rebuilding and reoptimization. It
must never be copied to another system as a final parameter set.

Before production, the researcher should inspect orbital shapes, document
cross-system correspondence, repeat localization at the chosen classical
level, and test at least one neighboring active space. Until then no expensive
four-system Hamiltonian/VQE run is scientifically defensible.

Expected computational cost at the historical definition is substantial: the
single finite-shot run recorded roughly 12.7 hours and 57,600 shots locally.
Term and circuit counts for the candidate spaces cannot be assumed equal until
their Hamiltonians are built.

