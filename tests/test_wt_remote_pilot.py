import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_wt_remote_molecular_pilot.py"


def test_remote_pilot_has_explicit_submission_and_cost_gates():
    tree = ast.parse(SCRIPT.read_text())
    text = SCRIPT.read_text()
    assert "--confirm-submit" in text
    assert "--cost-approved" in text
    assert 'args.backend != "H2-Emulator"' in text
    assert "args.shots != 100" in text
    assert any(isinstance(node, ast.Call) for node in ast.walk(tree))


def test_remote_pilot_persists_before_wait_and_prevents_duplicates():
    text = SCRIPT.read_text()
    assert text.index("write(MANIFEST, payload)  # Persist") < text.index(
        "qnx.jobs.wait_for"
    )
    assert "A saved pilot job already exists; retrieve it instead." in text
    assert "Requested job ID does not match the saved manifest." in text


def test_remote_pilot_can_adopt_but_not_submit_a_manual_nexus_retry():
    text = SCRIPT.read_text()
    assert "--adopt-manual-retry-job" in text
    assert "--replaces-job" in text
    assert '"submitted_by_repository_tooling": False' in text
    assert "--replaces-job must exactly match" in text
