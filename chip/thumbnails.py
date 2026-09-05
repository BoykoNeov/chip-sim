"""Gallery thumbnails — the small images the four docs pages actually display.

Every banked figure in ``docs/figures/*.png`` is a ~130-dpi, ~1700-px-wide PNG (100–600 KB). The
gallery cards render them ~360 px wide, so serving the originals as thumbnails cost the physics
gallery ~3.3 MB of image bytes for one page load. This module banks a **WebP thumbnail** of every
figure at :data:`THUMB_WIDTH` px (~15–40 KB each) under ``docs/figures/thumbs/``; the galleries
display the thumbnail and link to the full PNG (one click for full size, as before).

It is a drift-guarded artifact like the pages themselves:

  * ``manifest.json`` (next to the thumbs) records, per thumbnail, a content hash of the **source
    PNG** it was cut from plus the thumbnail's pixel size. ``chip/tests/test_thumbnails.py`` recomputes
    the hash of every figure the galleries reference and fails the fast lane if a thumbnail is
    missing or was cut from a different (older) PNG — so re-banking a figure and forgetting the
    thumbnail is caught the same way a stale ``index.html`` is;
  * the galleries read the thumbnail's pixel size from the manifest (pure JSON, no image library) to
    emit ``width``/``height`` on every ``<img>`` — the browser then reserves the card's image box
    before the bytes arrive, so a page no longer re-flows card-by-card as lazy images land.

Only the *build* needs an image library: Pillow, which matplotlib itself requires, so it is present
wherever the figures can be produced (the ``viz`` extra). The read side (:func:`thumb_relpath`,
:func:`thumb_size`, :func:`source_digest`) is pure Python and rides the fast lane.

Regenerate after re-banking any figure (then commit ``docs/figures/thumbs/``)::

    python -m chip.thumbnails            # rebuilds only the stale / missing thumbnails
    python -m chip.thumbnails --force    # rebuilds every thumbnail
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = _REPO_ROOT / "docs"
FIGURES_DIR = DOCS_DIR / "figures"
THUMB_DIR = FIGURES_DIR / "thumbs"
MANIFEST = THUMB_DIR / "manifest.json"

THUMB_WIDTH = 760      # px — 2× the ~360-px card width, so the card stays crisp on a 2× display
WEBP_QUALITY = 80      # visually lossless for line plots at this size; ~15–40 KB per thumbnail
_DIGEST_CHARS = 16     # the manifest keeps a prefix of the source PNG's sha256 (enough to detect a re-bank)


def thumb_relpath(figure_relpath: str) -> str:
    """The thumbnail for a figure, both **relative to docs/** (``figures/x.png`` → ``figures/thumbs/x.webp``)."""
    p = Path(figure_relpath)
    return (p.parent / "thumbs" / (p.stem + ".webp")).as_posix()


def source_digest(png_path: Path) -> str:
    """The content hash the manifest records for a source PNG (a sha256 prefix)."""
    return hashlib.sha256(png_path.read_bytes()).hexdigest()[:_DIGEST_CHARS]


def load_manifest() -> dict:
    """The manifest as a dict ``{thumb file name: {"source", "digest", "width", "height"}}`` (``{}`` if absent)."""
    if not MANIFEST.is_file():
        return {}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def thumb_size(figure_relpath: str, manifest: dict | None = None) -> tuple[int, int]:
    """The thumbnail's ``(width, height)`` in px for a figure, from the manifest — no image library.

    Refuses loudly when the thumbnail was never built: the gallery generators call this per card,
    so a missing entry surfaces as *run ``python -m chip.thumbnails``*, not as a broken ``<img>``.
    """
    manifest = load_manifest() if manifest is None else manifest
    entry = manifest.get(Path(thumb_relpath(figure_relpath)).name)
    if entry is None:
        raise SystemExit(
            f"no thumbnail for {figure_relpath} — run `python -m chip.thumbnails` and commit docs/figures/thumbs/"
        )
    return int(entry["width"]), int(entry["height"])


def audit(figures, manifest: dict | None = None) -> dict[str, list[str]]:
    """The drift audit behind the thumbnail tests, for a set of displayed figures (docs-relative paths).

    Returns the offending figures under four keys — ``missing`` (no thumbnail / no manifest entry),
    ``stale`` (the manifest's source hash is not the PNG on disk: the figure was re-banked), ``big``
    (the thumbnail is not a fraction of its source) and ``aspect`` (its declared size is not the
    thumbnail width at the source's aspect ratio). Pure Python. Lives here (not in a test module) so
    the ``chip`` and ``fab_game`` test trees can each audit their own pages without ``chip`` ever
    importing ``fab_game`` (the one-way import rule, ADR 0005 §2).
    """
    manifest = load_manifest() if manifest is None else manifest
    out: dict[str, list[str]] = {"missing": [], "stale": [], "big": [], "aspect": []}
    for fig in sorted(set(figures)):
        src = DOCS_DIR / fig
        thumb = DOCS_DIR / thumb_relpath(fig)
        entry = manifest.get(thumb.name)
        if entry is None or not thumb.is_file():
            out["missing"].append(fig)
            continue
        if entry.get("digest") != source_digest(src):
            out["stale"].append(fig)
        if thumb.stat().st_size >= 0.5 * src.stat().st_size:
            out["big"].append(fig)
        sw, sh = png_size(src)
        if entry["width"] != THUMB_WIDTH or abs(entry["height"] - sh * THUMB_WIDTH / sw) > 1.0:
            out["aspect"].append(fig)
    return out


def png_size(png_path: Path) -> tuple[int, int]:
    """A PNG's pixel ``(width, height)`` from its IHDR chunk — 24 bytes, pure Python."""
    with open(png_path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"{png_path} is not a PNG")
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def build(force: bool = False) -> tuple[list[str], list[str]]:
    """Cut a thumbnail for every ``docs/figures/*.png`` whose entry is missing or stale; prune orphans.

    Returns ``(rebuilt, pruned)`` thumbnail file names. Needs Pillow (matplotlib's own dependency —
    present with the ``viz`` extra).
    """
    from PIL import Image   # lazy: the read side of this module stays image-library-free

    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    sources = sorted(FIGURES_DIR.glob("*.png"))
    rebuilt: list[str] = []
    fresh: dict = {}
    for png in sources:
        name = png.stem + ".webp"
        digest = source_digest(png)
        entry = manifest.get(name)
        target = THUMB_DIR / name
        if force or entry is None or entry.get("digest") != digest or not target.is_file():
            with Image.open(png) as im:
                im = im.convert("RGB")                       # figures are opaque; drop any alpha channel
                w, h = im.size
                th = max(1, round(h * THUMB_WIDTH / w))
                im = im.resize((THUMB_WIDTH, th), Image.LANCZOS)
                im.save(target, "WEBP", quality=WEBP_QUALITY, method=6)
            entry = {"source": png.name, "digest": digest, "width": THUMB_WIDTH, "height": th}
            rebuilt.append(name)
        fresh[name] = entry
    pruned = []
    for stale in THUMB_DIR.glob("*.webp"):
        if stale.name not in fresh:
            stale.unlink()
            pruned.append(stale.name)
    MANIFEST.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return rebuilt, pruned


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    force = "--force" in sys.argv[1:]
    rebuilt, pruned = build(force=force)
    total = len(load_manifest())
    print(f"Thumbnails: {len(rebuilt)} rebuilt, {len(pruned)} pruned, {total} banked → "
          f"{THUMB_DIR.relative_to(_REPO_ROOT).as_posix()}/")


if __name__ == "__main__":
    main()
