from pathlib import Path

import pytest

from scripts.run_wt_remote_molecular_pilot_chunked import chunk_sizes

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_wt_remote_molecular_pilot_chunked.py"


def test_one_hundred_shots_are_split_into_ten_detached_jobs():
    assert chunk_sizes(100, 10) == [10] * 10


@pytest.mark.parametrize("total,per_job", [(0, 10), (100, 0), (100, 30)])
def test_invalid_chunk_shapes_are_rejected(total, per_job):
    with pytest.raises(ValueError):
        chunk_sizes(total, per_job)


def test_chunked_runner_keeps_noise_and_never_waits_or_falls_back():
    text = SCRIPT.read_text()
    assert "noisy_simulation=True" in text
    assert "qnx.jobs.wait_for" not in text
    assert 'args.backend != "H2-Emulator"' in text
    assert "no fallback is allowed" in text
    assert "Persist each accepted ID before submitting the next chunk" in text


def test_retrieval_path_contains_no_submission_call():
    text = SCRIPT.read_text()
    retrieval = text[text.index("def retrieve(") : text.index("def main()")]
    assert "start_execute_job" not in retrieval
    assert "download_result" in retrieval
