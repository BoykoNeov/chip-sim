"""The historical-modes B12 banked artifact: the latchup bill that trench isolation came with.

The *isolation* rung of the **backward axis**, second half — and the rung that reads as a **sequel**
rather than a new topic. B5 (:mod:`chip.demo_locos_history`) ended on the wall LOCOS set: the bird's
beak eats active area from both edges, so a thick field oxide puts a floor under how tightly devices
can be packed, and shallow-trench isolation cleared it. This figure is what clearing it cost.

Two panels, one per cited condition — and the point is that **the panel that moves is not the panel
that decides**:

  * **Left — what the isolation change moved (and it is the inert one).** The parasitic loop gain
    against the lateral base width. The three points are the era: **LOCOS**, whose device-to-well
    spacing is the drawn width *plus the bird's beak B5 computes* (not a house constant — this demo
    calls :mod:`chip.locos_history` for it); **STI with its trench ignored**, the density the successor
    bought; and **STI as actually built**, where the trench forces the injected carrier down one wall
    and up the other and hands part of the base width back. The between-scheme *ratios* are labelled
    because they are **coefficient-free** — since ``β ≈ 2L²/W_B²`` the diffusion length cancels, so a
    ratio depends on geometry alone and on none of this module's flagged numbers.
  * **Right — the condition that actually decides, and the isolation scheme is not in it.** The trigger
    current ``I = V_be / R_sub`` against substrate resistivity, with the disturbance the part is asked
    to survive drawn as a line: the wafer latches where the curve falls below it. The band marks where
    *this simulator's own boule* sits, and the arrow marks the direction its Scheil drift travels —
    which is the era's practical answer, since the lever that moves this curve is the substrate, not
    the isolation.

**What the figure is careful not to claim.** The absolute loop gain is a useless upper bound (γ = 1
with ``W_B ≪ L`` puts it 10⁴–10¹² where real parasitics are ~1–10³) — so the left panel's y-axis is
labelled as a bound and only the *ratios* are quoted. The trigger current rides a flagged tap geometry,
so the right panel draws the **curve** and never quotes a crossing point as a result. Both are the
module's own admissions (:mod:`chip.latchup`), drawn rather than hidden.

Run headless::

    python -m chip.demo_latchup_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import latchup as lu
from . import lifetime, locos_history as lh

# --- The reference layout (held fixed; the figure sweeps around it) -------------------------------- #
DRAWN_SPACING_UM = 2.0                     # the drawn n⁺-to-well spacing both schemes start from
INJECTED_MA = 10.0                         # the disturbance the part is asked to survive (GIVEN, not modelled)
TAU_S = lifetime.TAU_BULK                  # a clean wafer — the loosest (most pessimistic) bound on β

BASE_SWEEP_UM = np.linspace(1.2, 5.0, 240)
RHO_SWEEP_OHM_CM = np.logspace(-2.0, 2.0, 240)

# The simulator's own boule, in resistivity — the band drawn on the right panel (see chip-sim's
# Scheil slice: boron k < 1, so concentration RISES down the boule and resistivity FALLS).
BOULE_RHO_SEED_OHM_CM = 0.1956             # z = 0.0, the seed end — the FIRST wafers off the boule
BOULE_RHO_TAIL_OHM_CM = 0.1362             # z = 0.9, the tail end

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-latchup-history.png"


@dataclass(frozen=True)
class LatchupHistoryResult:
    """The B12 bundle the figure and summary consume."""

    # The era geometry — LOCOS's allowance is COMPUTED by B5, not assumed here
    field_ox_um: float
    beak_um: float
    locos_spacing_um: float
    sti_spacing_um: float
    sti_base_um: float                     # with the trench detour
    # Left panel — the gain curve and the three era points
    base_um: np.ndarray
    loop_gain: np.ndarray
    gain_locos: float
    gain_sti_bare: float
    gain_sti_trench: float
    # Right panel — the condition that decides
    rho_ohm_cm: np.ndarray
    trigger_ma: np.ndarray
    injected_ma: float

    @property
    def density_penalty(self) -> float:
        """STI's gain ÷ LOCOS's, with the trench ignored — the cost of the density it bought."""
        return self.gain_sti_bare / self.gain_locos

    @property
    def as_built_penalty(self) -> float:
        """STI's gain ÷ LOCOS's as actually built — after the trench hands part of the base back."""
        return self.gain_sti_trench / self.gain_locos

    @property
    def trench_payback(self) -> float:
        """The fraction of the density penalty the trench buys back (∈ (0, 1) — it never gets it all)."""
        return (self.gain_sti_bare - self.gain_sti_trench) / (self.gain_sti_bare - self.gain_locos)


def compute() -> LatchupHistoryResult:
    """Read B5's beak, build the two schemes' geometry, and sweep both cited conditions."""
    field_ox = lh.field_oxide_thickness_um()
    beak = lh.birds_beak_length_um(field_ox)

    # LOCOS must leave the beak on BOTH edges of the isolation region; STI keeps the drawn width.
    locos_spacing = DRAWN_SPACING_UM + 2.0 * beak
    sti_spacing = DRAWN_SPACING_UM
    sti_base = lu.lateral_base_width_um(sti_spacing, trench_depth_um=lu.STI_DEPTH_UM)

    L_um = lu.diffusion_length_um(TAU_S)
    beta_pnp = lu.bipolar_gain(lu.WELL_DEPTH_UM, L_um)          # the vertical device, fixed across schemes

    def gain(base_um):
        return lu.bipolar_gain(base_um, L_um) * beta_pnp

    trigger_ma = np.array([
        lu.trigger_current_a(lu.substrate_resistance_from_resistivity_ohm(float(r))) * 1.0e3
        for r in RHO_SWEEP_OHM_CM
    ])

    return LatchupHistoryResult(
        field_ox_um=field_ox, beak_um=beak,
        locos_spacing_um=locos_spacing, sti_spacing_um=sti_spacing, sti_base_um=sti_base,
        base_um=BASE_SWEEP_UM,
        loop_gain=np.array([gain(float(w)) for w in BASE_SWEEP_UM]),
        gain_locos=gain(locos_spacing), gain_sti_bare=gain(sti_spacing), gain_sti_trench=gain(sti_base),
        rho_ohm_cm=RHO_SWEEP_OHM_CM, trigger_ma=trigger_ma, injected_ma=INJECTED_MA,
    )


def print_summary(r: LatchupHistoryResult) -> None:
    """Print the B12 story — the density STI bought, and the condition that actually decides."""
    print("\nHistorical-modes B12: CMOS latchup — the bill trench isolation came with "
          "(F7's remainder, the isolation rung's second half)\n")

    print(f"  B5's geometry, computed not assumed: field oxide {r.field_ox_um:.3f} µm → bird's beak "
          f"{r.beak_um:.3f} µm per edge.")
    print(f"    LOCOS device-to-well spacing = drawn {DRAWN_SPACING_UM:.1f} + 2×beak = "
          f"{r.locos_spacing_um:.3f} µm   (the beak is why LOCOS cannot pack tighter)")
    print(f"    STI  device-to-well spacing = drawn {r.sti_spacing_um:.3f} µm — no beak; its trench "
          f"({lu.STI_DEPTH_UM:.2f} µm, cited) then lengthens the parasitic base to {r.sti_base_um:.3f} µm.\n")

    print("  (A) The SUSTAINING condition — what the isolation change moved:")
    print(f"    LOCOS                loop gain {r.gain_locos:.3e}")
    print(f"    STI, trench ignored  loop gain {r.gain_sti_bare:.3e}   = {r.density_penalty:.3f}× LOCOS "
          f"(the density it bought)")
    print(f"    STI, as built        loop gain {r.gain_sti_trench:.3e}   = {r.as_built_penalty:.3f}× LOCOS")
    print(f"    → the trench buys back {r.trench_payback:.0%} of the density penalty — and no more. "
          f"The remainder is the bill.")
    print(f"    [the RATIOS are coefficient-free: β ≈ 2L²/W², so L cancels. The ABSOLUTE gains are an "
          f"upper bound (γ=1) and are not a claim.]\n")

    print("  (B) The TRIGGERING condition — what actually decides, and isolation is not in it:")
    for rho in (0.05, 0.1362, 0.1956, 1.0, 10.0):
        R = lu.substrate_resistance_from_resistivity_ohm(rho)
        ma = lu.trigger_current_a(R) * 1.0e3
        tag = "  ← LATCHES at the drawn disturbance" if ma < r.injected_ma else ""
        print(f"    ρ = {rho:>7.4f} Ω·cm → R_sub {R:>7.1f} Ω → trigger {ma:>8.2f} mA{tag}")
    print(f"    (disturbance drawn at {r.injected_ma:.0f} mA — GIVEN, never modelled: an I/O overshoot "
          f"or a radiation hit)")
    print(f"    This simulator's boule spans ρ = {BOULE_RHO_TAIL_OHM_CM:.4f}–{BOULE_RHO_SEED_OHM_CM:.4f} "
          f"Ω·cm, and boron's k < 1 means resistivity FALLS down the boule:")
    print(f"      the trigger current RISES with z, so the FIRST wafers off the boule are the vulnerable "
          f"ones — the opposite of every other drift in this game.\n")

    print("  The era's answer: the isolation scheme moves the gain, which never decides; the substrate "
          "moves the trigger, which always does.")
    print("    [seam: scheme=None ⇒ no step at all. Flagged: the tap geometry (a calibration) — so the "
          "right panel draws the CURVE and quotes no crossing point.]\n")


def save_figure(r: LatchupHistoryResult) -> Path:
    """Render and save the B12 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: what the isolation change moved — the parasitic loop gain --------------------------- #
    ax = axes[0]
    ax.plot(r.base_um, r.loop_gain, "-", color="0.55", lw=1.8,
            label="β_npn·β_pnp  (upper bound: γ=1)")
    ax.set_yscale("log")

    pts = [
        (r.locos_spacing_um, r.gain_locos, "tab:green", "LOCOS\n(drawn + B5's beak)"),
        (r.sti_base_um, r.gain_sti_trench, "tab:red", "STI as built\n(trench lengthens the base)"),
        (r.sti_spacing_um, r.gain_sti_bare, "tab:orange", "STI, trench ignored\n(the density it bought)"),
    ]
    for x, y, c, label in pts:
        ax.plot([x], [y], "o", color=c, ms=9, zorder=5)
        ax.axvline(x, color=c, ls=":", lw=1.0, alpha=0.7)
    ax.annotate("LOCOS", xy=(r.locos_spacing_um, r.gain_locos), xytext=(r.locos_spacing_um + 0.45, r.gain_locos * 0.45),
                fontsize=8.2, color="tab:green", ha="left",
                arrowprops=dict(arrowstyle="->", color="tab:green", lw=1.1))
    ax.annotate(f"STI, trench ignored\n{r.density_penalty:.2f}× LOCOS",
                xy=(r.sti_spacing_um, r.gain_sti_bare), xytext=(r.sti_spacing_um + 0.30, r.gain_sti_bare * 2.6),
                fontsize=8.0, color="tab:orange", ha="left",
                arrowprops=dict(arrowstyle="->", color="tab:orange", lw=1.1))
    ax.annotate(f"STI as built\n{r.as_built_penalty:.2f}× LOCOS",
                xy=(r.sti_base_um, r.gain_sti_trench), xytext=(r.sti_base_um + 0.55, r.gain_sti_trench * 1.9),
                fontsize=8.0, color="tab:red", ha="left",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1.1))

    # the payback bracket — from the bare-STI point down to the as-built point
    ax.annotate("", xy=(r.sti_base_um, r.gain_sti_trench), xytext=(r.sti_spacing_um, r.gain_sti_bare),
                arrowprops=dict(arrowstyle="->", color="tab:blue", lw=2.0, alpha=0.8))
    ax.text(0.5 * (r.sti_spacing_um + r.sti_base_um), (r.gain_sti_bare * r.gain_sti_trench) ** 0.5 * 0.72,
            f"the trench buys back\n{r.trench_payback:.0%} of it", fontsize=7.8, color="tab:blue",
            ha="center", va="top")

    ax.set_xlabel("parasitic lateral base width  W_B  (µm)   [= device-to-well spacing + any trench detour]")
    ax.set_ylabel("loop gain  β_npn·β_pnp   (an upper bound — see note)")
    ax.set_xlim(r.base_um.min(), r.base_um.max())
    ax.set_title("(A) What the isolation change moved: the parasitic gain", fontsize=9.5)
    ax.legend(fontsize=7.6, loc="upper right")
    ax.grid(True, alpha=0.18, which="both")
    ax.text(0.03, 0.05, "the RATIOS are coefficient-free (β ≈ 2L²/W² ⇒ L cancels);\n"
                        "the absolute values are a γ=1 bound and are NOT a claim —\n"
                        "this condition never decides anything below",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=6.8, color="0.35")

    # --- Right: the condition that decides — trigger current vs substrate resistivity --------------- #
    ax = axes[1]
    ax.plot(r.rho_ohm_cm, r.trigger_ma, "-", color="tab:purple", lw=2.4,
            label="trigger current  I = V_be / R_sub   (V_be = 0.7 V, cited)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axhline(r.injected_ma, color="tab:red", ls="--", lw=1.8,
               label=f"injected disturbance {r.injected_ma:.0f} mA (GIVEN, not modelled)")
    ax.fill_between(r.rho_ohm_cm, r.trigger_ma, r.injected_ma,
                    where=(r.trigger_ma < r.injected_ma), color="tab:red", alpha=0.13)
    ax.text(r.rho_ohm_cm.max() * 0.55, r.injected_ma * 0.30, "LATCHES\n(whole wafer)",
            fontsize=8.4, color="tab:red", ha="center", va="top")

    ax.axvspan(BOULE_RHO_TAIL_OHM_CM, BOULE_RHO_SEED_OHM_CM, color="tab:blue", alpha=0.22)
    # Both boule annotations live BELOW the disturbance line, where the curve is not: at this
    # resistivity the trigger is ~50–75 mA, so anything drawn near it would sit on top of the curve.
    ax.annotate("this sim's boule (seed → tail)",
                xy=(BOULE_RHO_SEED_OHM_CM, r.injected_ma * 0.30),
                xytext=(BOULE_RHO_SEED_OHM_CM * 3.2, r.injected_ma * 0.075),
                fontsize=7.8, color="tab:blue", ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color="tab:blue", lw=1.1))
    # the drift arrow — boron k<1 ⇒ resistivity falls down the boule ⇒ SAFER, not worse
    ax.annotate("", xy=(BOULE_RHO_TAIL_OHM_CM, r.injected_ma * 0.030),
                xytext=(BOULE_RHO_SEED_OHM_CM, r.injected_ma * 0.030),
                arrowprops=dict(arrowstyle="->", color="tab:blue", lw=2.0))
    ax.text((BOULE_RHO_TAIL_OHM_CM * BOULE_RHO_SEED_OHM_CM) ** 0.5, r.injected_ma * 0.021,
            "Scheil drift (k<1):\nlater wafers are SAFER", fontsize=7.2, color="tab:blue",
            ha="center", va="top")

    ax.set_xlabel("substrate resistivity  ρ  (Ω·cm)   [heavier doping ← → lighter doping]")
    ax.set_ylabel("latchup trigger current  (mA)")
    ax.set_title("(B) What actually decides — and the isolation scheme is not in it", fontsize=9.5)
    ax.legend(fontsize=7.2, loc="upper left")
    ax.grid(True, alpha=0.18, which="both")
    ax.text(0.97, 0.05, "the tap geometry is a flagged calibration, so this panel\n"
                        "draws the CURVE and quotes no crossing point",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8, color="0.4")

    fig.suptitle("Historical-modes B12 — the latchup bill: STI cleared B5's packing floor, and the density "
                 "it bought is the parasitic base width.\nThe trench pays back part of it — the substrate "
                 "is what actually decides.", fontsize=10.0)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    DOCS_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS_FIGURE, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, →, ≈, ∝, ² on legacy codepages

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
