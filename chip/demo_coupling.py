"""The v1.2 anchor demo: oxidation reaching back on the dopant profile — OED + segregation.

Phases 1–2 were **forward-only** — Phase 4 consumed a dopant profile and an oxide as if they were
independent. They are not: a thermal oxidation **back-reacts** on the underlying dopant
(:mod:`coupling`). This demo makes that visible by running the *same* predeposited seed through the
*same* oxidizing anneal three ways and overlaying them:

  * **inert drive-in** — the v1 assumption (no coupling: a sealed anneal);
  * **+ OED** — the oxidizing interface injects self-interstitials → the diffusivity is **enhanced**
    → the profile is pushed **deeper** (boron and phosphorus alike — both interstitialcy diffusers);
  * **+ segregation** — dopant **partitions** across the moving Si/SiO₂ interface: **boron (m < 1)
    depletes** at the surface (the oxide takes it), **phosphorus (m > 1) piles up** (the oxide
    rejects it) — the opposite-sign signatures, on the same figure.

The headline (the banked artifact `docs/figures/chip-oed-segregation.png`): two panels, **boron
depletion** beside **phosphorus pile-up**, each decomposing inert → +OED → +segregation. *Oxidation
is not a bystander — it enhances the diffusion and reshapes the surface.*

Cited basis (reference facts, not redistributed): the fractional interstitialcy ``f_I`` (B 0.30, P
0.38 — the dual I/V mechanism paper) and the segregation coefficients ``m`` (B 0.3, P 10 — Hollauer,
the same dissertation as the Massoud pin). The OED *amplitude* is calibrated (flagged) — so the
demo's enhancement magnitude is illustrative; the **directions** (enhanced; deplete vs pile-up) are
the validated content.

**Honesty caveat owned on the figure (the swept-sliver scope edge).** The segregation flux is a
moving-*interface* mass balance run on a non-moving grid, which double-counts the swept silicon
sliver (:mod:`coupling` docstring). So the **boron depletion is robust** (it is oxide-uptake-
dominated — the device-relevant case), while the **phosphorus pile-up direction is real but its
magnitude is ~2× inflated** (pile-up is intrinsically a moving-boundary effect). The demo presents
boron as the trustworthy case and phosphorus as the qualitative sign-contrast.

Run headless (saves the figure, prints the table):

    python -m projects.chip.demo_coupling
"""
from __future__ import annotations

from pathlib import Path

from engines.diffusion import uniform_grid

from . import coupling as cp
from . import diffusion_dopant as dd

# The demo recipe: a predep seed, then a dry oxidizing anneal (the gate-oxide ambient) at a
# representative temperature. The same seed + anneal is run inert / +OED / +OED+segregation.
T_PREDEP = 950.0               # °C — the seed predeposition
T_PREDEP_MIN = 15.0            # min
T_OXIDE = 1000.0               # °C — the oxidizing drive-in (dry O₂, the gate-oxide regime)
T_OXIDE_MIN = 30.0             # min
AMBIENT = "dry"
ORIENTATION = "100"            # the device-relevant face (Phase-4 MOS is built on (100))
LENGTH_UM = 3.0
N_CELLS = 600

# The two contrasting dopants: boron (m < 1 → depletion), phosphorus (m > 1 → pile-up).
DOPANT_CASES = ("B", "P")

_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-oed-segregation.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-oed-segregation.png"


def compute() -> list[dict]:
    """Run the inert / +OED / +OED+segregation triple for boron and phosphorus → the figure cases.

    Each case dict carries the seed and the three :class:`coupling.CoupledResult` variants over one
    shared grid, plus the cited ``f_I``/``m`` and the segregation ``sign`` the figure annotates.
    """
    grid = uniform_grid(LENGTH_UM * dd.CM_PER_UM, N_CELLS)
    cases = []
    for dop in DOPANT_CASES:
        seed = dd.predeposit(grid, dop, T_PREDEP, T_PREDEP_MIN * 60.0).N
        common = dict(orientation=ORIENTATION, model="deal-grove", n_steps=600)
        inert = cp.oxidize_couple(grid, seed, dop, AMBIENT, T_OXIDE, T_OXIDE_MIN,
                                  oed=False, segregation=False, **common)
        oed = cp.oxidize_couple(grid, seed, dop, AMBIENT, T_OXIDE, T_OXIDE_MIN,
                                oed=True, segregation=False, **common)
        coupled = cp.oxidize_couple(grid, seed, dop, AMBIENT, T_OXIDE, T_OXIDE_MIN,
                                    oed=True, segregation=True, **common)
        m = cp.SEGREGATION_COEFFICIENT[dop]
        cases.append({
            "name": {"B": "boron", "P": "phosphorus"}[dop],
            "dopant": dop,
            "seed": seed,
            "inert": inert,
            "oed": oed,
            "coupled": coupled,
            "f_I": cp.FRACTIONAL_INTERSTITIALCY[dop],
            "m": m,
            "sign": "depletion" if m < 1.0 else "pile-up",
        })
    return cases


def print_summary(cases: list[dict]) -> None:
    """Print the recipe → enhancement → surface-reshaping story — the demo's payoff in text."""
    print(f"\nThe Phase 1↔2 back-coupling: a {AMBIENT} O₂ anneal at {T_OXIDE:.0f} °C "
          f"for {T_OXIDE_MIN:.0f} min on ({ORIENTATION}) Si\n")
    for c in cases:
        inert, oed, coupled = c["inert"], c["oed"], c["coupled"]
        enh = oed.effective_Dt / (oed.D_inert * oed.t_seconds)
        # The segregation step is read against OED-only (isolating it from OED's spreading, which
        # drops the surface peak for both dopants); coupled-vs-inert would hide phosphorus pile-up.
        surf_ratio = coupled.surface_concentration / oed.surface_concentration
        print(f"  {c['name']:>10} (f_I={c['f_I']}, m={c['m']}):")
        print(f"      OED: effective ∫D dt = ×{enh:.2f} the inert value → profile pushed deeper, "
              f"surface {inert.surface_concentration:.3e} → {oed.surface_concentration:.3e}")
        print(f"      segregation (vs OED): surface {oed.surface_concentration:.3e} → "
              f"{coupled.surface_concentration:.3e} cm⁻³  (×{surf_ratio:.2f}, {c['sign']})")
        print(f"      conservation: Si + oxide-reservoir residual / dose = "
              f"{coupled.conservation_residual / coupled.si_dose_initial:.1e}  (machine-exact)\n")
    print("  → oxidation is not a bystander: it ENHANCES the diffusion (OED) and PARTITIONS the\n"
          "    dopant at the moving interface — boron depletes, phosphorus piles up.\n"
          "  (scope edge: the fixed grid double-counts the swept silicon sliver, so the boron\n"
          "   depletion is robust [oxide-uptake-dominated, device-relevant] but the phosphorus\n"
          "   pile-up MAGNITUDE is ~2× inflated — direction real, a moving-boundary effect.)\n")


def save_figure(cases: list[dict]) -> Path:
    """Render and save the back-coupling artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import coupling_figure

    fig = coupling_figure(cases)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ₂, µ, →, ∫ on legacy codepages

    cases = compute()
    print_summary(cases)
    try:
        saved = save_figure(cases)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
