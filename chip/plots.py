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
MASSOUD_COLOR = "#a93226"       # the v1.1 thin-dry burst (crimson — the corrected curve)
BASELINE_COLOR = "#888888"      # the same linear-parabolic law with the burst switched off

# Lithography (Phase 3) colours.
AERIAL_COLOR = "#6a3d9a"        # the assembled aerial image (violet — light/intensity)
MASK_COLOR = "#999999"          # the ideal mask transmission (the square wave we asked for)
THRESHOLD_COLOR = "#c0392b"     # the resist clip level + the printed CD
COHERENT_LIMIT_COLOR = "#2f6fb0"   # the k₁=0.5 coherent resolution limit (λ/NA)
TWO_BEAM_LIMIT_COLOR = "#d4711f"   # the k₁=0.25 two-beam resolution floor (λ/2NA)

# Coupling (v1.2) colours — the Phase 1↔2 back-coupling (oxidation reaching back on the profile).
INERT_COLOR = "#888888"         # the baseline: a sealed inert drive-in (no oxidation, no coupling)
OED_COLOR = "#d4711f"           # OED only — the enhanced, deeper profile (amber, like oxidation)
COUPLED_COLOR = "#2f6fb0"       # OED + segregation — the full back-coupling (boron depletion case)
PILEUP_COLOR = "#27795b"        # the phosphorus pile-up case (green — the opposite-sign signature)
SEED_COLOR = "#bbbbbb"          # the starting profile (the predep seed before the oxidizing anneal)

# High-concentration D(N) (v1.3) colours — the concentration-dependent-diffusivity box.
CONST_D_COLOR = "#888888"       # the constant intrinsic-D erfc baseline (grey — what Phase 1a assumed)
BOX_COLOR = "#2f6fb0"           # the enhanced D(N) box profile (the deeper, steeper phosphorus front)
NLINEAR_COLOR = "#d4711f"       # the n¹ companion (arsenic — boxier than constant, less than n²)
ENH_COLOR = "#a93226"           # the D_eff/D_intrinsic enhancement curve (crimson — the mechanism)
NI_COLOR = "#27795b"            # the intrinsic carrier concentration n_i (where the enhancement bites)

# Defocus (v1.4) colours — the Bossung curve & the through-focus fundamental.
BOSSUNG_COLOR = "#6a3d9a"       # the nominal-dose Bossung CD-vs-defocus curve (violet — same family as litho)
WINDOW_COLOR = "#27795b"        # the process window (the usable focus band)
ENVELOPE_COLOR = "#a93226"      # the exact 4c₀c₁cos φ analytic envelope (crimson — the tight anchor)
ONAXIS_COLOR = "#2f6fb0"        # the on-axis coherent fundamental (data points on the envelope)
PARTIAL_COLOR = "#d4711f"       # the σ-source fundamental — the null softened by partial coherence
DOF_COLOR = "#c0392b"           # the depth-of-focus event (the φ=π/2 null) marker

# PEB (v1.7) colours — the baked latent image & the PEB window (the bake's trade-off).
LATENT_COLOR = "#6a3d9a"        # the unbaked aerial/latent image (violet — the litho family)
BAKE_COLORS = ("#9a7bc0", "#c79fd9", "#e2c7ee")   # the cited 20/40/60 nm series, fading with σ
RIPPLE_COLOR = "#2f6fb0"        # standing-wave ripple retention (the thing the bake must erase)
KEEP_COLOR = "#27795b"          # lateral fundamental retention (the thing the bake must keep)
RULE_COLOR = "#c0392b"          # the cited half-period smoothing rule σ = λ/4n (the floor)
PEB_WINDOW_COLOR = "#27795b"    # the open PEB window (smooth enough ∧ image kept)

# Device (Phase 4) colours — the V_t waterfall (where the threshold voltage comes from).
VFB_COLOR = "#8e44ad"           # the flat-band voltage term (gate work function)
BAND_COLOR = "#2f6fb0"          # the 2φ_F surface-potential term
DEPL_COLOR = "#d4711f"          # the depletion-charge term Q_dep/C_ox
VT_COLOR = "#27795b"            # the resulting threshold voltage V_t


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


