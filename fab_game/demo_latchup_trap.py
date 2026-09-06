"""The deliberate wafer kill: the sliver of the high-res spec that cannot be built.

The player-facing companion to F7/B12 (``docs/plans/latchup-isolation-f7.md``). B12 established that
latchup is a **wafer** property -- the only condition that discriminates rides the substrate resistivity,
one number per wafer -- and **refused to grade it**, because a radial resistivity profile would have been
invented physics. What that refusal leaves is a genuine cliff, and this demo is the argument that the
cliff is worth having: a total loss teaches something a yield gradient cannot, provided the player can
see it coming and can tell afterwards which decision caused it.

**The trap.** The high-resistivity native part (:data:`fab_game.targets.HIGH_RES`) exists *because* a
light substrate is the right engineering choice: it buys the native low threshold voltage and, through
``BV`` proportional to ``N_A^-3/4``, the breakdown voltage the logic substrate cannot reach. Lighter is
better, and the part's window rewards it all the way down to ~2.5e15 cm^-3. The latchup crossing sits at
~2.7e15 -- **inside that window**. So the lightest sliver of a perfectly legitimate published spec is a
wafer that satisfies every one of its own acceptance criteria and is still scrap.

**Why it has to be this product.** On the default fast-logic part the cliff is invisible: its threshold
window rejects every substrate light enough to latch, so latchup is never the thing that kills you there
(pinned in ``fab_game/tests/test_journey.py``). The trap needs a product that *wants* the light wafer.

**What is new here: nothing.** The window is :data:`fab_game.targets.HIGH_RES`'s, the crossing is
:func:`chip.latchup.trigger_current_a` against the recipe's injected disturbance, and the wafer is
:func:`fab_game.pipeline.run_line`. The demo composes them and reads the number off.

**The bug this found.** Wiring it up exposed a live defect in :func:`fab_game.targets.regrade`: the
wafer-level latchup scrap was not carried into a sibling target's verdict, so the 2.5e15 wafer below --
scrapped by the line -- re-graded to **every die passing**. Fixed, and pinned in
``fab_game/tests/test_targets_highres.py::test_a_latched_wafer_cannot_be_regraded_back_to_life``.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from chip import latchup as lu
from chip.czochralski import resistivity

from .pipeline import run_line
from .recipe import DEFAULT_RECIPE
from .targets import HIGH_RES, regrade

# The substrate ladder the demo walks. Every rung is an ordinary silicon substrate; the game's own default
# (1e17) is the HEAVY end of it, not the middle -- which is the point. FLAGGED as a display choice.
# Trimmed to the rungs that carry the claim (below the window / the trap / buildable / the window top /
# above it / the game default), because each rung costs two full line runs and this demo rides the fast
# lane. The dense trigger CURVE in the figure is closed-form and unaffected.
SUBSTRATE_LADDER: tuple[float, ...] = (
    2.0e15, 2.5e15, 3.0e15, 1.0e16, 3.0e16, 1.0e17,
)
GRID_N = 7          # dies per side -- the same map the journey forecasts on. Do NOT "optimize"
#                     this down: the litho/carrier caches the rest of the suite keeps warm are
#                     keyed on the grid, so an off-size grid is ~7x SLOWER, not faster (measured).
SEED = 0

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-latchup-trap.png"


@dataclass(frozen=True)
class Rung:
    """One substrate on the ladder: what its part's own spec says, and whether the wafer survives."""

    n_seed: float
    rho_ohm_cm: float
    trigger_ma: float
    margin: float
    latches: bool
    passes_window: bool          # the high-res windows, isolation NOT engaged (the part on paper)
    shipped: int                 # dies actually shipped once isolation IS engaged
    n_dies: int
    window_reason: str


