from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IONQ_SCRIPTS = [
    ROOT / "scripts" / "check_ionq_environment.py",
    ROOT / "scripts" / "ionq_compile_report.py",
]


def test_ionq_scripts_parse() -> None:
    for path in IONQ_SCRIPTS:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_ionq_tools_have_no_submission_call() -> None:
    for path in IONQ_SCRIPTS:
        source = path.read_text(encoding="utf-8")
        assert ".run(" not in source
        assert "backend.run" not in source
        assert "submit" not in source.lower().replace("no-submit", "")
