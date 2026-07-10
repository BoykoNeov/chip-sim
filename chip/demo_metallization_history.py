"""The historical-modes B6 banked artifact: aluminium junction spiking → the shallow-junction short.

The period contact metallization (pure aluminium) run against the observable it broke — the reverse
leakage :mod:`chip.lifetime` computes — showing *why the shallow, implant-era junction forced Al–Si
alloys and diffusion barriers*. One figure, two panels:

  * **Left — the headline coupling: shorted-area fraction vs junction depth.** At a fixed sinter, the
    fraction of the junction a spike shorts (:func:`chip.metallization_history.shorted_area_fraction`,
    the graded yield-loss observable) climbs steeply as ``x_j`` shrinks. **Pure Al** kills the shallow
    implant-era junction; the **Al–Si** alloy suppresses it; the **barrier** is flat at zero (the seam).
    *The shallower the junction — which implant enables — the worse the spike.*
  * **Right — the device consequence + the seam: leakage vs sinter temperature.** At a shallow
    ``x_j``, the aggregate reverse leakage (log axis) rises catastrophically for pure Al as the sinter
    heats (more Si dissolves — :func:`chip.metallization_history.silicon_solubility_in_al`), while the
    **barrier sits exactly on the clean lifetime baseline** at every temperature (the byte-for-bit seam).
    A shorted contact is dead — it blows the leakage spec by many decades.

Tight legs: the seam (``scheme="barrier"`` → :func:`chip.lifetime.generation_leakage_density`
bit-for-bit) + the sign/topology (shorts the *shallower* junction; monotone in T / t_Al). Flagged: the
Si-in-Al solubility curve, the spike-concentration lump κ, the exponential spike-depth shape, the
ohmic-short density (see :mod:`chip.metallization_history`). Run headless:

    python -m chip.demo_metallization_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import metallization_history as mh
from . import lifetime as lt

# --- Recipe: a metal-1 line sintered on a diffused junction ------------------------------------- #
AL_THICK_UM = 0.8              # µm — a metal-1 aluminium line (the Si sink)
N_A = 1.0e17                   # cm⁻³ — substrate the intact junction leakage reads
SCHEMES = ("Al", "Al-Si", "barrier")

# Left panel — the x_j coupling at a fixed sinter
SINTER_T = 450.0               # °C — a typical sub-eutectic contact sinter
X_J_SWEEP = np.linspace(0.05, 1.2, 160)     # µm — implant-shallow → predep-deep
X_J_IMPLANT = 0.15             # µm — an implant-era shallow junction (the vulnerable regime)
X_J_PREDEP = 0.6               # µm — an old deep predep-era junction (safer)

# Right panel — the T dependence at a fixed shallow junction
X_J_SHALLOW = 0.2              # µm — the shallow junction the T-sweep sits on
T_SWEEP = np.linspace(300.0, 577.0, 160)    # °C — up to the 577 °C eutectic
LEAK_SPEC_NA = 1.0             # nA/cm² — an illustrative reverse-leakage spec line

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-metallization-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-metallization-history.png"


@dataclass(frozen=True)
class MetallizationHistoryResult:
    """The B6 bundle the figure and summary consume."""

    schemes: tuple[str, ...]
    # left — shorted-area fraction vs x_j (fixed sinter T)
    x_j_um: np.ndarray
    f_short_vs_xj: dict[str, np.ndarray]        # scheme → f_short(%) vs x_j
    # right — leakage vs sinter T (fixed shallow x_j)
    T_celsius: np.ndarray
    j_leak_vs_T: dict[str, np.ndarray]          # scheme → j_leak(nA/cm²) vs T
    baseline_nA: float                          # the clean intact leakage (the seam floor)
    # narrative marks
    implant_marks: dict[str, mh.MetalSpiking]   # scheme → spiking at the shallow implant junction
    predep_marks: dict[str, mh.MetalSpiking]    # scheme → spiking at the deep predep junction


def compute() -> MetallizationHistoryResult:
    """Run the period metallization against the two contrasts → :class:`MetallizationHistoryResult`."""
    f_short_vs_xj: dict[str, np.ndarray] = {}
    j_leak_vs_T: dict[str, np.ndarray] = {}
    implant_marks: dict[str, mh.MetalSpiking] = {}
    predep_marks: dict[str, mh.MetalSpiking] = {}

    for s in SCHEMES:
        f_short_vs_xj[s] = np.array([
            mh.metal_spiking(xj, scheme=s, T_celsius=SINTER_T, al_thickness_um=AL_THICK_UM,
                             N_A=N_A).f_short_percent for xj in X_J_SWEEP])
        j_leak_vs_T[s] = np.array([
            mh.metal_spiking(X_J_SHALLOW, scheme=s, T_celsius=T, al_thickness_um=AL_THICK_UM,
                             N_A=N_A).j_leak_nA_cm2 for T in T_SWEEP])
        implant_marks[s] = mh.metal_spiking(X_J_IMPLANT, scheme=s, T_celsius=SINTER_T,
                                            al_thickness_um=AL_THICK_UM, N_A=N_A)
        predep_marks[s] = mh.metal_spiking(X_J_PREDEP, scheme=s, T_celsius=SINTER_T,
                                           al_thickness_um=AL_THICK_UM, N_A=N_A)

    # the clean intact leakage (the byte-for-bit seam floor the barrier reproduces)
    baseline = lt.device_leakage(None, N_A).j_leak * 1.0e9      # nA/cm²

    return MetallizationHistoryResult(
        schemes=SCHEMES, x_j_um=X_J_SWEEP, f_short_vs_xj=f_short_vs_xj,
        T_celsius=T_SWEEP, j_leak_vs_T=j_leak_vs_T, baseline_nA=baseline,
        implant_marks=implant_marks, predep_marks=predep_marks,
    )


def print_summary(r: MetallizationHistoryResult) -> None:
    """Print the B6 story — pure Al shorts the shallow junction; alloy/barrier clear the wall."""
    print("\nHistorical-modes B6: aluminium junction spiking (the shallow-junction short)\n")
    print(f"  Metal-1 Al line ({AL_THICK_UM} µm) sintered at {SINTER_T:.0f} °C; the shallower x_j"
          f" (implant enables) the worse the spike:")
    print(f"\n    at an implant-era x_j = {X_J_IMPLANT} µm (shallow):")
    for s in r.schemes:
        m = r.implant_marks[s]
        print(f"      {s:<8} d_spike = {m.d_spike_um:.3f} µm  shorted area = {m.f_short_percent:5.1f}%"
              f"  j_leak = {m.j_leak_nA_cm2:.2e} nA/cm²")
    print(f"\n    at a predep-era x_j = {X_J_PREDEP} µm (deep):")
    for s in r.schemes:
        m = r.predep_marks[s]
        print(f"      {s:<8} d_spike = {m.d_spike_um:.3f} µm  shorted area = {m.f_short_percent:5.1f}%"
              f"  j_leak = {m.j_leak_nA_cm2:.2e} nA/cm²")
    print(f"\n    → pure Al kills the shallow junction; Al–Si suppresses it; the barrier is flat at the")
    print(f"      clean baseline {r.baseline_nA:.2e} nA/cm² (the byte-for-bit seam).")
    print(f"    [Si-in-Al solubility, spike-concentration κ, ohmic-short density all FLAGGED; the graded")
    print(f"     shorted-area fraction + the barrier seam are the tight legs]\n")


def save_figure(r: MetallizationHistoryResult) -> Path:
    """Render and save the B6 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    colors = {"Al": "tab:red", "Al-Si": "tab:orange", "barrier": "tab:green"}
    labels = {"Al": "pure Al (period)", "Al-Si": "Al–Si alloy (fix #1)", "barrier": "barrier metal (modern)"}

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: the coupling — shorted-area fraction climbs as x_j shrinks ------------------------- #
    ax = axes[0]
    for s in r.schemes:
        ax.plot(r.x_j_um, r.f_short_vs_xj[s], "-", color=colors[s], lw=2.2, label=labels[s])
    ax.axvspan(X_J_SWEEP[0], 0.3, color="tab:red", alpha=0.05)
    ax.axvline(X_J_IMPLANT, color="0.5", ls=":", lw=1.2)
    ax.axvline(X_J_PREDEP, color="0.5", ls=":", lw=1.2)
    ax.annotate("implant-era\nshallow x_j\n(vulnerable)", xy=(X_J_IMPLANT, 55), fontsize=7.4,
                color="tab:red", ha="center", va="center")
    ax.annotate("predep-era\ndeep x_j\n(safer)", xy=(X_J_PREDEP, 55), fontsize=7.4,
                color="0.4", ha="center", va="center")
    ax.set_xlabel("junction depth  x_j  (µm)")
    ax.set_ylabel("shorted junction area  f_short  (%)")
    ax.set_xlim(X_J_SWEEP[0], X_J_SWEEP[-1])
    ax.set_ylim(0, 100)
    ax.set_title(f"Spiking shorts the shallower junction ({AL_THICK_UM} µm Al, {SINTER_T:.0f} °C sinter)",
                 fontsize=9.5)
    ax.legend(fontsize=7.8, loc="upper right")
    ax.text(0.97, 0.55, "graded: shorted-AREA\nfraction (yield gradient)", transform=ax.transAxes,
            ha="right", va="top", fontsize=7, color="0.4")

    # --- Right: the device consequence + the seam — leakage vs sinter T --------------------------- #
    ax = axes[1]
    for s in r.schemes:
        ax.semilogy(r.T_celsius, r.j_leak_vs_T[s], "-", color=colors[s], lw=2.2, label=labels[s])
    ax.axhline(r.baseline_nA, color="0.4", ls="--", lw=1.4,
               label=f"clean baseline (seam): {r.baseline_nA:.1e} nA/cm²")
    ax.axhline(LEAK_SPEC_NA, color="tab:blue", ls="-.", lw=1.2, label=f"leakage spec ({LEAK_SPEC_NA:g} nA/cm²)")
    ax.axvline(AL_SI_EUT := mh.AL_SI_EUTECTIC_CELSIUS, color="0.6", ls=":", lw=1.0)
    ax.text(AL_SI_EUT - 4, r.baseline_nA * 4, "577 °C Al–Si eutectic", rotation=90, fontsize=7,
            color="0.5", ha="right", va="bottom")
    ax.set_xlabel("contact sinter temperature  (°C)")
    ax.set_ylabel("reverse junction leakage  j_leak  (nA/cm²)")
    ax.set_xlim(r.T_celsius[0], r.T_celsius[-1])
    ax.set_title(f"Leakage vs sinter T at a shallow x_j = {X_J_SHALLOW} µm (barrier = the seam floor)",
                 fontsize=9.5)
    ax.legend(fontsize=7.4, loc="lower left")

    fig.suptitle("Historical-modes B6 — aluminium junction spiking: pure Al shorts the shallow "
                 "(implant-era) junction; Al–Si and barrier metals clear the wall", fontsize=11)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ⁻³, →, ° on legacy codepages

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
