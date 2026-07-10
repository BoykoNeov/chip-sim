"""The historical-modes A3 banked artifact: HCl gettering & high-pressure oxidation.

Two period oxidation ambients, each landing on an observable the sim already computes — one figure, two
panels (the two modes are orthogonal: ``V_t`` vs the ``∫D dt`` budget):

  * **Left — HCl gettering → V_t recovery (the Na→Q_ox→V_t chain, G4a).** A marginal-Na gate oxide walks
    ``V_t`` **down** (positive mobile-ion charge, ``ΔV_FB = −Q_ox/C_ox``). Adding HCl getters the mobile Na
    (:func:`chip.oxidation_history.chlorine_gettering_fraction`) → ``Q_ox`` falls → ``V_t`` climbs back
    toward the clean-oxide value. ``Cl = 0`` is the **pre-HCl period** (the full penalty); the flag turns on
    the successor. *Static offset, not the bias-temperature drift — the named scope edge.*
  * **Right — high-pressure oxidation → collateral-budget collapse (the ∫D dt chain, E1).** Both Deal–Grove
    rate constants scale ``∝ P`` (cited, equal exponent), so a **thick** field oxide grows in ``∝ 1/P`` time
    → the underlying dopant spends ``∝ 1/P`` collateral ``∫D dt`` at fixed ``T`` (the **exact** identity, all
    regimes). The bigger, *historical* win — trading pressure for **temperature** (same oxide, same time,
    lower ``T``) — collapses the Arrhenius ``D`` far more (a **flagged** worked example).

Tight legs: the two seams (``P = 1`` → :func:`chip.oxidation.grow_oxide` bit-for-bit; ``Cl = 0`` →
:func:`chip.purification.sodium_oxide_charge` bit-for-bit) + the exact ``1/P`` budget identity. Flagged: the
Cl gettering-efficiency curve + the T-reduction magnitude (see :mod:`chip.oxidation_history`). Run headless:

    python -m chip.demo_oxidation_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import oxidation_history as oh

# --- §A HCl recipe: a marginal-Na thin-gate n-MOS, swept over Cl % ------------------------------- #
N_NA = 1.0e16                  # cm⁻³ — a marginal residual mobile-Na feed (walks V_t down ~0.28 V)
N_A = 1.0e17                   # cm⁻³ — channel doping
T_OX_UM = 0.02                 # µm — a 20 nm gate oxide (the mobile-ion-sensitive thin regime)
GATE = "n+poly"
CL_PERCENTS = np.linspace(0.0, 6.0, 121)   # ambient Cl % sweep (0 = pre-HCl period)
CL_MARKS = (0.0, 1.0, 3.0, 6.0)            # annotated points

# --- §B HP recipe: a thick wet field/isolation oxide, swept over pressure ------------------------ #
X_FIELD_UM = 0.5               # µm — a thick isolation field oxide (parabolic regime; where 1/P bites)
HP_AMBIENT = "wet"
HP_T = 1050.0                  # °C — the field-oxide temperature at 1 atm
HP_DOPANT = "B"               # the underlying profile whose collateral drive-in is charged
PRESSURES = np.array([1.0, 2.0, 5.0, 10.0, 20.0])   # atm (Razouk–Lie–Deal ran 5–20 atm)
HP_T_REDUCTION_P = 20.0        # atm — the pressure for the flagged T-reduction worked example

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-oxidation-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-oxidation-history.png"


@dataclass(frozen=True)
class OxidationHistoryResult:
    """The A3 bundle the figure and summary consume."""

    # §A HCl — Q_ox→V_t recovery
    cl_percents: np.ndarray
    vt_vs_cl: np.ndarray              # V_t (V) vs Cl %
    vt_pre_hcl: float                 # V_t at Cl = 0 (the full Na penalty)
    vt_clean: float                   # V_t at Q_ox = 0 (the ideal-oxide ceiling)
    cl_marks: tuple[oh.HClOxidation, ...]
    # §B HP — collateral budget vs pressure
    pressures: np.ndarray
    t_ox_hours: np.ndarray            # oxidation time (hr) vs P — the 1/P law
    budget_vs_P: np.ndarray           # collateral ∫D dt (cm²) vs P at fixed T
    budget_1atm: float
    # §B HP — the flagged T-reduction worked example
    T_reduced: float                  # °C to grow the same oxide in the same time at HP_T_REDUCTION_P
    budget_T_reduced: float           # cm² collateral budget at the reduced T
    t_field_hours: float              # the fixed process time (the 1-atm grow time)


def compute() -> OxidationHistoryResult:
    """Run both period modes → :class:`OxidationHistoryResult`."""
    # §A — sweep Cl %, read V_t off the existing device model
    vt = np.array([oh.hcl_oxidation(N_NA, pct, N_A=N_A, t_ox_um=T_OX_UM, gate=GATE).device.V_t
                   for pct in CL_PERCENTS])
    marks = tuple(oh.hcl_oxidation(N_NA, pct, N_A=N_A, t_ox_um=T_OX_UM, gate=GATE) for pct in CL_MARKS)
    vt_clean = oh.hcl_oxidation(0.0, 0.0, N_A=N_A, t_ox_um=T_OX_UM, gate=GATE).device.V_t  # Q_ox = 0

    # §B — sweep pressure at fixed T; the exact 1/P time & collateral budget
    hp = [oh.hp_oxidation(X_FIELD_UM, dopant=HP_DOPANT, ambient=HP_AMBIENT, T_celsius=HP_T,
                          pressure_atm=P) for P in PRESSURES]
    t_hours = np.array([h.t_ox_hours for h in hp])
    budget = np.array([h.budget for h in hp])

    # §B — the flagged T-reduction worked example: same oxide, same 1-atm time, at HP_T_REDUCTION_P
    t_field = hp[0].t_ox_hours
    T_red = oh.temperature_for_same_oxide(X_FIELD_UM, ambient=HP_AMBIENT, t_hours=t_field,
                                          pressure_atm=HP_T_REDUCTION_P)
    budget_red = oh.collateral_diffusion_budget(HP_DOPANT, T_red, t_field)

    return OxidationHistoryResult(
        cl_percents=CL_PERCENTS, vt_vs_cl=vt, vt_pre_hcl=float(vt[0]), vt_clean=vt_clean,
        cl_marks=marks,
        pressures=PRESSURES, t_ox_hours=t_hours, budget_vs_P=budget, budget_1atm=float(budget[0]),
        T_reduced=T_red, budget_T_reduced=budget_red, t_field_hours=t_field,
    )


def print_summary(r: OxidationHistoryResult) -> None:
    """Print the A3 story — the two period oxidation walls, on V_t and on the ∫D dt budget."""
    print("\nHistorical-modes A3: HCl gettering & high-pressure oxidation "
          "(two period ambients, two observables)\n")

    print("  §A  HCl / chlorine gettering → the Na→Q_ox→V_t chain (Cl = 0 is the pre-HCl period):")
    for h in r.cl_marks:
        tag = "  ← pre-HCl (full mobile-ion penalty)" if h.chlorine_percent == 0.0 else ""
        print(f"    Cl = {h.chlorine_percent:>4.1f}%  gettered {h.gettered_fraction*100:>4.1f}%  "
              f"Q_ox = {h.Q_ox:.2e} C/cm²  →  V_t = {h.device.V_t:.4f} V{tag}")
    print(f"    → HCl recovers V_t {r.vt_pre_hcl:.4f} → {r.cl_marks[-1].device.V_t:.4f} V, back toward the "
          f"clean-oxide {r.vt_clean:.4f} V (Q_ox = 0).")
    print(f"    [static mobile-ion offset, not the drift dynamics; gettering curve FLAGGED]\n")

    print(f"  §B  High-pressure oxidation → the collateral ∫D dt budget (a {X_FIELD_UM} µm {HP_AMBIENT} "
          f"field oxide, {HP_DOPANT} under it, {HP_T:.0f} °C):")
    for P, t, b in zip(r.pressures, r.t_ox_hours, r.budget_vs_P):
        print(f"    P = {P:>4.0f} atm   grow time = {t*60.0:>6.1f} min   collateral ∫D dt = {b:.3e} cm²   "
              f"(×{r.budget_1atm/b:.0f} less than 1 atm)")
    print(f"    → fixed-T: both time and budget scale EXACTLY as 1/P (tight, all regimes).")
    print(f"    → trading P for TEMPERATURE (same {X_FIELD_UM} µm in the same {r.t_field_hours*60:.0f} min "
          f"at {HP_T_REDUCTION_P:.0f} atm): T {HP_T:.0f} → {r.T_reduced:.0f} °C, collateral budget "
          f"{r.budget_1atm:.2e} → {r.budget_T_reduced:.2e} cm² (×{r.budget_1atm/r.budget_T_reduced:.0f} "
          f"less — the Arrhenius win; FLAGGED).\n")


def save_figure(r: OxidationHistoryResult) -> Path:
    """Render and save the A3 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: HCl gettering recovers V_t toward the clean-oxide value --------------------------- #
    ax = axes[0]
    ax.plot(r.cl_percents, r.vt_vs_cl, "-", color="tab:blue", lw=2.2, label="V_t after HCl gettering")
    ax.axhline(r.vt_clean, color="0.4", ls="--", lw=1.4, label=f"clean oxide (Q_ox=0): {r.vt_clean:.3f} V")
    ax.axhline(r.vt_pre_hcl, color="tab:red", ls=":", lw=1.4,
               label=f"pre-HCl (Cl=0): {r.vt_pre_hcl:.3f} V")
    for h in r.cl_marks:
        ax.plot(h.chlorine_percent, h.device.V_t, "o", color="tab:blue", ms=5)
    ax.annotate("pre-HCl period:\nmobile Na walks V_t down", xy=(0.0, r.vt_pre_hcl),
                xytext=(1.2, r.vt_pre_hcl - 0.02), fontsize=7.6, color="tab:red", va="top",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1))
    ax.fill_between(r.cl_percents, r.vt_vs_cl, r.vt_pre_hcl, color="tab:blue", alpha=0.06)
    ax.set_xlabel("chlorine in the oxidizing ambient  (%)")
    ax.set_ylabel("threshold voltage  V_t  (V)")
    ax.set_xlim(0.0, 6.0)
    ax.set_title(f"HCl gettering: mobile-Na V_t recovery (N_Na = {N_NA:.0e} cm⁻³, {T_OX_UM*1e3:.0f} nm gate)",
                 fontsize=9.5)
    ax.legend(fontsize=7.6, loc="lower right")
    ax.text(0.03, 0.90, "gettering curve FLAGGED;\nstatic offset, not drift dynamics",
            transform=ax.transAxes, ha="left", va="top", fontsize=7, color="0.4")

    # --- Right: the collateral ∫D dt budget collapses with pressure ------------------------------ #
    ax = axes[1]
    ax.loglog(r.pressures, r.budget_vs_P, "o-", color="tab:green", lw=2.2, ms=6,
              label="fixed-T budget  ∝ 1/P  (exact)")
    # the ideal 1/P reference line (visually confirms the exact scaling)
    ax.loglog(r.pressures, r.budget_1atm / r.pressures, "--", color="0.5", lw=1.2,
              label="1/P reference")
    # the flagged T-reduction worked example (same oxide, same time, lower T)
    ax.axhline(r.budget_T_reduced, color="tab:purple", ls=":", lw=1.6)
    ax.annotate(
        f"trade P for T at {HP_T_REDUCTION_P:.0f} atm:\n{HP_T:.0f}→{r.T_reduced:.0f} °C, "
        f"×{r.budget_1atm/r.budget_T_reduced:.0f} less budget\n(Arrhenius win — FLAGGED)",
        xy=(HP_T_REDUCTION_P, r.budget_T_reduced),
        xytext=(1.4, r.budget_T_reduced * 1.7), fontsize=7.4, color="tab:purple", va="bottom",
        arrowprops=dict(arrowstyle="->", color="tab:purple", lw=1))
    ax.set_xlabel("oxidation pressure  P  (atm)")
    ax.set_ylabel("collateral dopant budget  ∫D dt  (cm²)")
    ax.set_title(f"High-pressure oxidation: same {X_FIELD_UM} µm {HP_AMBIENT} oxide, less thermal budget",
                 fontsize=9.5)
    ax.legend(fontsize=7.8, loc="upper right")
    ax.grid(True, which="both", alpha=0.2)

    fig.suptitle("Historical-modes A3 — period oxidation ambients: HCl getters mobile Na (V_t), "
                 "pressure buys thermal budget (∫D dt)", fontsize=11.5)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ⁻³, →, ∫ on legacy codepages

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
