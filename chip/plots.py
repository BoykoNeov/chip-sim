"""Chip-local plot helpers — the render layer (Chip Phase 1a; ADR 0002).

The **viz floor**: static matplotlib figures that *consume* the plain arrays
:mod:`diffusion_dopant` / :mod:`junction` produce. Per ADR 0002 this layer is strictly
downstream of correctness — a figure draws already-validated numbers, it is never evidence of
validity (the triad tests do that). It is the only place in chip that imports a plotting
library; the compute modules stay headless so the test suite never needs matplotlib.

The headline view is the **mechanism** one ADR 0002 §5 calls for: the ``erfc`` → Gaussian
**profile morph** as predeposition gives way to drive-in, so a learner sees *why the junction
moves* — the fixed dose spreading deeper, the surface concentration falling, the profile
crossing the background doping further from the surface. These helpers start project-local; a
primitive earns promotion to a shared ``viz/`` only by rule-of-three (ARCHITECTURE.md §6) —
chip's concentration-vs-depth line is the candidate third use of steel's profile-vs-depth line.

Requires the optional ``viz`` extra (``pip install -e .[viz]``).
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from .diffusion_dopant import DopantProfile, CM_PER_UM
from .junction import Junction

# Stable colours: warm = the shallow predep source step, cool = the deep redistributed drive-in.
PREDEP_COLOR = "#e07b39"      # warm — the constant-source erfc, concentrated near the surface
DRIVEIN_COLOR = "#2f6fb0"     # cool — the sealed-surface Gaussian, spread deep
BACKGROUND_COLOR = "#888888"  # the wafer's opposite-type background doping N_B
JUNCTION_COLOR = "#c0392b"    # the pn junction (where the profile crosses N_B)

# Oxidation (Phase 2) colours: wet = cool blue (H₂O, fast), dry = warm amber (O₂, slow).
WET_COLOR = "#2f6fb0"
DRY_COLOR = "#d4711f"

# Lithography (Phase 3) colours.
AERIAL_COLOR = "#6a3d9a"        # the assembled aerial image (violet — light/intensity)
MASK_COLOR = "#999999"          # the ideal mask transmission (the square wave we asked for)
THRESHOLD_COLOR = "#c0392b"     # the resist clip level + the printed CD
COHERENT_LIMIT_COLOR = "#2f6fb0"   # the k₁=0.5 coherent resolution limit (λ/NA)
TWO_BEAM_LIMIT_COLOR = "#d4711f"   # the k₁=0.25 two-beam resolution floor (λ/2NA)


def _depth_um(x: np.ndarray) -> np.ndarray:
    """Cell-centre depths cm → µm (the reported length unit)."""
    return np.asarray(x) / CM_PER_UM


def junction_figure(
    predep: DopantProfile,
    drivein: DopantProfile,
    junction: Junction,
    morph: list[tuple[str, np.ndarray, np.ndarray]] | None = None,
    dopant_label: str = "boron",
) -> "plt.Figure":
    """The banked pn-junction artifact: the two-step profile + junction, beside the morph.

    Left panel (**the junction** — the banked readout): the predep ``erfc`` and the final
    drive-in profile on one depth axis (log concentration), the background ``N_B`` as a horizontal
    line, and the junction depth ``x_j`` marked where the drive-in crosses it — with ``x_j`` and
    ``R_s`` annotated. *Recipe in, junction out.*

    Right panel (**the mechanism** — why the junction moves): ``morph`` is an optional list of
    ``(label, x_cm, N)`` snapshots of the drive-in at increasing times, showing the ``erfc``
    relaxing toward a Gaussian as the fixed dose spreads deeper and the surface falls. If omitted,
    only the junction panel is drawn.

    Consumes plain arrays / the :class:`Junction` dataclass — no live solver object (ADR 0002).
    """
    ncols = 2 if morph else 1
    fig, axes = plt.subplots(1, ncols, figsize=(13 if morph else 7.5, 6), squeeze=False)
    ax_j = axes[0][0]

    # --- left: the junction readout -------------------------------------------------
    xj_um = junction.x_j_um
    ax_j.semilogy(_depth_um(predep.x), np.maximum(predep.N, 1.0), color=PREDEP_COLOR, lw=2,
                  label=f"predeposition (erfc), surface {predep.N[0]:.1e} cm⁻³")
    ax_j.semilogy(_depth_um(drivein.x), np.maximum(drivein.N, 1.0), color=DRIVEIN_COLOR, lw=2.4,
                  label=f"drive-in (≈Gaussian), surface {drivein.N[0]:.1e} cm⁻³")
    ax_j.axhline(junction.N_background, color=BACKGROUND_COLOR, ls="--", lw=1.4,
                 label=f"background $N_B$ = {junction.N_background:.0e} cm⁻³")
    ax_j.axvline(xj_um, color=JUNCTION_COLOR, ls=":", lw=1.8)
    ax_j.plot([xj_um], [junction.N_background], "o", color=JUNCTION_COLOR, ms=8, zorder=5)
    ax_j.annotate(
        f"pn junction\n$x_j$ = {xj_um:.2f} µm\n$R_s$ = {junction.R_s:.0f} Ω/sq",
        xy=(xj_um, junction.N_background),
        xytext=(xj_um * 0.42, junction.N_background * 40),
        color=JUNCTION_COLOR, fontsize=10, ha="center",
        arrowprops=dict(arrowstyle="->", color=JUNCTION_COLOR, lw=1.2),
    )
    upper = max(predep.N[0], drivein.N[0]) * 3
    ax_j.set_ylim(junction.N_background * 0.2, upper)
    ax_j.set_xlim(0, min(_depth_um(drivein.x)[-1], xj_um * 2.2))
    ax_j.set_xlabel("depth  (µm)")
    ax_j.set_ylabel("dopant concentration $N$  (cm⁻³)")
    ax_j.set_title(f"pn junction from a two-step {dopant_label} diffusion")
    ax_j.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    ax_j.grid(True, which="both", alpha=0.18)

    # --- right: the erfc → Gaussian morph (mechanism) -------------------------------
    if morph:
        ax_m = axes[0][1]
        n = len(morph)
        cmap = plt.get_cmap("viridis")
        for k, (label, x, N) in enumerate(morph):
            ax_m.semilogy(_depth_um(x), np.maximum(N, 1.0), lw=2,
                          color=cmap(k / max(n - 1, 1)), label=label)
        ax_m.axhline(junction.N_background, color=BACKGROUND_COLOR, ls="--", lw=1.2)
        ax_m.set_ylim(junction.N_background * 0.2, morph[0][2][0] * 3)
        ax_m.set_xlim(0, min(_depth_um(drivein.x)[-1], xj_um * 2.2))
        ax_m.set_xlabel("depth  (µm)")
        ax_m.set_ylabel("dopant concentration $N$  (cm⁻³)")
        ax_m.set_title("the morph: erfc → Gaussian as the dose drives in")
        ax_m.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
        ax_m.grid(True, which="both", alpha=0.18)

    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return fig


def oxidation_figure(
    t_hours: np.ndarray,
    curves: list[tuple[str, np.ndarray, float, float, str]],
    T_celsius: float = 1100.0,
    orientation: str = "100",
) -> "plt.Figure":
    """The banked Deal–Grove artifact: oxide thickness vs time (wet vs dry) + the growth-rate mechanism.

    ``curves`` is a list of ``(label, x_ox, B, A, color)`` — one per ambient, all sharing the time
    axis ``t_hours`` (oxide thickness ``x_ox`` in µm; rate constants ``B`` µm²/hr, ``A`` µm).

    Left panel (**the banked readout** — log-log): ``x_ox(t)`` for each ambient, with its **linear**
    ``(B/A)·t`` (slope 1, dotted) and **parabolic** ``√(B·t)`` (slope ½, dashed) asymptotes drawn —
    the curve riding the linear asymptote when thin and bending onto the parabolic one when thick.
    The two regimes the plan names, annotated straight on the curve.

    Right panel (**the mechanism** — why it bends): the growth rate ``dx_ox/dt = B/(A+2·x_ox)`` vs
    thickness — flat at the linear plateau ``B/A`` while thin (reaction-limited), then rolling off as
    the thickening film throttles oxidant diffusion (the diffusion bottleneck). *Why* growth slows
    from linear to parabolic.

    Consumes plain arrays only (ADR 0002) — no live model object.
    """
    fig, (ax_t, ax_r) = plt.subplots(1, 2, figsize=(13, 6))
    t = np.asarray(t_hours, dtype=float)

    # --- left: oxide thickness vs time, wet & dry, with the two asymptotes -----------
    for label, x_ox, B, A, color in curves:
        ax_t.loglog(t, x_ox, color=color, lw=2.6, label=label, zorder=4)
        ax_t.loglog(t, (B / A) * t, color=color, lw=1.0, ls=":", alpha=0.7)      # linear (slope 1)
        ax_t.loglog(t, np.sqrt(B * t), color=color, lw=1.0, ls="--", alpha=0.7)  # parabolic (slope ½)
    ax_t.set_xlim(t[0], t[-1])
    ymax = max(x_ox.max() for _, x_ox, _, _, _ in curves)
    ax_t.set_ylim(min(x_ox.min() for _, x_ox, _, _, _ in curves), ymax * 1.4)
    ax_t.set_xlabel("oxidation time  (hr)")
    ax_t.set_ylabel("oxide thickness  $x_{ox}$  (µm)")
    ax_t.set_title(f"Deal–Grove oxide growth at {T_celsius:.0f} °C, (" + orientation + ") Si")
    # Annotate the two regimes on the curve (dotted = linear B/A·t, dashed = parabolic √Bt).
    ax_t.text(0.04, 0.93, "···  linear  $(B/A)\\,t$   (reaction-limited, slope 1)\n"
              "– –  parabolic  $\\sqrt{B\\,t}$   (diffusion-limited, slope ½)",
              transform=ax_t.transAxes, fontsize=8.5, va="top",
              bbox=dict(boxstyle="round", fc="white", ec="#cccccc", alpha=0.9))
    ax_t.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax_t.grid(True, which="both", alpha=0.18)

    # --- right: the growth-rate mechanism dx/dt = B/(A+2x) --------------------------
    for label, x_ox, B, A, color in curves:
        xx = np.linspace(1e-3, float(x_ox.max()), 300)
        rate = B / (A + 2.0 * xx)                     # oxidation.growth_rate
        ax_r.plot(xx, rate, color=color, lw=2.4, label=label)
        ax_r.axhline(B / A, color=color, ls=":", lw=1.0, alpha=0.7)     # the linear plateau B/A
    ax_r.set_xlabel("oxide thickness  $x_{ox}$  (µm)")
    ax_r.set_ylabel("growth rate  $dx_{ox}/dt$  (µm/hr)")
    ax_r.set_title("the mechanism: rate $= B/(A+2x_{ox})$ — diffusion throttles growth")
    ax_r.text(0.5, 0.92, "plateau at $B/A$ (thin, reaction-limited)\n→ rolls off as $B/2x_{ox}$ (thick, diffusion-limited)",
              transform=ax_r.transAxes, fontsize=8.5, va="top", ha="center",
              bbox=dict(boxstyle="round", fc="white", ec="#cccccc", alpha=0.9))
    ax_r.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax_r.grid(True, alpha=0.18)

    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return fig


def litho_figure(
    x_nm: np.ndarray,
    image: np.ndarray,
    partials: list[tuple[str, np.ndarray]],
    mask: np.ndarray,
    threshold: float,
    cd_span: tuple[float, float] | None,
    pitch_nm: float,
    pitches_nm: np.ndarray,
    contrasts: np.ndarray,
    pitch_coherent: float,
    pitch_two_beam: float,
    wavelength_nm: float,
    NA: float,
    sigma: float,
) -> "plt.Figure":
    """The banked lithography artifact: the aerial image assembling from its orders + contrast-vs-pitch.

    Left panel (**the mechanism** — why a pitch resolves, ADR 0002 §5): the aerial image of a line/space
    grating *assembling from its diffraction orders*. ``partials`` is a list of ``(label, I)`` partial
    sums — the DC (0th) order alone (a flat field), then + the 1st order (the fundamental cos fringe),
    then + higher orders (the line squares up) — converging onto the full collected ``image``. The ideal
    ``mask`` transmission (the square wave we asked for) is drawn faint for reference, the constant resist
    ``threshold`` as a dashed line, and the printed line (``cd_span`` = the dark region below threshold)
    shaded with its CD. *Fewer orders collected → a coarser image; the pupil throwing away the high
    orders is why the printed edge rounds.*

    Right panel (**the benchmark** — where the pattern stops resolving): image ``contrasts`` vs
    ``pitches_nm`` for this system, falling to ~0 at the pupil cutoff. The two Rayleigh limits are marked
    — ``pitch_coherent`` = λ/NA (half-pitch k₁=0.5, conventional) and ``pitch_two_beam`` = λ/2NA (k₁=0.25,
    the two-beam floor) — with the sub-resolution region shaded. The classic resolution curve.

    Consumes plain arrays only (ADR 0002) — no live imaging object.
    """
    fig, (ax_i, ax_c) = plt.subplots(1, 2, figsize=(13, 6))
    x = np.asarray(x_nm)

    # --- left: the aerial image assembling from its diffraction orders ----------------
    ax_i.plot(x, mask, color=MASK_COLOR, lw=1.2, ls="-", alpha=0.55,
              label="ideal mask (the square wave)")
    cmap = plt.get_cmap("viridis")
    n = len(partials)
    for k, (label, I_partial) in enumerate(partials):
        ax_i.plot(x, I_partial, color=cmap(k / max(n, 1) * 0.8), lw=1.6, alpha=0.85, label=label)
    ax_i.plot(x, image, color=AERIAL_COLOR, lw=3.0, label="aerial image (all collected orders)", zorder=5)
    ax_i.axhline(threshold, color=THRESHOLD_COLOR, ls="--", lw=1.6,
                 label=f"resist threshold = {threshold:.2f}")
    if cd_span is not None:
        x0, x1 = cd_span
        ax_i.axvspan(x0, x1, color=THRESHOLD_COLOR, alpha=0.10)
        ax_i.annotate(f"printed line\nCD = {x1 - x0:.0f} nm",
                      xy=((x0 + x1) / 2, threshold), xytext=((x0 + x1) / 2, threshold + 0.18 * image.max()),
                      color=THRESHOLD_COLOR, fontsize=9, ha="center",
                      arrowprops=dict(arrowstyle="->", color=THRESHOLD_COLOR, lw=1.2))
    ax_i.set_xlim(float(x[0]), float(x[-1]))
    ax_i.set_ylim(0, image.max() * 1.35)
    ax_i.set_xlabel("position  $x$  (nm)")
    ax_i.set_ylabel("aerial-image intensity  $I(x)$")
    ax_i.set_title(f"the aerial image assembling from its orders  (pitch {pitch_nm:.0f} nm)")
    ax_i.legend(loc="upper right", fontsize=8.0, framealpha=0.95)
    ax_i.grid(True, alpha=0.18)

    # --- right: contrast vs pitch — where the pattern stops resolving ------------------
    pitches_nm = np.asarray(pitches_nm)
    contrasts = np.asarray(contrasts)
    ax_c.plot(pitches_nm, contrasts, color=AERIAL_COLOR, lw=2.6, zorder=4,
              label=f"contrast (σ = {sigma:.2f})")
    ax_c.axvline(pitch_coherent, color=COHERENT_LIMIT_COLOR, ls="--", lw=1.6,
                 label=f"coherent limit λ/NA = {pitch_coherent:.0f} nm  ($k_1$=0.5)")
    ax_c.axvline(pitch_two_beam, color=TWO_BEAM_LIMIT_COLOR, ls=":", lw=1.8,
                 label=f"two-beam floor λ/2NA = {pitch_two_beam:.0f} nm  ($k_1$=0.25)")
    ax_c.axvspan(float(pitches_nm.min()), pitch_two_beam, color=TWO_BEAM_LIMIT_COLOR, alpha=0.08)
    ax_c.set_xlim(float(pitches_nm.min()), float(pitches_nm.max()))
    ax_c.set_ylim(0, 1.05)
    ax_c.set_xlabel("grating pitch  $p$  (nm)")
    ax_c.set_ylabel("image contrast  $(I_{max}-I_{min})/(I_{max}+I_{min})$")
    ax_c.set_title(f"resolution: contrast vs pitch  (λ={wavelength_nm:.0f} nm, NA={NA:.2f})")
    ax_c.text(0.30, 0.30, "← pattern stops resolving\n(contrast → 0 at the cutoff)",
              transform=ax_c.transAxes, fontsize=9, va="center", ha="center", color="#555555")
    ax_c.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    ax_c.grid(True, alpha=0.18)

    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return fig
