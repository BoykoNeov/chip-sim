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
OUTPUT_LOCAL_HTML = DOCS_DIR / "index.local.html"

# --- the local edition (docs/index.local.html) -------------------------------------------------
# A second, deterministic render whose links open in a *running* JupyterLab instead of on GitHub,
# so the teaching-notebook card becomes a real click->live-notebook launch (the one thing GitHub's
# read-only viewer can't do). These are fixed localhost strings — no machine path — so this page
# stays as golden-testable as the public one. It does NOT replace index.html: the public Pages
# gallery is untouched; you open this file locally (a browser tab over file://, or via the lab).
# A click can only REACH a server that is already up — it cannot start `jupyter lab` for you.
_LOCAL_PORT = 8888
_LAB = f"http://localhost:{_LOCAL_PORT}/lab/tree"   # "open this repo-relative path in JupyterLab"
_LAB_ROOT = f"http://localhost:{_LOCAL_PORT}/lab"


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
    Demo("demo_device_2d", "v1.11",
         "2-D MOSFET cross-section — lateral S/D diffusion shortens the channel (L_eff), not V_t."),
    Demo("demo_implant", "§5",
         "Ion implantation — the buried peak a predep cannot make; the honest V_t-adjust implant."),
    Demo("demo_doping_history", "hist·A1",
         "Pre-implant doping's dose-control wall — the solubility-pinned surface can't meter a light V_t-adjust dose; implant can."),
    Demo("demo_oxidation_history", "hist·A3",
         "Period oxidation ambients — HCl getters mobile Na (V_t recovery); high pressure grows the same oxide for 1/P the thermal budget."),
    Demo("demo_metallization_history", "hist·B6",
         "Aluminium junction spiking — pure Al shorts the shallow (implant-era) junction; Al–Si and barrier metals clear the wall."),
    Demo("demo_litho_history", "hist·A2",
         "Period lithography — the wavelength/lens ladder (g-line→EUV) moves the Rayleigh floor; contact/proximity printing hits the √(λg) gap wall projection broke."),
    Demo("demo_resist_history", "hist·A4",
         "Period photoresist — negative-resist (KTFR) solvent swelling bridges fine lines at a floor ≈ the film thickness (optics-independent); positive/CAR don't swell and clear it."),
    Demo("demo_locos_history", "hist·B5",
         "LOCOS isolation — oxidant under the nitride mask grows the bird's beak that eats active area; opposing beaks merge and pinch off below a min pitch (∝ field-oxide thickness); STI's vertical walls clear it."),
    Demo("demo_silicide_history", "hist·B7",
         "Silicide / contact resistance — the source series-R is two terms with different R_sh exponents (access linear + TLM contact sublinear); salicide shunts the sheet so access collapses and the bottleneck flips to the contact."),
    Demo("demo_highk_history", "hist·B8",
         "High-κ gate dielectric — one thickness feeds two currencies: SiO₂ scales into a tunnelling wall at EOT ≈ 1.5 nm, and HfO₂ clears it with a 6.4× thicker barrier at the SAME electrical gate (V_t / C_ox byte-identical)."),
    Demo("demo_beol_history", "hist·B9",
         "BEOL interconnect — τ_wire ∝ 1/W² climbs past a transistor that never moved, so a +3% device buys a +0.7% part; copper bought 0.64 of a node, and on the bulk-ρ axis there is no third metal."),
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


def figure_relpath(demo: Demo, pkg: str = "chip") -> str:
    """The demo's banked figure, **relative to docs/** — introspected from the module's DOCS_FIGURE.

    Importing a demo module is viz-free (matplotlib is imported lazily inside its ``save_figure``),
    so this is safe in the fast lane without the ``viz`` extra installed. ``pkg`` lets the sibling
    ``fab_game`` gallery reuse this for its own ``fab_game.demo_*`` modules (fab_game → chip is the
    allowed import direction, ADR 0005 §2); ``pkg="chip"`` keeps this module's own output identical.
    """
    mod = importlib.import_module(f"{pkg}.{demo.module}")
    return Path(mod.DOCS_FIGURE).relative_to(DOCS_DIR).as_posix()  # e.g. "figures/chip-oed-segregation.png"


