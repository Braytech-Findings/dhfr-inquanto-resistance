# Optional IonQ Toolchain

This repository keeps IonQ support optional and submission-safe. The public
`dhfr-qc` environment can install the official Qiskit provider for IonQ, create
local compilation reports, and prepare multicircuit inputs without consuming
credits.

## Install or update

```bash
conda env update -f environment.yml --prune
conda activate dhfr-qc
```

The environment uses Python 3.11, Qiskit 2.x, and `qiskit-ionq` 1.1.1.

Verify the installation without an IonQ account or API key:

```bash
python scripts/check_ionq_environment.py \
  --backend simulator \
  --output results/ionq/preflight.json
```

This command builds and locally transpiles small Bell and GHZ test circuits. It
does not call `backend.run()` and cannot submit a job.

## Credentials

An API key is not required for installation or local preflight work. After an
IonQ project is approved, place the key only in the shell environment:

```bash
export IONQ_API_KEY="..."
```

Never place a real key in `.env.example`, source code, notebooks, issue text, or
committed files. The verification scripts report only whether a key exists and
never print its value.

## Create a compilation report

Export real project circuits as OpenQASM 2 (`.qasm`), OpenQASM 3 (`.qasm3`), or
Qiskit QPY (`.qpy`). Then run:

```bash
python scripts/ionq_compile_report.py \
  circuits/wt_tmp_4q.qpy \
  --backend qpu.forte-1 \
  --optimization-level 1 \
  --output-json results/ionq/wt_tmp_4q_compilation.json \
  --output-csv results/ionq/wt_tmp_4q_compilation.csv
```

The report contains:

- number of circuits and qubits;
- total circuit depth;
- two-qubit-gate depth;
- total and two-qubit gate counts;
- median, 95th-percentile, and maximum two-qubit metrics.

IonQ recommends Qiskit transpilation optimization level 0 or 1 before its own
compiler. These scripts reject higher levels.

## Important interpretation

The report is a local Qiskit preflight estimate. It is not a physical-hardware
result, a final IonQ compiler report, or a guaranteed resource charge. Final
system-specific counts and costs must be confirmed with IonQ after account and
target access are available.

## Safe execution boundary

The two IonQ scripts in this repository are intentionally no-submit utilities.
They do not contain a simulator or QPU submission code path. A separate,
reviewed submission script should be created only after:

1. the active space and circuit family are frozen;
2. local exact and finite-shot checks pass;
3. IonQ confirms the target and credit allocation;
4. a human explicitly approves the job payload and shot count.
