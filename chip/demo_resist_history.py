"""The historical-modes A4 banked artifact: negative-resist swelling & the optics-independent CD floor.

Three photoresist generations developed on the **same fixed aerial image**, so the only variable is the
resist chemistry — one figure, two panels:

  * **Left — the swelling mechanism (space vs pitch).** The *same* fine optics developed as **positive**
    (DQN/novolak — dissolves, no swell) and **negative** (Kodak KTFR — the exposed line crosslinks then
    **swells** by a fixed ``2·s`` per feature). The positive space stays open down to the **optical**
    (Rayleigh) floor; the negative space shrinks and crosses zero — the swollen lines **bridge** — at a
    much coarser pitch (shaded). CAR (the DUV successor, :func:`chip.litho.expose_grating_car`) resolves in
    the bridged band. *Positive = :func:`chip.litho.expose_grating` bit-for-bit (the seam).*
  * **Right — the floor the wavelength race can't touch (floor vs film thickness).** The negative-resist
    swelling half-pitch floor ``≈ film thickness`` (:func:`chip.resist_history.swelling_resolution_floor`)
    rises **linearly with thickness and is independent of λ/NA** — orthogonal to A2's Rayleigh floor
    ``k₁·λ/NA`` (flat here, a horizontal line). Below the crossing, swelling — not the optics — sets the
    resolution. Only switching resist (positive / CAR) removes it; sharpening the optics does nothing.

Tight legs: the positive seam (= :func:`chip.litho.expose_grating`), the swelling **sign** (it only grows
the line → the space bridges), the CAR delegation, and the floor's ``∝ thickness`` / optics-independence.
Flagged: the swelling coefficient (see :mod:`chip.resist_history`). Run headless:

    python -m chip.demo_resist_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import litho
from . import resist_history as rh

# --- The fixed optics (held constant to isolate the RESIST variable — the A4 method) --------------- #
# A representative fine projection (i-line-class): its optical floor (~0.8 µm pitch) is far below the
# thickness-set swelling floor, so the negative resist — not the lens — is the binding wall. The swelling
# floor is optics-independent, so this choice only sets how much finer the positive/CAR successors reach.
IMAGING = litho.Imaging(365.0, 0.45, 0.5)
THICKNESS_NM = rh.RESIST_THICKNESS_NM          # 1 µm — the era resist film
PITCHES_NM = np.linspace(600.0, 4000.0, 120)   # spans the optical floor → well past the swelling wall
PITCH_MARKS_NM = (1000.0, 1600.0, 2400.0, 3200.0)   # annotated points (two bridged, two resolved)
CAR_MARK_PITCH_NM = 1600.0                     # a pitch where the negative bridges but CAR resolves

# --- The floor-vs-thickness panel: swelling floor ∝ thickness (optics-independent) ----------------- #
THICKNESSES_NM = np.linspace(200.0, 2200.0, 100)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-resist-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-resist-history.png"


@dataclass(frozen=True)
class ResistHistoryResult:
    """The A4 bundle the figure and summary consume."""

    # Left — the swelling mechanism (space vs pitch), one curve per chemistry
    pitches_nm: np.ndarray
    positive_space_nm: np.ndarray
    negative_space_nm: np.ndarray
    negative_cd_nm: np.ndarray
    optical_floor_pitch_nm: float                # the positive (Rayleigh) floor
    swelling_floor_pitch_nm: float               # the negative (thickness-set) floor — closed form
    negative_bridge_pitch_nm: float              # the ACTUAL bridge pitch of the develop
    pitch_marks: tuple[rh.ResistFeature, ...]    # positive marks
    negative_marks: tuple[rh.ResistFeature, ...]
    car_mark: rh.ResistFeature                   # CAR resolving where the negative bridges
    # Right — the floor vs film thickness (optics-independence)
    thicknesses_nm: np.ndarray
    swelling_halfpitch_floor_nm: np.ndarray      # ∝ thickness (independent of λ/NA)
    optical_halfpitch_floor_nm: float            # flat (independent of thickness)
    thickness_nm: float


def _smallest_resolving_pitch(chemistry: str) -> float:
    """The finest pitch that still resolves in ``chemistry`` (the empirical floor of the develop)."""
    resolving = [float(p) for p in PITCHES_NM
                 if rh.develop_resist(IMAGING, float(p), chemistry).resolved]
    return min(resolving) if resolving else float("nan")


def compute() -> ResistHistoryResult:
    """Run the three resist chemistries on the fixed optics → :class:`ResistHistoryResult`."""
    pos = [rh.develop_resist(IMAGING, float(p), "positive") for p in PITCHES_NM]
    neg = [rh.develop_resist(IMAGING, float(p), "negative") for p in PITCHES_NM]

    positive_space = np.array([f.space_nm for f in pos])
    negative_space = np.array([f.space_nm for f in neg])
    negative_cd = np.array([f.cd_nm for f in neg])

    optical_floor = _smallest_resolving_pitch("positive")
    swelling_floor = rh.swelling_resolution_floor(THICKNESS_NM)      # closed form (optics-independent)
    negative_bridge = _smallest_resolving_pitch("negative")         # the actual develop's bridge

    marks = tuple(rh.develop_resist(IMAGING, p, "positive") for p in PITCH_MARKS_NM)
    neg_marks = tuple(rh.develop_resist(IMAGING, p, "negative") for p in PITCH_MARKS_NM)
    car_mark = rh.develop_resist(IMAGING, CAR_MARK_PITCH_NM, "car")

    swell_floor_vs_t = np.array(
        [rh.swelling_resolution_floor(float(t)) / 2.0 for t in THICKNESSES_NM])   # half-pitch
    optical_halfpitch = IMAGING.pitch_min_coherent / 2.0

    return ResistHistoryResult(
        pitches_nm=PITCHES_NM, positive_space_nm=positive_space, negative_space_nm=negative_space,
        negative_cd_nm=negative_cd, optical_floor_pitch_nm=optical_floor,
        swelling_floor_pitch_nm=swelling_floor, negative_bridge_pitch_nm=negative_bridge,
        pitch_marks=marks, negative_marks=neg_marks, car_mark=car_mark,
        thicknesses_nm=THICKNESSES_NM, swelling_halfpitch_floor_nm=swell_floor_vs_t,
        optical_halfpitch_floor_nm=optical_halfpitch, thickness_nm=THICKNESS_NM,
    )


def print_summary(r: ResistHistoryResult) -> None:
    """Print the A4 story — the resist that swells, the floor it sets, and the successors that clear it."""
    print("\nHistorical-modes A4: photoresist generations — negative-resist swelling & the CD floor "
          "(one aerial image, three resists)\n")

    print(f"  The mechanism (same {IMAGING.wavelength_nm:.0f} nm / NA {IMAGING.NA:.2f} optics, "
          f"{r.thickness_nm*1e-3:.1f} µm film): the exposed NEGATIVE line crosslinks, then swells by "
          f"2·s = {2*rh.swell_length(r.thickness_nm):.0f} nm.")
    print(f"    {'pitch':>6}   {'POSITIVE space':>15}   {'NEGATIVE line→space':>22}")
    for pos, neg in zip(r.pitch_marks, r.negative_marks):
        tag = "  BRIDGED (short)" if neg.bridged else "  resolves"
        print(f"    {pos.pitch_nm:>5.0f}   {pos.space_nm:>11.0f} nm   "
              f"{neg.cd_nm:>7.0f}→{neg.space_nm:>7.0f} nm{tag}")
    print(f"    → the same feature: positive keeps an open space; negative bridges once the swollen "
          f"lines touch.\n")

    print(f"  The two floors (finest resolving pitch on this fixed optics):")
    print(f"    positive (optical / Rayleigh floor)   ≈ {r.optical_floor_pitch_nm:>6.0f} nm")
    print(f"    negative (swelling floor, thickness-set) ≈ {r.negative_bridge_pitch_nm:>4.0f} nm   "
          f"(closed-form {r.swelling_floor_pitch_nm:.0f} nm ≈ 2× the {r.thickness_nm*1e-3:.0f} µm film)")
    print(f"    CAR successor at {r.car_mark.pitch_nm:.0f} nm (a bridged pitch): "
          f"contrast {r.car_mark.contrast:.2f}, {'resolves' if r.car_mark.resolved else 'flat'} "
          f"(litho.expose_grating_car).")
    print(f"    → the swelling floor ∝ thickness and is INDEPENDENT of λ/NA: the wavelength race (A2) "
          f"can't clear it — only a non-swelling resist can.")
    print(f"    [positive = expose_grating bit-for-bit (seam); swelling grows the line (tight sign); "
          f"swell coefficient FLAGGED]\n")


def save_figure(r: ResistHistoryResult) -> Path:
    """Render and save the A4 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: the swelling mechanism — space vs pitch, positive vs negative --------------------- #
    ax = axes[0]
    ax.plot(r.pitches_nm, r.positive_space_nm, "-", color="tab:green", lw=2.2,
            label="positive (DQN) — space open to the optical floor")
    ax.plot(r.pitches_nm, r.negative_space_nm, "-", color="tab:red", lw=2.2,
            label="negative (KTFR) — swollen line, space shrinks")
    ax.axhline(0.0, color="0.4", lw=1.0)
    # shade the bridged band (negative space ≤ 0)
    ax.fill_between(r.pitches_nm, r.negative_space_nm, 0.0,
                    where=(r.negative_space_nm <= 0.0), color="tab:red", alpha=0.15)
    ax.set_ylim(-1150, 1950)
    ax.axvline(r.negative_bridge_pitch_nm, color="tab:red", ls=":", lw=1.6)
    ax.annotate(f"negative bridges below\n≈ {r.negative_bridge_pitch_nm:.0f} nm\n(swollen lines touch)",
                xy=(r.negative_bridge_pitch_nm, -150.0),
                xytext=(r.negative_bridge_pitch_nm + 420.0, -780.0),
                fontsize=7.6, color="tab:red", va="center", ha="left",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1))
    ax.axvline(r.optical_floor_pitch_nm, color="tab:green", ls=":", lw=1.4)
    ax.annotate(f"optical floor\n≈ {r.optical_floor_pitch_nm:.0f} nm",
                xy=(r.optical_floor_pitch_nm, 900.0),
                xytext=(r.optical_floor_pitch_nm + 250.0, 1500.0),
                fontsize=7.6, color="tab:green", va="center",
                arrowprops=dict(arrowstyle="->", color="tab:green", lw=1))
    # CAR resolves in the bridged band
    ax.plot(r.car_mark.pitch_nm, 0.0, "D", color="tab:blue", ms=8, zorder=5)
    ax.annotate(f"CAR resolves here\n(DUV successor)", xy=(r.car_mark.pitch_nm, 0.0),
                xytext=(r.car_mark.pitch_nm - 150.0, 700.0), fontsize=7.4, color="tab:blue",
                ha="right", va="center", arrowprops=dict(arrowstyle="->", color="tab:blue", lw=1))
    ax.set_xlabel("grating pitch  (nm)")
    ax.set_ylabel("space between lines  (nm)   [< 0 ⇒ bridged]")
    ax.set_title("Negative-resist swelling: the exposed line grows until the space bridges", fontsize=9.5)
    ax.legend(fontsize=7.4, loc="upper left")
    ax.grid(True, alpha=0.18)
    ax.text(0.97, 0.05, "positive = expose_grating (seam);\nswelling grows the line (tight); "
            "coeff FLAGGED", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8, color="0.4")

    # --- Right: the optics-independent floor — swelling half-pitch floor vs thickness ------------- #
    ax = axes[1]
    ax.plot(r.thicknesses_nm * 1e-3, r.swelling_halfpitch_floor_nm * 1e-3, "-", color="tab:red", lw=2.4,
            label="negative swelling floor  ∝ thickness")
    ax.axhline(r.optical_halfpitch_floor_nm * 1e-3, color="tab:green", ls="--", lw=2.0,
               label=f"optical floor (λ/NA) — flat, {r.optical_halfpitch_floor_nm:.0f} nm")
    ax.plot([r.thickness_nm * 1e-3], [rh.swelling_resolution_floor(r.thickness_nm) / 2.0 * 1e-3],
            "o", color="tab:red", ms=7)
    ax.annotate(f"{r.thickness_nm*1e-3:.0f} µm film →\nfloor ≈ {rh.swelling_resolution_floor(r.thickness_nm)/2.0*1e-3:.1f} µm "
                f"(≈ 1× thickness)",
                xy=(r.thickness_nm * 1e-3, rh.swelling_resolution_floor(r.thickness_nm) / 2.0 * 1e-3),
                xytext=(r.thickness_nm * 1e-3 - 0.15, rh.swelling_resolution_floor(r.thickness_nm) / 2.0 * 1e-3 + 0.35),
                fontsize=7.6, color="tab:red", ha="right", va="center",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1))
    ax.set_xlabel("resist film thickness  (µm)")
    ax.set_ylabel("resolvable half-pitch floor  (µm)")
    ax.set_title("The floor the wavelength race can't touch: swelling ∝ thickness, not λ/NA", fontsize=9.5)
    ax.legend(fontsize=7.6, loc="upper left")
    ax.grid(True, alpha=0.18)
    ax.text(0.97, 0.05, "swelling floor is optics-independent;\nonly a non-swelling resist "
            "(positive/CAR) clears it", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=6.8, color="0.4")

    fig.suptitle("Historical-modes A4 — period photoresist: negative-resist swelling set a CD floor "
                 "≈ the film thickness that no wavelength could clear (positive & CAR did)", fontsize=11.0)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, →, ≈, ∝, λ on legacy codepages

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
