"""The educational-mode prose — what each knob/readout *is* and *what to do* (headless, tested).

The content twin of :mod:`fab_game.dashboard` / :mod:`fab_game.session_view` for **educational
mode** (the launch-time *Educational* vs *Hardcore* choice; ``docs/plans/fab-game-tui.md``). The
TUI's hardcore mode is the bare cockpit — knobs, the wafer map, the failure trail. Educational mode
layers on a plain-language **guide**: a glossary of every selector and readout (*what each thing is
and does*) plus screen-specific *what-to-do* strategy. A standalone learner can read the panel and
understand "defocus", "NILS", "V_t", "Scheil drift" without leaving the terminal.

**Why this is its own import-pure module — not prose baked into ``tui.py``.** Same doctrine as
:mod:`fab_game.session_view` / :mod:`fab_game.dashboard`: the load-bearing string-building lives
**outside** the swallow-prone Textual surface, so it is testable on its own (a Textual App, like
``ipywidgets.interact``, can swallow a callback exception and still look green). This module imports
neither ``textual`` nor ``matplotlib``; it is re-exported from :mod:`fab_game` and tested by
``tests/test_guide.py``. :mod:`fab_game.tui` renders these strings **verbatim** (the fidelity
contract — the App computes no prose).

Educational mode is **presentation only** — it changes no knob, no recipe, no physics, and never the
seam (hardcore is byte-for-byte today's TUI). The same headless strings could later surface in the
notebook dashboard; nothing here is painted into the terminal.
"""
from __future__ import annotations

from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# The glossary — one entry per selector and per readout concept the UI shows
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Term:
    """One explained concept: a stable ``key``, a display ``name``, a one-line ``summary``, the ``detail``.

    ``key`` matches the dashboard knob ids where the term *is* a knob (``defocus_nm`` …) so the legend
    and the live Input line up; the readout concepts (``v_t``, ``nils`` …) carry their own keys.
    """

    key: str
    name: str
    summary: str
    detail: str


# The selectors the dashboard exposes (keys match fab_game.tui._KNOB_FIELDS / dashboard.run_dashboard).
_KNOBS: tuple[Term, ...] = (
    Term(
        "defocus_nm", "Defocus (nm)",
        "how far the wafer sits off the lens's sharp focal plane",
        "The stepper projects the mask through a lens; defocus is the wafer's distance (in nm) from "
        "best focus. At 0 the gate edge prints crisp; as defocus grows the projected (aerial) image "
        "blurs, the edge slope NILS collapses, and the gate stops printing reliably. With the "
        "centre-to-edge focus bowl on, the wafer edge defocuses first — so a large defocus kills an "
        "outer RING of dies while the centre survives.",
    ),
    Term(
        "defect_density", "Defect density (cm⁻²)",
        "how many killer particles land on the wafer, per cm²",
        "Each die that catches a killer particle is dead *functionally* — the transistor is built but "
        "shorted/broken. Yield follows the Murphy/Poisson law Y = exp(−D₀·A): raise D₀ and the map "
        "fills with SCATTERED random kills anywhere on the wafer (no ring — unlike defocus).",
    ),
    Term(
        "slice_z", "Boule slice z [0,1)",
        "where down the crystal this wafer was cut (seed 0 → tail ~1)",
        "One crystal (boule) is sliced into wafers. Boron segregates as the crystal freezes (Scheil), "
        "so wafers cut later (higher z) start with MORE substrate doping, which walks the device "
        "threshold V_t upward. Early slices pass easily; the tail drifts out of spec. This is the "
        "game's difficulty curve.",
    ),
    Term(
        "oxide_minutes", "Gate-oxide drive (min)",
        "how long the gate oxide is grown — sets its thickness t_ox",
        "A thinner gate oxide lowers V_t *and* raises I_Dsat, so this is the 'adapt' lever: thin it to "
        "pull a drifted (high-V_t) tail wafer back into spec and toward the premium bin. The catch — "
        "over-thinning pushes I_Dsat over its ceiling (a Goldilocks limit on the extreme tail).",
    ),
    Term(
        "seed", "Seed",
        "the random seed for the within-wafer spread",
        "The physics is deterministic in (seed, knobs): the same seed reproduces the EXACT same wafer "
        "map — a roguelike 'seed' you can replay. Change it to roll a different wafer at identical "
        "settings.",
    ),
)