def thin_oxide_figure(
    t_min: np.ndarray,
    curves: dict,
    rates,
    gate_t_min: float,
    gate_massoud_nm: float,
    gate_v1_nm: float,
    T_celsius: float = 1000.0,
    orientation: str = "100",
) -> "plt.Figure":
    """The v1.1 thin-oxide artifact: the Massoud burst before/after, beside its decaying rate.

    ``curves`` carries the µm thickness sweeps (``massoud``, ``plain_same_ba``, ``v1_dg1965``)
    and the nm/min rate sweeps (``rate_massoud``, ``rate_plain``) over ``t_min`` (minutes);
    ``rates`` is the evaluated Massoud set (for the τ annotations); the ``gate_*`` scalars mark
    the Phase-4 gate-oxide recipe point on both models.

    Left panel (**the banked readout** — linear axes, the thin regime): oxide thickness vs time —
    the Massoud curve outrunning both the same-B,A baseline (the burst isolated) and the v1
    plain-1965 prediction, with the gate-recipe before/after gap marked. The ~25 nm anomaly
    ceiling is drawn as the named scope line.

    Right panel (**the mechanism** — why): the growth rate vs time, log-y — the Massoud rate
    starting several × the linear plateau and decaying on τ₁/τ₂ onto the plain linear-parabolic
    rate (the burst is a *finite* transient, not a new regime).

    Consumes plain arrays/scalars only (ADR 0002).
    """
    fig, (ax_x, ax_r) = plt.subplots(1, 2, figsize=(13, 6))
    t = np.asarray(t_min, dtype=float)
    nm = 1.0e3

    # --- left: thickness vs time — the before/after ---------------------------------
    ax_x.plot(t, curves["massoud"] * nm, color=MASSOUD_COLOR, lw=2.6, zorder=5,
              label="Massoud time-decay model (cited)")
    ax_x.plot(t, curves["plain_same_ba"] * nm, color=BASELINE_COLOR, lw=1.8, ls="--",
              label="same B, A — burst switched off")
    ax_x.plot(t, curves["v1_dg1965"] * nm, color=DRY_COLOR, lw=2.2,
              label="v1 chain: plain Deal–Grove (1965 constants)")
    ax_x.axhline(25.0, color="#555555", ls=":", lw=1.2)
    ax_x.text(0.985, 25.6, "≈ end of the thin-regime anomaly (~25 nm)", fontsize=8,
              color="#555555", ha="right", transform=ax_x.get_yaxis_transform())
    # The gate-recipe before/after gap.
    ax_x.plot([gate_t_min, gate_t_min], [gate_v1_nm, gate_massoud_nm],
              color=JUNCTION_COLOR, lw=1.4, ls="-", marker="o", ms=6, zorder=6)
    ax_x.annotate(
        f"the gate-oxide recipe ({gate_t_min:.0f} min):\n"
        f"{gate_v1_nm:.1f} nm → {gate_massoud_nm:.1f} nm "
        f"(+{gate_massoud_nm - gate_v1_nm:.0f} nm the v1 chain missed)",
        xy=(gate_t_min, 0.5 * (gate_v1_nm + gate_massoud_nm)),
        xytext=(gate_t_min * 1.22, gate_v1_nm * 0.55),
        fontsize=9, color=JUNCTION_COLOR,
        arrowprops=dict(arrowstyle="->", color=JUNCTION_COLOR, lw=1.2),
    )
    ax_x.set_xlim(t[0], t[-1])
    ax_x.set_ylim(0, max(float((curves["massoud"] * nm).max()) * 1.12, 28.0))
    ax_x.set_xlabel("oxidation time  (min)")
    ax_x.set_ylabel("oxide thickness  $x_{ox}$  (nm)")
    ax_x.set_title(f"the thin-dry burst at {T_celsius:.0f} °C, (" + orientation + ") Si, dry O₂")
    ax_x.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax_x.grid(True, alpha=0.18)

    # --- right: the decaying growth rate (the mechanism) ----------------------------
    interior = t > 0
    ax_r.semilogy(t[interior], curves["rate_massoud"][interior], color=MASSOUD_COLOR, lw=2.4,
                  label="Massoud rate  $(B+K_1e^{-t/\\tau_1}+K_2e^{-t/\\tau_2})/(A+2x)$")
    ax_r.semilogy(t[interior], curves["rate_plain"][interior], color=BASELINE_COLOR, lw=1.8,
                  ls="--", label="plain rate  $B/(A+2x)$ — same B, A")
    for tau, name in ((rates.tau1, "$\\tau_1$"), (rates.tau2, "$\\tau_2$")):
        ax_r.axvline(tau, color="#555555", ls=":", lw=1.1)
        ax_r.text(tau, 0.965, f" {name} = {tau:.1f} min", fontsize=8.5, color="#555555",
                  va="top", transform=ax_r.get_xaxis_transform())
    ax_r.set_xlim(t[0], t[-1])
    ax_r.set_xlabel("oxidation time  (min)")
    ax_r.set_ylabel("growth rate  $dx_{ox}/dt$  (nm/min)")
    ax_r.set_title("the mechanism: a finite burst decaying onto linear-parabolic")
    ax_r.text(0.5, 0.84, "the enhancement is worth exactly $M_1{+}M_2 = K_1\\tau_1{+}K_2\\tau_2$\n"
              "of extra $x^2{+}Ax$ — then Deal–Grove again",
              transform=ax_r.transAxes, fontsize=8.5, va="top", ha="center",
              bbox=dict(boxstyle="round", fc="white", ec="#cccccc", alpha=0.9))
    ax_r.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    ax_r.grid(True, which="both", alpha=0.18)

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


