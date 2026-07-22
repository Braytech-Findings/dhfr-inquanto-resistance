# WT_TMP Estimator Trace

OBJECTIVE COMPUTATIONAL OUTPUT — RESEARCHER INTERPRETATION REQUIRED

The protected calculation was produced by `scripts/run_local_pauli_energy.py`.
It loads `data/processed/WT_TMP_qubit_hamiltonian.json`, constructs an InQuanto
`ExpectationValue`, and calls `PauliAveraging.build_from`. That protocol grouped
1,818 non-identity Pauli observables into 576 measurement circuits. The identity
term is the Hamiltonian constant `-2585.31709236164` Hartree and is not measured.

The protocol compiled every grouped circuit for the offline `H2-1LE` target,
ran 100 shots per circuit, then evaluated the original expectation with
`energy.evaluate(protocol.get_evaluator())`. The uncertainty came from
`protocol.evaluate_expectation_uvalue`. The exported measurement table contains
one unique mean and standard error for every non-identity Hamiltonian term.

`src/dhfr_quantum/energy_reconstruction.py` independently joins those 1,818
rows to the Hamiltonian by exact Pauli string, multiplies each mean and standard
error by its signed coefficient, adds the identity constant, and combines the
saved per-term errors in quadrature. It reconstructs
`-2587.9171188214327` Hartree with standard error
`0.00764704514062616` Hartree, agreeing with the protected values within normal
floating-point summation tolerance.

The raw 57,600 individual shots were not exported as portable counts. The
historical completed protocol checkpoint retains evaluator state, while the
2.5-GB partition CSV embeds large circuit representations. Consequently the
saved energy is reproducible from exported expectations, but the exact 576
circuit basis rotations, group membership, bit mapping, and covariance cannot
yet be recreated from a compact public manifest. Remote molecular submission
must remain disabled until that mapping is extracted and locally validated.

Relevant files:

- `scripts/run_local_pauli_energy.py`: original build, compile, run, evaluation.
- `data/processed/WT_TMP_qubit_hamiltonian.json`: 1,819 signed Pauli terms.
- `results/quantum/WT_TMP_H2-1LE_100shots_pauli_measurements.csv`: exported
  non-identity expectations and errors.
- `results/quantum/measurement_plans/WT_TMP_H2-1LE_100shots_plan.json`: circuit
  and shot totals.
- `results/quantum/protocol_checkpoints/*completed.pkl`: historical InQuanto
  evaluator/checkpoint state.
- `artifacts/final_validation/wt_tmp_reconstruction_validation.json`: compact
  independent reconstruction proof.
