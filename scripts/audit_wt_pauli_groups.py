#!/usr/bin/env python3
"""Classify every recovered WT Pauli group by commutation compatibility."""

from __future__ import annotations

import csv
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/max_shot_production/WT_TMP/measurement_map.csv"
OUTPUT = ROOT / "artifacts/max_shot_production/WT_TMP/group_commutation_audit.csv"


def parse_pauli(text: str) -> dict[int, str]:
    result: dict[int, str] = {}
    for token in text.split():
        axis, index = token[0], token[1:]
        if axis not in "XYZ" or not index.isdigit():
            raise ValueError(f"Malformed Pauli token: {token}")
        qubit = int(index)
        if qubit in result:
            raise ValueError(f"Duplicate Pauli qubit: {text}")
        result[qubit] = axis
    return result


def qubit_wise_commute(left: dict[int, str], right: dict[int, str]) -> bool:
    return all(left.get(q) == right.get(q) for q in set(left) & set(right))


def commute(left: dict[int, str], right: dict[int, str]) -> bool:
    conflicts = sum(left[q] != right[q] for q in set(left) & set(right))
    return conflicts % 2 == 0


def main() -> None:
    groups: dict[int, list[dict[int, str]]] = defaultdict(list)
    with SOURCE.open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups[int(row["group_index"])].append(parse_pauli(row["pauli_string"]))
    if sorted(groups) != list(range(576)):
        raise SystemExit("Recovered group indices are incomplete")
    records = []
    invalid_groups = []
    for index in sorted(groups):
        values = groups[index]
        pairs = list(combinations(values, 2))
        incompatible = sum(not commute(left, right) for left, right in pairs)
        qwc = all(qubit_wise_commute(left, right) for left, right in pairs)
        general = incompatible == 0
        if incompatible:
            classification = "INVALID"
            invalid_groups.append(index)
        elif qwc:
            classification = "QWC"
        else:
            classification = "GENERAL_COMMUTING"
        involved = sorted({qubit for value in values for qubit in value})
        records.append(
            {
                "group_id": f"WT_TMP_G{index + 1:04d}",
                "observable_count": len(values),
                "qwc": str(qwc).lower(),
                "generally_commuting": str(general).lower(),
                "incompatible_pair_count": incompatible,
                "involved_qubits": ";".join(map(str, involved)),
                "proposed_strategy": "NonConflictingSets" if qwc else "CommutingSets",
                "validation_status": "fail" if incompatible else "pass",
                "notes": classification,
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    if invalid_groups:
        raise SystemExit(f"Invalid noncommuting groups: {invalid_groups}")
    counts = {
        label: sum(row["notes"] == label for row in records)
        for label in ("QWC", "GENERAL_COMMUTING", "INVALID")
    }
    print(counts)


if __name__ == "__main__":
    main()
