"""The CG-3 banked artifact: the Stefan interface balance → where CG-2's gradient comes from, and the
latent-heat cap on the vacancy supersaturation.

The third and last Czochralski **crystal-growth deepening** (plan §6a CG-3). CG-2 took the interface
thermal gradient ``G`` as a flagged house knob and let the Voronkov ratio ``ξ = V/G`` grow without
bound as you pull faster. But ``G`` is not free: at the moving freezing front the latent heat of
solidification must be carried off by the conductive-flux jump (the **Stefan condition**), so the
crystal-side gradient ``G_s = (L·ρ·V + k_l·G_l)/k_s`` rises *with* the pull rate. THE consequence
(:func:`chip.czochralski.max_voronkov_ratio`): ``ξ = V/G_s`` **saturates** at ``ξ_max = k_s/(L·ρ) ≈
0.3 mm²/(K·min)`` — latent heat caps the vacancy supersaturation. The cost of fast pull is **bounded**,
not the runaway cliff CG-2's fixed ``G`` implied.

This is **not** a transient free-boundary solve (the Neumann √t front is a different, transient
scenario with no consumer here — so the engine stays untouched, no ADR, per the repo's anti-over-build
rule and the v1.2 receding-mesh precedent). It is the quasi-steady interface balance, a closed form,
whose **named consumer is CG-2's ``G``**. Three panels:

1. **The saturation (ξ vs pull).** Under the Stefan coupling ``ξ(V)`` rises but caps at ``ξ_max`` for
   every melt-side gradient ``G_l`` — vs CG-2's fixed-``G`` line ``ξ = V/G`` that diverges. The headline.
2. **The coupling (G_s vs pull).** The crystal-side gradient rises **linearly** with pull (the latent
   term ``L·ρ·V/k_s``) — that is *why* ξ saturates — vs CG-2's frozen, flat ``G``.
3. **The bounded cost (defect yield vs pull).** The CG-2 grown-in COP defect yield
   (``poisson_yield(void_density(ξ), A)``, the same analytic law the G3 scatter converges to) **floors**
   under the Stefan coupling — there is a worst-case COP yield — while CG-2's fixed ``G`` collapses it to 0.

**Honesty (the repo's bar).** ``G_l`` (the melt-side gradient / hot-zone superheat) is **still a house
number** — CG-3 moves the house-ness up one level and adds the *coupling* ``G_s(V)`` + the *cap*
``ξ_max``; it does **not** make ``G`` first-principles. The triad is the tight V→0 / V→∞ limits + cited
Si melt-point constants — **no independent conservation leg** (the flux balance read back from ``G_s``
is by-construction, the same honesty tier as CG-2). ``ξ_max`` is order-of-magnitude (set by the cited
constants); the saturation assumes ``G_l`` is roughly independent of ``V``.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_stefan
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.czochralski import (
    VORONKOV_CRITICAL_RATIO,
    grown_in_defect_regime,
    max_voronkov_ratio,
    stefan_interface_gradient,
    void_defect_density,
    voronkov_ratio,
)
from chip.wafer_prep import poisson_yield

from .state import die_area_cm2

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
XI_T = VORONKOV_CRITICAL_RATIO                      # ξ_t = 0.13 (cited Voronkov)
XI_MAX = max_voronkov_ratio()                      # ξ_max = k_s/(L·ρ) ≈ 0.32 (cited Si constants)
MELT_GRADS_K_PER_MM = (0.5, 1.5, 3.0)              # the melt-side gradient family (the hot-zone lever)
G_L_REF = 0.5                                       # the reference melt gradient for the CG-2 contrast
PULL_SWEEP_MM_MIN = tuple(float(v) for v in np.linspace(0.1, 6.0, 80))
# The CG-2 "fixed G" contrast: freeze G at its Stefan value at a reference pull (V=1), then let CG-2's
# ξ=V/G run unbounded from there — an apples-to-apples "what if G didn't couple to V".
V_REF_MM_MIN = 1.0
# The die-map scale the analytic Poisson yield uses (the single die_area_cm2 the G3 map uses).
GRID_N = 5
WAFER_DIAMETER_MM = 200.0

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-cg3.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-cg3.png"


@dataclass(frozen=True)
class DemoResult:
    """The ξ-saturation + the G_s(V) coupling + the bounded-cost contrast vs CG-2's fixed G (no score)."""

    xi_t: float
    xi_max: float
    die_area_cm2: float
    melt_grads: tuple[float, ...]
    pull_sweep: tuple[float, ...]
    xi_by_melt: dict                                # G_l → ξ(V) under the Stefan coupling (CG-3)
    gs_by_melt: dict                                # G_l → G_s(V) (K/mm) under the Stefan coupling
    g_l_ref: float
    g_fixed: float                                  # the CG-2 frozen G = G_s(V_ref, G_l_ref)
    xi_cg2_fixed: tuple[float, ...]                 # CG-2's unbounded ξ = V/G_fixed
    yield_cg3_ref: tuple[float, ...]                # CG-3 defect yield at G_l_ref (floors)
    yield_cg2_fixed: tuple[float, ...]              # CG-2 fixed-G defect yield (collapses)
    yield_floor: float                              # poisson_yield(void(ξ_max), A) — the worst-case floor
    # The realistic operating point (the honest anchor):
    realistic_ratio: float
    realistic_regime: str


