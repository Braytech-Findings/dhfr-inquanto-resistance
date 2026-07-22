import numpy as np

from scripts.run_wt_local_finite_shots import _group_sample


class Result:
    def __init__(self, shots):
        # Aer returns unsigned-byte readouts; signed conversion is essential.
        self.shots = np.asarray(shots, dtype=np.uint8)

    def get_shots(self, cbits):
        return self.shots[:, : len(cbits)]


def test_group_sample_preserves_covariance_and_invert():
    mappings = [
        {"bits": "0", "invert": "false", "pauli_string": "Zq[0]"},
        {"bits": "0;1", "invert": "true", "pauli_string": "Zq[0] Zq[1]"},
    ]
    result = Result([[0, 0], [0, 1], [1, 0], [1, 1]])
    values = np.array([1.0 - 2.0, 1.0 + 2.0, -1.0 + 2.0, -1.0 - 2.0])
    mean, variance = _group_sample(
        result, mappings, {"Zq[0]": 1.0, "Zq[0] Zq[1]": 2.0}, 4
    )
    assert mean == np.mean(values)
    assert variance == np.var(values, ddof=1)


def test_missing_result_is_not_converted_to_zero():
    class Missing:
        def get_shots(self, cbits):
            raise RuntimeError("missing result")

    mappings = [{"bits": "0", "invert": "false", "pauli_string": "Zq[0]"}]
    try:
        _group_sample(Missing(), mappings, {"Zq[0]": 1.0}, 2)
    except RuntimeError as exc:
        assert "missing result" in str(exc)
    else:
        raise AssertionError("Missing data must remain missing")
