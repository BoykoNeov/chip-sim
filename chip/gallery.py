"""The gallery generator — the single clickable front door to every visualization.

Builds ``docs/index.html``: a clickable gallery that maps the four things a newcomer
asks for —

  * **visualizations** — each demo's banked figure (clickable to full size),
  * **demos** — its ``python -m chip.demo_*`` run command + a link to the source module,
  * **experiments** — the v1.x *deepenings*, each promoting a named scope edge of its phase,
  * **notebook** — the single guided interactive tour (``chip/chip.ipynb``).

It is **generated, not hand-written**, so it cannot silently drift:

  * the figure for every card is **introspected** from the demo module's own ``DOCS_FIGURE``
    — never re-typed here (that is the one mapping that silently breaks, e.g.
    ``demo_coupling → chip-oed-segregation.png``);
  * inclusion is anchored to the ``chip/demo_*.py`` **glob**, so a new demo cannot be forgotten;
  * ``chip/tests/test_gallery.py`` fails the fast lane if a demo is missing from the manifest
    below, if a figure is absent, or if the committed ``docs/index.html`` is stale.

The manifest below carries only what the code is *not* the source of truth for: the human-readable
label, blurb and ordering (kept verbatim with the README's *Demonstrations* catalog).

Regenerate after adding/renaming a demo or editing a blurb (then commit ``docs/index.html``):

    python -m chip.gallery
"""
from __future__ import annotations

import html
import importlib
from dataclasses import dataclass
from pathlib import Path

# --- repo coordinates (absolute links — Pages serves /docs, so anything OUTSIDE /docs,
#     i.e. the demo .py files / the notebook / the ADRs, must be linked absolutely) ---------
REPO = "BoykoNeov/chip-sim"
BRANCH = "main"
_BLOB = f"https://github.com/{REPO}/blob/{BRANCH}"
_TREE = f"https://github.com/{REPO}/tree/{BRANCH}"
_REPO_URL = f"https://github.com/{REPO}"

_REPO_ROOT = Path(__file__).resolve().parents[1]
CHIP_DIR = _REPO_ROOT / "chip"
DOCS_DIR = _REPO_ROOT / "docs"
OUTPUT_HTML = DOCS_DIR / "index.html"


@dataclass(frozen=True)
class Demo:
    """One gallery card. ``module`` is the ``chip.<module>`` suffix; the figure is NOT stored
    here — it is read from the module's ``DOCS_FIGURE`` at render time (see ``figure_relpath``)."""

    module: str   # e.g. "demo_junction"
    label: str    # the phase / version tag, e.g. "Phase 1a", "v1.1"
    blurb: str    # the one-liner (verbatim with the README catalog)


# The process spine — the four phases, in build order (start here).
SPINE = [
    Demo("demo_junction", "Phase 1a",
         "A pn junction from a two-step boron diffusion: junction depth x_j + sheet resistance R_s."),
    Demo("demo_oxidation", "Phase 2",
         "Deal–Grove thermal oxide, wet vs dry, the linear→parabolic bend."),
    Demo("demo_litho", "Phase 3",
         "The aerial image assembling from its diffraction orders + contrast-vs-pitch."),
    Demo("demo_device", "Phase 4",
         "The whole process→device chain → MOS threshold voltage V_t."),
]

# The deepenings — the experiments, each promoting a named scope edge of its phase.
DEEPENINGS = [
    Demo("demo_thin_oxide", "v1.1",
         "Massoud thin-dry oxide correction — gate-oxide before/after, the V_t shift."),
    Demo("demo_coupling", "v1.2",
         "Phase 1↔2 back-coupling: OED deepening + segregation (boron depletes / phosphorus piles up)."),
    Demo("demo_diffusion_highconc", "v1.3",
         "Concentration-dependent diffusivity D(N) — the high-concentration box."),
    Demo("demo_defocus", "v1.4",
         "Lithographic defocus — the depth of focus & the Bossung curve."),
    Demo("demo_peb", "v1.7",
         "PEB acid-diffusion blur: the latent image dissolving + the PEB window."),
    Demo("demo_lateral_diffusion", "v1.8",
         "2-D lateral diffusion under a mask edge — the junction curving under the mask."),
    Demo("demo_car", "v1.9",
         "CAR reaction–diffusion PEB — the chemically-amplified bake."),
    Demo("demo_zernike", "v1.10",
         "Zernike aberrations (coma / astigmatism / spherical) — a pupil phase."),
]

ALL_DEMOS = SPINE + DEEPENINGS


def glob_demo_modules() -> set[str]:
    """The demo modules actually on disk — the inclusion anchor (a new demo appears here)."""
    return {p.stem for p in CHIP_DIR.glob("demo_*.py")}


