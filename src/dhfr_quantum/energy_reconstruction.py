"""Reconstruct Pauli-observable energies from counts or saved expectations."""

from __future__ import annotations

import csv
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Reconstruction:
    energy_hartree: float
    standard_error_hartree: float
    observable_count: int


def _clean_bitstring(value: str) -> str:
    bits = value.replace(" ", "").replace(",", "").replace("(", "").replace(")", "")
    if not bits or set(bits) - {"0", "1"}:
        raise ValueError(f"Malformed bitstring: {value!r}")
    return bits


def pauli_qubits(pauli_string: str) -> tuple[int, ...]:
    if not pauli_string.strip():
        return ()
    result = []
    for token in pauli_string.split():
        if token[0] not in "IXYZ" or not token[1:].isdigit():
            raise ValueError(f"Malformed Pauli token: {token!r}")
        if token[0] != "I":
            result.append(int(token[1:]))
    if len(result) != len(set(result)):
        raise ValueError(f"Duplicate qubit in Pauli string: {pauli_string!r}")
    return tuple(result)


def expectation_from_counts(
    counts: Mapping[str, int],
    pauli_string: str,
    *,
    qubit_to_bit: Mapping[int, int] | None = None,
    bit_order: str = "big",
) -> tuple[float, float]:
    """Return expectation and standard error after required basis rotations.

    Counts are assumed to come from a circuit already rotated into the Pauli
    measurement basis. ``qubit_to_bit`` maps logical qubits to displayed bit
    positions; without it, qubit zero maps to the rightmost bit for ``big``.
    """
    if bit_order not in {"big", "little"}:
        raise ValueError("bit_order must be 'big' or 'little'")
    qubits = pauli_qubits(pauli_string)
    if not counts:
        raise ValueError("Counts are missing")
    normalized: list[tuple[str, int]] = []
    for raw, count in counts.items():
        if not isinstance(count, int) or count < 0:
            raise ValueError("Counts must be non-negative integers")
        normalized.append((_clean_bitstring(raw), count))
    widths = {len(bits) for bits, _ in normalized}
    if len(widths) != 1:
        raise ValueError("Count bitstrings have inconsistent widths")
    width = widths.pop()
    shots = sum(count for _, count in normalized)
    if shots <= 0:
        raise ValueError("Total counts must be positive")
    if not qubits:
        return 1.0, 0.0
    parity_sum = 0
    for bits, count in normalized:
        parity = 0
        for qubit in qubits:
            bit = qubit_to_bit[qubit] if qubit_to_bit is not None else qubit
            if bit < 0 or bit >= width:
                raise ValueError(f"Bit mapping {bit} is outside width {width}")
            position = width - 1 - bit if bit_order == "big" else bit
            parity ^= int(bits[position])
        parity_sum += (1 if parity == 0 else -1) * count
    mean = parity_sum / shots
    variance_of_mean = max(0.0, 1.0 - mean * mean) / shots
    return mean, math.sqrt(variance_of_mean)


def reconstruct(
    coefficients: Mapping[str, float],
    measurements: Mapping[str, tuple[float, float]],
) -> Reconstruction:
    """Combine a constant and one unique measurement per non-identity term."""
    expected = set(coefficients) - {""}
    actual = set(measurements)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise ValueError(f"Observable mismatch; missing={missing}, extra={extra}")
    energy = float(coefficients.get("", 0.0))
    variance = 0.0
    for observable in sorted(expected):
        mean, standard_error = measurements[observable]
        if not -1.0 <= mean <= 1.0:
            raise ValueError(f"Expectation outside [-1, 1]: {observable}")
        if standard_error < 0 or not math.isfinite(standard_error):
            raise ValueError(f"Invalid standard error: {observable}")
        coefficient = float(coefficients[observable])
        energy += coefficient * mean
        variance += (coefficient * standard_error) ** 2
    return Reconstruction(energy, math.sqrt(variance), len(expected))


def reconstruct_from_measurement_table(
    hamiltonian: Mapping[str, object], measurement_csv: Path
) -> Reconstruction:
    terms = hamiltonian.get("terms")
    if not isinstance(terms, Sequence):
        raise ValueError("Hamiltonian terms are missing")
    coefficients: dict[str, float] = {}
    for term in terms:
        if not isinstance(term, Mapping):
            raise ValueError("Malformed Hamiltonian term")
        name = str(term["pauli_string"])
        if name in coefficients:
            raise ValueError(f"Duplicate Hamiltonian term: {name!r}")
        coefficient = term["coefficient"]
        if not isinstance(coefficient, Mapping) or float(coefficient["imag"]) != 0.0:
            raise ValueError(f"Hamiltonian coefficient is not real: {name!r}")
        coefficients[name] = float(coefficient["real"])
    measurements: dict[str, tuple[float, float]] = {}
    with measurement_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["Pauli string"]
            if name in measurements:
                raise ValueError(f"Duplicate measurement: {name!r}")
            measurements[name] = (float(row["Mean"]), float(row["Standard error"]))
    return reconstruct(coefficients, measurements)
