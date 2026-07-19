#!/usr/bin/env python3
"""Guarded Quantinuum Nexus Bell-circuit access test.

Dry-run and command validation do not import licensed Quantinuum packages, log in,
or contact Nexus. Hosted execution uses only documented qnexus APIs and an exact
user-group name supplied with --user-group or QNEXUS_USER_GROUP. The script never
guesses or brute-forces group names and cannot bypass Nexus access controls.

H2-1SC is a syntax checker: its counts are artificial and scientifically unusable.
H2-Emulator uses Nexus simulation quota rather than HQCs. Visible/online targets
do not prove execution entitlement.
"""
from __future__ import annotations

import argparse
import math
import os
from datetime import datetime, timezone
from typing import Any

HARDWARE_NAMES = {"H2-1E", "H2-2E", "H2-1", "H2-2", "H1-1"}
SYNTAX_CHECKERS = {"H2-1SC", "H2-2SC"}
NEXUS_EMULATORS = {"H2-EMULATOR", "H1-EMULATOR"}
SUPPORTED_TARGETS = HARDWARE_NAMES | SYNTAX_CHECKERS | NEXUS_EMULATORS
DEFAULT_PROJECT = "ee45224b-05fb-4520-9a0e-45b5be2528c3"
GROUP_ENV = "QNEXUS_USER_GROUP"


def load_nexus() -> tuple[Any, Any]:
    """Import optional licensed/runtime dependencies only for real Nexus calls."""
    try:
        import qnexus as qnx
        from qnexus import QuantinuumConfig
    except ImportError as exc:
        raise SystemExit(
            "Real Nexus access requires qnexus and pytket in the active environment. "
            "Dry-run does not require them. Activate the licensed dhfr-inquanto environment."
        ) from exc
    return qnx, QuantinuumConfig


def bell():
    try:
        from pytket import Circuit
    except ImportError as exc:
        raise SystemExit("pytket is required for a real Nexus Bell test.") from exc
    return Circuit(2, 2).H(0).CX(0, 1).measure_all()


