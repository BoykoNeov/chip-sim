"""The fab-game gallery drift guard — keeps ``docs/fab-game.html`` honest without a human re-checking it.

The sibling of ``chip/tests/test_gallery.py`` for the game layer's own front door. Same three asserts
make currency structural rather than a chore:

  1. **completeness** — every ``fab_game/demo_*.py`` has a manifest entry (add a demo, this fails until
     you list it; rename one, it fails until you fix the manifest);
  2. **figures exist** — every entry's banked ``fab-game-*.png`` is on disk;
  3. **HTML is current** — the committed ``docs/fab-game.html`` (+ the local edition) equals a fresh
     regeneration (edit a blurb or the manifest, forget ``python -m fab_game.gallery``, this fails).

All import + file-existence only — no matplotlib — so they ride the fast lane (importing a demo module
is viz-free: each imports matplotlib lazily inside its ``save_figure``). The cross-link tests pin the
two-gallery split (ADR 0005): the public edition keeps GitHub links, the local edition is all-localhost.
"""
from fab_game import gallery


def test_manifest_covers_every_demo():
    on_disk = gallery.glob_demo_modules()
    in_manifest = {d.module for d in gallery.ALL_DEMOS}
    assert on_disk == in_manifest, (
        "fab-game gallery manifest out of sync with fab_game/demo_*.py — "
        f"missing from manifest: {sorted(on_disk - in_manifest)}; "
        f"stale (no such demo): {sorted(in_manifest - on_disk)}. "
        "Update LINE/DEEPENINGS in fab_game/gallery.py."
    )


def test_no_duplicate_entries():
    modules = [d.module for d in gallery.ALL_DEMOS]
    assert len(modules) == len(set(modules)), f"duplicate manifest entry: {modules}"


def test_every_figure_exists():
    for demo in gallery.ALL_DEMOS:
        rel = gallery.figure_relpath(demo, gallery._PKG)
        assert (gallery.DOCS_DIR / rel).is_file(), f"{demo.module}: missing figure {rel}"


def test_committed_html_is_current():
    committed = gallery.OUTPUT_HTML.read_text(encoding="utf-8")
    assert committed == gallery.render_html(), (
        "docs/fab-game.html is stale — regenerate it with `python -m fab_game.gallery` and commit the result."
    )


def test_committed_local_html_is_current():
    committed = gallery.OUTPUT_LOCAL_HTML.read_text(encoding="utf-8")
    assert committed == gallery.render_html(local=True), (
        "docs/fab-game.local.html is stale — regenerate it with `python -m fab_game.gallery` and commit it."
    )


def test_local_edition_is_all_local_no_github():
    """The local edition's whole point: every link is local (a running JupyterLab), none to GitHub."""
    local = gallery.render_html(local=True)
    assert "github.com" not in local, "the local fab-game gallery must not link to GitHub anywhere"
    assert f"http://localhost:{gallery._LOCAL_PORT}/lab/tree/fab_game/fab_game.ipynb" in local, (
        "the notebook card must be a click->live-notebook launch into the running JupyterLab"
    )


def test_public_edition_still_points_to_github():
    """Guard the split: the public Pages gallery keeps its GitHub links (localhost would dead-end there)."""
    public = gallery.render_html()
    assert "github.com" in public and "localhost" not in public


def test_galleries_cross_link():
    """The two front doors link to each other (the split is navigable, not a dead end)."""
    assert 'href="index.html"' in gallery.render_html(), "public fab-game gallery must link back to the physics gallery"
    assert 'href="index.local.html"' in gallery.render_html(local=True), (
        "local fab-game gallery must link back to the physics gallery's local edition"
    )
