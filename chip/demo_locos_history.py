"""The historical-modes B5 banked artifact: LOCOS isolation, the bird's beak & the active-pitch wall.

The *isolation* rung of the **backward axis**, and the 2-D oxidation regime's historical consumer — one
figure, two panels:

  * **Left — the bird's beak (oxide thickness across a cross-section).** A field | nitride | field
    cross-section developed at the reference field-oxidation recipe: thick **field oxide** in the open
    field (the plateau = :func:`chip.oxidation.grow_oxide` **bit-for-bit**, the seam), tapering through
    the **bird's beak** — oxidant that diffused laterally under the nitride edge — into the thin/zero
    **active** region it protects. The beak eats a strip ``L_beak`` off each active edge.
  * **Right — the wall the beak set (surviving active width vs drawn width).** The two-field solve's
    surviving active width vs the drawn nitride width, beside the single-edge subtraction ``W − 2·L_beak``
    and the **STI** successor (``active = drawn`` — vertical walls, no beak). The two-field curve tracks
    the subtraction at wide stripes (the cross-check) but **pinches off earlier** — the two opposing
    beaks' oxidant fields overlap (the genuinely-2-D merge) — so LOCOS is *worse* than the isolated-edge
    estimate. Below pinch-off the active island is fully consumed: the minimum isolable pitch, which
    **scales with the field-oxide thickness** (beak ∝ t_field). STI has no beak and clears it.

Tight legs: the planar seam (field plateau = :func:`chip.oxidation.grow_oxide`), the monotone inward
encroachment (``m ∈ [0, 1]``), and the two-field ≡ subtraction agreement at wide stripes. The earned 2-D
finding (qualitative): the beak overlap pinches the island off *before* ``2·L_beak``. Flagged: the
beak/field-oxide ratio and the merge coefficient (see :mod:`chip.locos_history`). Run headless:

    python -m chip.demo_locos_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import locos_history as lh

# --- The reference field-oxidation recipe (held fixed; the module defaults) ------------------------ #
DRAWN_PROFILE_UM = 4.0                             # the profiled stripe — wide enough to survive with a clear beak
DRAWN_WIDTHS_UM = np.linspace(1.2, 8.0, 90)       # the wall sweep — spans pinch-off → comfortably isolated

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-locos-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-locos-history.png"


@dataclass(frozen=True)
class LocosHistoryResult:
    """The B5 bundle the figure and summary consume."""

    field_ox_um: float
    beak_um: float
    beak_ratio: float
    # Left — the bird's-beak cross-section
    profile: lh.FieldOxideProfile
    # Right — the active-pitch wall
    drawn_um: np.ndarray
    active_true_um: np.ndarray
    active_approx_um: np.ndarray                   # single-edge subtraction W − 2·L_beak (floored at 0)
    pinch_true_um: float                           # drawn width where the two-field solve pinches off
    pinch_approx_um: float                         # where the subtraction predicts it (2·L_beak)


def compute() -> LocosHistoryResult:
    """Grow the field oxide, read the beak, and sweep the drawn active width → :class:`LocosHistoryResult`."""
    field_ox = lh.field_oxide_thickness_um()
    beak = lh.birds_beak_length_um(field_ox)
    profile = lh.field_oxide_profile(DRAWN_PROFILE_UM, field_ox)

    active_true = np.array([lh.active_width_um(float(w), field_ox) for w in DRAWN_WIDTHS_UM])
    active_approx = np.maximum(DRAWN_WIDTHS_UM - 2.0 * beak, 0.0)

    # The two pinch-off widths: the honest two-field solve vs the single-edge subtraction (2·L_beak).
    resolved = DRAWN_WIDTHS_UM[active_true > 0.0]
    pinch_true = float(resolved.min()) if resolved.size else float("nan")
    pinch_approx = 2.0 * beak

    return LocosHistoryResult(
        field_ox_um=field_ox, beak_um=beak, beak_ratio=beak / field_ox, profile=profile,
        drawn_um=DRAWN_WIDTHS_UM, active_true_um=active_true, active_approx_um=active_approx,
        pinch_true_um=pinch_true, pinch_approx_um=pinch_approx,
    )


def print_summary(r: LocosHistoryResult) -> None:
    """Print the B5 story — the beak that eats the active area and the pitch wall it set."""
    print("\nHistorical-modes B5: LOCOS isolation — the bird's beak & the active-pitch wall "
          "(field oxidation under a nitride mask)\n")

    print(f"  The field oxide (wet {lh.FIELD_T_CELSIUS:.0f} °C / {lh.FIELD_T_MINUTES:.0f} min): "
          f"{r.field_ox_um:.3f} µm  (= oxidation.grow_oxide bit-for-bit — the seam).")
    print(f"  The bird's beak encroaches L_beak = {r.beak_um:.3f} µm per edge "
          f"(≈ {r.beak_ratio:.2f}× the field oxide — the cited LOCOS rule, FLAGGED).")
    print(f"  Profiled {DRAWN_PROFILE_UM:.1f} µm drawn active → {r.profile.active_width_um:.3f} µm "
          f"survives (the beak ate {DRAWN_PROFILE_UM - r.profile.active_width_um:.3f} µm).\n")

    print(f"  The wall (surviving active width vs drawn nitride width):")
    for w in (2.0, 2.5, 3.0, 4.0, 6.0):
        true = lh.active_width_um(w, r.field_ox_um)
        approx = max(w - 2.0 * r.beak_um, 0.0)
        tag = "  PINCHED OFF (island lost)" if true <= 0.0 else ""
        print(f"    drawn {w:>4.1f} µm → two-field {true:>5.2f} µm   (single-edge W−2·L_beak {approx:>4.2f} µm){tag}")
    print(f"    → LOCOS pinches off at ≈ {r.pinch_true_um:.1f} µm drawn — EARLIER than the single-edge "
          f"2·L_beak = {r.pinch_approx_um:.2f} µm:")
    print(f"      the two beaks' oxidant fields overlap (the 2-D merge). Min isolable pitch ∝ field-oxide "
          f"thickness; STI (no beak) clears it.")
    print(f"    [planar seam = grow_oxide bit-for-bit (tight); two-field ≡ subtraction at wide stripes "
          f"(tight); beak ratio + merge width FLAGGED]\n")


def save_figure(r: LocosHistoryResult) -> Path:
    """Render and save the B5 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: the bird's-beak cross-section — oxide thickness across field | nitride | field ------- #
    ax = axes[0]
    p = r.profile
    x, t = p.x_um, p.t_ox_um
    ax.fill_between(x, 0.0, t, color="tab:blue", alpha=0.20)
    ax.plot(x, t, "-", color="tab:blue", lw=2.2, label="field oxide  t_ox(x) = grow_oxide · m(x)")
    ax.axhline(r.field_ox_um, color="tab:blue", ls=":", lw=1.4)
    ax.annotate(f"field-oxide plateau\n= grow_oxide = {r.field_ox_um:.2f} µm (seam)",
                xy=(x.max() * 0.72, r.field_ox_um), xytext=(x.max() * 0.30, r.field_ox_um * 1.06),
                fontsize=7.6, color="tab:blue", va="bottom", ha="center",
                arrowprops=dict(arrowstyle="->", color="tab:blue", lw=1))
    # the surviving active region (centre), where the beak has NOT filled in
    half = 0.5 * p.active_width_um
    ax.axvspan(-half, half, color="tab:green", alpha=0.14)
    ax.annotate(f"surviving active\n{p.active_width_um:.2f} µm",
                xy=(0.0, r.field_ox_um * 0.16), fontsize=7.8, color="tab:green", ha="center", va="center")
    # the beak on the right edge
    beak_x = half + 0.5 * r.beak_um
    ax.annotate("bird's beak", xy=(beak_x, r.field_ox_um * 0.5),
                xytext=(beak_x + 0.7, r.field_ox_um * 0.78), fontsize=7.8, color="tab:red", ha="left",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1.2))
    ax.set_xlabel("lateral position  x  (µm)   [0 = active-stripe centre]")
    ax.set_ylabel("oxide thickness  (µm)")
    ax.set_ylim(0.0, r.field_ox_um * 1.28)
    ax.set_title(f"LOCOS cross-section: oxidant under the nitride grows the beak "
                 f"(drawn active {DRAWN_PROFILE_UM:.0f} µm)", fontsize=9.5)
    ax.legend(fontsize=7.6, loc="upper right")
    ax.grid(True, alpha=0.18)

    # --- Right: the active-pitch wall — surviving active width vs drawn width ----------------------- #
    ax = axes[1]
    ax.plot(r.drawn_um, r.drawn_um, "-", color="0.55", lw=1.6,
            label="STI successor: active = drawn (no beak)")
    ax.plot(r.drawn_um, r.active_approx_um, "--", color="tab:orange", lw=1.8,
            label="single-edge estimate  W − 2·L_beak")
    ax.plot(r.drawn_um, r.active_true_um, "-", color="tab:red", lw=2.4,
            label="LOCOS (two-field solve): surviving active")
    ax.axhline(0.0, color="0.4", lw=1.0)
    # shade the pinched-off band (two-field active = 0)
    ax.fill_between(r.drawn_um, 0.0, r.drawn_um, where=(r.active_true_um <= 0.0),
                    color="tab:red", alpha=0.10)
    ax.axvline(r.pinch_true_um, color="tab:red", ls=":", lw=1.6)
    ax.annotate(f"LOCOS pinches off\n≈ {r.pinch_true_um:.1f} µm drawn\n(beaks merge)",
                xy=(r.pinch_true_um, 0.35), xytext=(r.pinch_true_um + 0.7, 1.7),
                fontsize=7.6, color="tab:red", va="center", ha="left",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1))
    ax.axvline(r.pinch_approx_um, color="tab:orange", ls=":", lw=1.3)
    ax.annotate(f"single-edge 2·L_beak\n= {r.pinch_approx_um:.2f} µm",
                xy=(r.pinch_approx_um, 3.4), xytext=(r.pinch_approx_um - 0.3, 4.6),
                fontsize=7.4, color="tab:orange", va="center", ha="right",
                arrowprops=dict(arrowstyle="->", color="tab:orange", lw=1))
    ax.set_xlabel("drawn active (nitride) width  (µm)")
    ax.set_ylabel("surviving active width  (µm)")
    ax.set_xlim(r.drawn_um.min(), r.drawn_um.max())
    ax.set_ylim(-0.4, r.drawn_um.max())
    ax.set_title("The wall: opposing beaks merge → the island pinches off before 2·L_beak", fontsize=9.5)
    ax.legend(fontsize=7.4, loc="upper left")
    ax.grid(True, alpha=0.18)
    ax.text(0.97, 0.05, "two-field ≡ subtraction at wide stripes (tight);\nmerge width FLAGGED "
            "(rides L_D)", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8, color="0.4")

    fig.suptitle("Historical-modes B5 — LOCOS: the bird's beak eats active area and merges below a "
                 "min pitch (∝ field-oxide thickness); STI's vertical walls cleared it", fontsize=11.0)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
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
