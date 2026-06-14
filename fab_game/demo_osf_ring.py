"""The A2 banked artifact: the OSF ring — CG-2 made radial (the across-wafer crystal-growth deepening).

CG-2 (the Voronkov V/G criterion, :mod:`fab_game.demo_voronkov`) gave the crystal **one** defect regime
for the whole wafer (``ξ = V/G`` a single number). A2 lets the interface gradient ``G`` vary with wafer
**radius** — the periphery cools faster, so ``G`` rises outward (:func:`chip.czochralski.radial_thermal_gradient`)
— and then ``ξ(r) = V/G(r)`` **falls** from centre to edge. A single pull can leave the **centre
vacancy-rich** (COP voids) and the **edge interstitial-rich**, with the **OSF (oxidation-induced
stacking-fault) ring** at the annulus where ``ξ(r) = ξ_t`` (:func:`chip.czochralski.osf_ring_radius`) —
the CG-2 V/I boundary made visible *on the wafer*. The consumer is the existing per-die G3 defect map:
the grown-in killer density becomes per-die (keyed on ``radius_frac``), so edge and centre dies see
different yield — an across-wafer **non-uniformity**.

THE honest finding (lead with it — the CG-1/CG-2 honest-magnitude pattern). The yield consequence reuses
CG-2's vacancy-side :func:`chip.czochralski.void_defect_density`, which is **monotone in ξ** — so the
killer-COP density **peaks at the high-ξ centre and falls to zero AT the ring**, then stays zero across
the interstitial rim. The wafer map is therefore a **COP-degraded vacancy core + a clean interstitial rim
— NOT a ring of dead dies**. The OSF ring is the *boundary* where the kills **stop**, not a band of kills.
(Honest magnitude: the void coefficient is the same capped CG-2 house number, so the core mortality is
*modest* — the kill rate merely climbs toward the centre; what is provable is that the rim is clean.)
(A literal *degraded ring* — the stacking faults' own junction leakage — would feed the interstitial /
:mod:`chip.lifetime` channel, the separately-deferred A1 edge; so it stays a named deferred refinement.)

And the second honesty (the magnitude flag): the ring's **on-wafer existence is a tuned house profile** —
``G(r)`` (its shape, the radial ``boost``) is chosen so the V/I boundary lands in ``[0, 1]``. What is
**tight** is the ring *location given the profile* (``ξ(r_OSF) = ξ_t``, coefficient-robust) and the
topology *signs* (vacancy centre / interstitial edge); the profile and the ring's existence are flagged.
**No engine** participates (the Robin-``G`` heat-mode sourcing was verified-and-falsified, deferred — a
steady radial gradient is closed-form). Three panels:

1. **The radial criterion (ξ(r) across the wafer).** ``ξ(r) = V/G(r)`` falls from centre to edge,
   crossing the cited ``ξ_t`` at ``r_OSF`` — the three zones: vacancy core / OSF ring / interstitial rim.
2. **The radial consequence (where the kills stop).** The grown-in void density ``D(r)`` and the analytic
   per-die survival ``exp(−D(r)·A)`` vs radius: survival climbs from the degraded core to a clean rim, the
   kills ending **at** the ring (the law the per-die G3 scatter converges to — the CG-2 analytic-demo discipline).
3. **The wafer map (the consumer).** A seeded stochastic realization on a clean line: killer COPs land
   **only in the vacancy core**, the rim survives — the edge-vs-centre non-uniformity made physical, with
   the OSF ring drawn as the boundary and each die shaded by its grown-in density.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_osf_ring
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.czochralski import (
    VORONKOV_CRITICAL_RATIO,
    osf_ring_radius,
    radial_defect_regime,
    radial_thermal_gradient,
    void_defect_density,
    voronkov_ratio,
)
from chip.wafer_prep import poisson_yield

from .pipeline import run_line
from .recipe import CzochralskiKnobs, Recipe, WaferPrepKnobs
from .state import WaferState, die_area_cm2
from .variation import Variation

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
XI_T = VORONKOV_CRITICAL_RATIO                      # ξ_t = 0.13 mm²/(K·min) (cited Voronkov)
# A balanced radial hot zone with the V/I ring mid-wafer: ξ(0)=V/G_center=0.40 > ξ_t > ξ(1)=0.057.
# (House profile — chosen so the boundary lands in [0, 1]; the ring's existence is illustrative.)
V_MM_MIN = 2.0                                     # the pull rate
G_CENTER_K_PER_MM = 5.0                            # centre interface gradient G_center (a cool, insulated core)
RADIAL_BOOST = 6.0                                 # the flagged centre→edge steepening (G(edge)=G_center·(1+boost))
# The die map for the analytic survival + the stochastic wafer-map panel (the G3 consumer).
GRID_N = 9
WAFER_DIAMETER_MM = 200.0
# Defects-only variation: the ONLY stochastic effect is the killer-COP scatter (the device physics is the
# clean nominal), so the radial map isolates the A2 across-wafer signal (as the wiring test does).
_DEFECTS_ONLY = Variation(enabled=True, focus_tilt_nm=0.0, t_ox_edge_frac=0.0,
                          focus_sigma_nm=0.0, cd_sigma_nm=0.0, t_ox_sigma_frac=0.0)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-a2.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-a2.png"


@dataclass(frozen=True)
class DemoResult:
    """The radial criterion + the radial consequence + the stochastic wafer map (the consumer)."""

    xi_t: float
    v: float
    g_center: float
    boost: float
    ring_radius: float                              # r_OSF (the V/I boundary), in [0, 1]
    zones: tuple[str, str]                          # (centre, edge) regimes — the topology signs
    die_area_cm2: float
    grid_n: int
    # Panels 1–2 — the analytic radial sweep:
    r_grid: tuple[float, ...]
    g_of_r: tuple[float, ...]
    xi_of_r: tuple[float, ...]
    density_of_r: tuple[float, ...]                 # grown-in void density D(r) (peaks centre, 0 at/past ring)
    survival_of_r: tuple[float, ...]                # analytic exp(−D(r)·A) (degraded core → clean rim)
    # Panel 3 — the stochastic wafer map (the per-die G3 consumer):
    wafer: WaferState
    map_seed: int
    core_dies: int
    core_killed: int
    rim_dies: int
    rim_killed: int


def _radial_recipe() -> Recipe:
    """The A2 radial recipe on a clean line (so the only kills are the grown-in COPs)."""
    cz = CzochralskiKnobs(pull_rate_mm_min=V_MM_MIN, thermal_gradient_K_per_mm=G_CENTER_K_PER_MM,
                          radial_gradient_boost=RADIAL_BOOST)
    return Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.0))


def compute() -> DemoResult:
    """Build the radial criterion, the analytic radial consequence, and the stochastic wafer map."""
    area = die_area_cm2(GRID_N, WAFER_DIAMETER_MM)
    ring = osf_ring_radius(V_MM_MIN, G_CENTER_K_PER_MM, boost=RADIAL_BOOST)
    zones = (radial_defect_regime(0.0, V_MM_MIN, G_CENTER_K_PER_MM, RADIAL_BOOST),
             radial_defect_regime(1.0, V_MM_MIN, G_CENTER_K_PER_MM, RADIAL_BOOST))

    # The analytic radial sweep (panels 1–2): G(r) → ξ(r) → void density D(r) → survival exp(−D·A).
    r_grid = np.linspace(0.0, 1.0, 200)
    g_of_r = radial_thermal_gradient(r_grid, G_CENTER_K_PER_MM, boost=RADIAL_BOOST)
    xi_of_r = np.array([voronkov_ratio(V_MM_MIN, g) for g in g_of_r])
    density_of_r = np.array([void_defect_density(x) for x in xi_of_r])
    survival_of_r = np.array([poisson_yield(d, area) for d in density_of_r])

    # The stochastic wafer map (panel 3 — the consumer): a clean line + the radial growth → COPs land
    # only in the vacancy core; the rim is clean (provably — zero grown-in density past the ring).
    wafer = run_line(_radial_recipe(), seed=SEED, variation=_DEFECTS_ONLY,
                     grid_n=GRID_N, wafer_id="W_osf")
    core = [d for d in wafer.dies if d.radius_frac < ring]
    rim = [d for d in wafer.dies if d.radius_frac >= ring]

    return DemoResult(
        xi_t=XI_T, v=V_MM_MIN, g_center=G_CENTER_K_PER_MM, boost=RADIAL_BOOST,
        ring_radius=ring, zones=zones, die_area_cm2=area, grid_n=GRID_N,
        r_grid=tuple(float(x) for x in r_grid), g_of_r=tuple(float(x) for x in g_of_r),
        xi_of_r=tuple(float(x) for x in xi_of_r), density_of_r=tuple(float(x) for x in density_of_r),
        survival_of_r=tuple(float(x) for x in survival_of_r),
        wafer=wafer, map_seed=SEED,
        core_dies=len(core), core_killed=sum(d.killed_by_defect for d in core),
        rim_dies=len(rim), rim_killed=sum(d.killed_by_defect for d in rim),
    )


def print_summary(r: DemoResult) -> None:
    """Print the radial-criterion → radial-consequence → wafer-map story — the demo's payoff in text."""
    print("\nCrystal growth A2: the OSF ring — CG-2 made radial (the across-wafer non-uniformity)\n")

    print(f"  Radial gradient (FLAGGED house profile): G(r) = G_center·(1 + boost·r²), "
          f"G_center={r.g_center:.1f} K/mm, boost={r.boost:.1f}")
    print(f"     → G rises from {r.g_center:.1f} (centre) to {r.g_center * (1 + r.boost):.1f} K/mm (edge), "
          f"so ξ = V/G FALLS outward (V={r.v:.1f} mm/min):")
    print(f"     ξ(centre) = {r.xi_of_r[0]:.3f}  >  ξ_t = {r.xi_t:.2f}  >  ξ(edge) = {r.xi_of_r[-1]:.3f}\n")

    print(f"  The OSF ring (the V/I boundary, ξ(r)=ξ_t): r_OSF = {r.ring_radius:.3f} of the wafer radius")
    print(f"     centre = {r.zones[0].upper()}-rich (COP voids)   →   edge = {r.zones[1].upper()}-rich "
          f"(dislocations, defect-free for GOI)\n")

    print(f"  THE finding — the void density is monotone in ξ, so it PEAKS at the centre and is ZERO at "
          f"the ring:")
    idx = [0, len(r.r_grid) // 4, len(r.r_grid) // 2, 3 * len(r.r_grid) // 4, len(r.r_grid) - 1]
    print(f"     {'radius r':>10}  {'ξ(r)':>7}  {'void D(r) cm⁻²':>15}  {'survival exp(−D·A)':>19}")
    for i in idx:
        ring_mark = "  ← OSF ring" if abs(r.r_grid[i] - r.ring_radius) < 0.06 else ""
        print(f"     {r.r_grid[i]:>10.2f}  {r.xi_of_r[i]:>7.3f}  {r.density_of_r[i]:>15.4f}  "
              f"{r.survival_of_r[i]:>19.3f}{ring_mark}")
    core_mortality = 1.0 - r.survival_of_r[0]
    print(f"  → a COP-degraded vacancy CORE (modest — {core_mortality:.0%} centre mortality, the same "
          f"capped CG-2 coefficient)\n     + a CLEAN interstitial RIM: the ring is the *boundary* where "
          f"the kills STOP, NOT a ring of kills.\n")

    print(f"  The wafer map (the G3 consumer, seed {r.map_seed}, A = {r.die_area_cm2:.2f} cm², clean line):")
    print(f"     vacancy core  (r < {r.ring_radius:.2f}): {r.core_killed:>2}/{r.core_dies} dies killed by "
          f"grown-in COPs")
    print(f"     interstitial rim (r ≥ {r.ring_radius:.2f}): {r.rim_killed:>2}/{r.rim_dies} dies killed   "
          f"(provably clean — zero grown-in density past the ring)")
    print(f"  → edge-vs-centre yield NON-UNIFORMITY: the same recipe yields differently by die radius.\n")

    print(f"  Honesty (the repo's bar): the ring's on-wafer EXISTENCE is a tuned house profile (G(r), the "
          f"boost) — \n"
          f"  illustrative, not a prediction. TIGHT = the ring LOCATION (ξ(r_OSF)=ξ_t, coefficient-robust) "
          f"+ the\n"
          f"  topology SIGNS (vacancy centre / interstitial edge). No engine (the Robin-G sourcing was "
          f"falsified).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the A2 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import osf_ring_figure

    fig = osf_ring_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # ξ, →, ≈ on legacy codepages

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
