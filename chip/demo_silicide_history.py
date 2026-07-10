"""The historical-modes B7 banked artifact: silicide / contact resistance — the two-term series-R (F2).

The period contact metallization (direct aluminium on the diffused source/drain) run against the
observable it limited — the drive current ``I_Dsat`` the journey already computes through the
``R_series_ohm`` source-degeneration seam — showing *why self-aligned silicide (salicide) recovered the
drive, and why the contact — not the access resistance — became the next-era frontier*. One figure,
two panels:

  * **Left — the era comparison + the bottleneck flip.** The source series resistance ``R_series``
    decomposed into its two terms (access + TLM contact, :func:`chip.contact_resistance.series_resistance`)
    for **direct Al** vs **salicide**. Direct Al is **access-limited** (the diffused sheet dominates);
    salicide shunts that sheet ~12× so **access collapses while the contact term barely follows** — the
    bottleneck **flips from access to contact**. The recovered ``I_Dsat`` (fed through
    :func:`chip.device.saturation_current`) is annotated on each bar: a lopsided recovery a scalar
    "multiply R_series by 0.3" cannot produce.
  * **Right — the discriminator: different ``R_sh`` exponents (why no scalar can fake it).** With ``ρ_c``
    **held fixed**, the two terms swept over the sheet-resistance shunt on log–log: **access ∝ R_sh¹**
    (slope 1) but **contact ∝ R_sh^p, p ≤ ½** (a shallower slope — √R_sh at long contacts, and
    ``R_sh``-*independent* at the scaled sub-micron contact this operating point uses). Because access is
    linear and contact sublinear, the contact's *share* of ``R_series`` **rises monotonically as the
    sheet falls** — the robust, ``ρ_c``-independent leg. The diffused (direct-Al) and silicide operating
    sheets are marked; the gap between the curves at the silicide sheet *is* the flip.

Tight legs: the seam (access-only :func:`chip.contact_resistance.access_resistance` = today's ``R_s·n_□``
byte-for-byte) + the sign/topology (access linear, contact sublinear ⇒ contact share rises as R_sh
falls). Flagged: the house contact length, per-scheme ``ρ_c`` and silicide sheet, the calibrated
operating point (see :mod:`chip.contact_resistance`). Run headless:

    python -m chip.demo_silicide_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import contact_resistance as cr
from . import device as dev

# --- Recipe: a wide-access MOSFET whose S/D is contacted direct-Al vs salicide ------------------- #
DIFFUSED_R_SH = 60.0           # Ω/□ — the diffused S/D sheet resistance (the inherited die.R_s)
N_SQUARES = 1.0                # □ — a wide access run (n_□ = L_access/W); the stated operating point
DEVICE_WIDTH_UM = 10.0         # µm — device width W (the TLM contact width)
SCHEMES = ("direct-Al", "salicide")

# The device the R_series degrades (a representative thin-oxide n-MOSFET, as chip.demo_device)
CHANNEL_N_A = 1.0e17           # cm⁻³ — p-type channel
T_OX_UM = 0.014                # µm — ~14 nm gate oxide
CHANNEL_L_UM = 0.35            # µm — printed gate length (sets W/L)
GATE = "n+poly"
OVERDRIVE_V = 1.0              # V_GS − V_t

# Right panel — the controlled exponent sweep (ρ_c held at the direct-Al value)
R_SH_SWEEP = np.logspace(np.log10(3.0), np.log10(120.0), 160)   # Ω/□ — silicide-thin → diffused-thick

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-silicide-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-silicide-history.png"


@dataclass(frozen=True)
class SilicideHistoryResult:
    """The B7 bundle the figure and summary consume."""

    schemes: tuple[str, ...]
    series: dict[str, cr.SeriesResistance]      # scheme → the decomposed R_series
    i_dsat_mA: dict[str, float]                 # scheme → the degraded drive current (mA)
    i_dsat_ideal_mA: float                      # the R_series = 0 ideal drive (the ceiling)
    # right — the controlled exponent sweep (ρ_c held)
    R_sh: np.ndarray
    R_access: np.ndarray                        # access ∝ R_sh¹
    R_contact: np.ndarray                       # contact ∝ R_sh^p, p ≤ ½ (ρ_c held)


def _i_dsat_mA(R_series_ohm: float) -> float:
    """The drive current (mA) of the representative device with source series resistance ``R_series_ohm``."""
    mos = dev.threshold_voltage(CHANNEL_N_A, T_OX_UM, gate=GATE, channel_length_um=CHANNEL_L_UM)
    return dev.saturation_current(
        mos, mos.V_t + OVERDRIVE_V, DEVICE_WIDTH_UM, R_series_ohm=R_series_ohm) * 1.0e3


def compute() -> SilicideHistoryResult:
    """Run the direct-Al → salicide contrast → :class:`SilicideHistoryResult`."""
    series = {s: cr.series_resistance(DIFFUSED_R_SH, N_SQUARES, DEVICE_WIDTH_UM, scheme=s)
              for s in SCHEMES}
    i_dsat = {s: _i_dsat_mA(series[s].R_series_ohm) for s in SCHEMES}
    i_ideal = _i_dsat_mA(0.0)

    # right panel — hold ρ_c at the direct-Al interface, sweep the sheet: expose the exponent gap
    rho_held = cr.RHO_C_DIRECT_AL
    R_access = np.array([cr.access_resistance(R, N_SQUARES) for R in R_SH_SWEEP])
    R_contact = np.array([cr.contact_resistance(rho_held, R, DEVICE_WIDTH_UM) for R in R_SH_SWEEP])

    return SilicideHistoryResult(
        schemes=SCHEMES, series=series, i_dsat_mA=i_dsat, i_dsat_ideal_mA=i_ideal,
        R_sh=R_SH_SWEEP, R_access=R_access, R_contact=R_contact,
    )


def print_summary(r: SilicideHistoryResult) -> None:
    """Print the B7 story — salicide collapses access; the contact becomes the new bottleneck."""
    print("\nHistorical-modes B7: silicide / contact resistance (the two-term series-R)\n")
    print(f"  Wide-access n-MOSFET (W = {DEVICE_WIDTH_UM:.0f} µm, n_□ = {N_SQUARES:.1f}, diffused"
          f" R_sh = {DIFFUSED_R_SH:.0f} Ω/□); ideal-contact I_Dsat = {r.i_dsat_ideal_mA:.3f} mA:\n")
    for s in r.schemes:
        sr = r.series[s]
        limit = "contact-limited" if sr.contact_limited else "access-limited "
        print(f"    {s:<10} R_access = {sr.R_access_ohm:6.1f} Ω  R_contact = {sr.R_contact_ohm:5.1f} Ω "
              f" R_series = {sr.R_series_ohm:6.1f} Ω  ({sr.contact_share*100:2.0f}% contact, {limit})"
              f"  I_Dsat = {r.i_dsat_mA[s]:.3f} mA")
    al, sil = r.series["direct-Al"], r.series["salicide"]
    print(f"\n    → salicide shunts the sheet {al.R_sh_ohm_sq / sil.R_sh_ohm_sq:.0f}× → access drops"
          f" {al.R_access_ohm / sil.R_access_ohm:.0f}× (linear); the contact barely follows the sheet"
          f" (only {al.R_contact_ohm / sil.R_contact_ohm:.1f}×, from the modest ρ_c improvement — the sheet")
    print(f"      shunt alone does ~nothing to it, see the right panel) → the bottleneck flips"
          f" access→contact; I_Dsat recovers {r.i_dsat_mA['salicide'] / r.i_dsat_mA['direct-Al']:.2f}×"
          f" (lopsided — a scalar can't fake it).")
    print(f"    [contact length, per-scheme ρ_c / silicide sheet FLAGGED; the seam (access-only) + the")
    print(f"     exponent gap (access linear, contact sublinear) are the tight legs]\n")


def save_figure(r: SilicideHistoryResult) -> Path:
    """Render and save the B7 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    colors = {"direct-Al": "tab:red", "salicide": "tab:green"}
    labels = {"direct-Al": "direct Al (period)", "salicide": "self-aligned TiSi₂ (modern)"}

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: the era comparison — stacked access + contact, the flip, the I_Dsat recovery --------- #
    ax = axes[0]
    x = np.arange(len(r.schemes))
    access = [r.series[s].R_access_ohm for s in r.schemes]
    contact = [r.series[s].R_contact_ohm for s in r.schemes]
    ax.bar(x, access, width=0.55, color="tab:blue", label="access  R_sh·n_□  (∝ R_sh, linear)")
    ax.bar(x, contact, width=0.55, bottom=access, color="tab:orange",
           label="contact  √(ρ_c·R_sh)/W·coth  (∝ R_sh^p, p ≤ ½)")
    for i, s in enumerate(r.schemes):
        sr = r.series[s]
        limit = "contact-limited" if sr.contact_limited else "access-limited"
        ax.text(i, sr.R_series_ohm + 3.0, f"I_Dsat = {r.i_dsat_mA[s]:.2f} mA\n({limit})",
                ha="center", va="bottom", fontsize=8, color=colors[s], fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([labels[s] for s in r.schemes], fontsize=9)
    ax.set_ylabel("source series resistance  R_series  (Ω)")
    ax.set_ylim(0, max(r.series[s].R_series_ohm for s in r.schemes) * 1.28)
    ax.set_title(f"Salicide collapses access; contact lingers → the bottleneck flips\n"
                 f"(diffused R_sh = {DIFFUSED_R_SH:.0f} Ω/□, n_□ = {N_SQUARES:.0f}, W = {DEVICE_WIDTH_UM:.0f} µm)",
                 fontsize=9.5)
    ax.legend(fontsize=7.6, loc="upper center")

    # --- Right: the discriminator — the two exponents (ρ_c held) ----------------------------------- #
    ax = axes[1]
    ax.loglog(r.R_sh, r.R_access, "-", color="tab:blue", lw=2.2, label="access ∝ R_sh¹ (slope 1)")
    ax.loglog(r.R_sh, r.R_contact, "-", color="tab:orange", lw=2.2,
              label="contact ∝ R_sh^p, p ≤ ½ (sublinear)")
    ax.axvline(DIFFUSED_R_SH, color="tab:red", ls=":", lw=1.3)
    ax.axvline(cr.R_SH_SALICIDE, color="tab:green", ls=":", lw=1.3)
    ax.annotate("diffused\n(direct-Al)", xy=(DIFFUSED_R_SH, r.R_access[0] * 0.5), fontsize=7.4,
                color="tab:red", ha="center", va="top")
    ax.annotate("silicide\nsheet", xy=(cr.R_SH_SALICIDE, r.R_access[0] * 0.5), fontsize=7.4,
                color="tab:green", ha="center", va="top")
    ax.set_xlabel("effective sheet resistance  R_sh  (Ω/□)   [ρ_c held fixed]")
    ax.set_ylabel("resistance term  (Ω)")
    ax.set_title("Different R_sh exponents — the thing a scalar can't fake\n"
                 "(access linear, contact sublinear ⇒ contact's share rises as R_sh falls)", fontsize=9.5)
    ax.legend(fontsize=7.8, loc="lower right")
    ax.grid(True, which="both", alpha=0.15)

    fig.suptitle("Historical-modes B7 — silicide / contact resistance: salicide solves the ACCESS "
                 "resistance so well that the CONTACT becomes the next-era bottleneck", fontsize=11)
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
