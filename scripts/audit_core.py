#!/usr/bin/env python3
"""Shared safety and provenance rules for the DHFR workflows.

This local-only module gives scripts one source of truth for molecular-system
names, backend labels, shot arithmetic, checksums, and the protected WT_TMP
benchmark. It reads values and returns metadata; it never contacts a service,
submits a job, or changes a scientific result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SYSTEMS = ("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")
SYSTEM_ALIASES = {
    "WT_4-DTMP": "WT_4DTMP",
    "WT_4′DTMP": "WT_4DTMP",
    "L28R_4-DTMP": "L28R_4DTMP",
    "L28R_4′DTMP": "L28R_4DTMP",
}

VERIFIED_WT_TMP = {
    "ideal_vqe_energy_hartree": -2587.912001526413,
    "finite_shot_energy_hartree": -2587.917118821447,
    "standard_error_hartree": 0.007647045141,
    "measurement_circuits": 576,
    "shots_per_circuit": 100,
    "total_shots": 57_600,
    "backend": "Quantinuum H2-1LE local noiseless emulator",
}

_BACKENDS = {
    "H2-1LE": {
        "label": "Quantinuum H2-1LE local noiseless emulator",
        "location": "local",
        "kind": "noiseless_emulator",
        "physical_hardware": False,
        "may_consume_credits": False,
    },
    "H2-EMULATOR": {
        "label": "Quantinuum Nexus hosted H2 emulator",
        "location": "remote",
        "kind": "hosted_emulator",
        "physical_hardware": False,
        "may_consume_credits": True,
    },
    "H2-1SC": {
        "label": "Quantinuum H2-1 syntax checker",
        "location": "remote",
        "kind": "syntax_checker",
        "physical_hardware": False,
        "may_consume_credits": False,
    },
}


def canonical_system(value: str) -> str:
    """Return one approved system ID or raise a clear error.

    Common punctuation aliases for 4′-DTMP are accepted. Unknown values are
    rejected before they can become misleading file names or result labels.
    """
    candidate = value.strip()
    canonical = SYSTEM_ALIASES.get(candidate, candidate)
    if canonical not in SYSTEMS:
        raise ValueError(
            f"Unknown molecular system {value!r}; choose one of: {', '.join(SYSTEMS)}"
        )
    return canonical


def total_shots(circuits: int, shots_per_circuit: int, replicates: int = 1) -> int:
    """Calculate circuits × shots per circuit × independent job replicates."""
    values = (circuits, shots_per_circuit, replicates)
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TypeError("circuits, shots_per_circuit, and replicates must be integers")
    if circuits < 0 or shots_per_circuit <= 0 or replicates <= 0:
        raise ValueError(
            "circuits cannot be negative; shots_per_circuit and replicates must be positive"
        )
    return circuits * shots_per_circuit * replicates


def backend_metadata(name: str) -> dict[str, Any]:
    """Describe a backend without claiming that it was actually used."""
    key = name.strip().upper()
    if key in _BACKENDS:
        return {"name": name, **_BACKENDS[key]}
    if key.endswith("SC"):
        kind = "syntax_checker"
    elif key.endswith("EMULATOR"):
        kind = "hosted_emulator"
    elif key.endswith("E") or key in {"H1-1", "H2-1", "H2-2"}:
        kind = "physical_hardware"
    else:
        kind = "unknown_unverified"
    return {
        "name": name,
        "label": f"Unverified backend identifier: {name}",
        "location": "remote" if kind != "unknown_unverified" else "unknown",
        "kind": kind,
        "physical_hardware": kind == "physical_hardware",
        "may_consume_credits": kind in {"hosted_emulator", "physical_hardware"},
    }


def classify_access_error(error: BaseException | str) -> str:
    """Classify access code 14 separately from scientific-code failures."""
    text = str(error).lower()
    access_markers = ("code 14", "error 14", "access", "entitlement", "quota")
    return "access_or_entitlement" if any(x in text for x in access_markers) else "unknown"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a file without changing it."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object and give clear errors for missing or corrupt files."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Required JSON file does not exist: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def validate_verified_wt_tmp(record: Mapping[str, Any]) -> None:
    """Reject altered, placeholder, or wrongly labeled WT_TMP benchmark metadata."""
    for field, expected in VERIFIED_WT_TMP.items():
        if record.get(field) != expected:
            raise ValueError(
                f"WT_TMP verified field {field!r} must be {expected!r}, "
                f"not {record.get(field)!r}"
            )
    if record.get("placeholder") or record.get("example"):
        raise ValueError("Placeholder or example data cannot be verified evidence")
    if record.get("physical_hardware") is True or record.get("local") is False:
        raise ValueError("The verified WT_TMP benchmark is local emulation, not hardware")
    expected_shots = total_shots(
        int(record["measurement_circuits"]), int(record["shots_per_circuit"])
    )
    if record["total_shots"] != expected_shots:
        raise ValueError("WT_TMP shot total is inconsistent")
