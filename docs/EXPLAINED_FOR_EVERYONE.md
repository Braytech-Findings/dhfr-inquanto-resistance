# DHFR quantum chemistry, explained simply

DHFR is a protein. Proteins are tiny machines that cells use to do jobs. Trimethoprim is a drug that can slow this protein down. A mutation is a spelling change in genetic instructions that can change a protein. Drug resistance can happen when a changed protein no longer responds to a drug in the same way.

A molecule is a group of atoms. Atoms have electrons. Electrons follow quantum rules, so predicting their energy is hard. The **Hamiltonian** is the rulebook used to calculate that energy.

This project selects six electron “rooms,” called **orbitals**, from a much bigger calculation. This is a simplified analogy: it does not mean electrons are literally in rooms. Six spatial orbitals become twelve spin orbitals, represented by twelve **qubits**. A qubit is a quantum-information unit used to track possible electron arrangements.

**VQE** is a method that tries a circuit with different adjustable settings and looks for a low energy. **UCCSD** is the particular circuit recipe used here. A **shot** is one repeat of a measurement, like repeating a science experiment. Many different Pauli measurement groups are needed because different parts of the Hamiltonian ask different measurement questions.

What was completed: an ideal calculation and a 57,600-shot run on a local noiseless emulator. What was not completed: mutant comparisons, noisy-emulator work, physical hardware work, biological validation, and medical conclusions. See [GLOSSARY.md](GLOSSARY.md).
