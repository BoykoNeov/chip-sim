"""The thumbnail drift guard — the small images the docs pages display stay in lock-step with the figures.

Mirrors ``test_gallery.py``'s discipline for ``docs/figures/thumbs/`` (:mod:`chip.thumbnails`), over
the three pages the ``chip`` package owns (physics gallery, era timeline, roadmap; the fab-game page
is audited by ``fab_game/tests/test_thumbnails.py`` — ``chip`` never imports ``fab_game``, ADR 0005 §2):

  1. **every displayed figure has a thumbnail** — the WebP exists and the manifest knows its size;
  2. **no thumbnail is stale** — the manifest's content hash of the *source PNG* equals the PNG on
     disk (re-bank a figure and forget ``python -m chip.thumbnails``, this fails);
  3. **a thumbnail is actually small** and its declared size is the thumbnail width at the source's
     aspect ratio (the ``width``/``height`` the pages emit reserve the right box);
  4. **the pages display the thumbnail and link the full PNG**;
  5. **the pure-Python PNG header reader is right** — on a synthetic PNG of known size.

All pure Python (hashlib, json, a 24-byte header read) — rides the fast lane, never ``importorskip``s.
"""
from __future__ import annotations

import struct
import zlib

import pytest

from chip import gallery, history_gallery, roadmap_gallery, thumbnails


def _displayed_figures() -> set[str]:
    """Every figure path (relative to docs/) that a chip-owned page puts on a card."""
    figs = {gallery.figure_relpath(d) for d in gallery.ALL_DEMOS}
    figs |= {gallery.figure_relpath(m, "chip") for m in history_gallery.MODES}
    figs |= {roadmap_gallery.figure_relpath(s) for s in roadmap_gallery.SLICES}
    return figs


@pytest.fixture(scope="module")
def report() -> dict:
    manifest = thumbnails.load_manifest()
    assert manifest, "docs/figures/thumbs/manifest.json is missing — run `python -m chip.thumbnails`"
    return thumbnails.audit(_displayed_figures(), manifest)


def test_every_displayed_figure_has_a_thumbnail(report):
    assert not report["missing"], (
        f"figures without a thumbnail: {report['missing']} — run `python -m chip.thumbnails`"
    )


def test_no_thumbnail_is_stale(report):
    assert not report["stale"], (
        f"thumbnails cut from an older PNG: {report['stale']} — the figure was re-banked; run "
        "`python -m chip.thumbnails` and commit docs/figures/thumbs/"
    )


def test_thumbnails_are_small_and_keep_the_aspect_ratio(report):
    assert not report["big"], f"not thumbnail-sized: {report['big']}"
    assert not report["aspect"], f"declared size breaks the aspect ratio: {report['aspect']}"


@pytest.mark.parametrize("render", [gallery.render_html, history_gallery.render_html, roadmap_gallery.render_html])
def test_pages_display_the_thumbnail_and_link_the_full_figure(render):
    page = render()
    shown = page.count('<img src="figures/thumbs/')
    assert shown > 0
    assert page.count("<img ") == shown                       # every <img> is a thumbnail, none a PNG
    assert page.count('width="760" height="') == shown        # every one declares its box
    assert page.count('href="figures/') >= shown              # every card still links the full PNG


def test_thumb_size_refuses_an_unbuilt_figure():
    with pytest.raises(SystemExit, match="python -m chip.thumbnails"):
        thumbnails.thumb_size("figures/no-such-figure.png", {})


def test_png_size_reads_the_header(tmp_path):
    w, h = 37, 11
    raw = b"".join(b"\x00" + b"\x00" * (3 * w) for _ in range(h))       # filter byte + RGB rows

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    p = tmp_path / "tiny.png"
    p.write_bytes(png)
    assert thumbnails.png_size(p) == (w, h)
    (tmp_path / "not.png").write_bytes(b"GIF89a" + b"\x00" * 30)
    with pytest.raises(ValueError):
        thumbnails.png_size(tmp_path / "not.png")
