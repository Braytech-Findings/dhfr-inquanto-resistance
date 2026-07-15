from scripts.analyze_endpoint import contrast


def test_difference_in_differences_sign():
    values = {"WT_TMP": -10.0, "L28R_TMP": -9.0, "WT_4DTMP": -8.0, "L28R_4DTMP": -7.5}
    assert contrast(values) == -0.5

