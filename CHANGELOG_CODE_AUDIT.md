# Code Audit Changelog

## 2026-07-21

- Inventoried 80 maintained logic/configuration artifacts and separated
  downloaded upstream code from maintained project code.
- Added local shared rules for four system IDs, punctuation aliases, backend
  classification, shot totals, access errors, checksums, JSON loading, and the
  protected WT_TMP benchmark.
- Changed the Nexus access helper's no-argument behavior from implicit login and
  device discovery to an offline help message.
- Classified access code 14 as access/entitlement rather than scientific failure.
- Made local QASM sampling validate system names and positive shots and record
  an unambiguous local-emulator label.
- Made measurement-plan preparation reject unreviewed systems, invalid shot
  counts, and unconverged RHF rather than continuing silently.
- Made endpoint bootstrap analysis require at least two labeled independent
  replicates per system and define its uncertainty method.
- Replaced unordered set iteration in endpoint resampling so a fixed seed is
  reproducible across separate Python processes.
- Added tests for safety, naming, backends, shot arithmetic, corrupt/missing
  JSON, checksums, protected evidence, placeholder rejection, and remote guards.
- Added audit, backend, scientific, environment, command, walkthrough, and open
  decision documentation. Historical scientific outputs were preserved.
