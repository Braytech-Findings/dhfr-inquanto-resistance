# Failure and Blocker Log

- `blocked_by_decision`: production active-space correspondence is not resolved for all four systems.
- `blocked_by_missing_evidence`: WT_4DTMP, L28R_TMP, and L28R_4DTMP lack Hamiltonians, saved VQE parameters, QASM, and local quantum results.
- `blocked_by_access`: no current live Nexus catalog or entitlement proof was collected because this pass was not authorized to authenticate or contact Nexus.
- `blocked_by_reproducibility`: current Python is 3.13 while the declared/historical environment uses Python 3.11 and licensed packages.
- `not_attempted_expensive`: the 12.7-hour historical finite-shot workflow was not rerun.
- `blocked_by_missing_evidence`: four-system local QASM preflight stopped before
  execution because WT_4DTMP, L28R_TMP, and L28R_4DTMP QASM files are missing.
- `not_applicable`: no remote submission, hardware execution, or paid action was attempted.
- `dependency`: `pip check` reports `quantum-architecture-comparison 0.1.0`
  requires Qiskit `<2`, while this mixed shell has Qiskit 2.5.0.
- `type_check`: the repository has no configured MyPy target; an attempted
  whole-tree run found 163 errors across 48 files, dominated by unavailable
  stubs/private scientific modules and existing annotations. Runtime tests,
  compilation, Ruff lint, and Ruff formatting pass, but static typing is not
  clean.
- `sandbox_then_resolved`: notebook kernels initially could not bind loopback
  ports inside the restricted sandbox. Approved local kernel execution was
  rerun successfully; no external network was used.
