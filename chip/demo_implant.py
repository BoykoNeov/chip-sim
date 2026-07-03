"""The §5 banked artifact: the buried peak a predep cannot make — the predep-vs-implant contrast.

Ion implantation's licence, on one figure. The **same areal dose ``Q``** is laid into silicon two ways:

  * **thermal predeposition** — a constant-source ``erfc`` (:func:`chip.diffusion_dopant.predeposit`),
    whose maximum is pinned **at the surface** and which falls monotonically with depth. It is physically
    incapable of putting the dopant peak below the surface.
  * **ion implantation** — a buried Gaussian (:func:`chip.diffusion_dopant.implant_profile`) whose peak
    sits at the projected range ``R_p(energy)`` (:func:`chip.diffusion_dopant.range_statistics`), rising
    from the surface toward it — a **retrograde** shape.

Same dose, opposite topology: that buried peak is the observable predep cannot produce *at all* (not a
redundant second route to the same junction) — the discriminator that licenses the regime, and the
historical step (production silicon, early 1970s) that modernised the ~1968 thermal-predep planar line
this simulator otherwise is. The identical sealed drive-in then redistributes either initial condition
(no new solver); the implant's peak stays buried.

The device payoff (the honest de-fake): a shallow **acceptor** V_t-adjust implant of the same dose shifts
the threshold by ``ΔV_t = +q·Q/C_ox`` (:func:`chip.device.vt_adjust_shift`) — the real, dose-controlled
source of the threshold adjust the device model previously **faked** with a uniform substrate offset.

Run headless (saves the figure, prints the flow):

    python -m chip.demo_implant
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import device as dev
from . import diffusion_dopant as dd

# --- The contrast recipe: one dose Q, laid two ways ------------------------- #
SPECIES = "B"                  # boron — the canonical acceptor V_t-adjust / retrograde implant
DOSE = 5.0e11                  # cm⁻² — a realistic V_t-adjust dose (predep would lay this at the surface)
IMPLANT_ENERGY_KEV = 15.0      # keV → a shallow buried peak (R_p ≈ 0.05 µm), the realistic V_t-adjust energy:
                               # R_p + ΔR_p (~0.07 µm) sits WITHIN the threshold depletion width W (~0.10 µm),
                               # so the sheet-charge ΔV_t = q·Q/C_ox is coherent (dose inside the depletion
                               # region — the shallow-sheet regime; a deeper implant would strain it → the
                               # deferred deep/retrograde effective-N_A slice).
LENGTH_UM = 1.5                # substrate depth domain
N_CELLS = 600

PREDEP = (900.0, 30.0)         # the matched predep (°C, min) — N_s tuned so its dose equals DOSE
DRIVEIN = (1000.0, 30.0)       # the shared drive-in schedule (°C, min)

# The device the V_t-adjust implant lands in (the coherent MIT-style n-MOSFET)
CHANNEL_N_A = 1.0e17           # cm⁻³ — p-type channel
T_OX_UM = 0.015                # µm — 15 nm gate oxide (the MIT worked-example device)
GATE = "n+poly"

PEARSON_ENERGY_KEV = 120.0     # keV — a device energy clearly in boron's NEGATIVE-skew regime (slice 2):
                               # the sub-keV crossover to positive skew is far below, so the surface tail
                               # and deeper-than-R_p peak read cleanly.

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-implant.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-implant.png"
DOCS_FIGURE_PEARSON = _REPO_ROOT / "docs" / "figures" / "chip-implant-pearson.png"
OUTPUT_FIGURE_PEARSON = _REPO_ROOT / "outputs" / "chip-implant-pearson.png"


@dataclass(frozen=True)
class ContrastResult:
    """The predep-vs-implant contrast bundle the figure and summary consume."""

    x_um: np.ndarray
    predep_ic: np.ndarray          # as-deposited erfc (surface-peaked)
    implant_ic: np.ndarray         # as-implanted buried Gaussian
    predep_drivein: np.ndarray     # erfc after the drive-in
    implant_drivein: np.ndarray    # buried Gaussian after the drive-in
    R_p_um: float
    dRp_um: float
    dose_predep: float             # the erfc's grid dose (matched to DOSE)
    dose_implant: float            # the buried Gaussian's grid dose (Q, minus surface truncation)
    mos_base: dev.MOSDevice        # no adjust implant
    mos_adjust: dev.MOSDevice      # + the acceptor V_t-adjust implant


def compute() -> ContrastResult:
    """Run the same-dose predep-vs-implant contrast end to end → :class:`ContrastResult` (no plotting)."""
    grid = dd.uniform_grid(LENGTH_UM * dd.CM_PER_UM, N_CELLS)

    # Predep matched to DOSE: choose the surface concentration N_s so ∫ erfc = DOSE (the predep_dose
    # identity Q = 1.128·N_s·√(Dt)), then run the real constant-source predep at that N_s.
    D_predep = dd.diffusivity(SPECIES, PREDEP[0])
    t_predep = PREDEP[1] * 60.0
    N_s = DOSE / ((2.0 / math.sqrt(math.pi)) * math.sqrt(D_predep * t_predep))
    predep, predep_drivein = dd.two_step(
        SPECIES, T_predep=PREDEP[0], t_predep_min=PREDEP[1], N_surface=N_s,
        T_drivein=DRIVEIN[0], t_drivein_min=DRIVEIN[1], length_um=LENGTH_UM, n_cells=N_CELLS,
    )

    # Implant of the SAME dose — the only difference is the topology (buried vs surface-peaked).
    implant = dd.Implant(dose=DOSE, energy_keV=IMPLANT_ENERGY_KEV, species=SPECIES)
    implant_ic, implant_drivein = dd.two_step(
        SPECIES, implant=implant,
        T_drivein=DRIVEIN[0], t_drivein_min=DRIVEIN[1], length_um=LENGTH_UM, n_cells=N_CELLS,
    )
    R_p, dRp = implant.range_statistics()

    # The device payoff: the acceptor V_t-adjust implant raises V_t by q·Q/C_ox (the honest de-fake).
    mos_base = dev.threshold_voltage(CHANNEL_N_A, T_OX_UM, gate=GATE)
    mos_adjust = dev.threshold_voltage(
        CHANNEL_N_A, T_OX_UM, gate=GATE, implant_dose=DOSE, implant_kind=dd.DOPANTS[SPECIES].kind,
    )

    return ContrastResult(
        x_um=grid.centers / dd.CM_PER_UM,
        predep_ic=predep.N, implant_ic=implant_ic.N,
        predep_drivein=predep_drivein.N, implant_drivein=implant_drivein.N,
        R_p_um=R_p / dd.CM_PER_UM, dRp_um=dRp / dd.CM_PER_UM,
        dose_predep=predep.dose, dose_implant=implant_ic.dose,
        mos_base=mos_base, mos_adjust=mos_adjust,
    )


def print_summary(r: ContrastResult) -> None:
    """Print the same-dose contrast story — the demo's payoff in text."""
    i_predep = int(np.argmax(r.predep_ic))
    i_implant = int(np.argmax(r.implant_ic))
    print("\nIon implantation §5: the buried peak a predep cannot make (same dose, laid two ways)\n")
    print(f"  dose Q = {DOSE:.2e} cm⁻²  ({SPECIES}, {IMPLANT_ENERGY_KEV:.0f} keV implant)")
    print(f"  predep   erfc  : grid dose {r.dose_predep:.2e} cm⁻², peak at x = "
          f"{r.x_um[i_predep]:.3f} µm  (AT THE SURFACE, falls with depth)")
    print(f"  implant  Gauss : grid dose {r.dose_implant:.2e} cm⁻², peak at x = "
          f"{r.x_um[i_implant]:.3f} µm  (BURIED at R_p = {r.R_p_um:.3f} µm, ΔR_p = {r.dRp_um:.3f} µm)")
    print(f"  → the implant peak is buried {r.x_um[i_implant]:.3f} µm below the surface — the observable "
          f"a monotone erfc cannot produce.\n")
    b, a = r.mos_base, r.mos_adjust
    W_um = (b.Q_dep / (dev.Q_ELEMENTARY * b.N_A)) / dd.CM_PER_UM   # threshold depletion width (µm)
    print(f"  V_t-adjust : base V_t = {b.V_t:.3f} V  →  + {SPECIES} acceptor implant "
          f"({DOSE:.1e} cm⁻²)  →  V_t = {a.V_t:.3f} V   (ΔV_t = {a.vt_adjust:+.3f} V = +q·Q/C_ox)")
    print(f"  → the honest, dose-controlled threshold adjust (was faked by a uniform substrate offset).")
    print(f"  → coherence: R_p + ΔR_p = {r.R_p_um + r.dRp_um:.3f} µm < depletion width W = {W_um:.3f} µm "
          f"→ the dose sits WITHIN the depletion region (the shallow-sheet regime the shift assumes).\n")


