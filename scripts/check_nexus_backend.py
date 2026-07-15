#!/usr/bin/env python3
"""Authenticate to Nexus and check an emulator; does not submit a paid job."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="H2-Emulator")
    parser.add_argument("--login", action="store_true")
    args = parser.parse_args()
    try:
        from qnexus import QuantinuumConfig
        from qnexus.client import auth, devices, projects
    except ImportError as exc:
        raise SystemExit("Install qnexus and the licensed inquanto-nexus extension") from exc
    if args.login:
        auth.login()
    project = projects.get_or_create(name="DHFR InQuanto Resistance", description="DHFR active-space experiments", properties={})
    backend = QuantinuumConfig(device_name=args.device)
    print(f"project={project}; device={args.device}; status={devices.status(backend)}")
    print("No job was submitted. Use the inquanto-nexus workflow after resource estimation and explicit cost review.")


if __name__ == "__main__":
    main()

