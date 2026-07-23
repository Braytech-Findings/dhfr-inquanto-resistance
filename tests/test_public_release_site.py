import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_r_release_figures_and_sources_exist():
    out = ROOT / "results/publication/figures/r"
    for stem in (
        "wt_tmp_shot_convergence_r",
        "four_system_classical_pilot_r",
        "evidence_completion_map_r",
    ):
        assert (out / f"{stem}.png").stat().st_size > 10_000
        assert (out / f"{stem}.svg").stat().st_size > 10_000
        assert (out / f"{stem}_source.csv").stat().st_size > 50


def test_four_public_3d_models_have_provenance():
    out = ROOT / "visualization/public_structures"
    provenance = json.loads((out / "provenance.json").read_text())
    assert {row["system"] for row in provenance} == {
        "WT_TMP",
        "WT_4DTMP",
        "L28R_TMP",
        "L28R_4DTMP",
    }
    for row in provenance:
        model = ROOT / row["public_file"]
        assert model.stat().st_size > 100_000
        assert row["scientific_boundary"] == (
            "static prepared structure; not molecular dynamics"
        )


def test_ai_log_is_truthful_not_an_invented_percentage_split():
    text = (ROOT / "AI_ASSISTANCE_LOG.md").read_text().lower()
    assert "codex extensively" in text
    assert "50/50" not in text
    assert "student review required" in text


def test_site_links_to_public_models_not_ignored_processed_data():
    html = (ROOT / "docs/site/molecule.html").read_text()
    assert "visualization/public_structures" in html
    assert "data/processed" not in html
    assert "not molecular dynamics" in html.lower()


def test_simple_public_guide_and_site_pages_are_present():
    guide = (ROOT / "docs/SIMPLE_GUIDE.md").read_text()
    assert "four computer models" in guide
    assert "not proof" in guide.lower()
    assert "retry" in guide.lower()
    for page in (
        "index.html",
        "results.html",
        "figures.html",
        "methods.html",
        "limitations.html",
    ):
        assert (ROOT / "docs/site" / page).stat().st_size > 500
