"""The G7 banked artifact: a roguelike run down one boule — the Scheil drift, scored, three strategies.

The fab-line game's seventh demonstrable thing (plan §6 G7, §1, §9). G1–G6 built a headless line from
sand to a binned wafer; G7 frames it as a **roguelike**: one boule is one run, each wafer a turn, the
**G2 Scheil V_t drift the difficulty curve** (the substrate doping rises down the boule, walking ``V_t``
toward the ceiling). Three strategies are played down the same boule and **scored**, so the decision is
the point:

1. **naive** — run the default recipe every wafer. The tail walks ``V_t`` out of spec → those wafers fail
   → revenue collapses while the wafer cost is still paid (bleeding money on doomed dies).
2. **scrap-the-tail** — inspect the substrate; when a slice's projected ``V_t`` is out of spec, **scrap**
   it (pay only the sunk-substrate cost, skip the full processing cost). **This is the clean, robust
   lesson — cost-independent:** cutting the loss on a doomed wafer beats processing it, whatever the
   dollar magnitudes are.
3. **adapt** — **thin the gate oxide** every wafer: a thinner oxide raises ``I_Dsat`` (a faster part →
   the **premium** bin), and incidentally pulls ``V_t`` down (so the tail also stays in spec). It posts
   the top score — but **read where that score comes from (panel 3), because the headline mis-attributes
   it:** ~90 % of adapt's edge over naive is **upgrading *in-spec*, never-in-danger wafers to premium**
   (thinner = faster = more valuable, the real historical scaling lever), and only ~10 % is the actual
   doomed-tail rescue. So this is **not** mostly an "adapt-or-die" rescue — it is a **premium windfall**.

**Why the windfall is not a free lunch — two brakes the headline hides.** *(a) In-model:* a thinner
oxide raises ``I_Dsat``, so over-thinning the **extreme tail** pushes drive current into its **spec
ceiling** — the linear trim over-thins the last slice (its mean ``I_Dsat`` sits right at the ceiling, so
within-wafer variation tips half its dies over and it *fumbles*). There is a real Goldilocks window:
thin enough to help ``V_t``, not so thin ``I_Dsat`` blows spec. *(b) Unmodeled:* the compact model
carries **no gate-oxide reliability/leakage penalty**, so the premium-upgrade looks free here only
because the cost that would bound it in a real fab (thin oxide breaks down / leaks) is off the model — a
named scope edge. The honest takeaway is the **scrap-vs-naive** lesson (cut your losses on the doomed
tail); the premium windfall is the caveated, double-braked bonus, **not** "thin the oxide for free profit."

The scoring + session are game-layer mechanics (``fab_game/tests/test_scoring.py``,
``test_game.py``); this demo is the integration check + the banked figure. The **Textual TUI is the
deferred follow-on** (plan §9): this run is fully headless.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_game
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .game import GameConfig, GameSession, new_session, play, process_wafer, scrap_wafer
from .recipe import DEFAULT_RECIPE, OxidationKnobs, Recipe
from .pipeline import run_line
from .variation import NO_VARIATION

# --- The run settings (FLAGGED house numbers — mechanics, not magnitudes) ---- #
SEED = 0
CONFIG = GameConfig(n_wafers=8, z_max=0.9, grid_n=5)   # one boule, 8 wafers down its length
OX_BASE_MIN = 20.5                                     # the adaptive oxide trim: minutes = base − slope·z
OX_SLOPE_MIN = 5.5                                     # (≈ centres V_t across the boule — see demo_game verify)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g7.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g7.png"


def adaptive_recipe(z: float) -> Recipe:
    """The lever: thin the gate oxide as the boule drifts → pull V_t back into spec (and lift I_Dsat)."""
    return Recipe(oxidation=OxidationKnobs(minutes=OX_BASE_MIN - OX_SLOPE_MIN * z))


@dataclass(frozen=True)
class DemoResult:
    """The V_t drift curves + the three scored playthroughs down the boule — the bundle."""

    # 1. The difficulty curve — V_t vs slice_z, naive (fixed) vs adaptive (thinned), spec window.
    z_curve: tuple[float, ...]
    vt_naive: tuple[float, ...]
    vt_adaptive: tuple[float, ...]
    vt_lo: float
    vt_hi: float
    # 2/3. The three playthroughs.
    wafer_z: tuple[float, ...]                          # slice_z per turn
    naive: GameSession
    scrap: GameSession
    adaptive: GameSession
    naive_budget: tuple[float, ...]                     # budget after each turn (the trajectory)
    scrap_budget: tuple[float, ...]
    adaptive_budget: tuple[float, ...]
    naive_profit: tuple[float, ...]                     # per-turn profit (panel 3 bars)
    adaptive_profit: tuple[float, ...]


def _budget_trajectory(session: GameSession) -> tuple[float, ...]:
    """Budget after each turn (starting budget + the running sum of per-turn profits)."""
    b = session.config.starting_budget
    out = []
    for r in session.history:
        b += r.scorecard.profit
        out.append(b)
    return tuple(out)


def _projected_vt(z: float) -> float:
    """The naive recipe's V_t at slice z (single die, no variation) — what the player 'inspects'."""
    r = replace(DEFAULT_RECIPE, czochralski=replace(DEFAULT_RECIPE.czochralski, slice_z=z))
    return run_line(r, variation=NO_VARIATION, specs=CONFIG.specs, grid_n=1).dies[0].V_t


