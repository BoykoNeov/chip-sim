"""The fab-line game gallery generator — a *separate* front door for the game layer.

Builds ``docs/fab-game.html`` (and the ``…local.html`` JupyterLab edition): the same clickable
gallery the physics side ships (:mod:`chip.gallery`), but over ``fab_game/demo_*.py`` — the gamified
full-line layer, *recipe in → yield out, and you can see why a die died.*

Why a separate page (not a section bolted onto ``docs/index.html``):

  * **The layering is one-way (ADR 0005 §2).** ``fab_game → chip`` is allowed; the reverse is
    forbidden and enforced by ``fab_game/tests/test_import_direction.py``. A single generator owned by
    ``chip/`` could not introspect ``fab_game.demo_*`` without ``chip`` importing ``fab_game``. So the
    *game* gallery is generated *here*, in the game layer, reusing the physics gallery's primitives
    (the shared CSS ``_STYLE`` + the pkg-parametrized ``_card`` / ``figure_relpath``) the allowed way.
  * The two galleries cross-link (the physics "Go deeper" → here; here → back), so a newcomer can
    walk from the diffusion engine out to a binned chip without ever leaving the front door.

Same drift-proofing as the physics gallery: the figure for every card is **introspected** from the
demo module's own ``DOCS_FIGURE`` (never re-typed); inclusion is anchored to the ``fab_game/demo_*.py``
glob; and ``fab_game/tests/test_gallery.py`` fails the fast lane if a demo is missing from the manifest
below, a figure is absent, or the committed HTML is stale.

Regenerate after adding/renaming a demo or editing a blurb (then commit the HTML):

    python -m fab_game.gallery
"""
from __future__ import annotations

from pathlib import Path

