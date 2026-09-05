"""The fab-game page's thumbnail drift guard — the game-layer half of ``chip/tests/test_thumbnails.py``.

Same audit (:func:`chip.thumbnails.audit`), over the figures ``docs/fab-game.html`` displays. Split
across the two test trees because ``chip`` may never import ``fab_game`` (ADR 0005 §2), while
``fab_game → chip`` is the allowed direction — so the shared audit lives in ``chip.thumbnails`` and
this module points it at the fab-game manifest.
"""
from __future__ import annotations

import pytest

from chip import thumbnails
from chip.gallery import figure_relpath
from fab_game import gallery


@pytest.fixture(scope="module")
def report() -> dict:
    manifest = thumbnails.load_manifest()
    assert manifest, "docs/figures/thumbs/manifest.json is missing — run `python -m chip.thumbnails`"
    return thumbnails.audit({figure_relpath(d, "fab_game") for d in gallery.ALL_DEMOS}, manifest)


def test_every_fab_game_figure_has_a_current_small_thumbnail(report):
    assert not report["missing"], f"figures without a thumbnail: {report['missing']} — run `python -m chip.thumbnails`"
    assert not report["stale"], (
        f"thumbnails cut from an older PNG: {report['stale']} — run `python -m chip.thumbnails` and commit"
    )
    assert not report["big"], f"not thumbnail-sized: {report['big']}"
    assert not report["aspect"], f"declared size breaks the aspect ratio: {report['aspect']}"


def test_fab_game_page_displays_thumbnails_and_links_the_full_figures():
    page = gallery.render_html()
    shown = page.count('<img src="figures/thumbs/')
    assert shown == len(gallery.ALL_DEMOS)
    assert page.count("<img ") == shown
    assert page.count('width="760" height="') == shown
