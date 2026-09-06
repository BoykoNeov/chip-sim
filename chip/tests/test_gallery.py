"""The gallery drift guard — keeps ``docs/index.html`` honest without a human re-checking it.

This test *is* the "keep it up to date" mechanism. Three asserts make currency structural
rather than a chore a maintainer has to remember:

  1. **completeness** — every ``chip/demo_*.py`` has a manifest entry (add a demo, this fails
     until you list it; rename one, it fails until you fix the manifest);
  2. **figures exist** — every entry's banked figure is on disk (catches a renamed/missing PNG);
  3. **HTML is current** — the committed ``docs/index.html`` equals a fresh regeneration (edit a
     blurb or the manifest, forget ``python -m chip.gallery``, this fails).

All three are import + file-existence only — no matplotlib — so they ride the fast lane and never
``importorskip`` away to a green skip. (Importing a demo module is viz-free: each one imports
matplotlib lazily inside its ``save_figure``.)
"""
import html

from chip import gallery


def test_manifest_covers_every_demo():
    on_disk = gallery.glob_demo_modules()
    in_manifest = {d.module for d in gallery.ALL_DEMOS}
    assert on_disk == in_manifest, (
        "gallery manifest out of sync with chip/demo_*.py — "
        f"missing from manifest: {sorted(on_disk - in_manifest)}; "
        f"stale (no such demo): {sorted(in_manifest - on_disk)}. "
        "Update SPINE/DEEPENINGS in chip/gallery.py."
    )


def test_no_duplicate_or_misordered_entries():
    modules = [d.module for d in gallery.ALL_DEMOS]
    assert len(modules) == len(set(modules)), f"duplicate manifest entry: {modules}"


def test_every_figure_exists():
    for demo in gallery.ALL_DEMOS:
        rel = gallery.figure_relpath(demo)
        assert (gallery.DOCS_DIR / rel).is_file(), f"{demo.module}: missing figure {rel}"


def test_committed_html_is_current():
    committed = gallery.OUTPUT_HTML.read_text(encoding="utf-8")
    assert committed == gallery.render_html(), (
        "docs/index.html is stale — regenerate it with `python -m chip.gallery` and commit the result."
    )


def test_committed_local_html_is_current():
    committed = gallery.OUTPUT_LOCAL_HTML.read_text(encoding="utf-8")
    assert committed == gallery.render_html(local=True), (
        "docs/index.local.html is stale — regenerate it with `python -m chip.gallery` and commit the result."
    )


def test_local_edition_is_all_local_no_github():
    """The local edition's whole point: every link is local (a running JupyterLab), none to GitHub."""
    local = gallery.render_html(local=True)
    assert "github.com" not in local, "the local gallery must not link to GitHub anywhere"
    assert gallery._PAGES_URL not in local, (
        "the local gallery must name no remote origin at all — the Pages URL is a github.IO host, "
        "so the github.com assert above does not catch it (rel=canonical would have walked straight "
        "through). This is the assert that keeps the canonical link public-only."
    )
    assert f"http://localhost:{gallery._LOCAL_PORT}/lab/tree/chip/chip.ipynb" in local, (
        "the notebook card must be a click->live-notebook launch into the running JupyterLab"
    )


def test_public_edition_still_points_to_github():
    """Guard the split: the public Pages gallery keeps its GitHub links (localhost would dead-end there)."""
    public = gallery.render_html()
    assert "github.com" in public and "localhost" not in public


def test_blurbs_survive_the_clamp_verbatim():
    """The blurb is *clamped* (CSS), never shortened: the manifest text is kept verbatim with the
    README catalog, so the page must still carry every character of it. Compare against the escaped
    form — ``_card`` escapes before interpolating, so the raw string is not what lands in the HTML."""
    for page in (gallery.render_html(), gallery.render_html(local=True)):
        for demo in gallery.ALL_DEMOS:
            assert html.escape(demo.blurb) in page, (
                f"{demo.module}: blurb text no longer appears verbatim in the page — the clamp must "
                "hide the overflow visually, not truncate the source text."
            )


def test_favicon_data_uri_carries_no_raw_hash():
    """The one N7 failure no golden test can see. A raw ``#`` inside a ``data:`` URI terminates it
    as a fragment identifier, so the tab silently renders no icon at all — and the golden tests
    compare the page to itself, which a broken URI passes exactly as happily as a working one."""
    assert "#" not in gallery._FAVICON, (
        "the favicon data URI must percent-encode '#' as %23 (a raw '#' ends the URI as a fragment "
        f"and silently yields an iconless tab): {gallery._FAVICON}"
    )
    for page in (gallery.render_html(), gallery.render_html(local=True)):
        assert f'<link rel="icon" href="{gallery._FAVICON}">' in page


def test_public_canonical_names_the_file_it_is_served_as():
    """``rel=canonical`` has to point at *this* page's Pages URL — the one head tag whose slug is
    typed rather than derived, so pin it to the output file's own name."""
    public = gallery.render_html()
    assert f'<link rel="canonical" href="{gallery._PAGES_URL}/{gallery.OUTPUT_HTML.name}">' in public
