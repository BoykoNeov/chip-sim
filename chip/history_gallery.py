"""The era timeline — the shared display surface for the *backward* (historical-modes) axis.

Builds ``docs/history.html`` (and the ``…local.html`` JupyterLab edition): a timeline that lays
each **historical mode** on the process spine and reads its one contrast — *here is the period
result, here is the wall it hit, here is the modern step that cleared it.* This is **Chunk H0** of
``docs/plans/historical-modes.md``: the mode plan's "era display surface," the shared consumer that
converts a Tier-2 mode from "no dedicated device consumer" into "feeds the timeline."

Why a *third* generator (not a section bolted onto the physics gallery ``chip.gallery``):

  * The physics gallery lists **every** ``chip/demo_*.py`` in build order — a mode's dose/leakage
    figure surfaces there as one more card. The timeline is a **different cut** of the *same*
    figures: the ``demo_*_history.py`` subset, re-ordered along the process spine and annotated with
    the **period → wall → successor** framing the flat gallery has no slot for. Two views, one set of
    banked figures — so this reuses the physics gallery's primitives (the shared CSS ``_STYLE`` + the
    introspected ``figure_relpath``) rather than duplicating them, and adds only the timeline chrome.
  * It lives in ``chip/`` (not ``fab_game/``) because the modes it reads are ``chip/demo_*_history.py``
    — a chip→chip import, no ADR-0005 direction problem (unlike the game gallery).

Same drift-proofing as the two galleries: the figure for every mode is **introspected** from the demo
module's own ``DOCS_FIGURE`` (never re-typed); inclusion is anchored to the ``chip/demo_*_history.py``
glob (a new history mode cannot be forgotten from the timeline); and ``chip/tests/test_history_gallery.py``
fails the fast lane if a mode is missing from the manifest below, a figure is absent, or the committed
HTML is stale. The manifest carries only what the code is not the source of truth for: the human
timeline text (era, the wall, the successor), kept verbatim with the plan's historical/educational spine.

Regenerate after building/renaming a history mode or editing its timeline text (then commit the HTML):

    python -m chip.history_gallery
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path

# Reuse the physics gallery's primitives the same way the game gallery does: _STYLE keeps all three
# pages visually one system; figure_relpath introspects each demo's banked figure (viz-free import);
# the link constants carry the public(GitHub)/local(JupyterLab) split. None of these are edited here —
# the timeline chrome is added below as _TIMELINE_CSS, so chip.gallery's own output stays byte-identical.
from chip.gallery import (
    _STYLE,
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
CHIP_DIR = _REPO_ROOT / "chip"
OUTPUT_HTML = DOCS_DIR / "history.html"
OUTPUT_LOCAL_HTML = DOCS_DIR / "history.local.html"

_PKG = "chip"


@dataclass(frozen=True)
class HistoryMode:
    """One rung on the timeline. ``module`` is the ``chip.<module>`` suffix (a ``demo_*_history``);
    the figure is NOT stored here — it is read from the module's ``DOCS_FIGURE`` at render time via
    :func:`chip.gallery.figure_relpath`, so the timeline can never drift from the banked contrast.

    The rest is the timeline text the code is not the source of truth for, verbatim with the plan's
    historical/educational spine (``docs/plans/historical-modes.md``): ``stage`` = the process step,
    ``era`` = the period the wall belonged to, ``period`` = what the period line did, ``wall`` = the
    limitation that motivated the successor, ``successor`` = the modern step that cleared it."""

    module: str      # e.g. "demo_doping_history" — figure introspected from its DOCS_FIGURE
    tag: str         # the mode id, e.g. "A1"
    stage: str       # the process stage this mode sits on, e.g. "Doping"
    era: str         # the period the wall belonged to, e.g. "≈1960s"
    period: str      # the period line — what it did / how it was configured
    wall: str        # the limitation that motivated the successor (the discriminating observable)
    successor: str   # the modern step that cleared the wall


# The backward axis, ordered along the process spine (doping → oxidation → metallization) — the same
# order as the plan's "historical/educational spine." Each rung's wall/successor text is lifted from
# that spine; the figure is the mode's own modern-vs-period contrast, introspected at render time.
MODES = [
    HistoryMode(
        module="demo_doping_history", tag="A1", stage="Doping", era="≈1960s",
        period="Predep planar doping from a constant diffusion source (POCl₃ / BBr₃), the surface "
        "flooded at the solid-solubility limit.",
        wall="The source floods at a fixed material constant (Trumbore solubility), so it cannot "
        "reproducibly meter a light V_t-adjust dose — laying 5e11 boron needs a sub-millisecond predep.",
        successor="Ion implantation — meters dose electrically by beam charge and sets depth "
        "independently by energy, the decoupling the predep line could not reach.",
    ),
    HistoryMode(
        module="demo_oxidation_history", tag="A3", stage="Oxidation", era="≈1970s",
        period="Neutral thermal oxidation at 1 atm — no chlorine in the ambient, atmospheric-pressure "
        "growth for thick isolation oxides.",
        wall="Pre-HCl gate oxides drifted from mobile Na⁺ (unstable V_t); and a thick 1-atm oxide "
        "costs a large collateral diffusion budget while it grows.",
        successor="Chlorine (HCl) gettering removes the mobile Na → V_t recovers; high-pressure "
        "oxidation grows the same oxide for 1/P of the thermal budget (or the same oxide at lower T).",
    ),
    HistoryMode(
        module="demo_metallization_history", tag="B6", stage="Metallization", era="≈1970s",
        period="Evaporated pure-aluminium contacts, sintered sub-eutectically onto the silicon.",
        wall="The Al dissolves silicon and spikes through the shallow (implant-era) junction — a "
        "graded shorted-area fraction; the shallower the junction, the worse the short.",
        successor="Barrier metals (Ti/TiN) stop the silicon uptake (Al–Si alloy is the partial fix); "
        "later Cu damascene — the spike wall never reaches the junction.",
    ),
]


def glob_history_modules() -> set[str]:
    """The history demos actually on disk — the inclusion anchor (a new ``demo_*_history`` appears here)."""
    return {p.stem for p in CHIP_DIR.glob("demo_*_history.py")}


def assert_manifest_complete() -> None:
    """Loudly refuse to render a stale timeline: the manifest must match ``chip/demo_*_history.py`` exactly."""
    on_disk = glob_history_modules()
    in_manifest = {m.module for m in MODES}
    missing, stale = on_disk - in_manifest, in_manifest - on_disk
    if missing or stale:
        raise SystemExit(
            "chip/history_gallery.py manifest is out of sync with chip/demo_*_history.py — "
            f"add to the manifest: {sorted(missing)}; remove (no such mode): {sorted(stale)}"
        )


# Timeline chrome — layered ON TOP of the shared _STYLE (imported unchanged), so all three pages read
# as one system while the era rows get their own spine. Deterministic (no dates, no machine paths).
_TIMELINE_CSS = """
      /* --- the era timeline (history page only) --------------------------------------- */
      .timeline { position: relative; margin-top: 1.4rem; padding-left: 1.6rem;
                  border-left: 2px solid var(--line); }
      .rung { position: relative; margin-bottom: 2rem; }
      .rung::before { content: ""; position: absolute; left: calc(-1.6rem - 6px); top: .4rem;
                      width: 11px; height: 11px; border-radius: 50%; background: var(--accent);
                      box-shadow: 0 0 0 4px var(--bg); }
      .rung .era { display: inline-block; font-weight: 700; font-size: .82rem; letter-spacing: .03em;
                   color: var(--accent); margin-right: .5rem; }
      .rung .stage { font-weight: 600; }
      .rung .rtag { align-self: flex-start; font-weight: 700; font-size: .72rem; letter-spacing: .03em;
                    text-transform: uppercase; color: var(--accent); background: #eaf2fb;
                    border-radius: 999px; padding: .1rem .5rem; margin-left: .4rem; }
      .rung .contrast { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
                        overflow: hidden; margin-top: .6rem; display: grid; gap: 0;
                        grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); }
      @media (max-width: 720px) { .rung .contrast { grid-template-columns: 1fr; } }
      .rung .contrast .shot { border-bottom: none; border-right: 1px solid var(--line); }
      @media (max-width: 720px) { .rung .contrast .shot { border-right: none;
                                  border-bottom: 1px solid var(--line); } }
      .rung .contrast .shot img { display: block; width: 100%; height: auto; }
      .rung .story { padding: 1rem 1.1rem; display: flex; flex-direction: column; gap: .6rem; }
      .rung .story .row { display: flex; gap: .55rem; }
      .rung .story .k { flex: 0 0 5.4rem; font-weight: 700; font-size: .74rem; letter-spacing: .03em;
                        text-transform: uppercase; padding-top: .12rem; }
      .rung .story .k.period { color: var(--muted); }
      .rung .story .k.wall { color: #b23c2f; }
      .rung .story .k.next { color: #2e7d46; }
      .rung .story .v { margin: 0; flex: 1; font-size: .92rem; }
      .rung .story .links { display: flex; align-items: center; gap: .6rem; margin-top: .2rem;
                            padding-top: .6rem; border-top: 1px dashed var(--line); }"""


def _rung(mode: HistoryMode, local: bool = False) -> str:
    fig = figure_relpath(mode, _PKG)  # introspected from the demo's DOCS_FIGURE (never re-typed)
    era = html.escape(mode.era)
    stage = html.escape(mode.stage)
    tag = html.escape(mode.tag)
    period = html.escape(mode.period)
    wall = html.escape(mode.wall)
    successor = html.escape(mode.successor)
    run = html.escape(f"python -m {_PKG}.{mode.module}")
    src = f"{_LAB}/{_PKG}/{mode.module}.py" if local else f"{_BLOB}/{_PKG}/{mode.module}.py"
    tgt = ' target="_blank" rel="noopener"' if local else ""
    return f"""        <div class="rung">
          <div class="head">
            <span class="era">{era}</span><span class="stage">{stage}</span><span class="rtag">{tag}</span>
          </div>
          <div class="contrast">
            <a class="shot" href="{fig}" title="open the full modern-vs-period figure">
              <img src="{fig}" alt="{tag} — {stage} modern-vs-period contrast" loading="lazy">
            </a>
            <div class="story">
              <div class="row"><span class="k period">Period</span><p class="v">{period}</p></div>
              <div class="row"><span class="k wall">The wall</span><p class="v">{wall}</p></div>
              <div class="row"><span class="k next">Replaced by</span><p class="v">{successor}</p></div>
              <div class="links">
                <code>{run}</code>
                <a class="src" href="{src}"{tgt}>source&nbsp;&#8599;</a>
              </div>
            </div>
          </div>
        </div>"""


def render_html(local: bool = False) -> str:
    """Render the whole era timeline to a deterministic HTML string (no dates, no machine paths).

    ``local=True`` renders ``docs/history.local.html``: the same timeline, but every link that would go
    to GitHub instead opens in a *running* JupyterLab (``localhost``). The public ``history.html``
    (``local=False``) is byte-for-byte unchanged. Both depend only on the manifest + fixed strings, so
    both stay golden-testable (``chip/tests/test_history_gallery.py``)."""
    rungs = "\n".join(_rung(m, local) for m in MODES)
    item_attr = ' target="_blank" rel="noopener"' if local else ""
    if local:
        title = "chip-sim &mdash; the era timeline (local edition)"
        repo_link = f'<a class="repo" href="{_LAB_ROOT}"{item_attr}>Open the repo in Jupyter&nbsp;Lab&nbsp;&#8599;</a>'
        note = (
            '\n      <p class="lead" style="background:#fff7e6;border:1px solid #f0d8a8;border-radius:8px;'
            'padding:.6rem .8rem;margin-top:1rem;"><strong>Local edition.</strong> Every source link here '
            "opens in your <strong>running JupyterLab</strong> &mdash; start it once from the repo root "
            f"(<code>jupyter lab</code>). Links target <code>localhost:{_LOCAL_PORT}</code>; a click can&rsquo;t "
            "start the server, only reach one already running.</p>"
        )
        physics = "index.local.html"
        fabgame = "fab-game.local.html"
        plan = f"{_LAB}/docs/plans/historical-modes.md"
    else:
        title = "chip-sim &mdash; the era timeline (the backward axis)"
        repo_link = f'<a class="repo" href="{_REPO_URL}">View the repository on GitHub&nbsp;&#8599;</a>'
        note = ""
        physics = "index.html"
        fabgame = "fab-game.html"
        plan = f"{_BLOB}/docs/plans/historical-modes.md"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
{_STYLE}
{_TIMELINE_CSS}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>chip-sim &mdash; the era timeline</h1>
      <p class="tagline"><em>What each modern step was built to clear.</em> The backward axis: every
        process re-run in the period mode whose limitation motivated its successor.</p>
      <p class="lead">The rest of the gallery runs every step in its <strong>modern</strong>
        configuration. This page runs the other direction: each rung re-runs a step we already model in
        its <strong>period mode</strong> and reads the one contrast the sim can show &mdash;
        <strong>the period result, the wall it hit, and the modern step that cleared it</strong>. A mode
        earns a rung only when its limitation is <em>visible</em> in a quantity the sim already computes
        (dose, V_t, thermal budget, junction leakage). Every mode is opt-in: the modern default
        reproduces today's result byte-for-byte, so this timeline is pure contrast. (The forward axis &mdash;
        each modern step <em>built</em> &mdash; is the <a href="{physics}">physics gallery</a>.)</p>
      {repo_link}{note}
    </div>
  </header>

  <main>
    <section>
      <h2>The backward axis, along the process spine</h2>
      <p class="sub">Doping &rarr; oxidation &rarr; metallization &mdash; each rung is a built historical
        mode; click a figure for the full modern-vs-period contrast.</p>
      <div class="timeline">
{rungs}
      </div>
    </section>

    <section>
      <h2>Go deeper</h2>
      <p class="sub">The two front doors this timeline is a cut of, and the plan behind the axis.</p>
      <div class="deeper">
        <a class="item" href="{physics}"{item_attr}>
          <h3>The physics gallery &#8599;</h3>
          <p>The forward axis: the four-phase process spine + the litho/implant deepenings &mdash; each
            modern step <em>built</em>, recipe in &rarr; device out. The history figures live there too,
            as flat cards; this page is their timeline cut.</p>
        </a>
        <a class="item" href="{fabgame}"{item_attr}>
          <h3>The fab-line game &#8599;</h3>
          <p>The gamified full line built on the same physics &mdash; sand &rarr; a binned chip, and you
            can see <em>why</em> a die died.</p>
        </a>
        <a class="item" href="{plan}"{item_attr}>
          <h3>The historical-modes plan &#8599;</h3>
          <p>historical-modes.md &mdash; the backward axis, the three-tier consumer bar, and why a period
            variant earns code only when its limitation is observable.</p>
        </a>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap">Generated from the <code>demo_*_history</code> modules by
      <code>python -m chip.history_gallery</code> &mdash; figure paths are introspected, never hand-typed,
      so this timeline stays in lock-step with the banked contrasts. The backward axis complements the
      forward one (<code>docs/plans/future-steps.md</code>): same observables, opposite direction.</div>
  </footer>
</body>
</html>
"""


def write_html(local: bool = False) -> Path:
    """Write a timeline edition with LF newlines (golden-test stable on Windows + CI).

    ``local=False`` → the public ``docs/history.html`` (GitHub links, served by Pages);
    ``local=True``  → ``docs/history.local.html`` (source links open in a running JupyterLab)."""
    out = OUTPUT_LOCAL_HTML if local else OUTPUT_HTML
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(local), encoding="utf-8", newline="\n")
    return out


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # the → / µm in the message, on legacy codepages
    assert_manifest_complete()
    public = write_html()
    local = write_html(local=True)
    print(f"Era timeline written → {public.relative_to(_REPO_ROOT)} + "
          f"{local.relative_to(_REPO_ROOT)}  ({len(MODES)} modes)")


if __name__ == "__main__":
    main()
