#!/usr/bin/env python3
"""Create a sanitized, discovery-only Quantinuum Nexus access report."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import qnexus as qnx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "quantinuum_access"


def package_versions() -> dict[str, str]:
    result = {}
    for name in ("qnexus", "inquanto", "pytket", "pytket-quantinuum", "pytket-qiskit"):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = "not installed"
    return result


def dataframe_rows(fetcher, label: str) -> tuple[list[dict], str | None]:
    try:
        value = fetcher()
        frame = value.df() if hasattr(value, "df") else value
        return json.loads(frame.to_json(orient="records", date_format="iso")), None
    except Exception as exc:  # Diagnostic must report unavailable APIs, not guess.
        return [], f"{label}: {type(exc).__name__}: {exc}"


def write_csv(name: str, rows: list[dict]) -> None:
    try:
        import pandas as pd
        pd.DataFrame(rows).to_csv(OUT / name, index=False)
    except Exception:
        (OUT / name).write_text("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitized Quantinuum Nexus discovery")
    parser.add_argument("--login", action="store_true", help="Use normal qnexus browser login if required")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    authenticated = False
    try:
        if args.login:
            qnx.login()
        # A documented authenticated call is safer than inspecting credentials.
        quota_rows, quota_error = dataframe_rows(qnx.quotas.get_all, "quotas")
        authenticated = quota_error is None
        if quota_error:
            errors.append(quota_error)
    except Exception as exc:
        quota_rows = []
        errors.append(f"authentication: {type(exc).__name__}: {exc}")

    project_rows, project_error = dataframe_rows(qnx.projects.get_all, "projects")
    device_rows, device_error = dataframe_rows(qnx.devices.get_all, "devices")
    for error in (project_error, device_error):
        if error:
            errors.append(error)
    write_csv("quotas.csv", quota_rows)
    write_csv("projects.csv", project_rows)
    write_csv("available_targets.csv", device_rows)
    write_csv("groups.csv", [])  # qnexus 0.46.0 exposes no documented groups module.
    (OUT / "software_versions.json").write_text(json.dumps(package_versions(), indent=2) + "\n")
    (OUT / "error_history.json").write_text(json.dumps(errors, indent=2) + "\n")
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "authenticated": authenticated, "authentication_method": "normal qnexus session/browser flow only", "platform": platform.platform(), "python": sys.version, "quotas": len(quota_rows), "projects": len(project_rows), "visible_targets": len(device_rows), "errors": errors, "security": "No tokens, cookies, API keys, or credential objects were inspected or written."}
    (OUT / "access_report.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "access_report.md").write_text("# Quantinuum access diagnostic\n\n" + "\n".join(f"- **{key}**: {value}" for key, value in report.items() if key != "errors") + "\n\n## Errors or unavailable endpoints\n" + "\n".join(f"- {error}" for error in errors) + "\n")
    (OUT / "support_packet.md").write_text("# Sanitized support packet\n\nProject: `dhfr-h2-hardware` (`ee45224b-05fb-4520-9a0e-45b5be2528c3`)\n\nPrevious H2-1E job: `ed5127b9-8b92-4ad3-b0a4-02a5d3202586` returned machine-access code 14. This report lists visible targets and quota API results without credentials. Ask the organization administrator/Quantinuum support whether the account has a hardware machine entitlement, a simulation-time allocation, and the required user-group assignment.\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