def device_figure(result) -> "plt.Figure":
    """The banked Phase-4 artifact: the whole process→device flow on one figure — recipe in, V_t out.

    The chip's payoff figure (counterpart of Steel's four-curves anchor): one coherent n-MOSFET chained
    through every process module, the device parameter read off the end. ``result`` is the demo's plain
    :class:`~chip.demo_device.FlowResult` bundle (frozen dataclasses + arrays — no live solver
    object, ADR 0002). Four panels, the forward flow:

      ① **diffusion** — the n⁺ source/drain profile into the p-type channel, junction depth marked;
      ② **oxidation** — the Deal–Grove growth curve with the thin **gate-oxide** point marked;
      ③ **litho** — the gate aerial image, the printed CD (= channel length) shaded;
      ④ **device** — the ``V_t`` *waterfall*: ``V_FB`` + ``2φ_F`` + ``Q_dep/C_ox`` stacking to the
         threshold voltage, with ``γ``, ``C_ox`` and the long-channel ``I_Dsat`` annotated.

    The coherence is the message: the three process outputs describe the **same** device, so ``V_t`` is
    the genuine consequence of the recipe (the advisor's flagged requirement — not three unrelated
    numbers on one canvas).
    """
    r = result
    m = r.mos
    fig, ((ax_d, ax_o), (ax_l, ax_v)) = plt.subplots(2, 2, figsize=(13.5, 10))

    # --- ① diffusion: n⁺ S/D into the p-channel -------------------------------------
    xum = _depth_um(r.sd_drivein.x)
    ax_d.semilogy(xum, np.maximum(r.sd_drivein.N, 1.0), color=DRIVEIN_COLOR, lw=2.4,
                  label=f"n⁺ {r.sd_junction.dopant} source/drain")
    ax_d.axhline(m.N_A, color=BACKGROUND_COLOR, ls="--", lw=1.4,
                 label=f"p-channel $N_A$ = {m.N_A:.0e} cm⁻³")
    xj = r.sd_junction.x_j_um
    ax_d.axvline(xj, color=JUNCTION_COLOR, ls=":", lw=1.6)
    ax_d.plot([xj], [m.N_A], "o", color=JUNCTION_COLOR, ms=7, zorder=5)
    ax_d.annotate(f"S/D junction\n$x_j$ = {xj:.2f} µm", xy=(xj, m.N_A),
                  xytext=(xj * 0.5, m.N_A * 60), color=JUNCTION_COLOR, fontsize=9, ha="center",
                  arrowprops=dict(arrowstyle="->", color=JUNCTION_COLOR, lw=1.1))
    ax_d.set_xlim(0, min(float(xum[-1]), xj * 3))
    ax_d.set_ylim(m.N_A * 0.3, float(r.sd_drivein.N[0]) * 3)
    ax_d.set_xlabel("depth  (µm)")
    ax_d.set_ylabel("dopant concentration $N$  (cm⁻³)")
    ax_d.set_title("① diffusion — n⁺ source/drain into the p-channel")
    ax_d.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    ax_d.grid(True, which="both", alpha=0.18)

    # --- ② oxidation: the thin gate oxide on the Deal–Grove curve --------------------
    t = r.t_hours
    ax_o.loglog(t, r.oxide_curve, color=DRY_COLOR, lw=2.6, label="dry O₂ growth (Deal–Grove)")
    tg = r.gate_oxide.t_minutes / 60.0
    ax_o.plot([tg], [r.gate_oxide.t_ox], "o", color=THRESHOLD_COLOR, ms=8, zorder=6)
    ax_o.annotate(f"gate oxide\n$t_{{ox}}$ = {r.gate_oxide.t_ox_nm:.0f} nm", xy=(tg, r.gate_oxide.t_ox),
                  xytext=(tg * 0.22, r.gate_oxide.t_ox * 2.3), color=THRESHOLD_COLOR, fontsize=9, ha="center",
                  arrowprops=dict(arrowstyle="->", color=THRESHOLD_COLOR, lw=1.1))
    ax_o.set_xlim(float(t[0]), float(t[-1]))
    ax_o.set_xlabel("oxidation time  (hr)")
    ax_o.set_ylabel("oxide thickness  $x_{ox}$  (µm)")
    ax_o.set_title("② oxidation — a thin dry gate oxide (reaction-limited)")
    ax_o.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    ax_o.grid(True, which="both", alpha=0.18)

    # --- ③ litho: the gate aerial image → CD (channel length) ------------------------
    x, I = np.asarray(r.litho_x_nm), np.asarray(r.litho_intensity)
    ax_l.plot(x, I, color=AERIAL_COLOR, lw=2.6, label="gate aerial image")
    ax_l.axhline(r.litho_threshold, color=THRESHOLD_COLOR, ls="--", lw=1.5,
                 label=f"resist threshold = {r.litho_threshold:.2f}")
    cd = r.gate_feature.cd_nm
    centre = r.gate_feature.pitch_nm / 2.0               # the dark line (clear-space centre at x=0)
    ax_l.axvspan(centre - cd / 2, centre + cd / 2, color=THRESHOLD_COLOR, alpha=0.12)
    ax_l.annotate(f"gate length\nCD = {cd:.0f} nm", xy=(centre, r.litho_threshold),
                  xytext=(centre, r.litho_threshold + 0.30 * I.max()), color=THRESHOLD_COLOR,
                  fontsize=9, ha="center", arrowprops=dict(arrowstyle="->", color=THRESHOLD_COLOR, lw=1.1))
    ax_l.set_xlim(float(x[0]), float(x[-1]))
    ax_l.set_ylim(0, I.max() * 1.35)
    ax_l.set_xlabel("position  $x$  (nm)")
    ax_l.set_ylabel("aerial-image intensity  $I(x)$")
    ax_l.set_title("③ litho — the gate aerial image → CD = channel length")
    ax_l.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    ax_l.grid(True, alpha=0.18)

    # --- ④ device: the V_t waterfall (where the threshold voltage comes from) ---------
    segments = [
        ("$V_{FB}$", 0.0, m.V_FB, VFB_COLOR),
        ("$+\\,2\\phi_F$", m.V_FB, m.V_FB + m.two_phi_F, BAND_COLOR),
        ("$+\\,Q_{dep}/C_{ox}$", m.V_FB + m.two_phi_F, m.V_t, DEPL_COLOR),
    ]
    for i, (_, lo, hi, color) in enumerate(segments):
        ax_v.bar(i, hi - lo, bottom=lo, width=0.68, color=color, edgecolor="white", zorder=3)
        ax_v.text(i, hi + (0.03 if hi >= lo else -0.03) * (1 if hi >= 0 else -1),
                  f"{hi - lo:+.2f}", ha="center", va="bottom" if hi >= lo else "top", fontsize=9)
        if i > 0:                                         # connector from the previous segment top
            ax_v.plot([i - 1 + 0.34, i - 0.34], [lo, lo], color="#999999", lw=0.9, ls=":", zorder=2)
    ax_v.bar(3, m.V_t, bottom=0.0, width=0.68, color=VT_COLOR, edgecolor="white", zorder=3)
    ax_v.axhline(0.0, color="#444444", lw=0.8)
    ax_v.annotate(f"$V_t$ = {m.V_t:.3f} V", xy=(3, m.V_t), xytext=(3, m.V_t + 0.16),
                  ha="center", fontsize=11, fontweight="bold", color=VT_COLOR)
    ax_v.set_xticks([0, 1, 2, 3])
    ax_v.set_xticklabels(["$V_{FB}$", "$2\\phi_F$", "$Q_{dep}/C_{ox}$", "$V_t$"], fontsize=9)
    ax_v.set_ylabel("contribution to $V_t$  (V)")
    ax_v.set_title("④ device — the threshold voltage and where it comes from")
    ax_v.text(0.03, 0.04,
              f"$N_A$ = {m.N_A:.0e} cm⁻³,  $t_{{ox}}$ = {m.t_ox_um * 1e3:.0f} nm,  {m.gate} gate\n"
              f"$C_{{ox}}$ = {m.C_ox:.2e} F/cm²,  $\\gamma$ = {m.gamma:.2f} V$^{{1/2}}$,  "
              f"$I_{{Dsat}}$ = {r.i_dsat * 1e3:.1f} mA",
              transform=ax_v.transAxes, fontsize=8.5, va="bottom",
              bbox=dict(boxstyle="round", fc="white", ec="#cccccc", alpha=0.9))
    ax_v.grid(True, axis="y", alpha=0.18)

    fig.suptitle("Microchip: process → device — a coherent n-MOSFET, recipe in → $V_t$ out",
                 fontsize=13, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return fig


def coupling_figure(cases: list[dict]) -> "plt.Figure":
    """The banked v1.2 artifact: oxidation reaching back on the dopant profile (OED + segregation).

    One panel per dopant ``case`` (a dict from :func:`demo_coupling.compute`), each over-plotting the
    same depth axis (log concentration):

      * the **seed** (the predep before the oxidizing anneal, faint);
      * the **inert** drive-in (grey baseline — what v1 assumed: no back-coupling);
      * **OED only** (amber — the profile pushed *deeper*, the diffusivity enhanced by injected
        interstitials);
      * **OED + segregation** (the full coupling — the surface reshaped: **boron depletes**,
        **phosphorus piles up**), with the surface concentration shift annotated.

    The teaching point drawn straight on the figure: *oxidation is not a bystander — it enhances the
    diffusion and partitions the dopant at the moving interface.* Consumes plain arrays / the
    :class:`coupling.CoupledResult` dataclasses (no live solver object, ADR 0002).
    """
    n = len(cases)
    fig, axes = plt.subplots(1, n, figsize=(6.6 * n, 6), squeeze=False)
    for ax, case in zip(axes[0], cases):
        inert, oed, coupled = case["inert"], case["oed"], case["coupled"]
        sig_color = COUPLED_COLOR if case["sign"] == "depletion" else PILEUP_COLOR
        x_um = _depth_um(inert.x)

        ax.semilogy(x_um, np.maximum(case["seed"], 1.0), color=SEED_COLOR, lw=1.4, ls=":",
                    label=f"seed (predep), surface {case['seed'][0]:.1e}")
        ax.semilogy(x_um, np.maximum(inert.N, 1.0), color=INERT_COLOR, lw=2.0,
                    label=f"inert drive-in, surface {inert.surface_concentration:.1e}")
        ax.semilogy(x_um, np.maximum(oed.N, 1.0), color=OED_COLOR, lw=2.2,
                    label=f"+ OED (×{oed.effective_Dt / (oed.D_inert * oed.t_seconds):.2f} eff. $\\int\\!D\\,dt$)")
        ax.semilogy(x_um, np.maximum(coupled.N, 1.0), color=sig_color, lw=2.6,
                    label=f"+ segregation, surface {coupled.surface_concentration:.1e}")

        # Annotate the surface shift (the segregation signature): depletion (down) or pile-up (up).
        # Read against OED-only — the amber→coloured step — so it ISOLATES segregation from OED's
        # spreading (OED deepens the profile, dropping the surface peak for both dopants; segregation
        # then reshapes it: boron further down, phosphorus back up). Coupled-vs-inert would conflate
        # the two and hide phosphorus pile-up behind the OED drop.
        ratio = coupled.surface_concentration / oed.surface_concentration
        verb = "depletes" if case["sign"] == "depletion" else "piles up"
        ax.annotate(
            f"surface {verb} vs OED\n×{ratio:.2f}  (m = {case['m']})",
            xy=(x_um[coupled.surface_index], coupled.surface_concentration),
            # text low-centre, well clear of the upper-right legend (arrow runs to the surface cell).
            xytext=(x_um[-1] * 0.34, coupled.surface_concentration * 0.10),
            color=sig_color, fontsize=9.5, ha="center",
            arrowprops=dict(arrowstyle="->", color=sig_color, lw=1.2),
        )
        floor = min(inert.surface_concentration, coupled.surface_concentration) * 1e-3
        ceil = max(case["seed"][0], coupled.surface_concentration) * 4
        ax.set_ylim(max(floor, 1e13), ceil)
        ax.set_xlim(0, x_um[-1] * 0.6)
        ax.set_xlabel("depth  (µm)")
        ax.set_ylabel("dopant concentration $N$  (cm⁻³)")
        ax.set_title(f"{case['name']} — {case['sign']} ($f_I$ = {case['f_I']})")
        ax.legend(loc="upper right", fontsize=8.3, framealpha=0.95)
        ax.grid(True, which="both", alpha=0.18)
        # The moving boundary (default) recedes the silicon surface 0.44·x_ox as oxide grows, so the
        # swept-sliver double-count is gone — both signatures are quantitative now. Note the recession.
        recede_nm = coupled.interface_depth / CM_PER_UM * 1e3
        note = (f"robust (oxide-uptake-dominated)\nsurface receded {recede_nm:.0f} nm"
                if case["sign"] == "depletion"
                else f"quantitative (moving boundary)\nsurface receded {recede_nm:.0f} nm")
        ax.text(0.03, 0.03, note, transform=ax.transAxes, fontsize=7.6, va="bottom", ha="left",
                color="#555555", style="italic",
                bbox=dict(boxstyle="round", fc="white", ec="#dddddd", alpha=0.85))

    fig.suptitle("Microchip v1.2: the Phase 1↔2 back-coupling — oxidation reshapes the dopant profile",
                 fontsize=13, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def highconc_figure(case: dict) -> "plt.Figure":
    """The banked v1.3 artifact: concentration-dependent ``D(N)`` → the high-concentration box.

    Two panels from a :func:`demo_diffusion_highconc.compute` ``case`` dict:

      * **left — the box profile.** Log concentration vs depth: the constant-intrinsic-``D`` ``erfc``
        (grey, what Phase 1a assumed), the **active-carrier-capped** ``D(N)`` box (solid blue, the
        physical headline), and the **full-activation** box (faint blue — the ``n=N`` upper bound,
        ~10× larger magnitude: the activation caveat, drawn). The intrinsic ``n_i`` line marks where
        the enhancement bites; the junction depths into the background ``N_B`` are marked.
      * **right — the mechanism.** ``D_eff(N)/D_intrinsic`` along the (capped) box profile: the
        diffusivity is large near the surface (``N ≫ n_i``), plateaus at the activation cap, and
        collapses to ``1`` in the dilute tail — *that* depth-varying enhancement is what carves the box.

    Drawn straight on the figure: the box front + deeper junction are captured; the anomalous
    phosphorus **tail** is the named scope edge (non-equilibrium, not in an equilibrium ``D(n)``).
    Consumes plain arrays (no live solver object, ADR 0002).
    """
    fig, (ax, axm) = plt.subplots(1, 2, figsize=(13.2, 6))
    x_um = _depth_um(case["x"])
    n_i, N_B = case["n_i"], case["N_background"]

    # -- left: the profiles ------------------------------------------------- #
    ax.semilogy(x_um, np.maximum(case["const"], 1.0), color=CONST_D_COLOR, lw=2.0, ls="--",
                label=f"constant intrinsic $D$ (erfc), $x_j$ = {case['xj_const']:.2f} µm")
    if "box_uncapped" in case:
        ax.semilogy(x_um, np.maximum(case["box_uncapped"], 1.0), color=BOX_COLOR, lw=1.5, ls=":",
                    alpha=0.55,
                    label=f"box, full activation $n=N$ (upper bound), $x_j$ = {case['xj_box_uncapped']:.2f} µm")
    ax.semilogy(x_um, np.maximum(case["box"], 1.0), color=BOX_COLOR, lw=2.6,
                label=f"$D(N)$ box ({case['name']}, $n^2$, capped), $x_j$ = {case['xj_box']:.2f} µm")
    ax.axhline(n_i, color=NI_COLOR, lw=1.2, ls=":", label=f"$n_i$ = {n_i:.1e} cm⁻³")
    ax.axhline(N_B, color=BACKGROUND_COLOR, lw=1.2, ls="-.", label=f"background $N_B$ = {N_B:.0e} cm⁻³")
    for xj, col in ((case["xj_const"], CONST_D_COLOR), (case["xj_box"], BOX_COLOR)):
        if np.isfinite(xj):
            ax.axvline(xj, color=col, lw=1.0, ls=":", alpha=0.7)
    ax.set_xlim(0, x_um[-1] * 0.85)
    ax.set_ylim(max(N_B * 1e-2, 1e13), case["N_surface"] * 4)
    ax.set_xlabel("depth  (µm)")
    ax.set_ylabel("dopant concentration $N$  (cm⁻³)")
    ax.set_title(f"the box: concentration-dependent $D$ pushes {case['name']} deeper, steeper")
    ax.legend(loc="upper right", fontsize=8.3, framealpha=0.95)
    ax.grid(True, which="both", alpha=0.18)
    ax.text(0.03, 0.03,
            "front captured; anomalous tail NOT modelled\n(non-equilibrium — the named scope edge)",
            transform=ax.transAxes, fontsize=7.6, va="bottom", ha="left", color="#555555",
            style="italic", bbox=dict(boxstyle="round", fc="white", ec="#dddddd", alpha=0.85))

    # -- right: the mechanism (D enhancement vs depth) ---------------------- #
    axm.semilogy(x_um, np.maximum(case["enhancement"], 1e-3), color=ENH_COLOR, lw=2.4)
    axm.axhline(1.0, color=CONST_D_COLOR, lw=1.4, ls="--", label="intrinsic $D$ (×1)")
    axm.set_xlim(0, x_um[-1] * 0.85)
    axm.set_xlabel("depth  (µm)")
    axm.set_ylabel("$D_\\mathrm{eff}(N)\\,/\\,D_\\mathrm{intrinsic}$")
    axm.set_title(f"why: $D$ is ×{case['surface_enhancement']:.0f} at the surface (capped), ×1 in the tail")
    axm.legend(loc="upper right", fontsize=9)
    axm.grid(True, which="both", alpha=0.18)

    fig.suptitle("Microchip v1.3: concentration-dependent diffusivity $D(N)$ — the high-concentration box "
                 "(within the engine)", fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def defocus_figure(
    data: dict,
    wavelength_nm: float,
    NA: float,
    sigma: float,
    pitch_nm: float,
    dose_fractions: tuple,
    cd_spec: float,
) -> "plt.Figure":
    """The banked v1.4 artifact: the Bossung curve & the through-focus fundamental (depth of focus).

    ``data`` is the :func:`demo_defocus.compute` bundle (plain arrays/scalars — no live imaging object,
    ADR 0002). Two panels:

    Left panel (**the banked readout** — the Bossung curve): printed **CD vs defocus** at each fixed dose
    (the Bossung "smile" family), the **process window** (CD within ±``cd_spec`` of target at the nominal
    dose) shaded, and the Rayleigh ``DOF = k₂·λ/NA²`` marked. *Where the printed feature stays on-size as
    focus drifts — the usable focus budget.*

    Right panel (**the mechanism** — why focus runs out): the on-axis three-beam **fundamental** vs
    defocus (markers) lying on the exact ``4·c₀·c₁·cos φ`` **envelope** (line) — the tight anchor —
    **nulling at φ = π/2** = the depth-of-focus event, beyond which the fundamental reverses and the image
    frequency-doubles (contrast reversal). The σ-source curve shows partial coherence softening the null.
    """
    fig, (ax_b, ax_f) = plt.subplots(1, 2, figsize=(13, 6))
    z = np.asarray(data["zabs"])
    dof, z_null = data["dof"], data["z_null"]

    # --- left: the Bossung family + the process window -------------------------------
    nominal = 0.50 if 0.50 in dose_fractions else dose_fractions[len(dose_fractions) // 2]
    for f in dose_fractions:
        cd = np.asarray(data["bossung"][f], dtype=float).copy()
        cd[cd <= 0.0] = np.nan                          # don't dive to the axis where the feature stops printing
        is_nom = abs(f - nominal) < 1e-9
        ax_b.plot(z, cd, color=BOSSUNG_COLOR, lw=2.6 if is_nom else 1.6,
                  alpha=1.0 if is_nom else 0.55, zorder=4 if is_nom else 3,
                  label=f"dose {f*100:.0f} %" + ("  (nominal)" if is_nom else ""))
    if data["window"] is not None:
        lo, hi = data["window"]
        ax_b.axvspan(lo, hi, color=WINDOW_COLOR, alpha=0.13, zorder=1,
                     label=f"process window (±{cd_spec*100:.0f} % CD): {hi - lo:.0f} nm")
    for s in (-1.0, 1.0):
        ax_b.axvline(s * dof, color=DOF_COLOR, ls="--", lw=1.4, alpha=0.8,
                     label=(f"±DOF = ±{dof:.0f} nm  ($k_2$=0.5)" if s > 0 else None))
    ax_b.set_xlim(float(z[0]), float(z[-1]))
    ax_b.set_xlabel("defocus  $z$  (nm)")
    ax_b.set_ylabel("printed CD  (nm)")
    ax_b.set_title(f"the Bossung curve: CD vs defocus  (pitch {pitch_nm:.0f} nm, σ={sigma:.2f})")
    ax_b.legend(loc="lower center", fontsize=8.3, framealpha=0.95)
    ax_b.grid(True, alpha=0.18)

    # --- right: the fundamental through focus — the exact envelope + the null --------
    ax_f.plot(z, data["envelope"], color=ENVELOPE_COLOR, lw=2.4, zorder=3,
              label="exact envelope  $4c_0c_1\\cos\\varphi$")
    ax_f.plot(z[::6], np.asarray(data["on_axis"])[::6], "o", color=ONAXIS_COLOR, ms=4.5, zorder=5,
              label="on-axis fundamental (coherent)")
    ax_f.plot(z, data["partial"], color=PARTIAL_COLOR, lw=2.0, ls="-", alpha=0.9,
              label=f"σ={sigma:.2f} fundamental (null softened)")
    ax_f.axhline(0.0, color="#444444", lw=0.8)
    for s in (-1.0, 1.0):
        ax_f.axvline(s * z_null, color=DOF_COLOR, ls=":", lw=1.6,
                     label=(f"φ=π/2 null at ±{z_null:.0f} nm (DOF event)" if s > 0 else None))
    # Shade and label the frequency-doubling (contrast-reversal) zone beyond the null.
    ax_f.axvspan(z_null, float(z[-1]), color=DOF_COLOR, alpha=0.06)
    ax_f.axvspan(float(z[0]), -z_null, color=DOF_COLOR, alpha=0.06)
    ax_f.text(0.985, 0.04, "beyond the null:\nfrequency doubling\n(contrast reversal)", fontsize=8,
              color=DOF_COLOR, ha="right", va="bottom", transform=ax_f.transAxes,
              bbox=dict(boxstyle="round", fc="white", ec="#e3c0bc", alpha=0.9))
    ax_f.set_xlim(float(z[0]), float(z[-1]))
    ax_f.set_xlabel("defocus  $z$  (nm)")
    ax_f.set_ylabel("image fundamental  $\\langle I,\\cos(2\\pi x/p)\\rangle$")
    ax_f.set_title("why: the fundamental fades to a null, then reverses (the DOF)")
    ax_f.legend(loc="upper right", fontsize=8.0, framealpha=0.95)
    ax_f.grid(True, alpha=0.18)

    fig.suptitle("Microchip v1.4: lithographic defocus — the Bossung curve & the depth of focus "
                 "(within the litho module)", fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def peb_figure(
    data: dict,
    wavelength_nm: float,
    NA: float,
    sigma_src: float,
    pitch_nm: float,
    n_resist: float,
    keep_floor: float,
) -> "plt.Figure":
    """The banked v1.7 artifact: the baked latent image & the PEB window (acid-diffusion blur).

    ``data`` is the :func:`demo_peb.compute` bundle (plain arrays/scalars — no live solver object,
    ADR 0002). Two panels:

    Left panel (**the banked readout** — the latent image dissolving): the aerial image at the demo
    pitch and its post-bake latent images over the cited 20/40/60 nm diffusion-length series, with
    the blur-invariant mean clip drawn once — *the harmonics die as exp(−2π²k²σ²/p²), the profile
    collapses toward its conserved mean, and the CD walks onto the pure-fundamental p/2 readout.*

    Right panel (**the mechanism** — the PEB window): retention vs σ for the bake's two jobs —
    erasing the standing-wave depth ripple (period λ/2n) and keeping the lateral image fundamental
    (period p) — engine points riding the two analytic heat-kernel envelopes; the cited half-period
    smoothing rule marks the floor, and the open window is shaded. One bake, two clocks: the same σ
    sits on both curves, so the window is wherever the blue curve is dead and the green one alive.
    """
    fig, (ax_i, ax_w) = plt.subplots(1, 2, figsize=(13, 6))

    # --- left: the aerial image + the cited baked family --------------------------------
    x = np.asarray(data["x"])
    ax_i.plot(x, data["aerial"], color=LATENT_COLOR, lw=2.4, zorder=4,
              label="aerial image (σ = 0 — unbaked)")
    series = [s for s in data["family_sigmas"] if s > 0.0]
    for s, color in zip(series, BAKE_COLORS):
        cd = data["features"][s].cd_nm
        ax_i.plot(x, data["family"][s], color=color, lw=2.0, zorder=3,
                  label=f"baked σ = {s:.0f} nm   (CD {cd:.1f} nm)")
    ax_i.axhline(data["dose"], color=THRESHOLD_COLOR, ls="--", lw=1.4, alpha=0.85,
                 label="mean clip (dose) — blur-invariant")
    cd0 = data["features"][0.0].cd_nm
    ax_i.set_xlim(float(x[0]), float(x[-1]))
    ax_i.set_xlabel("position  $x$  (nm)")
    ax_i.set_ylabel("intensity / latent acid  (a.u.)")
    ax_i.set_title(f"the latent image dissolving  (pitch {pitch_nm:.0f} nm; unbaked CD {cd0:.1f} nm)")
    ax_i.legend(loc="lower center", fontsize=8.3, framealpha=0.95)
    ax_i.grid(True, alpha=0.18)

    # --- right: the PEB window — two retentions, one σ ----------------------------------
    sig = np.asarray(data["sigmas"])
    ax_w.plot(sig, data["ripple_analytic"], color=RIPPLE_COLOR, lw=2.2, zorder=3,
              label=f"standing-wave ripple (period λ/2n = {data['t_sw']:.0f} nm) — erase me")
    ax_w.plot(sig[::4], np.asarray(data["ripple_engine"])[::4], "o", color=RIPPLE_COLOR, ms=4.5,
              zorder=5, label="engine (peb_blur along z)")
    ax_w.plot(sig, data["keep_analytic"], color=KEEP_COLOR, lw=2.2, zorder=3,
              label=f"image fundamental (pitch {pitch_nm:.0f} nm) — keep me")
    ax_w.plot(sig[::4], np.asarray(data["keep_engine"])[::4], "s", color=KEEP_COLOR, ms=4.5,
              zorder=5, label="engine (peb_blur along x)")
    rule, keep_edge = data["sigma_rule"], data["sigma_keep"]
    ax_w.axvline(rule, color=RULE_COLOR, ls="--", lw=1.5,
                 label=f"cited smoothing rule σ = λ/4n = {rule:.0f} nm")
    ax_w.axvspan(rule, keep_edge, color=PEB_WINDOW_COLOR, alpha=0.12, zorder=1,
                 label=f"the PEB window  [{rule:.0f}, {keep_edge:.0f}] nm "
                       f"(≥{keep_floor:.0%} fundamental kept)")
    ax_w.axhline(keep_floor, color="#888888", lw=0.8, ls=":")
    ax_w.text(0.985, 0.60, f"closes at p_close ≈ {data['p_close']:.0f} nm\n"
                           f"(= λ/4nc — NA-independent); optical\n"
                           f"cutoff λ/NA(1+σ): {data['p_cutoff']:.0f}→{data['p_cutoff_hi']:.0f} nm at\n"
                           f"NA 0.85→0.93 → lens out-resolves\nthe bake → use a BARC",
              fontsize=8, color="#444444", ha="right", va="center", transform=ax_w.transAxes,
              bbox=dict(boxstyle="round", fc="white", ec="#cccccc", alpha=0.9))
    ax_w.set_xlim(float(sig[0]), float(sig[-1]))
    ax_w.set_ylim(0.0, 1.05)
    ax_w.set_xlabel("acid diffusion length  σ = √(2Dt)  (nm)")
    ax_w.set_ylabel("modulation retention  (per heat kernel)")
    ax_w.set_title("the PEB window: erase the ridges, keep the image")
    ax_w.legend(loc="upper right", fontsize=8.0, framealpha=0.95)
    ax_w.grid(True, alpha=0.18)

    fig.suptitle("Microchip v1.7: PEB acid-diffusion blur — the resist back-end rides the engine "
                 f"(λ = {wavelength_nm:.0f} nm, NA = {NA:.2f}, σ_src = {sigma_src:.2f}, "
                 f"resist n = {n_resist:.2f})", fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


# Lateral diffusion (v1.8) colours — the 2-D mask-edge regime.
JUNCTION_CONTOUR_COLOR = "#c0392b"   # the N = N_B junction contour (crimson — same as the 1-D junction)
MASK_BAR_COLOR = "#555555"           # the masking film on the surface (the sealed region)
WINDOW_BAR_COLOR = "#e07b39"         # the open window (warm — where the source enters, like the predep)
RATIO_CURVE_COLOR = "#2f6fb0"        # the engine lateral/vertical ratio vs contour
RATIO_BAND_COLOR = "#27795b"         # the cited 0.75–0.85 rule-of-thumb band
DEVICE_JUNCTION_COLOR = "#6a3d9a"    # the realistic device junction (the headline contour)


def lateral_diffusion_figure(data) -> "plt.Figure":
    """The banked 2-D artifact: the junction curving under the mask, beside the ratio-vs-contour.

    Left panel (**the banked readout** — the genuinely-2-D junction): the boron field ``N(x, y)``
    (log fill, depth downward), the mask drawn on the surface (open window | hatched mask), and the
    device ``N = N_B`` junction contour overlaid — flat/deep under the window, wrapping up under the
    mask at the edge. The **vertical** (window centre) and **lateral** (under-mask reach) extents
    are marked; their ratio is the headline.

    Right panel (**the mechanism** — the contour-dependence): the engine lateral/vertical ratio vs
    ``C_B/N_s``. The shallow contours sit in the cited **0.75–0.85 band** (shaded) and the ratio
    **rises toward deeper contours** (Kennedy–O'Brien 1965); the curve runs a touch *above* the band
    deeper, so the device junction reaches ~0.9 — the model's own deep-contour value (a *loose*
    benchmark — within the read-off uncertainty of the cited graph, not a sourced number).

    Consumes plain arrays / the demo dict (ADR 0002) — no live solver object.
    """
    p = data["profile"]
    dev = data["device"]
    x_um = p.x / CM_PER_UM
    y_um = p.y / CM_PER_UM
    x_edge_um = p.x_edge / CM_PER_UM
    N = p.N

    fig, (ax_f, ax_r) = plt.subplots(1, 2, figsize=(13, 6))

    # --- left: the 2-D field + the junction contour curving under the mask ----------
    floor = max(data["N_B_device"] * 1e-2, 1.0)
    logN = np.log10(np.maximum(N.T, floor))             # transpose → (ny, nx): rows = depth
    X, Y = np.meshgrid(x_um, y_um)
    cf = ax_f.contourf(X, Y, logN, levels=24, cmap="magma")
    cb = fig.colorbar(cf, ax=ax_f, pad=0.02)
    cb.set_label("$\\log_{10} N$  (cm⁻³)")
    # the device junction contour N = N_B
    ax_f.contour(X, Y, N.T, levels=[data["N_B_device"]], colors=[JUNCTION_CONTOUR_COLOR],
                 linewidths=2.2)
    # the mask on the surface (a thin bar at y≈0): open window then hatched mask
    span = y_um[-1] - y_um[0]
    bar_h = 0.035 * span
    ax_f.add_patch(plt.Rectangle((x_um[0], -bar_h), x_edge_um - x_um[0], bar_h,
                                 color=WINDOW_BAR_COLOR, alpha=0.9, zorder=4, clip_on=False))
    ax_f.add_patch(plt.Rectangle((x_edge_um, -bar_h), x_um[-1] - x_edge_um, bar_h,
                                 facecolor=MASK_BAR_COLOR, hatch="//", edgecolor="white",
                                 alpha=0.95, zorder=4, clip_on=False))
    ax_f.axvline(x_edge_um, color="white", ls=":", lw=1.2, alpha=0.7)
    ax_f.text((x_um[0] + x_edge_um) / 2, -bar_h * 0.5, "window", ha="center", va="center",
              fontsize=8.5, color="white", zorder=5)
    ax_f.text((x_edge_um + x_um[-1]) / 2, -bar_h * 0.5, "mask", ha="center", va="center",
              fontsize=8.5, color="white", zorder=5)
    # vertical (window-centre) and lateral (under-mask) extents
    ax_f.annotate("", xy=(x_um[0] + 0.02, dev.vertical_um), xytext=(x_um[0] + 0.02, 0),
                  arrowprops=dict(arrowstyle="<->", color="white", lw=1.6))
    ax_f.text(x_um[0] + 0.08, dev.vertical_um * 0.5, f"vertical\n{dev.vertical_um:.2f} µm",
              color="white", fontsize=9, va="center")
    ax_f.annotate("", xy=(x_edge_um + dev.lateral_um, 0.06 * span),
                  xytext=(x_edge_um, 0.06 * span),
                  arrowprops=dict(arrowstyle="<->", color=JUNCTION_CONTOUR_COLOR, lw=1.6))
    ax_f.text(x_edge_um + dev.lateral_um * 0.5, 0.12 * span,
              f"lateral {dev.lateral_um:.2f} µm", color=JUNCTION_CONTOUR_COLOR, fontsize=9,
              ha="center")
    ax_f.set_ylim(y_um[-1], -bar_h)                     # depth downward, surface (and bar) at top
    ax_f.set_xlabel("lateral position $x$  (µm)")
    ax_f.set_ylabel("depth $y$  (µm)")
    ax_f.set_title(f"{p.dopant} junction under a mask edge "
                   f"($N_B$ = {data['N_B_device']:.0e}, ratio = {dev.ratio:.2f})")

    # --- right: the lateral/vertical ratio vs contour (the dependence) ----------------
    fracs, ratios = data["fracs"], data["ratios"]
    lo, hi = data["ratio_band"]
    ax_r.axhspan(lo, hi, color=RATIO_BAND_COLOR, alpha=0.16,
                 label=f"cited rule {lo:.2f}–{hi:.2f}")
    ax_r.semilogx(fracs, ratios, "o-", color=RATIO_CURVE_COLOR, lw=2, ms=7,
                  label="engine: lateral / vertical")
    frac_dev = data["N_B_device"] / p.N_surface
    ax_r.semilogx([frac_dev], [dev.ratio], "D", color=DEVICE_JUNCTION_COLOR, ms=10, zorder=5,
                  label=f"device junction ($C_B/N_s$ = {frac_dev:.0e})")
    ax_r.invert_xaxis()                                 # deeper contours (smaller C_B/N_s) to the right
    ax_r.set_xlabel("contour level  $C_B / N_s$")
    ax_r.set_ylabel("lateral / vertical ratio")
    ax_r.set_title("the ratio is contour-dependent (rises toward deeper contours)")
    ax_r.set_ylim(0.6, 1.0)
    ax_r.legend(loc="lower left", fontsize=9, framealpha=0.95)
    ax_r.grid(True, which="both", alpha=0.18)

    fig.suptitle("Microchip v1.8: lateral diffusion under a mask edge — the 2-D regime, "
                 f"banked  ({p.dopant}, {p.T_celsius:.0f} °C / {p.t / 60:.0f} min)",
                 fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


# CAR (v1.9) colours — the chemically-amplified reaction–diffusion bake.
ACID_COLOR = "#6a3d9a"           # the latent acid image (violet — the litho/latent family)
DEPRO_COLORS = ("#2f6fb0", "#1f8a5b", "#d4711f")   # deprotection over the bake series (cool→warm = more bake)
DEVELOP_COLOR = "#c0392b"        # the develop threshold (the dissolution contour) + nominal CD
CD_CURVE_COLOR = "#2f6fb0"       # the CD-vs-bake sensitivity curve
CAR_WINDOW_COLOR = "#27795b"     # the PEB process window (the bake latitude holding CD near nominal)
ACIDLOSS_COLOR = "#a93226"       # the exact acid-loss decay e^{−k_loss·t} (the catalyst leg, visible)
ACID_NILS_COLOR = "#999999"      # the unbaked acid-edge NILS reference (what amplification beats)


def car_figure(
    data: dict,
    wavelength_nm: float,
    NA: float,
    sigma_src: float,
    pitch_nm: float,
    acid_dose: float,
) -> "plt.Figure":
    """The banked v1.9 artifact: the latent image developing & the PEB process window (CAR PEB).

    ``data`` is the :func:`demo_car.compute` bundle (plain arrays/scalars — no live solver object,
    ADR 0002). Two panels:

    Left panel (**amplification sharpens** — the latent image developing): the dose-normalized latent
    acid image and the deprotection profiles ``1−m`` it grows over a bake-time series, with the develop
    threshold drawn once — *the superlinear hⁿ map steepens the edge above the acid's (NILS up), and
    development clips the deprotection where v1.7 clipped the acid.*

    Right panel (**the PEB process window** — CD is acutely bake-sensitive): the developed CD vs bake
    time (steep — the cited "control is critical"), the ±tol window holding CD near nominal shaded, and
    the exact acid-loss decay ``e^{−k_loss·t}`` (engine points on the analytic curve — the catalyst /
    conservation leg made visible) overlaid on a twin axis.
    """
    fig, (ax_i, ax_w) = plt.subplots(1, 2, figsize=(13, 6))

    # --- left: the latent acid image + the developing deprotection family --------------
    x = np.asarray(data["x"])
    ax_i.plot(x, data["acid"], color=ACID_COLOR, lw=2.4, zorder=4,
              label=f"latent acid (unbaked, NILS {data['acid_nils']:.2f})")
    for t, color in zip(data["family_times"], DEPRO_COLORS):
        f = data["features"][t]
        ax_i.plot(x, data["family"][t], color=color, lw=2.0, zorder=3,
                  label=f"deprotection, bake {t:.0f} s  (CD {f.cd_nm:.0f} nm, NILS {f.nils:.2f})")
    ax_i.axhline(data["develop_threshold"], color=DEVELOP_COLOR, ls="--", lw=1.4, alpha=0.85,
                 label=f"develop at {data['develop_threshold']:.0%} deprotection")
    ax_i.set_xlim(float(x[0]), float(x[-1]))
    ax_i.set_ylim(0.0, 1.02)
    ax_i.set_xlabel("position  $x$  (nm)")
    ax_i.set_ylabel("latent acid  /  deprotection  $1-m$   (a.u.)")
    ax_i.set_title(f"the latent image developing — amplification sharpens  (pitch {pitch_nm:.0f} nm)")
    ax_i.legend(loc="center right", fontsize=8.2, framealpha=0.95)
    ax_i.grid(True, alpha=0.18)

    # --- right: the CD-vs-bake sensitivity + the window + the acid-loss decay ----------
    t = np.asarray(data["times"])
    ax_w.plot(t, data["cd_of_t"], color=CD_CURVE_COLOR, lw=2.4, zorder=4, label="developed CD")
    ax_w.axhline(data["nominal_cd"], color=DEVELOP_COLOR, ls=":", lw=1.3,
                 label=f"nominal CD {data['nominal_cd']:.0f} nm")
    ax_w.axvspan(data["t_win_lo"], data["t_win_hi"], color=CAR_WINDOW_COLOR, alpha=0.14, zorder=1,
                 label=f"PEB window  [{data['t_win_lo']:.0f}, {data['t_win_hi']:.0f}] s "
                       f"(CD ±{(data['window_hi'] / data['nominal_cd'] - 1.0):.0%})")
    ax_w.axhspan(data["window_lo"], data["window_hi"], color=CAR_WINDOW_COLOR, alpha=0.07, zorder=0)
    ax_w.set_xlim(float(t[0]), float(t[-1]))
    ax_w.set_ylim(0.0, max(float(np.max(data["cd_of_t"])), data["window_hi"]) * 1.05)
    ax_w.set_xlabel("post-exposure bake time  $t$  (s)")
    ax_w.set_ylabel("developed CD  (nm)")
    ax_w.set_title("the PEB process window — CD is acutely bake-sensitive")
    ax_w.grid(True, alpha=0.18)

    ax_a = ax_w.twinx()                                  # the acid-loss decay (the catalyst leg)
    ax_a.plot(t, data["acid_loss_analytic"], color=ACIDLOSS_COLOR, lw=1.8, ls="-", alpha=0.9, zorder=3,
              label=r"acid $\int h$ : exact $e^{-k_{loss} t}$")
    ax_a.plot(data["sample_t"], data["acid_loss_engine"], "o", color=ACIDLOSS_COLOR, ms=5, zorder=5,
              label="engine (catalyst: dose only lost)")
    ax_a.set_ylim(0.0, 1.05)
    ax_a.set_ylabel(r"acid retention  $\int h(t)\,/\int h(0)$", color=ACIDLOSS_COLOR)
    ax_a.tick_params(axis="y", labelcolor=ACIDLOSS_COLOR)

    h1, l1 = ax_w.get_legend_handles_labels()
    h2, l2 = ax_a.get_legend_handles_labels()
    ax_w.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8.0, framealpha=0.95)

    fig.suptitle("Microchip v1.9: CAR reaction–diffusion PEB — amplification vs diffusion + loss "
                 f"(λ = {wavelength_nm:.0f} nm, NA = {NA:.2f}, σ_src = {sigma_src:.2f}, "
                 f"APEX-E, dose {acid_dose:.2f})", fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig
