"""The G2 banked artifact: the Czochralski boule → a batch's V_t spread → yield down the boule.

The fab-line game's second demonstrable thing (plan §6 G2) and the **first new front-of-line
physics**: :mod:`chip.czochralski` — the cited **Scheil** axial-segregation closed form — wired
through the *already-validated* diffusion → oxidation → litho → device back end.

A single boron boule is grown; wafers sliced from successive axial positions start at successively
**higher** substrate doping (boron's ``k ≈ 0.8 < 1`` rejects solute into the shrinking melt, so the
solid that freezes later is more doped). That rising ``N_A`` **alone** — one crystal-growth knob, no
process change — walks the device ``V_t`` up across the spec window, so the boule's tail is scrapped.
This is the unit-of-run reconciliation in action (plan §10): a *run* is one wafer at axial ``z``; a
**batch** is the boule sliced down its length, surfacing where each slice sits on the Scheil curve.

It is the first front-of-line *propagation* story: Scheil resistivity spread → ``V_t`` spread →
yield, traced through the wafer state. The Scheil math is cited and triad-tested
(``chip/tests/test_czochralski.py``); the ``V_t``/yield consequence rides the validated device, so
the only new thing asserted here is the *wiring*. Run with :data:`NO_VARIATION` so the batch isolates
the axial Scheil effect — the only difference between wafers is the substrate the boule handed them.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_boule
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .pipeline import BatchResult, run_batch
from .recipe import DEFAULT_RECIPE
from .spec import DEFAULT_SPECS

# --- The demo batch (one boule, sliced down its length) ---------------------- #
SEED = 0
N_WAFERS = 10
Z_MAX = 0.9                                   # stop short of the unphysical z→1 tail
GRID_N = 5

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g2.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g2.png"


@dataclass(frozen=True)
class DemoResult:
    """The scored batch + the scrap threshold (the first z whose wafer leaves spec) — the bundle."""

    batch: BatchResult
    scrap_z: float | None                     # first axial fraction whose wafer is scrapped (None if all pass)
    v_t_lo: float
    v_t_hi: float


def compute() -> DemoResult:
    """Grow a boule, slice a batch down it, score each wafer → :class:`DemoResult` (no plotting)."""
    batch = run_batch(DEFAULT_RECIPE, n_wafers=N_WAFERS, z_max=Z_MAX, seed=SEED, grid_n=GRID_N)
    # The scrap threshold: the first slice down the boule whose yield has collapsed.
    scrap_z = next((z for z, y in zip(batch.z_positions, batch.yields) if y < 1.0), None)
    return DemoResult(batch=batch, scrap_z=scrap_z,
                      v_t_lo=DEFAULT_SPECS.v_t.lo, v_t_hi=DEFAULT_SPECS.v_t.hi)


def print_summary(r: DemoResult) -> None:
    """Print the boule → Scheil spread → V_t → yield story — the demo's payoff in text."""
    b = r.batch
    boule = b.boule
    print("\nThe fab line: one boule, sliced down its length → the Scheil V_t spread → the tail is scrapped\n")
    print(f"  Czochralski boule: {boule.dopant} substrate, seed N_A = {boule.N_seed:.2e} cm⁻³, "
          f"k = {boule.k:.2f} (Trumbore)")
    print(f"    → melt was richer: C₀ = N_seed/k = {boule.melt_concentration:.2e} cm⁻³; "
          f"seed resistivity ρ = {b.resistivities[0]:.3f} Ω·cm\n")
    print(f"  V_t spec window: [{r.v_t_lo:.2f}, {r.v_t_hi:.2f}] V  (a wafer is scrapped once its V_t leaves it)\n")
    print("    z (frac)   N_A (cm⁻³)   ρ (Ω·cm)   V_t (V)   yield")
    for z, w in zip(b.z_positions, b.wafers):
        vt = b.mean_V_t(w)
        flag = "" if (r.v_t_lo <= vt <= r.v_t_hi) else "  ← out of spec"
        y = next(rec.summary["yield"] for rec in w.provenance if rec.step == "test")
        print(f"    {z:5.2f}     {w.channel_N_A:.3e}   {w.resistivity_ohm_cm:6.3f}    {vt:.3f}    {y:4.0%}{flag}")
    if r.scrap_z is not None:
        n_scrapped = sum(y < 1.0 for y in b.yields)
        print(f"\n  → the boule tail is scrapped from z ≈ {r.scrap_z:.2f} ({n_scrapped}/{len(b.wafers)} slices): "
              f"the SUBSTRATE doping alone — one growth knob — walked V_t out of spec.")
    else:
        print("\n  → the whole boule passed (widen the slice range or tighten the V_t window to see the tail fail).")
    print("\n  New physics: the cited Scheil segregation (chip.czochralski, triad-tested). The V_t/yield")
    print("  consequence rides the validated device — only the front-of-line wiring is new.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the boule → batch artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import boule_figure

    fig = boule_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ₂, φ, → on legacy codepages

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
