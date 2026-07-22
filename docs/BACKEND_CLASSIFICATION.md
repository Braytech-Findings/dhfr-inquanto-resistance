# Backend Classification

Backend visibility, authentication, compilation, job creation, and job
completion are different events. None proves the next event occurred.

| Kind | Location | Meaning | Evidence it can support |
|---|---|---|---|
| Local noiseless emulator | Local | Software reproduces a target interface without modeled noise | Local circuit/finite-shot result only |
| Local noisy simulator | Local | Software samples a documented noise model | Result for that model only |
| Hosted emulator | Remote | Provider runs a simulation; quota may be used | Hosted emulation after a completed saved result |
| Syntax checker | Remote or local | Checks accepted instructions; counts may be artificial | Syntax/compatibility only |
| Compiler-only | Local or remote | Translates a circuit | Compilation/resource report only |
| Physical hardware | Remote | A quantum processor executes a completed job | Hardware result only with completed-job artifact |
| Unknown/unverified | Unknown | Identity or execution evidence is incomplete | No backend claim |

`H2-1LE` in this repository means **Quantinuum H2-1LE local noiseless
emulator**. It is not H2 hardware and is not a hosted Nexus run. `H2-1SC` is a
syntax checker. `H2-Emulator` is a Nexus-hosted emulator. Names ending in `E`,
such as `H2-1E`, are guarded physical-hardware targets in the access helper.

Remote submission requires `--confirm-submit`. Hardware additionally requires
`--confirm-hardware` and a positive `--max-hqc`. No audit command used these
flags. Access code 14 is classified as `access_or_entitlement`; it is not a
failure of molecular science code.