def unique_name(label: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"dhfr-bell-{label}-{stamp}"


def normalize_group(value: str | None) -> str | None:
    value = value.strip() if value else ""
    return value or None


def resolve_user_group(args: argparse.Namespace) -> tuple[str | None, str]:
    cli_group = normalize_group(args.user_group)
    env_group = normalize_group(os.getenv(GROUP_ENV))
    if cli_group and env_group and cli_group != env_group:
        raise SystemExit(
            f"Conflicting user groups: --user-group={cli_group!r} and "
            f"{GROUP_ENV}={env_group!r}. Refusing to guess which is authorized."
        )
    if cli_group:
        return cli_group, "--user-group"
    if env_group:
        return env_group, GROUP_ENV
    if args.require_user_group:
        raise SystemExit(
            "No explicit Nexus user group was supplied. Set the exact group shown in "
            f"Nexus Settings > Organization with --user-group or {GROUP_ENV}."
        )
    return None, "Nexus default group"


def explain_error(exc: Exception, user_group: str | None) -> str:
    text = str(exc).lower()
    if "code 14" in text or "access code 14" in text or "entitlement" in text:
        if user_group:
            return (
                "Nexus rejected execution under the supplied group. The group name may be "
                "incorrect, the account may not belong to it, or the target may not be included."
            )
        return (
            "Nexus rejected execution under the default group with access code 14. Run the "
            f"same command with the exact authorized QuantumCT/SCSU Nexus group using "
            f"--user-group or {GROUP_ENV}."
        )
    if "quota" in text or "depleted" in text:
        return (
            "The selected user/default group has no available quota for this operation. "
            "H2-Emulator uses Nexus simulation time; Quantinuum hardware uses HQCs."
        )
    if "group" in text:
        return (
            "Nexus rejected the user-group assignment. Use the exact group identifier shown "
            "under Nexus Settings > Organization; teams and project roles are not quota groups."
        )
    if "auth" in text or "login" in text or "token" in text:
        return "Authentication appears expired; rerun through the normal qnexus browser login flow."
    return f"Nexus operation failed: {type(exc).__name__}: {exc}"


def project_for(qnx: Any, args: argparse.Namespace):
    return (
        qnx.projects.get(id=args.project_id)
        if args.project_id
        else qnx.projects.get(name=args.project_name)
    )


def display_frame(label: str, value: Any) -> None:
    try:
        frame = value.df() if hasattr(value, "df") else value
        print(f"\n{label}:\n{frame.to_string(index=False)}")
    except Exception as exc:
        print(f"\n{label}: unavailable ({type(exc).__name__}: {exc})")


def access_report(args: argparse.Namespace) -> None:
    qnx, _ = load_nexus()
    group, source = resolve_user_group(args)
    try:
        qnx.login()
        user = qnx.users.get_self()
        print(f"Authenticated Nexus user ID: {user.id}")
        print(f"Submission group: {group or '<default>'} (source: {source})")
        display_frame("User quotas", qnx.quotas.get_all())
        for quota_name in ("compilation", "simulation"):
            try:
                available = qnx.quotas.check_quota(name=quota_name)
            except Exception as exc:
                print(f"{quota_name} quota guard: unavailable ({type(exc).__name__}: {exc})")
            else:
                print(f"{quota_name} quota guard: {available}")
        devices = qnx.devices.get_all().df()
        if "device_name" in devices.columns:
            devices = devices[
                devices["device_name"].astype(str).str.upper().isin(SUPPORTED_TARGETS)
            ]
        display_frame("Relevant visible devices", devices)
        print(
            "\nGroup discovery note: qnexus exposes user quotas but no documented public "
            "group-list API. The exact authorized group is shown in Nexus Settings > Organization."
        )
    except Exception as exc:
        raise SystemExit(explain_error(exc, group)) from exc


def wait_and_print(qnx: Any, job: Any, project: Any, timeout: int) -> None:
    status = qnx.jobs.wait_for(job, timeout=timeout)
    status_name = status.status.value
    print(f"Status: {status_name}; reported cost: {status.cost}")
    print(f"Nexus job URL: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}")
    if "COMPLETED" not in status_name.upper() and "COMPLETED" not in str(status).upper():
        raise SystemExit("Job did not complete; inspect the Nexus job URL.")
    references = qnx.jobs.results(job)
    result = references[0].download_result()
    print("Counts:", {str(key): int(value) for key, value in result.get_counts().items()})


def estimate_hqc(qnx: Any, compiled: Any, config: Any, project: Any, args: argparse.Namespace) -> float:
    backend = args.backend.upper()
    if backend in SYNTAX_CHECKERS:
        print("Estimated HQC cost: 0 (syntax-checker submissions do not consume HQCs).")
        return 0.0
    if backend in NEXUS_EMULATORS:
        print("Estimated HQC cost: 0 (Nexus-hosted emulator uses simulation-time quota).")
        return 0.0
    estimated = qnx.circuits.cost(
        circuit_ref=compiled[0],
        n_shots=args.shots,
        backend_config=config,
        project=project,
    )
    if estimated is None:
        raise SystemExit("Nexus did not return an HQC estimate; refusing hardware execution.")
    estimated_float = float(estimated)
    print(f"Estimated HQC cost: {estimated_float} (maximum allowed: {args.max_hqc})")
    return estimated_float


def hosted_bell(args: argparse.Namespace) -> None:
    backend = args.backend.upper()
    if backend not in SUPPORTED_TARGETS:
        raise SystemExit(f"Unsupported guarded target {args.backend!r}.")
    if backend in HARDWARE_NAMES and not args.confirm_hardware:
        raise SystemExit(
            "H2-1E/H2-2E or physical hardware requires --confirm-hardware and --confirm-submit."
        )
    if args.shots <= 0:
        raise SystemExit("--shots must be positive.")
    if args.max_hqc < 0:
        raise SystemExit("--max-hqc must be non-negative.")
    if backend in HARDWARE_NAMES and args.max_hqc <= 0:
        raise SystemExit("Hardware/high-performance emulators require a positive --max-hqc.")

    group, source = resolve_user_group(args)
    print(f"Submission group: {group or '<default>'} (source: {source})")

    if args.dry_run:
        print(
            "DRY RUN: Bell circuit width=2, gates=4, depth=3. "
            "No qnexus import, login, upload, compile, cost request, or execution occurred."
        )
        return
    if not args.confirm_submit:
        raise SystemExit("Hosted execution requires --confirm-submit. Use --dry-run first.")

    qnx, QuantinuumConfig = load_nexus()
    try:
        qnx.login()
        project = project_for(qnx, args)
        circuit = bell()
        stamp = unique_name(backend.lower())
        print(
            f"Backend: {args.backend}; width={circuit.n_qubits}; "
            f"gates={circuit.n_gates}; depth={circuit.depth()}"
        )
        uploaded = qnx.circuits.upload(
            circuit=circuit,
            project=project,
            name=f"{stamp}-circuit",
        )

        hardware_hqc_ceiling = min(args.max_hqc, 20_000.0)
        config_kwargs: dict[str, Any] = {"device_name": args.backend}
        if backend in HARDWARE_NAMES and args.max_hqc > 0:
            config_kwargs["max_cost"] = math.ceil(hardware_hqc_ceiling)
        config = QuantinuumConfig(**config_kwargs)

        compiled = qnx.compile(
            programs=uploaded,
            backend_config=config,
            project=project,
            name=f"{stamp}-compile",
            optimisation_level=0,
            user_group=group,
            timeout=args.timeout,
        )
        compiled_circuit = compiled[0].download_circuit()
        print(
            f"Compiled width={compiled_circuit.n_qubits}; "
            f"gates={compiled_circuit.n_gates}; depth={compiled_circuit.depth()}"
        )

        estimated = estimate_hqc(qnx, compiled, config, project, args)
        if backend in HARDWARE_NAMES:
            print(f"Enforced hardware HQC ceiling: {hardware_hqc_ceiling}")
        if estimated > hardware_hqc_ceiling:
            raise SystemExit("Estimated HQC cost exceeds --max-hqc; refusing execution.")

        if backend in NEXUS_EMULATORS:
            print("H2-Emulator uses simulation-time quota, not HQCs; submitting directly after compilation.")

        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=args.shots,
            backend_config=config,
            project=project,
            name=f"{stamp}-execute",
            user_group=group,
        )
        print(f"Submitted Nexus job {job.id}")
        print(f"Nexus job URL: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}")
        if backend in SYNTAX_CHECKERS:
            print(
                "Syntax-checker counts are artificial all-zero validation output and are "
                "scientifically unusable."
            )
        if args.wait:
            wait_and_print(qnx, job, project, args.timeout)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(explain_error(exc, group)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--access-report", action="store_true")
    modes.add_argument("--nexus-emulator", action="store_true")
    modes.add_argument("--local-emulator", action="store_true")
    parser.add_argument("--backend", default="H2-1SC")
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT)
    parser.add_argument("--project-name", default="dhfr-h2-hardware")
    parser.add_argument("--user-group")
    parser.add_argument(
        "--require-user-group",
        action="store_true",
        help=f"Refuse default-group submission; require --user-group or {GROUP_ENV}.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
    parser.add_argument("--confirm-hardware", action="store_true")
    parser.add_argument("--max-hqc", type=float, default=0.0)
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.access_report:
        access_report(args)
        return
    if args.nexus_emulator:
        hosted_bell(args)
        return
    if args.local_emulator:
        raise SystemExit(
            "Use scripts/run_h2_smoke.py for the existing local test; "
            "this script guards Nexus-hosted execution."
        )
    qnx, _ = load_nexus()
    qnx.login()
    devices = qnx.devices.get_all().df()
    print(devices.to_string(index=False))


if __name__ == "__main__":
    main()
