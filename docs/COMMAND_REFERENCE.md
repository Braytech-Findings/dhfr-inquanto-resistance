# Command Reference

Run commands from the repository root. Commands marked **tested in audit** were
executed without remote work. Scientific production commands requiring licensed
software or long calculations were syntax/help checked only.

## Setup and validation

`conda env create -f environment.yml` downloads and installs the local public
environment; it may take time but consumes no quantum credits. It creates a
Conda environment, not result data.

`python -m pytest -q` runs local tests. **Tested in audit:** baseline `20 passed,
1 skipped`; final count is recorded in `FULL_CODE_AUDIT.md`.

`python -m compileall -q scripts tests` checks Python syntax. Success is silent.
It does not prove scientific correctness.

`python scripts/validate_repository.py` validates required files, protected
WT_TMP metadata, shot arithmetic, secret-like tracked names, remote guards, and
tests. **Tested in audit.** It creates no scientific result.

## Systems and local paths

`python -c "from scripts.audit_core import SYSTEMS; print(*SYSTEMS, sep='\n')"`
lists the four approved IDs. **Tested indirectly by unit tests.**

`python scripts/test_quantinuum_access.py` now prints help and exits without a
login or network request. **Tested in audit.** This is the default dry path.

`python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1SC
--dry-run` previews syntax-checker settings. It imports no Nexus client and
submits nothing. Syntax-checker readiness is not molecular evidence.

`python scripts/run_local_h2.py --help` describes local QASM sampling. A real
run uses `--system WT_TMP --shots 100`; `--recompile` ignores cached local
compilation. It creates a timestamped local counts JSON. Counts alone are not
an energy result.

`python scripts/prepare_local_pauli_energy.py --system WT_TMP
--shots-per-circuit 100` builds QASM/measurement protocol artifacts locally. It
may be expensive and needs the licensed stack. It does not submit anything.

`python scripts/run_local_pauli_energy.py --help` describes the historical
verified local WT_TMP workflow. Reproduction is computationally expensive and
may overwrite named result artifacts; archive results first. `H2-1LE` here is
local and noiseless.

## Figures and manifests

`python scripts/build_publication_assets.py` regenerates WT_TMP publication
tables, figures, and manifests from saved verified JSON. **Its associated tests
were run in audit.** Success creates PNG/PDF/CSV/JSON under
`results/publication/`; it does not add evidence for the other systems.

`python -c "from pathlib import Path; from scripts.audit_core import sha256_file;
p=Path('results/publication/data/verified_quantum_provenance.json');
print(sha256_file(p))"` prints a checksum without changing the file.

## Authentication and remote safeguards

`python scripts/test_quantinuum_access.py --discover` explicitly logs in and
queries visible devices. It can contact Nexus but does not submit a circuit.
Authentication and visibility do not prove entitlement.

Any intentional remote Bell submission must add `--confirm-submit`; hardware
also needs `--confirm-hardware --max-hqc LIMIT`. Always use the identical
command with `--dry-run` first. This reference deliberately provides no
automatic paid submission command. No remote command was executed in the audit.