def assert_manifest_complete() -> None:
    """Loudly refuse to render a stale gallery: the manifest must match ``chip/demo_*.py`` exactly."""
    on_disk = glob_demo_modules()
    in_manifest = {d.module for d in ALL_DEMOS}
    missing, stale = on_disk - in_manifest, in_manifest - on_disk
    if missing or stale:
        raise SystemExit(
            "chip/gallery.py manifest is out of sync with chip/demo_*.py — "
            f"add to the manifest: {sorted(missing)}; remove (no such demo): {sorted(stale)}"
        )


def figure_relpath(demo: Demo) -> str:
    """The demo's banked figure, **relative to docs/** — introspected from the module's DOCS_FIGURE.

    Importing a demo module is viz-free (matplotlib is imported lazily inside its ``save_figure``),
    so this is safe in the fast lane without the ``viz`` extra installed.
    """
    mod = importlib.import_module(f"chip.{demo.module}")
    return Path(mod.DOCS_FIGURE).relative_to(DOCS_DIR).as_posix()  # e.g. "figures/chip-oed-segregation.png"


def _card(demo: Demo) -> str:
    fig = figure_relpath(demo)
    label = html.escape(demo.label)
    blurb = html.escape(demo.blurb)
    run = html.escape(f"python -m chip.{demo.module}")
    src = f"{_BLOB}/chip/{demo.module}.py"
    return f"""        <article class="card">
          <a class="shot" href="{fig}" title="open the full figure">
            <img src="{fig}" alt="{label} — {html.escape(demo.module)} figure" loading="lazy">
          </a>
          <div class="body">
            <span class="tag">{label}</span>
            <p class="blurb">{blurb}</p>
            <div class="links">
              <code>{run}</code>
              <a class="src" href="{src}">source&nbsp;&#8599;</a>
            </div>
          </div>
        </article>"""


def _grid(demos: list[Demo]) -> str:
    return "\n".join(_card(d) for d in demos)


# Deterministic by construction: the output depends only on the manifest + introspected figure
# paths — no timestamps, no machine paths — so the golden test in test_gallery.py never thrashes.
_STYLE = """\
      :root {
        --bg: #f6f7f9; --card: #ffffff; --ink: #1c2530; --muted: #5b6772;
        --line: #e2e6ea; --accent: #2f6db5; --code: #0b3a66; --shot-bg: #fafbfc;
      }
      * { box-sizing: border-box; }
      body { margin: 0; background: var(--bg); color: var(--ink);
             font: 16px/1.55 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
      a { color: var(--accent); text-decoration: none; }
      a:hover { text-decoration: underline; }
      header { padding: 2.6rem 1.5rem 1.4rem; border-bottom: 1px solid var(--line);
               background: linear-gradient(180deg, #fff, var(--bg)); }
      .wrap { max-width: 1180px; margin: 0 auto; }
      h1 { margin: 0 0 .25rem; font-size: 1.9rem; letter-spacing: -.01em; }
      .tagline { margin: 0 0 1rem; color: var(--muted); font-size: 1.05rem; }
      .lead { margin: 0 0 1rem; max-width: 70ch; }
      .quick { margin: 0; padding: .7rem .9rem; background: #0d1b2a; color: #e6edf3;
               border-radius: 8px; overflow-x: auto; font: .85rem/1.5 ui-monospace, "Cascadia Code", Consolas, monospace; }
      .quick .c { color: #7fb0e0; }
      .repo { display: inline-block; margin-top: .8rem; font-weight: 600; }
      main { max-width: 1180px; margin: 0 auto; padding: 1.6rem 1.5rem 3rem; }
      section { margin-top: 2.2rem; }
      h2 { font-size: 1.3rem; margin: 0 0 .2rem; }
      .sub { margin: 0 0 1.1rem; color: var(--muted); }
      .grid { display: grid; gap: 1.1rem; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); }
      .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
              overflow: hidden; display: flex; flex-direction: column;
              transition: box-shadow .15s ease, transform .15s ease; }
      .card:hover { box-shadow: 0 8px 24px rgba(20,40,70,.12); transform: translateY(-2px); }
      .shot { display: block; background: var(--shot-bg); border-bottom: 1px solid var(--line); }
      .shot img { display: block; width: 100%; height: auto; }
      .body { padding: .9rem 1rem 1rem; display: flex; flex-direction: column; gap: .55rem; flex: 1; }
      .tag { align-self: flex-start; font-weight: 700; font-size: .76rem; letter-spacing: .03em;
             text-transform: uppercase; color: var(--accent); background: #eaf2fb;
             border-radius: 999px; padding: .12rem .6rem; }
      .blurb { margin: 0; flex: 1; }
      .links { display: flex; align-items: center; justify-content: space-between; gap: .6rem;
               margin-top: .2rem; padding-top: .6rem; border-top: 1px dashed var(--line); }
      .links code { color: var(--code); background: #eef3f8; border-radius: 6px;
                    padding: .2rem .45rem; font: .8rem ui-monospace, "Cascadia Code", Consolas, monospace;
                    overflow-x: auto; }
      .src { white-space: nowrap; font-size: .85rem; }
      .deeper { display: grid; gap: .8rem; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
      .deeper .item { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
                      padding: .9rem 1rem; }
      .deeper .item h3 { margin: 0 0 .25rem; font-size: 1rem; }
      .deeper .item p { margin: 0; color: var(--muted); font-size: .9rem; }
      footer { border-top: 1px solid var(--line); color: var(--muted); font-size: .85rem;
               padding: 1.4rem 1.5rem 2.4rem; }
      footer code { background: #eef3f8; border-radius: 5px; padding: .1rem .35rem;
                    font: .82rem ui-monospace, Consolas, monospace; }"""