def _card(demo: Demo, local: bool = False, pkg: str = "chip") -> str:
    fig = figure_relpath(demo, pkg)
    label = html.escape(demo.label)
    blurb = html.escape(demo.blurb)
    run = html.escape(f"python -m {pkg}.{demo.module}")
    src = f"{_LAB}/{pkg}/{demo.module}.py" if local else f"{_BLOB}/{pkg}/{demo.module}.py"
    tgt = ' target="_blank" rel="noopener"' if local else ""   # launch in a new tab, keep the gallery open
    return f"""        <article class="card">
          <a class="shot" href="{fig}" title="open the full figure">
            <img src="{fig}" alt="{label} — {html.escape(demo.module)} figure" loading="lazy">
          </a>
          <div class="body">
            <span class="tag">{label}</span>
            <p class="blurb">{blurb}</p>
            <div class="links">
              <code>{run}</code>
              <a class="src" href="{src}"{tgt}>source&nbsp;&#8599;</a>
            </div>
          </div>
        </article>"""


def _grid(demos: list[Demo], local: bool = False, pkg: str = "chip") -> str:
    return "\n".join(_card(d, local, pkg) for d in demos)


# Deterministic by construction: the output depends only on the manifest + introspected figure
# paths — no timestamps, no machine paths — so the golden test in test_gallery.py never thrashes.
# One stylesheet for all four pages (physics / fab-game / history / roadmap): every color is a
# CSS variable with a dark-scheme counterpart, so the whole site follows the reader's theme.
_STYLE = """\
      :root {
        --bg: #f6f7f9; --card: #ffffff; --ink: #1c2530; --muted: #5b6772;
        --line: #e2e6ea; --accent: #2f6db5; --code: #0b3a66; --shot-bg: #fafbfc;
        --tag-bg: #eaf2fb; --code-bg: #eef3f8; --head-glow: #ffffff;
        --note-bg: #fff7e6; --note-line: #f0d8a8;
        --wall: #b23c2f; --next: #2e7d46;
        --ok-ink: #2e7d46; --ok-bg: #e7f4ec; --part-ink: #8a5a00; --part-bg: #fdf3dd;
        --hold-ink: #5b6772; --hold-bg: #eef1f4;
        --shadow: 0 8px 24px rgba(20,40,70,.12);
      }
      @media (prefers-color-scheme: dark) {
        :root {
          --bg: #10151b; --card: #171e26; --ink: #e3e8ee; --muted: #97a3ae;
          --line: #2a333d; --accent: #6ea8e0; --code: #a8c7e8; --shot-bg: #fafbfc;
          --tag-bg: #1d2f42; --code-bg: #1c2733; --head-glow: #141b23;
          --note-bg: #2b2416; --note-line: #5a4a22;
          --wall: #e07a6d; --next: #58b878;
          --ok-ink: #58b878; --ok-bg: #16281d; --part-ink: #d9a53f; --part-bg: #2b2310;
          --hold-ink: #97a3ae; --hold-bg: #1d242c;
          --shadow: 0 8px 24px rgba(0,0,0,.45);
        }
      }
      * { box-sizing: border-box; }
      body { margin: 0; background: var(--bg); color: var(--ink);
             font: 16px/1.55 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
      a { color: var(--accent); text-decoration: none; }
      a:hover { text-decoration: underline; }
      a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
      header { padding: 2.2rem 1.5rem 1.4rem; border-bottom: 1px solid var(--line);
               background: linear-gradient(180deg, var(--head-glow), var(--bg)); }
      .wrap { max-width: 1180px; margin: 0 auto; }
      .crumbs { display: flex; flex-wrap: wrap; gap: .4rem .5rem; margin: 0 0 1.3rem;
                font-size: .84rem; }
      .crumbs a, .crumbs .here { display: inline-block; border: 1px solid var(--line);
                                 border-radius: 999px; padding: .16rem .75rem; background: var(--card); }
      .crumbs a:hover { text-decoration: none; border-color: var(--accent); }
      .crumbs .here { background: var(--accent); border-color: var(--accent); color: #fff;
                      font-weight: 600; }
      h1 { margin: 0 0 .25rem; font-size: 1.9rem; letter-spacing: -.01em; }
      .tagline { margin: 0 0 1rem; color: var(--muted); font-size: 1.05rem; }
      .lead { margin: 0 0 1rem; max-width: 70ch; }
      .localnote { background: var(--note-bg); border: 1px solid var(--note-line);
                   border-radius: 8px; padding: .6rem .8rem; margin-top: 1rem; }
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
              transition: box-shadow .15s ease, transform .15s ease, border-color .15s ease; }
      .card:hover { box-shadow: var(--shadow); transform: translateY(-2px);
                    border-color: var(--accent); }
      .shot { display: block; position: relative; background: var(--shot-bg);
              border-bottom: 1px solid var(--line); }
      .shot img { display: block; width: 100%; height: auto; }
      .body { padding: .9rem 1rem 1rem; display: flex; flex-direction: column; gap: .55rem; flex: 1; }
      .tag { align-self: flex-start; font-weight: 700; font-size: .76rem; letter-spacing: .03em;
             text-transform: uppercase; color: var(--accent); background: var(--tag-bg);
             border-radius: 999px; padding: .12rem .6rem; }
      .blurb { margin: 0; flex: 1; }
      .links { display: flex; align-items: center; justify-content: space-between; gap: .6rem;
               margin-top: .2rem; padding-top: .6rem; border-top: 1px dashed var(--line); }
      .links code { color: var(--code); background: var(--code-bg); border-radius: 6px;
                    padding: .2rem .45rem; font: .8rem ui-monospace, "Cascadia Code", Consolas, monospace;
                    overflow-x: auto; }
      .src { white-space: nowrap; font-size: .85rem; }
      .deeper { display: grid; gap: .8rem; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
      .deeper .item { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
                      padding: .9rem 1rem; transition: border-color .15s ease, box-shadow .15s ease; }
      .deeper .item:hover { border-color: var(--accent); box-shadow: var(--shadow); }
      .deeper .item h3 { margin: 0 0 .25rem; font-size: 1rem; color: var(--ink); }
      .deeper .item p { margin: 0; color: var(--muted); font-size: .9rem; }
      footer { border-top: 1px solid var(--line); color: var(--muted); font-size: .85rem;
               padding: 1.4rem 1.5rem 2.4rem; }
      footer code { background: var(--code-bg); border-radius: 5px; padding: .1rem .35rem;
                    font: .82rem ui-monospace, Consolas, monospace; }
      /* --- roadmap (planned-slice) cards — used by docs/roadmap.html only ---------------- */
      .ribbon { position: absolute; top: .55rem; left: .55rem; z-index: 1; font-weight: 700;
                font-size: .66rem; letter-spacing: .05em; text-transform: uppercase;
                color: #fff; background: rgba(28,37,48,.78); border-radius: 999px;
                padding: .16rem .6rem; pointer-events: none; }
      .tagrow { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; }
      .status { font-weight: 700; font-size: .76rem; letter-spacing: .03em;
                text-transform: uppercase; border-radius: 999px; padding: .12rem .6rem; }
      .status.ok { color: var(--ok-ink); background: var(--ok-bg); }
      .status.part { color: var(--part-ink); background: var(--part-bg); }
      .status.hold { color: var(--hold-ink); background: var(--hold-bg); }
      .facts { display: flex; flex-direction: column; gap: .35rem; }
      .facts .row { display: flex; gap: .55rem; }
      .facts .k { flex: 0 0 5.6rem; font-weight: 700; font-size: .72rem; letter-spacing: .03em;
                  text-transform: uppercase; color: var(--muted); padding-top: .14rem; }
      .facts .k.would { color: var(--next); }
      .facts .k.gate { color: var(--wall); }
      .facts .v { margin: 0; flex: 1; font-size: .9rem; }"""


