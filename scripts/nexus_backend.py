#!/usr/bin/env python3
"""Resolve Nexus backend requests without aliases, fallback, or network access."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


BACKEND_CATALOG = {
    "H2-Emulator": ("nexus_hosted", "emulator", True),
    "H1-Emulator": ("nexus_hosted", "emulator", True),
    "H2-1SC": ("quantinuum_hosted", "syntax_checker", False),
    "H2-2SC": ("quantinuum_hosted", "syntax_checker", False),
    "H2-1E": ("quantinuum_hosted", "hardware", True),
    "H2-2E": ("quantinuum_hosted", "hardware", True),
    "H2-1": ("quantinuum_hosted", "hardware", True),
    "H2-2": ("quantinuum_hosted", "hardware", True),
    "H1-1": ("quantinuum_hosted", "hardware", True),
    "H2-1LE": ("local", "noiseless_emulator", False),
}


@dataclass(frozen=True)
class BackendResolution:
    """One immutable backend decision used for compilation and execution."""

    requested_backend: str
    resolved_backend: str
    hosting_type: str
    backend_type: str
    location: str
    project_id: str | None
    project_name: str | None
    user_group: str | None
    may_consume_credits: bool
    entitlement_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_backend(
    requested: str,
    *,
    project_id: str | None = None,
    project_name: str | None = None,
    user_group: str | None = None,
    entitlement_verified: bool = False,
) -> BackendResolution:
    """Resolve an exact catalog name; never rewrite or choose a fallback."""
    requested = requested.strip()
    if requested not in BACKEND_CATALOG:
        case_match = next(
            (name for name in BACKEND_CATALOG if name.casefold() == requested.casefold()),
            None,
        )
        hint = f" Use exact spelling {case_match!r}." if case_match else ""
        raise ValueError(f"Unsupported backend {requested!r}.{hint}")
    hosting, backend_type, credits = BACKEND_CATALOG[requested]
    return BackendResolution(
        requested_backend=requested,
        resolved_backend=requested,
        hosting_type=hosting,
        backend_type=backend_type,
        location="local" if hosting == "local" else "remote",
        project_id=project_id,
        project_name=project_name,
        user_group=user_group,
        may_consume_credits=credits,
        entitlement_verified=entitlement_verified,
    )


def require_nexus_emulator(resolution: BackendResolution) -> None:
    """Reject syntax checkers, hardware, local emulators, and silent fallback."""
    if resolution.hosting_type != "nexus_hosted" or resolution.backend_type != "emulator":
        raise ValueError(
            "--nexus-emulator requires exactly a Nexus-hosted emulator such as "
            "H2-Emulator or H1-Emulator; syntax checkers and hardware are incompatible."
        )


def backend_is_visible(resolution: BackendResolution, visible_names: list[str]) -> bool:
    """Check exact catalog visibility without treating it as entitlement."""
    return resolution.resolved_backend in visible_names
