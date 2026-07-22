"""Read, validate, checksum, and write versioned estimator manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/energy_estimator_manifest.schema.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(payload: dict[str, Any]) -> None:
    jsonschema.validate(payload, json.loads(SCHEMA.read_text()))


def read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    validate_manifest(payload)
    return payload


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    validate_manifest(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def validate_file_checksum(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(
            f"Checksum mismatch for {path}: expected {expected}, got {actual}"
        )
