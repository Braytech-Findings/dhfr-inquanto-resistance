from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IONQ_SCRIPTS = [
    ROOT / "scripts" / "check_ionq_environment.py",
    ROOT / "scripts" / "ionq_compile_report.py",
]


def parsed_tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_ionq_scripts_parse() -> None:
    for path in IONQ_SCRIPTS:
        parsed_tree(path)


def test_ionq_tools_have_no_run_calls() -> None:
    for path in IONQ_SCRIPTS:
        calls = [node for node in ast.walk(parsed_tree(path)) if isinstance(node, ast.Call)]
        run_calls = [
            node
            for node in calls
            if isinstance(node.func, ast.Attribute) and node.func.attr == "run"
        ]
        assert not run_calls