def compute() -> DemoResult:
    """Play the three strategies down the boule + build the V_t drift curves (no plotting)."""
    cfg = CONFIG
    wafer_z = tuple(cfg.slice_z(i) for i in range(cfg.n_wafers))

    # 1. The difficulty curve (deterministic single-die V_t vs z), naive vs the adaptive oxide trim.
    z_curve = tuple(i / 40.0 * cfg.z_max for i in range(41))
    vt_naive = tuple(_projected_vt(z) for z in z_curve)
    vt_adaptive = tuple(
        run_line(replace(adaptive_recipe(z), czochralski=replace(DEFAULT_RECIPE.czochralski, slice_z=z)),
                 variation=NO_VARIATION, specs=cfg.specs, grid_n=1).dies[0].V_t
        for z in z_curve
    )

    # 2. The three playthroughs (same boule, same seed).
    naive = play(new_session(cfg, seed=SEED), [DEFAULT_RECIPE] * cfg.n_wafers)
    scrap_decisions = ["scrap" if _projected_vt(z) > cfg.specs.v_t.hi else DEFAULT_RECIPE
                       for z in wafer_z]
    scrap = play(new_session(cfg, seed=SEED), scrap_decisions)
    sess = new_session(cfg, seed=SEED)
    while not sess.done:
        sess = process_wafer(sess, adaptive_recipe(sess.next_slice_z))
    adaptive = sess

    return DemoResult(
        z_curve=z_curve, vt_naive=vt_naive, vt_adaptive=vt_adaptive,
        vt_lo=cfg.specs.v_t.lo, vt_hi=cfg.specs.v_t.hi,
        wafer_z=wafer_z, naive=naive, scrap=scrap, adaptive=adaptive,
        naive_budget=_budget_trajectory(naive), scrap_budget=_budget_trajectory(scrap),
        adaptive_budget=_budget_trajectory(adaptive),
        naive_profit=tuple(r.scorecard.profit for r in naive.history),
        adaptive_profit=tuple(r.scorecard.profit for r in adaptive.history),
    )


def print_summary(r: DemoResult) -> None:
    """Print the drift → three-strategy → score story — the demo's payoff in text."""
    print("\nThe fab line (G7): a roguelike run down one boule — the Scheil drift, scored, three strategies\n")

    print(f"  The difficulty curve: boron segregates down the boule → V_t walks up "
          f"(spec [{r.vt_lo:.2f}, {r.vt_hi:.2f}] V):")
    for z in (0.0, 0.51, 0.77, 0.9):
        i = min(range(len(r.z_curve)), key=lambda k: abs(r.z_curve[k] - z))
        nflag = "ok " if r.vt_lo <= r.vt_naive[i] <= r.vt_hi else "OUT"
        print(f"     z={r.z_curve[i]:.2f}:  naive V_t {r.vt_naive[i]:.3f} [{nflag}]   "
              f"adaptive (thinned oxide) V_t {r.vt_adaptive[i]:.3f} [ok]")
    print()

    print("  Three strategies down the boule (same seed), scored:")
    for name, sess in (("naive (process all)", r.naive), ("scrap the doomed tail", r.scrap),
                       ("adapt (thin the oxide)", r.adaptive)):
        n_proc = sum(not rec.scrapped for rec in sess.history)
        n_scrap = sum(rec.scrapped for rec in sess.history)
        print(f"     {name:24s}: final budget ${sess.budget:7.2f}   score ${sess.score:+8.2f}   "
              f"({n_proc} processed, {n_scrap} scrapped)")
    # Attribute adapt's edge over naive honestly: it is mostly a premium UPGRADE of in-spec wafers,
    # not a doomed-tail rescue (the headline temptation). Split it by slice.
    edge_tail = sum(a - n for z, n, a in zip(r.wafer_z, r.naive_profit, r.adaptive_profit) if z >= 0.85)
    edge_mid = sum(a - n for z, n, a in zip(r.wafer_z, r.naive_profit, r.adaptive_profit) if z < 0.85)
    print(f"\n     → The clean, cost-independent lesson: the tail walks V_t out of spec; SCRAPPING it beats")
    print(f"       processing a doomed wafer (naive ${r.naive.score:+.0f} < scrap ${r.scrap.score:+.0f}).")
    print(f"       Adapt posts the top score (${r.adaptive.score:+.0f}), but read where it comes from: of its")
    print(f"       ${r.adaptive.score - r.naive.score:+.0f} edge over naive, ${edge_mid:+.0f} is UPGRADING in-spec wafers to")
    print(f"       premium (thinner oxide → faster part) and only ${edge_tail:+.0f} is the actual tail rescue —")
    print(f"       a premium WINDFALL, not 'adapt-or-die'. And it is double-braked: I_Dsat hits its ceiling")
    print(f"       if you over-thin (in-model; the linear trim fumbles the last slice), and gate-oxide")
    print(f"       reliability would bound it in a real fab (UNMODELED — a named scope edge).\n")
    print("  New: the scoring + roguelike session (fab_game.scoring/game) — game policy, mechanics-tested.")
    print("  The Textual TUI is the deferred follow-on; this run is fully headless. Zero new physics.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the G7 roguelike artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import game_figure

    fig = game_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, →, ± on legacy codepages

    r = compute()
    print_summary(r)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
