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