def _rung(n_seed: float) -> Rung:
    cz = replace(DEFAULT_RECIPE.czochralski, N_seed=n_seed)
    iso = replace(DEFAULT_RECIPE.isolation, scheme="sti")

    # (a) the part on paper -- the line WITHOUT the isolation step, graded against its own target.
    paper = regrade(run_line(replace(DEFAULT_RECIPE, czochralski=cz), seed=SEED, grid_n=GRID_N), HIGH_RES)
    passes = all(d.verdict.passed for d in paper.dies)
    reason = "passes every high-res window" if passes else paper.dies[0].verdict.reasons[0]

    # (b) the wafer in fact -- the same line WITH the parasitic structure in it.
    built = regrade(run_line(replace(DEFAULT_RECIPE, czochralski=cz, isolation=iso),
                             seed=SEED, grid_n=GRID_N), HIGH_RES)
    shipped = sum(d.verdict.passed for d in built.dies)

    rho = float(resistivity(n_seed, DEFAULT_RECIPE.czochralski.dopant))
    r_sub = iso.substrate_resistance_ohm(rho)
    i_trig = lu.trigger_current_a(r_sub)
    return Rung(n_seed=n_seed, rho_ohm_cm=rho, trigger_ma=i_trig * 1.0e3,
                margin=i_trig / iso.injected_current_a, latches=i_trig < iso.injected_current_a,
                passes_window=passes, shipped=shipped, n_dies=len(built.dies), window_reason=reason)