def render_html() -> str:
    """Render the whole gallery to a deterministic HTML string (no dates, no machine paths)."""
    spine = _grid(SPINE)
    deepenings = _grid(DEEPENINGS)
    nb = f"{_BLOB}/chip/chip.ipynb"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>chip-sim — visualization &amp; demo gallery</title>
  <style>
{_STYLE}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>chip-sim &mdash; the gallery</h1>
      <p class="tagline"><em>Process recipe in, device out.</em> An educational microchip-fabrication simulator.</p>
      <p class="lead">Every fab step ships a self-contained demo that prints a cited validation table and
        banks a figure. This page is the clickable front door to all of it: the
        <strong>visualizations</strong> (click any figure for full size), the <strong>demos</strong> that
        produce them (run command + source), the v1.x <strong>experiments</strong>, and the guided
        <strong>notebook</strong>. The figures below are pre-committed, so the gallery browses without
        running anything.</p>
      <pre class="quick"><span class="c"># clone, install the figure stack, run any demo</span>
pip install -e ".[viz]"
python -m chip.demo_junction   <span class="c"># prints the table, banks docs/figures/chip-junction.png</span></pre>
      <a class="repo" href="{_REPO_URL}">View the repository on GitHub&nbsp;&#8599;</a>
    </div>
  </header>

  <main>
    <section>
      <h2>The process spine</h2>
      <p class="sub">The four phases, in build order &mdash; start here.</p>
      <div class="grid">
{spine}
      </div>
    </section>

    <section>
      <h2>The deepenings &mdash; experiments</h2>
      <p class="sub">Optional depth: each promotes a named scope edge of its phase. (v1.5&ndash;v1.6 are
        engine-internal amendments &mdash; native nonlinear D(u) and explicit stepping &mdash; with no chip
        demo of their own.)</p>
      <div class="grid">
{deepenings}
      </div>
    </section>

    <section>
      <h2>Go deeper</h2>
      <p class="sub">The interactive tour and the written record.</p>
      <div class="deeper">
        <a class="item" href="{nb}">
          <h3>The teaching notebook &#8599;</h3>
          <p>chip/chip.ipynb &mdash; one section per phase with live ipywidgets sliders, ending on the
            coherent process&rarr;device flow.</p>
        </a>
        <a class="item" href="{_BLOB}/README.md">
          <h3>README &amp; quickstart &#8599;</h3>
          <p>Layout, the tiered test gate, and the text Demonstrations catalog.</p>
        </a>
        <a class="item" href="{_BLOB}/chip/README.md#status">
          <h3>Status writeups &#8599;</h3>
          <p>Per-phase / per-version depth: cited references, headline numbers, scope edges, findings.</p>
        </a>
        <a class="item" href="{_TREE}/docs/decisions">
          <h3>Decision records &#8599;</h3>
          <p>ADRs 0001&ndash;0004 &mdash; language/perf, visualization/UX, test policy, the engine unfreeze.</p>
        </a>
        <a class="item" href="{_BLOB}/docs/plans/microchip-fabrication.md">
          <h3>The build plan &#8599;</h3>
          <p>microchip-fabrication.md &mdash; the full process&rarr;device pedagogy and build order.</p>
        </a>
        <a class="item" href="{_TREE}/engines/diffusion">
          <h3>The diffusion engine &#8599;</h3>
          <p>The separately-validated 1-D/2-D solver spine the whole simulator reuses.</p>
        </a>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap">Generated from the demo modules by <code>python -m chip.gallery</code> &mdash;
      figure paths are introspected, never hand-typed, so this gallery stays in lock-step with the demos.</div>
  </footer>
</body>
</html>
"""


def write_html() -> Path:
    """Write the gallery to ``docs/index.html`` with LF newlines (golden-test stable on Windows + CI)."""
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(render_html(), encoding="utf-8", newline="\n")
    return OUTPUT_HTML


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # the → in the message, on legacy codepages
    assert_manifest_complete()
    saved = write_html()
    print(f"Gallery written → {saved.relative_to(_REPO_ROOT)}  ({len(ALL_DEMOS)} demos)")


if __name__ == "__main__":
    main()
