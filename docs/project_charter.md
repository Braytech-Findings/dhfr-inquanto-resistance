# Frozen project charter

Frozen: 2026-07-15

## Primary question

Can mutation-specific electronic interaction signatures calculated with InQuanto explain, and help predict, why TMP and 4-DTMP steer bacterial DHFR resistance along different evolutionary paths?

## Hypotheses

1. The WT-to-L28R electronic interaction-energy change differs between TMP and 4-DTMP.
2. Prespecified electronic descriptors associate with experimental resistance or fitness in an expanded variant panel.
3. Quantum descriptors are useful only if they add held-out predictive information beyond sequence, structure, and competitive classical descriptors.
4. The sign of the primary contrast should survive reasonable structure, cluster, active-space, optimizer, and noise sensitivity analyses.

## Primary endpoint

For a frozen electronic interaction-energy proxy `E_int`:

`D = [E_int(L28R, 4-DTMP) - E_int(WT, 4-DTMP)] - [E_int(L28R, TMP) - E_int(WT, TMP)]`

The exact interaction-energy definition remains **unfrozen** until compact/expanded cluster definitions and fragment/counterpoise conventions pass Gate B/C. Emulator work is prohibited before that freeze.

## Exclusions

No binding-free-energy, physical-hardware, clinical-efficacy, resistance-prevention, new-antibiotic, or quantum-advantage claims. No post-quantum-result variant-panel selection.

