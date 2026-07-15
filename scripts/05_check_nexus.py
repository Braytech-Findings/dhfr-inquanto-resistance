#!/usr/bin/env python3
"""Report Nexus authentication, visible devices, and quotas without submitting."""

from __future__ import annotations

import importlib.metadata as metadata

import qnexus as qnx


def main() -> None:
    if not qnx.auth.is_logged_in():
        raise SystemExit("Not logged in. Run: python -c 'import qnexus as q; q.login()'")
    print(f"qnexus {metadata.version('qnexus')} | authenticated")
    print("\nVisible devices")
    devices = qnx.devices.get_all()
    print(devices.df().to_string(index=False) if len(devices) else "No devices returned")
    print("\nQuotas")
    quotas = qnx.quotas.get_all()
    print(quotas.df().to_string(index=False) if len(quotas) else "No quotas returned")
    print("\nRead-only check complete; no circuit, compilation, or execution job was submitted.")


if __name__ == "__main__":
    main()
