# Start here: the DHFR project in simple words

## What are we asking?

DHFR is a protein. A protein is like a tiny machine. TMP and 4-DTMP are two
related molecules that can sit near this machine. We ask whether changing one
part of DHFR—from WT to L28R—changes how the two molecules interact with our
simplified computer model.

## What did we compare?

We made four computer models:

1. WT with TMP
2. WT with 4-DTMP
3. L28R with TMP
4. L28R with 4-DTMP

This is like comparing two locks with two related keys.

## What did we find?

The small classical calculation says the protein change did not affect both
ligands in the same way. The measured comparison is about `-0.055 Hartree`.
That is a useful clue inside this model.

It is not proof that one drug works better. It is not a test in bacteria,
an animal, or a person. It is not a binding-free-energy calculation.

## Where does quantum computing fit?

One quantum model, `WT_TMP`, was checked very carefully. Its 1,818 measured
pieces matched the exact calculation, and using more simulated measurements
made its answer steadier. The other three systems do not yet have matching
finished quantum-energy results.

Two large remote molecular attempts timed out. The first WT_TMP measurement
group is now divided into ten smaller cloud jobs. They do not need the
researcher's computer to stay on, and they are not included in any conclusion
until every saved result is retrieved and checked.

## See the evidence

- [Read the plain-language results](PLAIN_LANGUAGE_RESULTS.md)
- [See all three main graphs](site/figures.html)
- [Open the four public structure files](../visualization/public_structures/)
- [Read what the project cannot prove](LIMITATIONS.md)
- [See the technical reproduction instructions](REPRODUCIBILITY.md)

The rule throughout this repository is simple: say what the data show, label
what is missing, and never turn a missing value into zero.