# The readout concepts the panels report (not knobs — outcomes / device numbers / policy).
_READOUTS: tuple[Term, ...] = (
    Term(
        "yield", "Yield",
        "the fraction of dies that pass every spec window",
        "The headline score for one wafer run — good dies / total dies on the map.",
    ),
    Term(
        "v_t", "V_t (threshold voltage)",
        "the gate voltage at which the transistor turns on (V)",
        "It must land inside its spec window: too low and the device leaks on; too high and it won't "
        "switch at the rated voltage. V_t RISES with substrate doping (the Scheil drift down the "
        "boule) and FALLS with a thinner gate oxide (the adapt lever) — the two forces the game pits "
        "against each other.",
    ),
    Term(
        "i_dsat", "I_Dsat (saturation drain current)",
        "the on-current the transistor drives — the speed proxy (mA)",
        "I_Dsat ∝ W/L, so a shorter channel (a smaller gate CD — from over-etch or a thinner oxide) "
        "drives it UP. Final test bins parts by it (premium = fast). It has a ceiling: push it too "
        "high and the part falls out of spec.",
    ),
    Term(
        "nils", "NILS (normalized image log slope)",
        "how steeply light falls across the gate edge — printability",
        "NILS = CD·d(lnI)/dx: a high value is a crisp, robust edge; defocus and lens aberrations "
        "collapse it. Below a floor the edge is too soft to print reliably and the die fails on NILS "
        "— the defocus chain's actual casualty (it hits NILS, not V_t).",
    ),
    Term(
        "cd", "CD (critical dimension)",
        "the printed width of the gate — the smallest feature (nm)",
        "CD sets the channel length L, so it drives I_Dsat. Litho prints a CD; etch can shrink it "
        "below the printed value (over-etch bias); it has its own spec window.",
    ),
    Term(
        "leakage", "Leakage (junction leakage)",
        "the reverse current the off transistor's diode leaks",
        "Deep-level metal contamination (Fe/Cu) drops the carrier lifetime τ (Shockley–Read–Hall) and "
        "lifts the generation leakage J ∝ N_metal/τ — a failure V_t CANNOT see (a clean-V_t part can "
        "still be scrapped on a leaky diode). The device consequence net doping can't carry. Two cures: "
        "purify harder (more zone passes), or INTERNAL GETTERING — crucible oxygen precipitates trap the "
        "metals out of the device region. But that same oxygen makes thermal donors that pull V_t DOWN, "
        "so gettering a leaky feed is a trade-off, not a free win (one knob, two opposite faces).",
    ),
    Term(
        "bins", "Speed bins (premium / typical / value)",
        "the price grade final test sorts each working part into",
        "Final test grades each surviving part by its I_Dsat: premium (fast) > typical (nominal) > "
        "value (slow but sellable). A tight process fills premium; a loose one spreads the grades and "
        "bins a tail OUT. Binning is a grading policy, not physics.",
    ),
    Term(
        "scheil", "Scheil drift (the difficulty curve)",
        "why wafers down the boule get harder",
        "Boron's segregation coefficient k ≈ 0.8 < 1, so the solid that freezes later is more doped. "
        "Slicing the boule seed-to-tail gives successively higher substrate N_A, which walks V_t up "
        "across the spec window — the per-wafer difficulty curve of a run.",
    ),
    Term(
        "budget", "Budget / score",
        "your bank and cumulative profit down the boule",
        "Profit = revenue from binned-good dies (premium > typical > value) minus wafer/scrap/rework "
        "cost. In roguelike mode a negative budget ends the run (bankrupt); sandbox never ends early. "
        "One boule is finite (a fixed number of slices).",
    ),
    Term(
        "trail", "The failure trail",
        "why the worst dead die died",
        "When a die fails, the sim records the cause — diagnose() names it (defocus → NILS, etch bias "
        "→ CD, contamination → leakage, …). The panel shows the worst (outer-most) dead die's trail, "
        "so you can read which knob killed the ring.",
    ),
)

# The roguelike actions (the decision the second screen asks for).
_ACTIONS: tuple[Term, ...] = (
    Term(
        "process", "Process",
        "run the next slice and bank the profit",
        "Run the next slice through the full line at your chosen recipe and bank the profit (revenue "
        "from binned-good dies minus the wafer cost). The default move.",
    ),
    Term(
        "adapt", "Adapt (the lever)",
        "thin the gate oxide before processing to save a drifted wafer",
        "Lower the Gate-oxide drive before processing to pull a high-V_t tail wafer back into spec — "
        "and toward the premium bin. Double-braked: the I_Dsat ceiling tips the extreme tail over "
        "in-model, and gate-oxide reliability is the unmodeled, off-book cost. It is not a free win.",
    ),
    Term(
        "scrap", "Scrap",
        "bail on a doomed slice — pay only the substrate cost",
        "Skip the next slice unprocessed: pay only the sunk substrate cost (no wafer cost, no "
        "revenue). The 'cut your losses' move when the tail slice will fail anyway.",
    ),
)

GLOSSARY: tuple[Term, ...] = _KNOBS + _READOUTS + _ACTIONS
GLOSSARY_BY_KEY: dict[str, Term] = {t.key: t for t in GLOSSARY}

