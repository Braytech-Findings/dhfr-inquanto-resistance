#!/usr/bin/env python3
"""Guarded Quantinuum Nexus-hosted emulator Bell-circuit access test.

Dry-run and command validation do not import licensed Quantinuum packages, log in,
or contact Nexus. Remote execution is intentionally limited to the SCSU-accessible
Nexus-hosted endpoints H2-Emulator and H1-Emulator. Hardware-tier emulator names
ending in ``E`` are not accepted by this script.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from typing import Any

NEXUS_EMULATORS = {
    "H2-EMULATOR": "H2-Emulator",
    "H1-EMULATOR": "H1-Emulator",
}
GROUP_ENV = "QNEXUS_USER_GROUP"
PROJECT_ID_ENV = "QNEXUS_PROJECT_ID"
PROJECT_NAME_ENV = "QNEXUS_PROJECT_NAME"


def load_nexus() -> tuple[Any, Any]:
    """Import optional runtime dependencies only for a real Nexus call."""
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


def normalize_value(value: str | None) -> str | None:
    value = value.strip() if value else ""
    return value or None


def canonical_backend(value: str) -> str:
    key = value.strip().upper()
    if key not in NEXUS_EMULATORS:
        allowed = ", ".join(NEXUS_EMULATORS.values())
        raise SystemExit(
            f"Unsupported endpoint {value!r}. Use a Nexus-hosted emulator: {allowed}. "
            "Do not use hardware-tier emulator names ending in 'E'."
        )
    return NEXUS_EMULATORS[key]


def resolve_user_group(args: argparse.Namespace) -> tuple[str | None, str]:
    cli_group = normalize_value(args.user_group)
    env_group = normalize_value(os.getenv(GROUP_ENV))
    if cli_group:
        return cli_group, "--user-group"
    if env_group:
        return env_group, GROUP_ENV
    if args.require_user_group:
        raise SystemExit(
            "No explicit Nexus user group was supplied. Set the exact authorized group "
            f"with --user-group or {GROUP_ENV}."
        )
    return None, "Nexus default group"


def resolve_project_selection(
    args: argparse.Namespace,
) -> tuple[str | None, str | None, str]:
    cli_id = normalize_value(args.project_id)
    cli_name = normalize_value(args.project_name)
    if cli_id and cli_name:
        raise SystemExit("Provide only one of --project-id or --project-name.")
    if cli_id:
        return cli_id, None, "--project-id"
    if cli_name:
        return None, cli_name, "--project-name"

    env_id = normalize_value(os.getenv(PROJECT_ID_ENV))
    env_name = normalize_value(os.getenv(PROJECT_NAME_ENV))
    if env_id and env_name:
        raise SystemExit(
            f"Set only one of {PROJECT_ID_ENV} or {PROJECT_NAME_ENV}; "
            "refusing ambiguous project selection."
        )
    if env_id:
        return env_id, None, PROJECT_ID_ENV
    if env_name:
        return None, env_name, PROJECT_NAME_ENV
    return None, None, "missing"


def explain_error(exc: Exception, user_group: str | None) -> str:
    text = str(exc).lower()
    if "code 14" in text or "access code 14" in text or "entitlement" in text:
        return (
            "Nexus rejected the job's entitlement. Confirm that the exact endpoint is "
            "H2-Emulator or H1-Emulator, then verify the project and user group with "
            "the SCSU Nexus administrator or Quantinuum support."
        )
    if "quota" in text or "depleted" in text:
        return (
            "The selected group has no available Nexus simulation-time quota. "
            "H2-Emulator and H1-Emulator are costed in seconds, not HQCs."
        )
    if "group" in text:
        return (
            "Nexus rejected the user-group assignment. Use the exact authorized group "
            "identifier; a team or organization display name may not be a quota group."
        )
    if "auth" in text or "login" in text or "token" in text:
        return "Authentication appears expired; rerun the normal qnexus browser login flow."
    return f"Nexus operation failed: {type(exc).__name__}: {exc}"


def project_for(qnx: Any, args: argparse.Namespace):
    project_id, project_name, source = resolve_project_selection(args)
    print(f"Project selection source: {source}")
    if project_id:
        return qnx.projects.get(id=project_id)
    if project_name:
        return qnx.projects.get(name=project_name)
    raise SystemExit(
        "Set an authorized project through --project-id, --project-name, "
        f"{PROJECT_ID_ENV}, or {PROJECT_NAME_ENV}."
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
        print("Authenticated Nexus session: available")
        print(f"Submission group: {group or '<default>'} (source: {source})")
        display_frame("User quotas", qnx.quotas.get_all())
        for quota_name in ("compilation", "simulation"):
            try:
                available = qnx.quotas.check_quota(name=quota_name)
            except Exception as exc:
                print(
                    f"{quota_name} quota guard: unavailable "
                    f"({type(exc).__name__}: {exc})"
                )
            else:
                print(f"{quota_name} quota guard: {available}")

        devices = qnx.devices.get_all().df()
        if "device_name" in devices.columns:
            devices = devices[
                devices["device_name"].astype(str).str.upper().isin(NEXUS_EMULATORS)
            ]
        display_frame("SCSU Nexus-hosted emulator targets", devices)
        print(
            "\nUse H2-Emulator by default. H1-Emulator is the supported fallback. "
            "Hardware-tier emulator endpoints ending in E are intentionally excluded."
        )
    except Exception as exc:
        raise SystemExit(explain_error(exc, group)) from exc


def wait_and_print(qnx: Any, job: Any, project: Any, timeout: int) -> None:
    status = qnx.jobs.wait_for(job, timeout=timeout)
    status_name = status.status.value
    print(f"Status: {status_name}; reported cost: {status.cost}")
    print(
        f"Nexus job URL: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}"
    )
    if (
        "COMPLETED" not in status_name.upper()
        and "COMPLETED" not in str(status).upper()
    ):
        raise SystemExit("Job did not complete; inspect the Nexus job URL.")
    references = qnx.jobs.results(job)
    result = references[0].download_result()
    print(
        "Counts:", {str(key): int(value) for key, value in result.get_counts().items()}
    )


def hosted_bell(args: argparse.Namespace) -> None:
    backend = canonical_backend(args.backend)
    if args.shots <= 0:
        raise SystemExit("--shots must be positive.")

    group, source = resolve_user_group(args)
    print(f"Submission group: {group or '<default>'} (source: {source})")
    print(f"Backend: {backend}; width=2; gates=4; depth=3; shots={args.shots}")

    if args.dry_run:
        print(
            "DRY RUN: no qnexus import, login, upload, compile, quota use, "
            "or execution occurred."
        )
        return
    if not args.confirm_submit:
        raise SystemExit(
            "Hosted execution requires --confirm-submit. Use --dry-run first."
        )

    qnx, QuantinuumConfig = load_nexus()
    try:
        qnx.login()
        project = project_for(qnx, args)
        circuit = bell()
        stamp = unique_name(backend.lower())
        uploaded = qnx.circuits.upload(
            circuit=circuit,
            project=project,
            name=f"{stamp}-circuit",
        )
        config = QuantinuumConfig(device_name=backend)
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
        print(
            f"{backend} uses Nexus simulation-time quota measured in seconds, not HQCs."
        )
        job = qnx.start_execute_job(
            programs=compiled,
            n_shots=args.shots,
            backend_config=config,
            project=project,
            name=f"{stamp}-execute",
            user_group=group,
        )
        print(f"Submitted Nexus job {job.id}")
        print(
            f"Nexus job URL: https://nexus.quantinuum.com/projects/{project.id}/jobs/{job.id}"
        )
        if args.wait:
            wait_and_print(qnx, job, project, args.timeout)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(explain_error(exc, group)) from exc


def discover_devices() -> None:
    qnx, _ = load_nexus()
    qnx.login()
    devices = qnx.devices.get_all().df()
    print(devices.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--access-report", action="store_true")
    modes.add_argument(
        "--nexus-emulator",
        "--hosted-emulator",
        dest="nexus_emulator",
        action="store_true",
    )
    modes.add_argument("--local-emulator", action="store_true")
    parser.add_argument("--backend", default="H2-Emulator")
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--project-id")
    parser.add_argument("--project-name")
    parser.add_argument("--user-group")
    parser.add_argument(
        "--require-user-group",
        action="store_true",
        help=f"Refuse default-group submission; require --user-group or {GROUP_ENV}.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-submit", action="store_true")
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
            "Use scripts/run_h2_smoke.py for the existing local H2-1LE test; "
            "this script is limited to Nexus-hosted H2-Emulator and H1-Emulator."
        )
    discover_devices()


if __name__ == "__main__":
    main()
