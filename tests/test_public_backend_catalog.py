import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "final_public_release"


def test_catalog_is_discovery_only_and_preserves_exact_emulator_names():
    catalog = json.loads((OUT / "backend_catalog.json").read_text())
    names = {row["exact_name"] for row in catalog["backends"]}
    assert catalog["discovery_only"] is True
    assert catalog["submission_count"] == 0
    assert {"H1-Emulator", "H2-Emulator"} <= names
    assert "H2-1E" not in names


def test_capability_matrix_does_not_claim_visibility_is_entitlement():
    with (OUT / "backend_capability_matrix.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(row["entitlement_verified"] == "False" for row in rows)
    assert all("Visibility is not entitlement" in row["notes"] for row in rows)