# Reuse the physics gallery's primitives the allowed direction (fab_game → chip). _STYLE keeps the two
# galleries visually identical; _card/_grid/figure_relpath are pkg-parametrized so they render
# fab_game.demo_* cards (run command, source link, introspected figure) without any duplication.
from chip.gallery import (
    Demo,
    _STYLE,
    _card,            # noqa: F401  (re-exported intent: shared card markup)
    _grid,
    figure_relpath,
    _BLOB,
    _TREE,
    _REPO_URL,
    _LAB,
    _LAB_ROOT,
    _LOCAL_PORT,
    DOCS_DIR,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
FAB_DIR = _REPO_ROOT / "fab_game"
OUTPUT_HTML = DOCS_DIR / "fab-game.html"
OUTPUT_LOCAL_HTML = DOCS_DIR / "fab-game.local.html"

_PKG = "fab_game"

# The line — sand → a binned chip, in process order (start here). G1 is all reuse (zero new physics);
# G2 onward each adds a cited, triad-tested chip/ module that the game layer consumes.
LINE = [
    Demo("demo_fab_game", "G1",
         "One bad knob → a dead die, with the failure trail: defocus → NILS collapse → off-spec → "
         "the wafer yield drops, and the trail names defocus as the cause."),
    Demo("demo_boule", "G2",
         "Czochralski + the Scheil axial boule → a V_t spread down the boule (k≈0.8, the tail scraps) "
         "— the difficulty curve of a run."),
    Demo("demo_wafer_prep", "G3",
         "The die map made physical: killer particles → the defect-limited yield law Y=exp(−D₀A) + the "
         "TTV/bow geometry scrap gate."),
    Demo("demo_purification", "G4",
         "Silicon purification (Pfann single-pass zone refining) → Na contamination → Q_ox → a V_t hit, "
         "recovered by rework."),
    Demo("demo_lifetime", "G4b",
         "Deep-level metals (Fe/Cu) → SRH lifetime killed → generation leakage → a leaky diode (the "
         "optional leakage spec window)."),
    Demo("demo_etch", "G5",
         "The mid-line etch & deposition: etch bias shrinks CD; a gap above the aspect-ratio limit voids "
         "the deposition (a functional kill)."),
    Demo("demo_packaging", "G6",
         "The back end: the cumulative assembly-yield funnel Y=Πyᵢ + speed binning into value grades "
         "(the bin-out tail)."),
    Demo("demo_game", "G7",
         "A roguelike run down one boule: thin the gate oxide against the rising Scheil V_t drift — a "
         "Goldilocks lever (over-thinning hits the I_Dsat ceiling)."),
    Demo("demo_journey", "J1",
         "The staged sand→chip journey (phases 1–4): purify a feed (refine → the graded Na edge ring), grow the "
         "boule (the two-sided Voronkov pull window — leakage rim ↔ void core), cut a wafer (where down "
         "the boule — a graded Scheil V_t centre core, how deep set by the phase-2 pull), then diffuse the S/D "
         "(the predep dose → R_s → a series-resistance-starved, centre-weighted I_Dsat core) — commit each decision and "
         "finish to a scored wafer."),
]

# The deepenings — the crystal-growth triad + the scope-edge promotions, each promoting a named edge
# into a device/yield consumer. Each is a cited, triad-tested chip/ module (the named-consumer bar).
DEEPENINGS = [
    Demo("demo_crystal_growth", "CG-1",
         "Pull rate → the Burton–Prim–Slichter effective segregation k_eff(v) → flattens the Scheil "
         "doping drift (one-sided: faster only helps)."),
    Demo("demo_voronkov", "CG-2",
         "The Voronkov V/G criterion → grown-in voids/COPs above ξ_t feed the same G3 defect map — the "
         "in-model brake on pulling faster."),
    Demo("demo_stefan", "CG-3",
         "The Stefan interface heat balance supplies CG-2's gradient G → ξ=V/G_s saturates at ξ_max, "
         "capping the vacancy cost."),
    Demo("demo_thermal_donors", "C1",
         "Crucible oxygen → thermal donors (initial rate ∝[Oᵢ]⁴) compensate the p-substrate (N_A−N_TD) "
         "→ V_t down — the crystal-growth electrical deepening."),
    Demo("demo_under_etch", "D1",
         "Under-etch → a residual film bridges the gate lines into a functional short — the mirror of "
         "the deposition void's open (the etch process window)."),
    Demo("demo_osf_ring", "A2",
         "The OSF ring: CG-2 made radial → a dead vacancy core + a clean rim. The ring is where the "
         "kills stop, not a ring of kills."),
    Demo("demo_dislocation", "A1",
         "The interstitial side of Voronkov: slow pull (ξ<ξ_t) → dislocations → junction leakage — the "
         "two-sided window (optimum at ξ_t)."),
    Demo("demo_thermal_budget", "E1",
         "A spike/RTA anneal's thermal budget ∫D(T(t))dt → a faster ramp → a smaller budget → a "
         "shallower x_j (why RTA, the OED effective_Dt twin)."),
]

ALL_DEMOS = LINE + DEEPENINGS


def glob_demo_modules() -> set[str]:
    """The demo modules actually on disk — the inclusion anchor (a new demo appears here)."""
    return {p.stem for p in FAB_DIR.glob("demo_*.py")}


def assert_manifest_complete() -> None:
    """Loudly refuse to render a stale gallery: the manifest must match ``fab_game/demo_*.py`` exactly."""
    on_disk = glob_demo_modules()
    in_manifest = {d.module for d in ALL_DEMOS}
    missing, stale = on_disk - in_manifest, in_manifest - on_disk
    if missing or stale:
        raise SystemExit(
            "fab_game/gallery.py manifest is out of sync with fab_game/demo_*.py — "
            f"add to the manifest: {sorted(missing)}; remove (no such demo): {sorted(stale)}"
        )


def render_html(local: bool = False) -> str:
    """Render the whole fab-game gallery to a deterministic HTML string (no dates, no machine paths).

    ``local=True`` renders ``docs/fab-game.local.html``: the same gallery, but every link that would go
    to GitHub instead opens in a *running* JupyterLab (``localhost``) — so the notebook card becomes a
    real click→live-notebook launch. The public ``fab-game.html`` (``local=False``) is byte-for-byte
    unchanged. Both depend only on the manifest + fixed strings, so both stay golden-testable.
    """
    line = _grid(LINE, local, _PKG)
    deepenings = _grid(DEEPENINGS, local, _PKG)
    item_attr = ' target="_blank" rel="noopener"' if local else ""  # local: launch alongside the gallery
    if local:
        title = "chip-sim &mdash; the fab-line game (local edition)"
        repo_link = f'<a class="repo" href="{_LAB_ROOT}"{item_attr}>Open the repo in Jupyter&nbsp;Lab&nbsp;&#8599;</a>'
        note = (
            '\n      <p class="lead" style="background:#fff7e6;border:1px solid #f0d8a8;border-radius:8px;'
            'padding:.6rem .8rem;margin-top:1rem;"><strong>Local edition.</strong> Every link here opens in '
            "your <strong>running JupyterLab</strong> &mdash; locally and live, not a static read-only page. "
            "Start it once from the repo root (<code>jupyter lab</code>), then click anything below: the "
            f"notebook card opens <em>live</em>, knobs and all. Links target <code>localhost:{_LOCAL_PORT}"
            "</code>; a click can&rsquo;t start the server, only reach one already running.</p>"
        )
        notebook_card = f"""<a class="item" href="{_LAB}/fab_game/fab_game.ipynb"{item_attr}>
          <h3>The game notebook &rarr; open it live</h3>
          <p>fab_game/fab_game.ipynb &mdash; the front-of-line tour (G1 mechanism &rarr; G2 boule &rarr; G3
            die map) ending on the guided <strong>command-the-whole-line</strong> slice. Clicking opens it
            <strong>interactively in your running JupyterLab</strong> &mdash; start <code>jupyter lab</code>
            from the repo root first; the link targets port&nbsp;{_LOCAL_PORT}.</p>
        </a>"""
        readme = f"{_LAB}/fab_game/README.md"
        adr = f"{_LAB}/docs/decisions/0005-fab-game-layering.md"
        plan = f"{_LAB}/docs/plans/fab-game.md"
        backlog = f"{_LAB}/docs/plans/scope-edge-backlog.md"
        physics = "index.local.html"   # back to the physics gallery's local edition (next to this file)
    else:
        title = "chip-sim &mdash; the fab-line game gallery"
        repo_link = f'<a class="repo" href="{_REPO_URL}">View the repository on GitHub&nbsp;&#8599;</a>'
        note = ""
        nb = f"{_BLOB}/fab_game/fab_game.ipynb"
        notebook_card = f"""<div class="item">
          <h3>The game notebook</h3>
          <p>fab_game/fab_game.ipynb &mdash; the front-of-line tour (G1 mechanism &rarr; G2 boule &rarr; G3
            die map) ending on the guided <strong>command-the-whole-line</strong> slice. GitHub renders it
            <em>read-only</em> (no live kernel); for the interactive knobs, install the extras
            (<code>pip install -e ".[viz,notebook]"</code>) and launch it locally:</p>
          <div class="links">
            <code>jupyter lab fab_game/fab_game.ipynb</code>
            <a class="src" href="{nb}">view on GitHub&nbsp;&#8599;</a>
          </div>
        </div>"""
        readme = f"{_BLOB}/fab_game/README.md"
        adr = f"{_BLOB}/docs/decisions/0005-fab-game-layering.md"
        plan = f"{_BLOB}/docs/plans/fab-game.md"
        backlog = f"{_BLOB}/docs/plans/scope-edge-backlog.md"
        physics = "index.html"   # back to the physics gallery (same /docs dir)
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
      <h1>chip-sim &mdash; the fab-line game</h1>
      <p class="tagline"><em>Recipe in, yield out &mdash; and you can see why a die died.</em> The gamified
        full-production-line layer, built on the validated physics.</p>
      <p class="lead">A wafer's whole journey, <strong>sand &rarr; a binned chip</strong>: a Czochralski
        boule sliced into wafers, the across-wafer die map, the front end, the mid-line, and the back end
        &mdash; each stage a cited <code>chip/</code> module the game layer turns into a <strong>yield</strong>.
        This is the clickable front door to all of it: the <strong>visualizations</strong> (click any figure
        for full size), the <strong>demos</strong> that produce them (run command + source), and the
        <strong>deepenings</strong>. The figures below are pre-committed, so the gallery browses without
        running anything. (The physics side has its <a href="{physics}">own gallery</a>.)</p>
      <pre class="quick"><span class="c"># clone, install the figure stack, run the dramatic first win</span>
pip install -e ".[viz]"
python -m fab_game.demo_fab_game   <span class="c"># prints the trail, banks docs/figures/fab-game-g1.png</span></pre>
      {repo_link}{note}
    </div>
  </header>

  <main>
    <section>
      <h2>The line</h2>
      <p class="sub">Sand to a binned chip, in process order &mdash; start here. G1 is all reuse (zero new
        physics); G2 onward each adds a cited, triad-tested module the game consumes.</p>
      <div class="grid">
{line}
      </div>
    </section>

    <section>
      <h2>The deepenings &mdash; crystal growth &amp; scope edges</h2>
      <p class="sub">Optional depth: the crystal-growth triad (CG-1&ndash;CG-3) and the scope-edge
        promotions (C1/D1/A2/A1/E1), each promoting a named edge into a real device/yield consumer.</p>
      <div class="grid">
{deepenings}
      </div>
    </section>

    <section>
      <h2>Go deeper</h2>
      <p class="sub">The guided notebook, the written record, and back to the physics.</p>
      <div class="deeper">
        {notebook_card}
        <a class="item" href="{physics}"{item_attr}>
          <h3>The physics gallery &#8599;</h3>
          <p>The other front door: the four-phase process spine + the litho deepenings that this game
            layer is built on &mdash; recipe in, device out.</p>
        </a>
        <a class="item" href="{readme}"{item_attr}>
          <h3>The fab_game README &#8599;</h3>
          <p>The two-layer design, the module map, and the per-stage narrative (G1 &rarr; the boule &rarr;
            the physical die map &rarr; the mid-line).</p>
        </a>
        <a class="item" href="{adr}"{item_attr}>
          <h3>ADR 0005 &mdash; the layering &#8599;</h3>
          <p>Why the game is a separate layer with a one-way dependency, and what lives in the game layer
            vs. the validated physics core.</p>
        </a>
        <a class="item" href="{plan}"{item_attr}>
          <h3>The build plan &#8599;</h3>
          <p>fab-game.md &mdash; the G-by-G build order, the design pillars, and the open questions each
            slice resolved.</p>
        </a>
        <a class="item" href="{backlog}"{item_attr}>
          <h3>The scope-edge backlog &#8599;</h3>
          <p>The named-but-deferred edges triaged by consumer &mdash; the anti-over-build bar (now
            exhausted: every remaining edge lacks a device/yield consumer).</p>
        </a>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap">Generated from the demo modules by <code>python -m fab_game.gallery</code> &mdash;
      figure paths are introspected, never hand-typed, so this gallery stays in lock-step with the demos.
      The physics it is built on lives in <code>chip/</code> + <code>engines/</code> (cited, triad-tested);
      this layer owns only the balance, the spec windows, and the fun (ADR 0005).</div>
  </footer>
</body>
</html>
"""


def write_html(local: bool = False) -> Path:
    """Write a gallery edition with LF newlines (golden-test stable on Windows + CI).

    ``local=False`` → the public ``docs/fab-game.html`` (GitHub links, served by Pages);
    ``local=True``  → ``docs/fab-game.local.html`` (links open in a running JupyterLab)."""
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
    print(f"Fab-game gallery written → {public.relative_to(_REPO_ROOT)} + "
          f"{local.relative_to(_REPO_ROOT)}  ({len(ALL_DEMOS)} demos)")


if __name__ == "__main__":
    main()
