"""Focused tests for exact Nexus backend recovery and resumable status."""

from __future__ import annotations

from argparse import Namespace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import four_system_workflow as workflow
from scripts import test_quantinuum_access as nexus
from scripts.nexus_backend import require_nexus_emulator, resolve_backend


def args(tmp_path: Path, **updates) -> Namespace:
    values = dict(
        backend="H2-Emulator",
        shots=10,
        max_hqc=0.0,
        confirm_hardware=False,
        confirm_submit=False,
        user_group="research-group",
        require_user_group=False,
        dry_run=True,
        compile_only=False,
        project_id="project-id",
        project_name=None,
        timeout=1,
        wait=False,
        metadata_output=tmp_path / "operation.json",
    )
    values.update(updates)
    return Namespace(**values)


def test_h2_emulator_is_preserved_exactly() -> None:
    resolution = resolve_backend("H2-Emulator")
    assert resolution.requested_backend == "H2-Emulator"
    assert resolution.resolved_backend == "H2-Emulator"
    assert resolution.resolved_backend != "H2-1E"
    assert resolution.hosting_type == "nexus_hosted"


def test_no_silent_h1_fallback() -> None:
    with pytest.raises(ValueError):
        resolve_backend("unavailable-emulator")
    assert resolve_backend("H2-Emulator").resolved_backend != "H1-Emulator"


@pytest.mark.parametrize("name", ["H2-1SC", "H2-1E", "H2-1LE"])
def test_nexus_emulator_rejects_incompatible_types(name: str) -> None:
    with pytest.raises(ValueError, match="Nexus-hosted emulator"):
        require_nexus_emulator(resolve_backend(name))


@pytest.mark.parametrize("mode", ["dry_run", "compile_only"])
def test_offline_modes_create_no_jobs(tmp_path: Path, monkeypatch, mode: str) -> None:
    monkeypatch.setattr(
        nexus, "load_nexus", lambda: pytest.fail("offline mode imported Nexus")
    )
    call_args = args(
        tmp_path, dry_run=mode == "dry_run", compile_only=mode == "compile_only"
    )
    nexus.hosted_bell(call_args)
    metadata = json.loads(call_args.metadata_output.read_text())
    assert metadata["job_created"] is False
    assert metadata["backend_resolution"]["resolved_backend"] == "H2-Emulator"


def test_submission_requires_confirmation(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="--confirm-submit"):
        nexus.hosted_bell(args(tmp_path, dry_run=False))


def test_authentication_does_not_mark_entitlement(tmp_path: Path, monkeypatch) -> None:
    class Devices:
        @staticmethod
        def get_all():
            import pandas as pd

            return SimpleNamespace(
                df=lambda: pd.DataFrame({"device_name": ["H2-Emulator"]})
            )

    fake = SimpleNamespace(
        login=lambda: None,
        quotas=SimpleNamespace(get_all=lambda: [], check_quota=lambda **_: True),
        devices=Devices(),
    )
    monkeypatch.setattr(nexus, "load_nexus", lambda: (fake, object))
    call_args = args(tmp_path)
    nexus.access_report(call_args)
    metadata = json.loads(call_args.metadata_output.read_text())
    assert metadata["authenticated"] is True
    assert metadata["entitlement_verified"] is False


def test_access_code_14_records_resolution_without_retry(
    tmp_path: Path, monkeypatch
) -> None:
    class FakeQnx:
        projects = SimpleNamespace(get=lambda **_: SimpleNamespace(id="project-id"))
        circuits = SimpleNamespace(
            upload=lambda **_: (_ for _ in ()).throw(RuntimeError("access code 14"))
        )
        login = staticmethod(lambda: None)

    monkeypatch.setattr(nexus, "load_nexus", lambda: (FakeQnx(), object))
    monkeypatch.setattr(
        nexus, "bell", lambda: SimpleNamespace(n_qubits=2, n_gates=1, depth=lambda: 1)
    )
    call_args = args(tmp_path, dry_run=False, confirm_submit=True)
    with pytest.raises(SystemExit, match="access_or_entitlement"):
        nexus.hosted_bell(call_args)
    metadata = json.loads(call_args.metadata_output.read_text())
    assert metadata["classification"] == "access_or_entitlement"
    assert metadata["backend_resolution"]["resolved_backend"] == "H2-Emulator"
    assert metadata["retry_attempted"] is False
    assert metadata["fallback_attempted"] is False


def test_retrieval_never_creates_replacement_job(tmp_path: Path, monkeypatch) -> None:
    calls = {"execute": 0}
    job = SimpleNamespace(id="existing-job")
    fake = SimpleNamespace(
        login=lambda: None,
        projects=SimpleNamespace(get=lambda **_: SimpleNamespace(id="project-id")),
        jobs=SimpleNamespace(get=lambda **_: job),
        start_execute_job=lambda **_: calls.__setitem__(
            "execute", calls["execute"] + 1
        ),
    )
    monkeypatch.setattr(nexus, "load_nexus", lambda: (fake, object))
    monkeypatch.setattr(nexus, "wait_and_print", lambda *_: None)
    call_args = args(tmp_path, retrieve_job="existing-job")
    nexus.retrieve_existing_job(call_args)
    assert calls["execute"] == 0
    assert (
        json.loads(call_args.metadata_output.read_text())["replacement_job_created"]
        is False
    )


def test_missing_four_system_results_stay_missing(monkeypatch) -> None:
    monkeypatch.setattr(Path, "is_file", lambda _self: False)
    status = workflow.build_status()
    for system in status["systems"].values():
        assert system["nexus_emulator_result"]["status"] == "missing"
        assert system["nexus_emulator_result"]["value"] is None
    assert status["missing_values_are_zero"] is False
