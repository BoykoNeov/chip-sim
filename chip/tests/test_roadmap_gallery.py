"""The roadmap-page drift guard — keeps ``docs/roadmap.html`` honest without a human re-checking it.

Mirrors ``test_gallery.py`` / ``test_history_gallery.py`` for the planned-slices page. The one
structural difference: this page shows what does **not** exist yet, so on top of the standard
manifest/figure/HTML-currency asserts it pins the page's *honesty chrome* — every card must be
ribboned as a planned schematic and the in-image stamp's figure files must be on disk, so a
roadmap preview can never quietly impersonate a banked demo artifact.

All import + file-existence only — no matplotlib (:mod:`chip.roadmap_figures` imports it lazily
inside ``main``) — so these ride the fast lane and never skip away.
"""
from chip import roadmap_figures
from chip import roadmap_gallery as rg


def test_manifest_matches_figure_registry():
    figures = set(roadmap_figures.FIGURES)
    manifest = {s.fid for s in rg.SLICES}
    assert figures == manifest, (
        "roadmap manifest out of sync with chip.roadmap_figures.FIGURES — "
        f"cards without a schematic: {sorted(manifest - figures)}; "
        f"schematics without a card: {sorted(figures - manifest)}. "
        "Update SLICES in chip/roadmap_gallery.py or FIGURES in chip/roadmap_figures.py."
    )


def test_no_duplicate_manifest_entries():
    fids = [s.fid for s in rg.SLICES]
    assert len(fids) == len(set(fids)), f"duplicate manifest entry: {fids}"


def test_every_badge_is_a_styled_class():
    for s in rg.SLICES:
        assert s.badge in rg.BADGES, f"{s.fid}: unknown badge {s.badge!r} (styled classes: {rg.BADGES})"


def test_every_schematic_exists():
    for s in rg.SLICES:
        rel = rg.figure_relpath(s)
        assert (rg.DOCS_DIR / rel).is_file(), (
            f"{s.fid}: missing schematic {rel} — regenerate with `python -m chip.roadmap_figures`"
        )


def test_committed_html_is_current():
    committed = rg.OUTPUT_HTML.read_text(encoding="utf-8")
    assert committed == rg.render_html(), (
        "docs/roadmap.html is stale — regenerate it with `python -m chip.roadmap_gallery` and commit."
    )


def test_committed_local_html_is_current():
    committed = rg.OUTPUT_LOCAL_HTML.read_text(encoding="utf-8")
    assert committed == rg.render_html(local=True), (
        "docs/roadmap.local.html is stale — regenerate with `python -m chip.roadmap_gallery` and commit."
    )


def test_every_card_is_ribboned_as_planned():
    """The honesty chrome: one planned-schematic ribbon per card, on both editions."""
    for local in (False, True):
        page = rg.render_html(local=local)
        assert page.count('<span class="ribbon">planned &mdash; schematic</span>') == len(rg.SLICES), (
            "every roadmap card must carry the planned-schematic ribbon — the page must never "
            "present a preview as a banked demo artifact"
        )
        assert "not simulator output" in page, "the page must state its figures are not simulator output"


def test_roadmap_never_shows_banked_demo_figures():
    """The categorical line: this page shows only roadmap-*.png previews, never a demo's artifact."""
    page = rg.render_html()
    for prefix in ("figures/chip-", "figures/fab-game-"):
        assert prefix not in page, (
            f"roadmap page references a banked demo figure ({prefix}*) — built work belongs on the "
            "galleries, not the roadmap"
        )


def test_local_edition_is_all_local_no_github():
    """The standing gallery rule: the local edition links only into the running JupyterLab."""
    local = rg.render_html(local=True)
    assert "github.com" not in local, "the local roadmap must not link to GitHub anywhere"
    assert f"localhost:{rg._LOCAL_PORT}" in local, "the local roadmap must link into the running JupyterLab"


def test_public_edition_still_points_to_github():
    """Guard the split: the public Pages roadmap keeps its GitHub links (localhost would dead-end)."""
    public = rg.render_html()
    assert "github.com" in public and "localhost" not in public


def test_pages_cross_link():
    """The nav strip: the roadmap links back to all three built-work pages, both editions."""
    assert 'href="index.html"' in rg.render_html()
    assert 'href="index.local.html"' in rg.render_html(local=True)
