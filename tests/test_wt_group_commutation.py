from scripts.audit_wt_pauli_groups import commute, parse_pauli, qubit_wise_commute


def test_pauli_commutation_classification() -> None:
    xx = parse_pauli("X0 X1")
    zz = parse_pauli("Z0 Z1")
    x0 = parse_pauli("X0")
    z0 = parse_pauli("Z0")
    assert commute(xx, zz) is True
    assert qubit_wise_commute(xx, zz) is False
    assert commute(x0, z0) is False
    assert qubit_wise_commute(x0, z0) is False
    assert qubit_wise_commute(parse_pauli("X0 Z2"), parse_pauli("X0 Z3")) is True