# --------------------------------------------------------------------------- #
# Slice 2 — the Pearson-IV skew: the SAME implant, symmetric Gaussian vs the real skewed profile
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PearsonResult:
    """The Gaussian-vs-Pearson-IV skew bundle (slice 2)."""

    x_um: np.ndarray
    gaussian: np.ndarray           # slice-1 symmetric two-moment profile (peak at R_p)
    pearson: np.ndarray            # slice-2 four-moment Pearson-IV (skewed: peak deeper, surface tail)
    R_p_um: float
    mode_um: float                 # the Pearson-IV mode R_p + b1 (deeper than R_p for boron)
    gamma: float                   # skewness (negative for boron)
    beta: float                    # kurtosis


def pearson_compute() -> PearsonResult:
    """The same boron implant as a symmetric Gaussian vs the real skewed Pearson-IV → :class:`PearsonResult`."""
    grid = dd.uniform_grid(LENGTH_UM * dd.CM_PER_UM, 4000)     # fine: the mode shift is ~0.1·ΔR_p
    gauss = dd.Implant(dose=DOSE, energy_keV=PEARSON_ENERGY_KEV, species=SPECIES)                    # gaussian
    skew = dd.Implant(dose=DOSE, energy_keV=PEARSON_ENERGY_KEV, species=SPECIES, shape="pearson")   # Pearson-IV
    R_p, dRp, gamma, beta = skew.moments()
    b0, b1, b2 = dd._pearson4_coeffs(dRp, gamma, beta)
    return PearsonResult(
        x_um=grid.centers / dd.CM_PER_UM,
        gaussian=dd.implant_profile(grid.centers, gauss),
        pearson=dd.implant_profile(grid.centers, skew),
        R_p_um=R_p / dd.CM_PER_UM, mode_um=(R_p + b1) / dd.CM_PER_UM,
        gamma=gamma, beta=beta,
    )