# The cross-gallery navigation strip — the same four pages on every page, the current one inert.
# Slugs match the docs/ file names; the local editions link to the sibling *.local.html files.
_PAGES = [
    ("index", "Physics gallery"),
    ("fab-game", "Fab-line game"),
    ("history", "Era timeline"),
    ("roadmap", "Roadmap"),
]


def _nav(current: str, local: bool = False) -> str:
    """The nav strip shared by all four docs pages; ``current`` is the page's slug (inert pill)."""
    ext = ".local.html" if local else ".html"
    pills = []
    for slug, label in _PAGES:
        if slug == current:
            pills.append(f'<span class="here">{label}</span>')
        else:
            pills.append(f'<a href="{slug}{ext}">{label}</a>')
    joined = "\n        ".join(pills)
    return f"""<nav class="crumbs" aria-label="chip-sim pages">
        {joined}
      </nav>"""


def render_html(local: bool = False) -> str:
    """Render the whole gallery to a deterministic HTML string (no dates, no machine paths).

    ``local=True`` renders ``docs/index.local.html``: the same gallery, but every link that would go
    to GitHub instead opens in a *running* JupyterLab (``localhost``) — so the notebook card becomes a
    real click->live-notebook launch. The public ``index.html`` (``local=False``) is byte-for-byte
    unchanged. Both depend only on the manifest + fixed strings, so both stay golden-testable.
    """
    spine = _grid(SPINE, local)
    deepenings = _grid(DEEPENINGS, local)
    item_attr = ' target="_blank" rel="noopener"' if local else ""  # local: launch alongside the gallery
    if local:
        title = "chip-sim &mdash; gallery (local edition)"
        repo_link = f'<a class="repo" href="{_LAB_ROOT}"{item_attr}>Open the repo in Jupyter&nbsp;Lab&nbsp;&#8599;</a>'
        note = (
            '\n      <p class="lead localnote"><strong>Local edition.</strong> Every link here opens in '
            "your <strong>running JupyterLab</strong> &mdash; locally and live, not a static read-only page. "
            "Start it once from the repo root (<code>jupyter lab</code>), then click anything below: the "
            f"notebook card opens <em>live</em>, sliders and all. Links target <code>localhost:{_LOCAL_PORT}"
            "</code>; a click can&rsquo;t start the server, only reach one already running.</p>"
        )
        notebook_card = f"""<a class="item" href="{_LAB}/chip/chip.ipynb"{item_attr}>
          <h3>The teaching notebook &rarr; open it live</h3>
          <p>chip/chip.ipynb &mdash; one section per phase with live ipywidgets sliders, ending on the
            coherent process&rarr;device flow. Clicking opens it <strong>interactively in your running
            JupyterLab</strong> &mdash; start <code>jupyter lab</code> from the repo root first; the link
            targets port&nbsp;{_LOCAL_PORT}.</p>
        </a>"""
        readme = f"{_LAB}/README.md"
        status = f"{_LAB}/chip/README.md"
        decisions = f"{_LAB}/docs/decisions"
        build_plan = f"{_LAB}/docs/plans/microchip-fabrication.md"
        engine = f"{_LAB}/engines/diffusion"
        fabgame = "fab-game.local.html"   # the sibling gallery's local edition (next to this file)
        history = "history.local.html"    # the era timeline's local edition (H0, next to this file)
        roadmap = "roadmap.local.html"    # the planned-slices page's local edition (next to this file)
    else:
        title = "chip-sim — visualization &amp; demo gallery"
        repo_link = f'<a class="repo" href="{_REPO_URL}">View the repository on GitHub&nbsp;&#8599;</a>'
        note = ""
        nb = f"{_BLOB}/chip/chip.ipynb"
        notebook_card = f"""<div class="item">
          <h3>The teaching notebook</h3>
          <p>chip/chip.ipynb &mdash; one section per phase with live ipywidgets sliders, ending on the
            coherent process&rarr;device flow. GitHub renders it <em>read-only</em> (no live kernel); for the
            interactive widgets, install the notebook extra (<code>pip install -e ".[viz,notebook]"</code>)
            and launch it locally:</p>
          <div class="links">
            <code>jupyter lab chip/chip.ipynb</code>
            <a class="src" href="{nb}">view on GitHub&nbsp;&#8599;</a>
          </div>
        </div>"""
        readme = f"{_BLOB}/README.md"
        status = f"{_BLOB}/chip/README.md#status"
        decisions = f"{_TREE}/docs/decisions"
        build_plan = f"{_BLOB}/docs/plans/microchip-fabrication.md"
        engine = f"{_TREE}/engines/diffusion"
        fabgame = "fab-game.html"   # the sibling gallery (the gamified full-line layer), in the same /docs dir
        history = "history.html"    # the era timeline (H0, the backward axis), in the same /docs dir
        roadmap = "roadmap.html"    # the planned-slices page (schematic previews), in the same /docs dir
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
{_STYLE}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      {_nav("index", local)}
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
      {repo_link}{note}
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
        <a class="item" href="{fabgame}"{item_attr}>
          <h3>The fab-line game &#8599;</h3>
          <p>A separate gallery: the gamified full-line layer built on this physics &mdash; sand &rarr; a
            binned chip across G1&ndash;G7, plus the crystal-growth and scope-edge deepenings. Recipe in
            &rarr; <strong>yield</strong> out, and you can see <em>why</em> a die died.</p>
        </a>
        <a class="item" href="{history}"{item_attr}>
          <h3>The era timeline &#8599;</h3>
          <p>The backward axis: the same steps re-run in their <em>period</em> mode &mdash; each
            historical figure above laid on the process spine with the wall it hit and the modern step
            that cleared it (doping&rarr;implant, drifting oxide&rarr;HCl, Al spiking&rarr;barrier metal).</p>
        </a>
        <a class="item" href="{roadmap}"{item_attr}>
          <h3>The roadmap &#8599;</h3>
          <p>The planned-but-unbuilt slices &mdash; high-&kappa; gate, BEOL interconnect RC, strained
            SiGe, FinFET/GAA &mdash; each with a <em>schematic preview</em> (not simulator output) and
            the named consumer that gates its build.</p>
        </a>
        {notebook_card}
        <a class="item" href="{readme}"{item_attr}>
          <h3>README &amp; quickstart &#8599;</h3>
          <p>Layout, the tiered test gate, and the text Demonstrations catalog.</p>
        </a>
        <a class="item" href="{status}"{item_attr}>
          <h3>Status writeups &#8599;</h3>
          <p>Per-phase / per-version depth: cited references, headline numbers, scope edges, findings.</p>
        </a>
        <a class="item" href="{decisions}"{item_attr}>
          <h3>Decision records &#8599;</h3>
          <p>ADRs 0001&ndash;0004 &mdash; language/perf, visualization/UX, test policy, the engine unfreeze.</p>
        </a>
        <a class="item" href="{build_plan}"{item_attr}>
          <h3>The build plan &#8599;</h3>
          <p>microchip-fabrication.md &mdash; the full process&rarr;device pedagogy and build order.</p>
        </a>
        <a class="item" href="{engine}"{item_attr}>
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


def write_html(local: bool = False) -> Path:
    """Write a gallery edition with LF newlines (golden-test stable on Windows + CI).

    ``local=False`` → the public ``docs/index.html`` (GitHub links, served by Pages);
    ``local=True``  → ``docs/index.local.html`` (links open in a running JupyterLab)."""
    out = OUTPUT_LOCAL_HTML if local else OUTPUT_HTML
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(local), encoding="utf-8", newline="\n")
    return out


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # the → in the message, on legacy codepages
    assert_manifest_complete()
    public = write_html()
    local = write_html(local=True)
    print(f"Gallery written → {public.relative_to(_REPO_ROOT)} + "
          f"{local.relative_to(_REPO_ROOT)}  ({len(ALL_DEMOS)} demos)")


if __name__ == "__main__":
    main()