# The keys each screen's legend walks (in display order). DASHBOARD_KNOBS matches the live Inputs.
DASHBOARD_KNOBS: tuple[str, ...] = tuple(t.key for t in _KNOBS)
DASHBOARD_READOUTS: tuple[str, ...] = ("yield", "v_t", "i_dsat", "nils", "cd", "trail")
ROGUELIKE_READOUTS: tuple[str, ...] = ("v_t", "i_dsat", "nils", "cd", "leakage", "bins", "budget")


# --------------------------------------------------------------------------- #
# The launch-time mode choice (rendered on the mode-select screen)
# --------------------------------------------------------------------------- #
MODE_INTRO: str = (
    "Choose how to play the fab line:\n\n"
    "  Educational — the guided line. Every selector and readout is explained on-screen, with what "
    "to try and how to read the wafer map and the score. Best if 'defocus', 'NILS', 'V_t' or 'Scheil "
    "drift' aren't yet second nature.\n\n"
    "  Hardcore — the bare cockpit. Just the knobs, the wafer map, and the failure trail. The exact "
    "same line, no hand-holding."
)


# --------------------------------------------------------------------------- #
# Rendering — plain strings the TUI shows verbatim (no markup, no Textual)
# --------------------------------------------------------------------------- #
def term_block(term: Term) -> str:
    """One glossary entry: ``• Name — summary`` then the wrapped detail on an indented line."""
    return f"• {term.name} — {term.summary}\n    {term.detail}"


def _legend(keys: tuple[str, ...]) -> str:
    """The :func:`term_block` of each key, in order (every key must be a known glossary term)."""
    return "\n".join(term_block(GLOSSARY_BY_KEY[k]) for k in keys)


def _section(title: str, body: str) -> str:
    return f"{title}\n{body}"


def dashboard_guide() -> str:
    """The dashboard screen's guide: what you're doing, **what to try**, then the knob + readout legends.

    The *what-to-try* block is exploratory strategy (crank a knob, watch the map) — distinct from the
    glossary's definitions; the roguelike guide carries the decision strategy instead.
    """
    intro = (
        "You're commanding the whole fab line — sand to a tested wafer. Set a few knobs, run the line, "
        "and read the wafer map (O = a die that passed every spec, X = a dead die) and the trail below "
        "it (why the worst die died)."
    )
    what_to_try = _section("What to try:", "\n".join((
        "  • Crank Defocus to ~90–250 nm: an edge RING dies while the centre survives — the image "
        "blurs, NILS collapses, the gate stops printing (defocus's casualty is NILS, never V_t).",
        "  • Raise Defect density: SCATTERED random kills appear anywhere (no ring — particles land "
        "where they land).",
        "  • Push Boule slice z toward 1: the whole map drifts to fail as the Scheil V_t walk pushes "
        "the wafer past its window.",
        "  • Then thin the Gate-oxide drive to pull that drifted wafer back into spec — the 'adapt' "
        "lever.",
        "  • Change the Seed to roll a different wafer at the same settings.",
    )))
    return "\n\n".join((
        intro,
        what_to_try,
        _section("The selectors:", _legend(DASHBOARD_KNOBS)),
        _section("The readouts:", _legend(DASHBOARD_READOUTS)),
    ))


def roguelike_guide() -> str:
    """The roguelike screen's guide: the run framing, the **process/adapt/scrap decision**, the readouts.

    The *what-to-do* here is the actual call the tail forces (adapt vs scrap, the Goldilocks ceiling) —
    distinct from the dashboard's exploratory strategy.
    """
    intro = (
        "This is a run: one crystal (boule), sliced seed to tail, one wafer per turn. The catch is "
        "physics — boron segregated as the crystal froze (Scheil), so each slice down the boule starts "
        "more heavily doped and the device threshold V_t walks upward. Early slices pass easily; the "
        "tail drifts out of spec and forces a decision."
    )
    decision = _section("Each turn — inspect the next slice (its projected V_t, in/out of spec), then:", "\n".join((
        "  • Process it at your recipe and bank the profit (the default move).",
        "  • Adapt — thin the Gate-oxide drive — to drop V_t back into the window and push I_Dsat "
        "toward the premium bin. Don't overshoot: too thin and I_Dsat tips over its ceiling (a real "
        "Goldilocks fumble on the last wafer).",
        "  • Scrap the slice unprocessed when it's doomed — pay only the substrate cost, not the full "
        "wafer.",
    )))
    scoring = (
        "You're scored on profit: revenue from binned-good dies (premium > typical > value) minus "
        "wafer/scrap/rework cost, on a budget. In roguelike mode a negative budget ends the run."
    )
    return "\n\n".join((
        intro,
        decision,
        scoring,
        _section("The readouts:", _legend(ROGUELIKE_READOUTS)),
    ))


def glossary_text() -> str:
    """The full glossary — every selector, readout, and action, one :func:`term_block` each."""
    return "\n".join(term_block(t) for t in GLOSSARY)
