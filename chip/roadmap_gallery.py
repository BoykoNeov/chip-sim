"""The roadmap page generator — the visual front door for the PLANNED, not-yet-built slices.

Builds ``docs/roadmap.html`` (and the ``…local.html`` JupyterLab edition): one card per unbuilt
slice of ``docs/plans/future-steps.md`` (F3 high-κ … F10 EUV), each showing its **schematic
preview** (:mod:`chip.roadmap_figures`), its **triage status** verbatim with the plan
(PROMOTABLE / COUPLED / partly built / DEFERRED), the **observable it would add**, and the
**named consumer that gates it** — the repo's anti-over-build bar made browsable.

Why a *fourth* page (not more cards on the physics gallery):

  * The three existing pages show **built** work — every figure on them is a banked artifact of
    a cited, triad-tested demo. A roadmap card is categorically different: its figure is a
    hand-drawn schematic of something that does **not exist in the code**. Mixing the two on one
    grid would blur exactly the line the repo's honesty discipline draws, so the planned slices
    get their own page, every image stamped in-image and ribboned on-page as *not simulator
    output*.
  * The page is the visual twin of the triage docs: statuses, gates and consumers are kept
    verbatim with ``future-steps.md`` (and the backlog for B1); when a slice ships, its card
    comes OFF this page and its real demo joins the galleries — the drift guard
    (``chip/tests/test_roadmap_gallery.py``) keeps manifest, figures and committed HTML in sync.

Same determinism as the other generators (no dates, no machine paths — golden-testable), same
shared stylesheet (``chip.gallery._STYLE``), same public(GitHub)/local(JupyterLab) split.

Regenerate after editing the manifest or the schematics (then commit the HTML):

    python -m chip.roadmap_gallery
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path

# Reuse the physics gallery's primitives the same way the game/history pages do: the shared
# _STYLE + _nav keep all four pages one system; the link constants carry the public/local split.
from chip.gallery import (
    _STYLE,
    _nav,
    _BLOB,
    _REPO_URL,
    _LAB,
    _LAB_ROOT,
    _LOCAL_PORT,
    DOCS_DIR,
)
from chip import roadmap_figures

_REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_HTML = DOCS_DIR / "roadmap.html"
OUTPUT_LOCAL_HTML = DOCS_DIR / "roadmap.local.html"

# The status badge classes the page styles: ok = promotable now, part = coupled / partly built,
# hold = deferred (no discriminating consumer yet). The drift guard pins badges to this set.
BADGES = ("ok", "part", "hold")


@dataclass(frozen=True)
class Slice:
    """One roadmap card. ``fid`` keys the schematic in :mod:`chip.roadmap_figures`; the status /
    gate / observable text is kept verbatim with the triage in ``docs/plans/future-steps.md``
    (B1's trigger with the scope-edge backlog) — the page displays the plan, it does not re-triage."""

    fid: str         # the plan's slice id, e.g. "F3" — also keys FIGURES / the banked PNG
    era: str         # the era transition the slice carries, e.g. "2007 · 45 nm"
    title: str       # the human name
    status: str      # the badge text, verbatim with the plan's verdict
    badge: str       # one of BADGES
    blurb: str       # the one-liner — what the slice is
    would_add: str   # the observable it would discriminate (the consumer, if built)
    gate: str        # what its build is gated on / why it is not built yet


SLICES = [
    Slice(
        fid="F3", era="2007 · 45 nm", title="High-κ / metal gate",
        status="Promotable", badge="ok",
        blurb="The oxide stage's modern successor: SiO₂ stopped scaling at ~1.2 nm because direct "
              "tunneling explodes; HfO₂ holds the same EOT at ~3× the physical thickness.",
        would_add="A gate-tunneling-leakage observable vs t_ox — a NEW output, plus the "
                  "SiO₂→high-κ era contrast on the existing oxide/t_ox machinery.",
        gate="Nothing structural — the first genuinely new-output decision (F3 vs F4 order is "
             "the open call in the plan).",
    ),
    Slice(
        fid="F4", era="1997 · Cu damascene", title="BEOL interconnect (RC delay)",
        status="Promotable", badge="ok",
        blurb="The back end the sim has never had: subtractive Al → Cu dual-damascene → Ru, with "
              "chip speed set by wire RC rather than the transistor.",
        would_add="Delay ∝ R_wire·C_wire — the first output the transistor chain does not set; "
                  "the richest remaining history arc. Also gives CMP (F8) its missing consumer.",
        gate="Nothing structural — the biggest build of the promotable three.",
    ),
    Slice(
        fid="F5", era="~2004 · 90 nm", title="SiGe strained source/drain",
        status="Promotable", badge="ok",
        blurb="The strain era: embedded SiGe pockets squeeze the p-channel (~2 GPa at ~20% Ge), "
              "and hole mobility — hence drive current — rises.",
        would_add="Mobility → I_Dsat through a strain-aware µ model — the channel-strain rung of "
                  "the era ladder.",
        gate="A µ(strain) mobility model in device.py — none exists yet; advanced-node, so it "
             "queues behind F3/F4.",
    ),
    Slice(
        fid="F6", era="bipolar epi · CMOS wells", title="Epitaxy (buried layer / retrograde well)",
        status="Coupled to F1", badge="part",
        blurb="An epitaxial layer over a doped substrate makes buried layers and retrograde "
              "wells — profiles a surface predep cannot reach.",
        would_add="The retrograde/buried-peak profile — but ion implantation (F1, BUILT) already "
                  "delivers exactly that contrast.",
        gate="Overlaps F1's consumer: a standalone epi slice stays deferred until it would "
             "discriminate something implant does not.",
    ),
    Slice(
        fid="F7", era="1998 · STI", title="Isolation remainder: STI process + latchup",
        status="Partly built (B5)", badge="part",
        blurb="LOCOS's bird's beak and the min-active-pitch wall are BUILT (history-mode B5, the "
              "2-D engine's 2nd consumer); the successor's own process is not.",
        would_add="The STI trench etch/fill step itself and a latchup electrical observable — "
                  "the two named leftovers of the isolation arc.",
        gate="A consumer for trench geometry / a latchup observable; the beak physics already "
             "shipped, so only the remainder is on the roadmap.",
    ),
    Slice(
        fid="F8", era="enables Cu damascene", title="CMP / dishing / planarity",
        status="Deferred — post-F4", badge="hold",
        blurb="Preston-class removal with pattern-density dishing and erosion — post-CMP "
              "thickness non-uniformity.",
        would_add="Post-CMP layer-thickness non-uniformity — IF something read a layer "
                  "thickness.",
        gate="No consumer today: nothing in the device or yield path reads a layer thickness "
             "(backlog D2). Re-evaluate after F4 makes wire cross-section an RC observable.",
    ),
    Slice(
        fid="F9", era="2011 FinFET · 2022 GAA", title="FinFET / gate-all-around",
        status="Deferred — needs 3-D (B1)", badge="hold",
        blurb="The gate wraps the channel — 3 sides (fin) then all 4 (nanosheets) — so the "
              "dopant/potential field is non-separable in three dimensions.",
        would_add="Width-dependent V_t / corner effects a 3-D depletion field carries — the "
                  "consumer that would finally promote the engine's last deferred regime.",
        gate="The 3-D engine (backlog B1, trigger recorded): 1-D depth + the 2-D cross-section "
             "serve every current device; 3-D waits for this consumer, exactly as 2-D waited "
             "for v1.8.",
    ),
    Slice(
        fid="F10", era="2019 · 7 nm", title="EUV / multipatterning",
        status="Deferred", badge="hold",
        blurb="The wavelength ladder's last rung (λ = 13.5 nm) and pitch-splitting "
              "(LELE) — the current frontier of the litho arc.",
        would_add="Nothing the model does not already have: litho.py computes the aerial image, "
                  "R = k₁λ/NA, defocus, PEB and CAR down the whole ladder.",
        gate="No discriminating consumer — a shorter λ or a split pitch adds no new observable "
             "(the plan's honest NO).",
    ),
]

# The page's sections, in the plan's own order: consumer strength first, the honest NO's last.
SECTIONS = [
    ("Promotable — the consumer is named",
     "Each of these already has a device observable waiting to read it; the plan's recommended "
     "sequence is F3/F4 (the new-output decision) then F5.",
     [s for s in SLICES if s.badge == "ok"]),
    ("Coupled &amp; partly built",
     "Real physics whose consumer is (partly) already served — built where the consumer exists, "
     "deferred where it would duplicate one.",
     [s for s in SLICES if s.badge == "part"]),
    ("Deferred — no discriminating consumer yet",
     "The honest NO&rsquo;s, kept visible: each is fenced behind a named consumer that does not "
     "exist today, with its promotion trigger recorded.",
     [s for s in SLICES if s.badge == "hold"]),
]


def assert_manifest_complete() -> None:
    """Loudly refuse to render a stale roadmap: the manifest must match the schematic registry
    (:data:`chip.roadmap_figures.FIGURES`) exactly, and every badge must be a styled class."""
    figures = set(roadmap_figures.FIGURES)
    manifest = {s.fid for s in SLICES}
    missing, stale = figures - manifest, manifest - figures
    if missing or stale:
        raise SystemExit(
            "chip/roadmap_gallery.py manifest is out of sync with chip.roadmap_figures.FIGURES — "
            f"add cards for: {sorted(missing)}; remove (no schematic): {sorted(stale)}"
        )
    bad = [s.fid for s in SLICES if s.badge not in BADGES]
    if bad:
        raise SystemExit(f"unknown badge class on {bad} — use one of {BADGES}")


def figure_relpath(s: Slice) -> str:
    """The slice's banked schematic, relative to docs/ — introspected from the figure registry."""
    return roadmap_figures.figure_path(s.fid).relative_to(DOCS_DIR).as_posix()


def _card(s: Slice, plan_href: str) -> str:
    fig = figure_relpath(s)
    fid = html.escape(s.fid)
    era = html.escape(s.era)
    title = html.escape(s.title)
    status = html.escape(s.status)
    blurb = html.escape(s.blurb)
    would = html.escape(s.would_add)
    gate = html.escape(s.gate)
    return f"""        <article class="card">
          <a class="shot" href="{fig}" title="open the full schematic (a preview, not simulator output)">
            <span class="ribbon">planned &mdash; schematic</span>
            <img src="{fig}" alt="{fid} — {title} schematic preview (planned, not simulator output)" loading="lazy">
          </a>
          <div class="body">
            <div class="tagrow">
              <span class="tag">{fid} &middot; {era}</span>
              <span class="status {s.badge}">{status}</span>
            </div>
            <p class="blurb"><strong>{title}.</strong> {blurb}</p>
            <div class="facts">
              <div class="row"><span class="k would">Would add</span><p class="v">{would}</p></div>
              <div class="row"><span class="k gate">Gated on</span><p class="v">{gate}</p></div>
            </div>
            <div class="links">
              <code>docs/plans/future-steps.md</code>
              <a class="src" href="{plan_href}">the triage&nbsp;&#8599;</a>
            </div>
          </div>
        </article>"""


def render_html(local: bool = False) -> str:
    """Render the roadmap page to a deterministic HTML string (no dates, no machine paths).

    ``local=True`` renders ``docs/roadmap.local.html``: the same page, but plan/backlog links open
    in a *running* JupyterLab (``localhost``) instead of on GitHub. Both editions depend only on
    the manifest + fixed strings, so both stay golden-testable."""
    item_attr = ' target="_blank" rel="noopener"' if local else ""
    if local:
        title = "chip-sim &mdash; the roadmap (local edition)"
        repo_link = f'<a class="repo" href="{_LAB_ROOT}"{item_attr}>Open the repo in Jupyter&nbsp;Lab&nbsp;&#8599;</a>'
        note = (
            '\n      <p class="lead localnote"><strong>Local edition.</strong> Every plan link here '
            "opens in your <strong>running JupyterLab</strong> &mdash; start it once from the repo root "
            f"(<code>jupyter lab</code>). Links target <code>localhost:{_LOCAL_PORT}</code>; a click can&rsquo;t "
            "start the server, only reach one already running.</p>"
        )
        plan = f"{_LAB}/docs/plans/future-steps.md"
        backlog = f"{_LAB}/docs/plans/scope-edge-backlog.md"
        history = "history.local.html"
        physics = "index.local.html"
    else:
        title = "chip-sim &mdash; the roadmap (planned, not yet built)"
        repo_link = f'<a class="repo" href="{_REPO_URL}">View the repository on GitHub&nbsp;&#8599;</a>'
        note = ""
        plan = f"{_BLOB}/docs/plans/future-steps.md"
        backlog = f"{_BLOB}/docs/plans/scope-edge-backlog.md"
        history = "history.html"
        physics = "index.html"
    sections = []
    for heading, sub, slices in SECTIONS:
        cards = "\n".join(_card(s, plan) for s in slices)
        sections.append(f"""    <section>
      <h2>{heading}</h2>
      <p class="sub">{sub}</p>
      <div class="grid">
{cards}
      </div>
    </section>""")
    sections_html = "\n\n".join(sections)
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
      {_nav("roadmap", local)}
      <h1>chip-sim &mdash; the roadmap</h1>
      <p class="tagline"><em>Planned, not yet built.</em> The future slices, triaged by the named
        consumer that would earn each one its build.</p>
      <p class="lead">Everything on the other three pages is <strong>built</strong> &mdash; every figure
        there is the banked artifact of a cited, tested demo. This page is the opposite and says so
        loudly: each card below is a slice from the roadmap triage
        (<a href="{plan}"{item_attr}>future-steps.md</a>) that does <strong>not exist in the code yet</strong>.
        The images are <strong>schematic previews</strong> &mdash; hand-drawn illustrations of what the
        slice would teach, stamped in-image and ribboned here, <em>never</em> simulator output. Each card
        carries the plan&rsquo;s verdict verbatim: what observable the slice <span class="status ok"
        style="font-size:.7rem">would add</span>, and the consumer its build is <span class="status hold"
        style="font-size:.7rem">gated on</span> &mdash; the repo&rsquo;s <em>no regime without a named
        consumer</em> bar, made browsable. When a slice ships, its card comes off this page and its real
        figures join the galleries.</p>
      {repo_link}{note}
    </div>
  </header>

  <main>
{sections_html}

    <section>
      <h2>Go deeper</h2>
      <p class="sub">The triage documents these cards are the visual twin of, and the built work.</p>
      <div class="deeper">
        <a class="item" href="{plan}"{item_attr}>
          <h3>The roadmap triage &#8599;</h3>
          <p>future-steps.md &mdash; the full future-slice triage: consumer observables, verdicts,
            the recommended F3/F4 sequence, and the honest NO&rsquo;s.</p>
        </a>
        <a class="item" href="{backlog}"{item_attr}>
          <h3>The scope-edge backlog &#8599;</h3>
          <p>The named-but-deferred edges (3-D engine B1, CMP D2, Stefan A5&hellip;) triaged by
            consumer &mdash; the anti-over-build bar these cards inherit.</p>
        </a>
        <a class="item" href="{history}"{item_attr}>
          <h3>The era timeline &#8599;</h3>
          <p>The <em>built</em> half of the same history: each period mode already modelled, with the
            wall it hit and the modern step that cleared it.</p>
        </a>
        <a class="item" href="{physics}"{item_attr}>
          <h3>The physics gallery &#8599;</h3>
          <p>Back to the front door: everything that IS built &mdash; the process spine, the
            deepenings, and the real banked figures.</p>
        </a>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap">Generated by <code>python -m chip.roadmap_gallery</code> from a manifest kept
      verbatim with <code>docs/plans/future-steps.md</code>; the schematics are drawn by
      <code>python -m chip.roadmap_figures</code> and stamped in-image as planned previews &mdash;
      nothing on this page is simulator output.</div>
  </footer>
</body>
</html>
"""


def write_html(local: bool = False) -> Path:
    """Write a roadmap edition with LF newlines (golden-test stable on Windows + CI).

    ``local=False`` → the public ``docs/roadmap.html`` (GitHub links, served by Pages);
    ``local=True``  → ``docs/roadmap.local.html`` (plan links open in a running JupyterLab)."""
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
    print(f"Roadmap written → {public.relative_to(_REPO_ROOT)} + "
          f"{local.relative_to(_REPO_ROOT)}  ({len(SLICES)} planned slices)")


if __name__ == "__main__":
    main()