def print_pearson_summary(p: PearsonResult) -> None:
    """Print the slice-2 skew story — the asymmetry the symmetric Gaussian misses."""
    print("Ion implantation §5 (slice 2): the Pearson-IV skew — boron's real asymmetric profile\n")
    print(f"  same implant ({SPECIES}, {PEARSON_ENERGY_KEV:.0f} keV, Q = {DOSE:.1e} cm⁻²), two shapes:")
    print(f"  gaussian (slice 1): symmetric, peak AT R_p = {p.R_p_um:.4f} µm")
    print(f"  pearson  (slice 2): skewness γ = {p.gamma:+.3f} (< 0), kurtosis β = {p.beta:.2f}  →  peak "
          f"DEEPER at {p.mode_um:.4f} µm, with a longer tail toward the surface")
    print(f"  → light-ion boron backscatters to 'skew the profile up' (Plummer §8): the mode shifts "
          f"{(p.mode_um - p.R_p_um) * 1e3:+.1f} nm past R_p — the asymmetry a symmetric Gaussian cannot carry.\n")


def save_pearson_figure(p: PearsonResult) -> Path:
    """Render and save the slice-2 Gaussian-vs-Pearson-IV skew artifact (needs the ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.6))
    ax.plot(p.x_um, p.gaussian, color="tab:blue", lw=2, ls="--", label="Gaussian (slice 1, symmetric)")
    ax.plot(p.x_um, p.pearson, color="tab:red", lw=2, label=f"Pearson-IV (slice 2, γ = {p.gamma:+.2f})")
    ax.axvline(p.R_p_um, color="0.5", ls=":", lw=1, label=f"$R_p$ = {p.R_p_um:.3f} µm")
    ax.axvline(p.mode_um, color="tab:red", ls=":", lw=1, label=f"Pearson mode = {p.mode_um:.3f} µm (deeper)")
    ax.set_xlabel("depth  x  (µm)")
    ax.set_ylabel("concentration  N(x)  (cm⁻³)")
    ax.set_xlim(0.0, min(0.9, p.x_um[-1]))
    ax.set_title(f"§5 slice 2 — boron {PEARSON_ENERGY_KEV:.0f} keV: the Pearson-IV skew "
                 f"(surface tail, peak past $R_p$)", fontsize=10)
    ax.legend(fontsize=8)
    # Honesty caption: the CITED content is the skew SIGN (γ<0 → deeper mode + surface tail); the taller
    # peak is the kurtosis β = 4.5, a house-calibrated value PINNED into the type-IV branch (real boron
    # β ≈ 3 is out of region) — a flagged magnitude, not a measured one.
    ax.text(0.98, 0.60, f"γ, β flagged (β={p.beta:.1f} pinned\ninto the type-IV branch);\nthe SIGN of γ is the cited part",
            transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color="0.35")
    fig.tight_layout()
    for target in (DOCS_FIGURE_PEARSON, OUTPUT_FIGURE_PEARSON):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE_PEARSON


def save_figure(r: ContrastResult) -> Path:
    """Render and save the predep-vs-implant contrast artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))

    for ax, predep, implant, title in (
        (axes[0], r.predep_ic, r.implant_ic, "As-deposited / as-implanted (same dose Q)"),
        (axes[1], r.predep_drivein, r.implant_drivein, "After the identical drive-in"),
    ):
        ax.plot(r.x_um, predep, color="tab:orange", lw=2, label="predep (erfc)")
        ax.plot(r.x_um, implant, color="tab:blue", lw=2, label="implant (buried Gaussian)")
        ax.axvline(r.R_p_um, color="tab:blue", ls=":", lw=1, alpha=0.7, label=f"$R_p$ = {r.R_p_um:.2f} µm")
        ax.set_xlabel("depth  x  (µm)")
        ax.set_ylabel("concentration  N(x)  (cm⁻³)")
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0.0, min(0.4, r.x_um[-1]))
        ax.legend(fontsize=8)

    ax = axes[2]
    b, a = r.mos_base, r.mos_adjust
    bars = ax.bar(["base", f"+ {SPECIES} adjust\nimplant"], [b.V_t, a.V_t],
                  color=["tab:gray", "tab:blue"])
    ax.set_ylabel("threshold voltage  $V_t$  (V)")
    ax.set_title(f"V_t-adjust: ΔV_t = {a.vt_adjust:+.3f} V = +q·Q/C_ox", fontsize=10)
    ax.bar_label(bars, fmt="%.3f V", fontsize=9)
    ax.margins(y=0.15)

    fig.suptitle("Ion implantation §5 — the buried peak a predep cannot make", fontsize=12)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ⁻³, φ, → on legacy codepages

    r = compute()
    print_summary(r)
    p = pearson_compute()
    print_pearson_summary(p)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
        saved_p = save_pearson_figure(p)
        print(f"Figure saved → {saved_p.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figures: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