def compute() -> DemoResult:
    """Build the ξ-saturation curves, the G_s(V) coupling, and the bounded-cost vs fixed-G contrast."""
    area = die_area_cm2(GRID_N, WAFER_DIAMETER_MM)
    v = np.asarray(PULL_SWEEP_MM_MIN)

    xi_by_melt: dict = {}
    gs_by_melt: dict = {}
    for g_l in MELT_GRADS_K_PER_MM:
        gs = np.array([stefan_interface_gradient(float(vv), g_l) for vv in v])
        xi = np.array([voronkov_ratio(float(vv), float(g)) for vv, g in zip(v, gs)])
        gs_by_melt[g_l] = tuple(float(x) for x in gs)
        xi_by_melt[g_l] = tuple(float(x) for x in xi)

    # The CG-2 "fixed G" contrast: G frozen at its Stefan value at the reference pull, then ξ = V/G.
    g_fixed = stefan_interface_gradient(V_REF_MM_MIN, G_L_REF)
    xi_cg2_fixed = tuple(float(vv) / g_fixed for vv in v)

    # Panel 3 — the analytic defect yield (the law the G3 scatter converges to).
    yield_cg3_ref = tuple(poisson_yield(void_defect_density(x), area) for x in xi_by_melt[G_L_REF])
    yield_cg2_fixed = tuple(poisson_yield(void_defect_density(x), area) for x in xi_cg2_fixed)
    yield_floor = float(poisson_yield(void_defect_density(XI_MAX), area))

    realistic_ratio = voronkov_ratio(V_REF_MM_MIN, stefan_interface_gradient(V_REF_MM_MIN, G_L_REF))
    return DemoResult(
        xi_t=XI_T, xi_max=XI_MAX, die_area_cm2=area,
        melt_grads=MELT_GRADS_K_PER_MM, pull_sweep=PULL_SWEEP_MM_MIN,
        xi_by_melt=xi_by_melt, gs_by_melt=gs_by_melt,
        g_l_ref=G_L_REF, g_fixed=g_fixed, xi_cg2_fixed=xi_cg2_fixed,
        yield_cg3_ref=yield_cg3_ref, yield_cg2_fixed=yield_cg2_fixed, yield_floor=yield_floor,
        realistic_ratio=realistic_ratio, realistic_regime=grown_in_defect_regime(realistic_ratio),
    )


def _at(seq, v_target: float) -> float:
    """The curve value nearest a target pull rate (for the text table)."""
    i = int(np.argmin(np.abs(np.asarray(PULL_SWEEP_MM_MIN) - v_target)))
    return seq[i]


def print_summary(r: DemoResult) -> None:
    """Print the Stefan-balance → saturation → bounded-cost story — the demo's payoff in text (no score)."""
    print("\nCrystal growth CG-3: the Stefan interface balance — where CG-2's gradient G comes from\n")

    print(f"  At the moving front the latent heat couples G to the pull rate (Stefan condition):")
    print(f"     G_s = (L·ρ·V + k_l·G_l) / k_s   →   ξ = V/G_s saturates at ξ_max = k_s/(L·ρ)\n")
    print(f"  ξ_max = {r.xi_max:.3f} mm²/(K·min)  ≈ {r.xi_max / r.xi_t:.1f}× ξ_t ({r.xi_t:.2f}) — the latent-heat-")
    print(f"  capped MAXIMUM vacancy supersaturation: even an infinitely fast pull lands only modestly")
    print(f"  vacancy-rich, NOT the unbounded ξ of CG-2's fixed G.\n")

    print(f"  ξ vs pull (melt gradient G_l = {r.g_l_ref:.1f} K/mm, the Stefan coupling vs CG-2's fixed G):")
    print(f"     {'V (mm/min)':>11}  {'G_s (K/mm)':>11}  {'ξ (CG-3)':>9}  {'ξ (CG-2 fixed)':>15}")
    for vt in (1.0, 2.0, 4.0, 6.0):
        gs = _at(r.gs_by_melt[r.g_l_ref], vt)
        xi3 = _at(r.xi_by_melt[r.g_l_ref], vt)
        xi2 = _at(r.xi_cg2_fixed, vt)
        print(f"     {vt:>11.1f}  {gs:>11.2f}  {xi3:>9.3f}  {xi2:>15.3f}")
    print(f"  → CG-3's ξ creeps toward {r.xi_max:.2f} (G_s rises with V); CG-2's ξ=V/G runs away.\n")

    print(f"  The bounded cost — grown-in COP defect yield (A = {r.die_area_cm2:.1f} cm²) at G_l={r.g_l_ref:.1f}:")
    for vt in (1.0, 2.0, 4.0, 6.0):
        y3 = _at(r.yield_cg3_ref, vt)
        y2 = _at(r.yield_cg2_fixed, vt)
        print(f"     V={vt:>4.1f}:  yield(CG-3 Stefan) = {y3:5.2f}   yield(CG-2 fixed G) = {y2:5.2f}")
    print(f"  → the Stefan yield FLOORS at ≈{r.yield_floor:.2f} (a worst-case COP yield); the fixed-G yield")
    print(f"     collapses to 0. The in-model cost of fast pull is CAPPED, not a cliff.\n")

    print(f"  Honest: G_l (the hot-zone superheat) is STILL a house number — CG-3 adds the coupling G_s(V)")
    print(f"  and the cap ξ_max, not first-principles G. Triad = the V→0 / V→∞ limits + cited Si constants;")
    print(f"  NO conservation leg. Opt-in (melt_gradient unset → CG-2/CG-3 off → the banked demos unchanged).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the CG-3 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import stefan_figure

    fig = stefan_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # ξ, ρ, →, ≈ on legacy codepages

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