def crossing_n_seed(*, lo: float = 1.0e14, hi: float = 1.0e18, tol: float = 1.0e-4) -> float:
    """The substrate doping at which the trigger current *equals* the injected disturbance (cm^-3).

    Solved from the closed form by bisection, **not** read off the ladder: the crossing is a continuous
    property of the substrate, and reading it off a ladder would make the demo's headline depend on how
    finely the ladder happened to be sampled. (It did, once -- trimming a rung silently collapsed the
    figure's trap band to zero width.) Monotone by construction: heavier substrate -> lower resistivity
    -> higher trigger current.
    """
    iso = replace(DEFAULT_RECIPE.isolation, scheme="sti")
    dopant = DEFAULT_RECIPE.czochralski.dopant

    def margin(n: float) -> float:
        r_sub = iso.substrate_resistance_ohm(float(resistivity(n, dopant)))
        return lu.trigger_current_a(r_sub) - iso.injected_current_a

    assert margin(lo) < 0.0 < margin(hi), "the crossing is not bracketed"
    while hi / lo - 1.0 > tol:
        mid = (lo * hi) ** 0.5                       # geometric bisection -- the axis is logarithmic
        if margin(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    return (lo * hi) ** 0.5


def run() -> tuple[Rung, ...]:
    """Walk the substrate ladder -- the demo's whole computation."""
    return tuple(_rung(n) for n in SUBSTRATE_LADDER)


def print_summary(rungs: tuple[Rung, ...]) -> None:
    """The text artifact -- the ladder, the window, and why the loss is total."""
    injected_ma = DEFAULT_RECIPE.isolation.injected_current_a * 1.0e3
    print()
    print("The deliberate wafer kill -- the sliver of the high-res spec that cannot be built")
    print("=" * 98)
    print(f"  product : {HIGH_RES.name} (the native high-resistivity part -- LIGHTER substrate is BETTER:")
    print("            lower native threshold, and BV ~ N_A^-3/4, which is why this part exists at all)")
    print(f"  hazard  : latchup, a WAFER property -- scrap is all {rungs[0].n_dies} dies or none, never a ring")
    print(f"  survive : {injected_ma:.1f} mA injected disturbance (a given, never modelled)")
    print()
    print(f"  {'substrate':>10}  {'rho':>8}  {'trigger':>9}  {'margin':>8}   {'on paper':>9}  {'shipped':>9}")
    print(f"  {'(cm^-3)':>10}  {'(ohm.cm)':>8}  {'(mA)':>9}  {'':>8}   {'':>9}  {'':>9}")
    print("  " + "-" * 94)
    for r in rungs:
        paper = "PASSES" if r.passes_window else "reject"
        tag = ""
        if r.passes_window and r.latches:
            tag = "  <== THE TRAP: a perfect part on paper, a dead wafer in fact"
        elif r.passes_window:
            tag = "  buildable"
        print(f"  {r.n_seed:10.1e}  {r.rho_ohm_cm:8.3f}  {r.trigger_ma:9.2f}  {r.margin:7.2f}x   "
              f"{paper:>9}  {r.shipped:>4}/{r.n_dies:<4}{tag}")
    print()

    window = [r for r in rungs if r.passes_window]
    trap = [r for r in window if r.latches]
    safe = [r for r in window if not r.latches]
    print("  What the ladder says")
    print("  " + "-" * 94)
    print(f"    The part's window runs {min(r.n_seed for r in window):.1e} -> "
          f"{max(r.n_seed for r in window):.1e} cm^-3: below it the native threshold falls under the")
    print("    floor, above it the breakdown voltage does. Inside it, the latchup crossing at "
          f"{crossing_n_seed():.2e} splits")
    print(f"    the window in two -- {len(trap)} rung(s) that ship NOTHING and {len(safe)} that ship "
          "everything. Nothing on the datasheet")
    print("    tells them apart, and no isolation scheme, rework or re-target recovers the first group.")
    print()
    print("  Why this is a cliff and not a slope, on purpose")
    print("  " + "-" * 94)
    print("    The house preference is graded failure whenever the physics honestly allows it. Here it does")
    print("    not: the discriminating quantity is the substrate resistivity, which is ONE number for the")
    print("    whole wafer, so there is no real spatial variation to grade on -- B12 refused to invent one.")
    print("    What is left is a total loss the player can SEE COMING (the margin column, available before")
    print("    committing via journey.substrate_trajectory) and can ATTRIBUTE afterwards (the journey")
    print("    forecast names GROW, not the isolation stage where the bill merely surfaced).")
    print()


def main() -> None:
    rungs = run()
    print_summary(rungs)
    try:
        saved = save_figure(rungs)
        print(f"Figure saved -> {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed -- install the viz extra to render the figure: "
              "pip install -e .[viz])")
    print()


# --------------------------------------------------------------------------- #
# The figure -- one panel, because the claim is one overlap
# --------------------------------------------------------------------------- #
def save_figure(rungs: tuple[Rung, ...]) -> Path:
    """Render the trap: the part's window, the latchup crossing, and where they overlap."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt
    import numpy as np

    iso = replace(DEFAULT_RECIPE.isolation, scheme="sti")
    injected_ma = iso.injected_current_a * 1.0e3

    # A dense trigger curve (closed form -- no line runs), plus the two window edges from the rungs.
    n_dense = np.logspace(np.log10(1.0e15), np.log10(2.0e17), 400)
    trig_ma = np.array([lu.trigger_current_a(iso.substrate_resistance_ohm(
        float(resistivity(n, DEFAULT_RECIPE.czochralski.dopant)))) * 1.0e3 for n in n_dense])
    window = [r for r in rungs if r.passes_window]
    w_lo, w_hi = min(r.n_seed for r in window), max(r.n_seed for r in window)
    crossing = crossing_n_seed()          # solved, not sampled -- see the docstring

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xscale("log")
    ax.set_yscale("log")

    # The part's own acceptance window, and the sliver of it that cannot be built.
    ax.axvspan(w_lo, w_hi, color="tab:green", alpha=0.10,
               label=f"the high-res part's window ({w_lo:.1e} - {w_hi:.1e} cm$^{{-3}}$)")
    ax.axvspan(w_lo, crossing, facecolor="tab:red", alpha=0.22, hatch="//", edgecolor="tab:red", lw=0.0,
               label="THE TRAP: inside the window, and the wafer latches")

    ax.plot(n_dense, trig_ma, "-", color="tab:blue", lw=2.4,
            label="latchup trigger current (STI, uniform wafer)")
    ax.axhline(injected_ma, color="tab:red", ls="--", lw=1.8,
               label=f"injected disturbance {injected_ma:.0f} mA -- below this line the wafer is scrap")
    ax.fill_between(n_dense, trig_ma, injected_ma, where=(trig_ma < injected_ma),
                    color="tab:red", alpha=0.10)
    ax.axvline(DEFAULT_RECIPE.czochralski.N_seed, color="0.45", ls="-.", lw=1.5,
               label=f"the game default ({DEFAULT_RECIPE.czochralski.N_seed:.0e}) -- the logic wafer, "
                     f"the HEAVY end")

    ax.set_xlabel("substrate doping  N$_{seed}$  (cm$^{-3}$)    "
                  "[<- lighter: better threshold and breakdown, worse latchup]")
    ax.set_ylabel("latchup trigger current  (mA)")
    ax.set_title("The deliberate wafer kill: the lightest sliver of a legitimate spec cannot be built",
                 fontsize=10.5)
    ax.legend(fontsize=7.4, loc="upper left")
    ax.grid(True, alpha=0.18, which="both")
    ax.text(0.985, 0.05,
            "latchup is a WAFER property -- one resistivity per wafer, so the loss is\n"
            "total by construction. B12 refused to grade it; this is what that refusal costs.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.0, color="0.35")

    fig.tight_layout()
    DOCS_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS_FIGURE, dpi=130)
    return DOCS_FIGURE


if __name__ == "__main__":
    main()
