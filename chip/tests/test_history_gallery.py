"""The era-timeline drift guard — keeps ``docs/history.html`` honest without a human re-checking it.

Mirrors ``test_gallery.py`` for Chunk H0 (the historical-modes display surface). The one structural
difference: the timeline's manifest is a **curated subset** — only the ``demo_*_history.py`` modes go
on the backward axis, not every ``demo_*.py`` — so completeness is anchored to that narrower glob.

Five asserts make currency structural rather than a chore:

  1. **completeness** — every ``chip/demo_*_history.py`` has a manifest rung (build a new history mode,
     this fails until it is on the timeline; rename one, it fails until the manifest is fixed);
  2. **figures exist** — every rung's banked figure is on disk (catches a renamed/missing PNG);
  3. **HTML is current** — the committed ``history.html`` / ``history.local.html`` equal a fresh
     regeneration (edit the timeline text or the manifest, forget ``python -m chip.history_gallery``,
     this fails);
  4/5. **the public/local split holds** — the public page links only to GitHub (localhost dead-ends on
     Pages); the local page links only to a running JupyterLab (the standing gallery rule).

All import + file-existence only — no matplotlib — so they ride the fast lane and never skip away.
"""
from chip import history_gallery as hg


def test_manifest_covers_every_history_mode():
    on_disk = hg.glob_history_modules()
    in_manifest = {m.module for m in hg.MODES}
    assert on_disk == in_manifest, (
        "history-timeline manifest out of sync with chip/demo_*_history.py — "
        f"missing from manifest: {sorted(on_disk - in_manifest)}; "
        f"stale (no such mode): {sorted(in_manifest - on_disk)}. "
        "Update MODES in chip/history_gallery.py."
    )


def test_no_duplicate_manifest_entries():
    modules = [m.module for m in hg.MODES]
    assert len(modules) == len(set(modules)), f"duplicate manifest entry: {modules}"


def test_every_figure_exists():
    for mode in hg.MODES:
        rel = hg.figure_relpath(mode, hg._PKG)
        assert (hg.DOCS_DIR / rel).is_file(), f"{mode.module}: missing figure {rel}"


def test_committed_html_is_current():
    committed = hg.OUTPUT_HTML.read_text(encoding="utf-8")
    assert committed == hg.render_html(), (
        "docs/history.html is stale — regenerate it with `python -m chip.history_gallery` and commit."
    )


def test_committed_local_html_is_current():
    committed = hg.OUTPUT_LOCAL_HTML.read_text(encoding="utf-8")
    assert committed == hg.render_html(local=True), (
        "docs/history.local.html is stale — regenerate with `python -m chip.history_gallery` and commit."
    )


def test_local_edition_is_all_local_no_github():
    """The local edition's whole point: every link is local (a running JupyterLab), none to GitHub."""
    local = hg.render_html(local=True)
    assert "github.com" not in local, "the local timeline must not link to GitHub anywhere"
    assert f"localhost:{hg._LOCAL_PORT}" in local, "the local timeline must link into the running JupyterLab"


def test_public_edition_still_points_to_github():
    """Guard the split: the public Pages timeline keeps its GitHub links (localhost would dead-end there)."""
    public = hg.render_html()
    assert "github.com" in public and "localhost" not in public
