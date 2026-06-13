"""Rendering for the fab-game demo — the wafer maps + the failure-trail panels (viz only).

Per ADR 0002 (and 0005 §4): compute is headless, a figure is **never** in the correctness path.
This module is the thin render skin over the plain :class:`~fab_game.state.WaferState` arrays — it
imports matplotlib (the opt-in ``viz`` extra) and is exercised only by a "builds without error"
smoke test, never asserted on. Nothing here computes physics or a verdict.
"""
from __future__ import annotations

import numpy as np

from .spec import DEFAULT_SPECS
from .state import WaferState


def _grid_n(wafer: WaferState) -> int:
    """Infer the square grid size from the die sites (the centre row/col + an edge die are present)."""
    return max(max(i, j) for (i, j) in (d.site for d in wafer.dies)) + 1


def _die_xy(wafer: WaferState) -> tuple[np.ndarray, np.ndarray]:
    """Normalized die-site coordinates on [-1, 1] (the wafer-radius units the map is drawn in)."""
    n = _grid_n(wafer)
    xs = np.array([(d.site[0] + 0.5) * (2.0 / n) - 1.0 for d in wafer.dies])
    ys = np.array([(d.site[1] + 0.5) * (2.0 / n) - 1.0 for d in wafer.dies])
    return xs, ys


def _wafer_map(ax, wafer: WaferState, title: str) -> None:
    """Draw one wafer: pass dies green, fail dies red, on the wafer circle."""
    import matplotlib.pyplot as plt

    xs, ys = _die_xy(wafer)
    passed = np.array([d.verdict is not None and d.verdict.passed for d in wafer.dies])
    n = _grid_n(wafer)
    size = (2.0 / n) * 0.92                                   # die square edge in axis units
    for x, y, ok in zip(xs, ys, passed):
        ax.add_patch(plt.Rectangle((x - size / 2, y - size / 2), size, size,
                                   facecolor="#2ca02c" if ok else "#d62728",
                                   edgecolor="white", linewidth=0.6))
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.4", linewidth=1.2))
    n_good = int(passed.sum())
    ax.set_title(f"{title}\nyield {n_good}/{len(wafer.dies)} = {n_good / len(wafer.dies):.0%}", fontsize=10)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def _nils_vs_radius(ax, wafer: WaferState) -> None:
    """NILS vs die radius for the defocused wafer — the printability floor catches the edge ring."""
    r = np.array([d.radius_frac for d in wafer.dies])
    nils = np.array([d.nils if d.nils is not None else np.nan for d in wafer.dies])
    passed = np.array([d.verdict is not None and d.verdict.passed for d in wafer.dies])
    ax.scatter(r[passed], nils[passed], c="#2ca02c", s=22, label="pass", zorder=3)
    ax.scatter(r[~passed], nils[~passed], c="#d62728", s=22, label="fail", zorder=3)
    floor = DEFAULT_SPECS.nils.lo
    if floor is not None:
        ax.axhline(floor, color="0.3", ls="--", lw=1.0)
        ax.text(0.02, floor + 0.1, f"NILS printability floor = {floor:.1f}", fontsize=8, color="0.3")
    ax.set_xlabel("die radius (centre → edge)", fontsize=9)
    ax.set_ylabel("NILS (image sharpness)", fontsize=9)
    ax.set_title("Defocus collapses NILS toward the edge", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")


# --------------------------------------------------------------------------- #
# G2 — the boule → batch artifact (the Scheil spread down the boule)
# --------------------------------------------------------------------------- #
def _scheil_panel(ax, result) -> None:
    """Axial substrate doping N_A(z) down the boule (Scheil), with resistivity on a twin axis."""
    import numpy as np

    b = result.batch
    boule = b.boule
    z = np.linspace(0.0, max(b.z_positions), 200)
    ax.plot(z, boule.axial_doping(z), color="#2f6db5", lw=2.0, label=f"Scheil N_A(z), k={boule.k:.2f}")
    ax.axhline(boule.N_seed, color="0.6", ls=":", lw=1.0, label="k→1 (no segregation)")
    ax.scatter(b.z_positions, b.channel_N_As, c="#2f6db5", s=22, zorder=3)
    ax.set_xlabel("axial position z (fraction solidified)", fontsize=9)
    ax.set_ylabel("substrate N_A (cm⁻³)", fontsize=9, color="#2f6db5")
    ax.set_title("Czochralski boule: boron piles up down the boule", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    rax = ax.twinx()
    rax.plot(b.z_positions, b.resistivities, color="#d62728", lw=1.4, marker="o", ms=3)
    rax.set_ylabel("resistivity ρ (Ω·cm)", fontsize=9, color="#d62728")


def _vt_window_panel(ax, result) -> None:
    """Device V_t vs axial z, with the spec window shaded — the Scheil walk across the limit."""
    b = result.batch
    z = list(b.z_positions)
    vt = [b.mean_V_t(w) for w in b.wafers]
    lo, hi = result.v_t_lo, result.v_t_hi
    ax.axhspan(lo, hi, color="#2ca02c", alpha=0.12, label=f"V_t spec [{lo:.2f}, {hi:.2f}]")
    in_spec = [lo <= v <= hi for v in vt]
    ax.plot(z, vt, color="0.4", lw=1.2, zorder=2)
    ax.scatter([zz for zz, ok in zip(z, in_spec) if ok], [v for v, ok in zip(vt, in_spec) if ok],
               c="#2ca02c", s=26, zorder=3, label="pass")
    ax.scatter([zz for zz, ok in zip(z, in_spec) if not ok], [v for v, ok in zip(vt, in_spec) if not ok],
               c="#d62728", s=26, zorder=3, label="scrapped")
    ax.set_xlabel("axial position z (fraction solidified)", fontsize=9)
    ax.set_ylabel("device V_t (V)", fontsize=9)
    ax.set_title("Rising substrate doping walks V_t out of spec", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def _yield_panel(ax, result) -> None:
    """Per-wafer yield down the boule — the consequence: the tail is scrapped."""
    b = result.batch
    ax.step(b.z_positions, [100 * y for y in b.yields], where="mid", color="#1c2530", lw=1.6)
    ax.scatter(b.z_positions, [100 * y for y in b.yields],
               c=["#2ca02c" if y >= 1.0 else "#d62728" for y in b.yields], s=26, zorder=3)
    if result.scrap_z is not None:
        ax.axvline(result.scrap_z, color="#d62728", ls="--", lw=1.0)
        ax.text(result.scrap_z + 0.01, 50, f"scrap from z≈{result.scrap_z:.2f}", fontsize=8, color="#d62728")
    ax.set_xlabel("axial position z (fraction solidified)", fontsize=9)
    ax.set_ylabel("wafer yield (%)", fontsize=9)
    ax.set_ylim(-5, 105)
    ax.set_title("Yield down the boule", fontsize=10)


def boule_figure(result):
    """Assemble the G2 boule artifact from a :class:`~fab_game.demo_boule.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    _scheil_panel(axes[0], result)
    _vt_window_panel(axes[1], result)
    _yield_panel(axes[2], result)
    fig.suptitle("G2 — one boule, sliced down its length: Scheil segregation → V_t spread → "
                 "the tail is scrapped", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


# --------------------------------------------------------------------------- #
# G3 — the die map made physical (particles + the cited yield law + geometry)
# --------------------------------------------------------------------------- #
def _particle_map(ax, wafer: WaferState, title: str) -> None:
    """Draw the wafer: pass dies green, fail dies red, with killer particles as black dots on top."""
    import matplotlib.pyplot as plt

    xs, ys = _die_xy(wafer)
    passed = np.array([d.verdict is not None and d.verdict.passed for d in wafer.dies])
    n = _grid_n(wafer)
    size = (2.0 / n) * 0.92
    for x, y, ok in zip(xs, ys, passed):
        ax.add_patch(plt.Rectangle((x - size / 2, y - size / 2), size, size,
                                   facecolor="#2ca02c" if ok else "#d62728",
                                   edgecolor="white", linewidth=0.6, zorder=1))
    # The killer particles at their locations (wafer-radius units — DefectEvent.x/y).
    px = [e.x for d in wafer.dies for e in d.defects]
    py = [e.y for d in wafer.dies for e in d.defects]
    ax.scatter(px, py, s=18, c="black", marker="x", linewidths=1.1, zorder=4, label="killer particle")
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.4", linewidth=1.2))
    n_good = int(passed.sum())
    ax.set_title(f"{title}\nyield {n_good}/{len(wafer.dies)} = {n_good / len(wafer.dies):.0%}, "
                 f"{len(px)} particles", fontsize=10)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(fontsize=8, loc="lower right")


def _defect_yield_curve(ax, result) -> None:
    """Empirical defect yield vs D₀ hugging the cited Poisson law exp(−D₀·A) — placement → physics."""
    D = np.array(result.sweep_densities)
    ax.plot(D, [100 * y for y in result.poisson_yields], color="#2f6db5", lw=2.0,
            label="cited law  Y = exp(−D₀·A)", zorder=2)
    ax.scatter(D, [100 * y for y in result.empirical_yields], c="#d62728", s=28, zorder=3,
               label="placement (Monte-Carlo mean)")
    ax.set_xlabel("killer-defect density D₀ (cm⁻²)", fontsize=9)
    ax.set_ylabel("defect-limited yield (%)", fontsize=9)
    ax.set_ylim(0, 105)
    ax.set_title(f"Random placement → the cited Poisson law\n(die area A = {result.die_area_cm2:.1f} cm²)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper right")


def _geometry_panel(ax, result) -> None:
    """The TTV scrap → re-polish recovery: TTV before/after vs the flatness spec, and the thickness cost."""
    from .spec import DEFAULT_SPECS

    g0, g1 = result.scrap_wafer.geometry, result.repolished_wafer.geometry
    ttv_hi = DEFAULT_SPECS.geometry.ttv_um.hi
    labels = ["as-prepped\n(weak CMP)", "after re-polish"]
    ttvs = [g0.ttv_um, g1.ttv_um]
    colors = ["#d62728" if t > ttv_hi else "#2ca02c" for t in ttvs]
    ax.bar(labels, ttvs, color=colors, width=0.55, zorder=2)
    ax.axhline(ttv_hi, color="0.3", ls="--", lw=1.0)
    ax.text(-0.45, ttv_hi + 0.03, f"flatness spec = {ttv_hi:.1f} µm", fontsize=8, color="0.3")
    ax.set_ylabel("wafer TTV (µm)", fontsize=9)
    ax.set_title(f"Geometry gate: scrap → re-polish\n(thickness {g0.thickness_um:.0f} → {g1.thickness_um:.0f} µm, "
                 f"−{g0.thickness_um - g1.thickness_um:.0f} µm)", fontsize=10)
    for i, t in enumerate(ttvs):
        ax.text(i, t + 0.03, f"{t:.2f}", ha="center", fontsize=8)


def wafer_prep_figure(result):
    """Assemble the G3 artifact from a :class:`~fab_game.demo_wafer_prep.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    _particle_map(axes[0], result.dirty_wafer,
                  f"Particle map (D₀ = {result.map_density:.3f} cm⁻²)")
    _defect_yield_curve(axes[1], result)
    _geometry_panel(axes[2], result)
    fig.suptitle("G3 — the die map made physical: killer particles → functional yield "
                 "(the cited Poisson law) + the TTV scrap/re-polish", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


# --------------------------------------------------------------------------- #
# G4 — bad purification → contamination → a dead device (the scrubbing + the V_t walk + the rework)
# --------------------------------------------------------------------------- #
def _scrubbing_panel(ax, result) -> None:
    """One zone pass: feed vs refined per species (log) — metals scrubbed ~5 orders, boron barely."""
    x = np.arange(len(result.species))
    feed = [result.feed_vector[s] for s in result.species]
    refined = [result.refined_vector[s] for s in result.species]
    ax.bar(x - 0.2, feed, width=0.4, color="#b0b0b0", label="feedstock (MGS)", zorder=2)
    ax.bar(x + 0.2, refined, width=0.4, color="#2f6db5", label="after 1 zone pass", zorder=2)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}\nk={result.k_values[s]:.0e}" for s in result.species], fontsize=8)
    ax.set_ylabel("concentration (cm⁻³)", fontsize=9)
    ax.set_title("Zone refining: metals scrubbed ~5 orders,\nboron barely (k≈0.8) — C_front/C₀ = k",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")


def _vt_grade_panel(ax, result) -> None:
    """V_t down the feedstock-grade ladder (one pass), spec window shaded — MGS falls out the bottom."""
    x = np.arange(len(result.grades))
    lo, hi = result.v_t_lo, result.v_t_hi
    ax.axhspan(lo, hi, color="#2ca02c", alpha=0.12, label=f"V_t spec [{lo:.2f}, {hi:.2f}]")
    colors = ["#2ca02c" if lo <= v <= hi else "#d62728" for v in result.vt_by_grade]
    ax.bar(x, result.vt_by_grade, width=0.6, color=colors, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(result.grades, fontsize=9)
    ax.set_ylabel("device V_t (V)", fontsize=9)
    ax.set_title("Dirtier feed → residual Na → V_t walks down\n(MGS scrapped, one pass)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    for i, v in enumerate(result.vt_by_grade):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)


def _rework_panel(ax, result) -> None:
    """V_t vs zone passes (MGS), spec shaded — more passes scrub the Na → V_t climbs back into spec."""
    lo, hi = result.v_t_lo, result.v_t_hi
    ax.axhspan(lo, hi, color="#2ca02c", alpha=0.12, label=f"V_t spec [{lo:.2f}, {hi:.2f}]")
    p = list(result.mgs_passes)
    ax.plot(p, result.vt_by_pass, color="0.4", lw=1.2, zorder=2)
    colors = ["#2ca02c" if lo <= v <= hi else "#d62728" for v in result.vt_by_pass]
    ax.scatter(p, result.vt_by_pass, c=colors, s=42, zorder=3)
    ax.set_xticks(p)
    ax.set_xlabel("zone-refining passes (the rework)", fontsize=9)
    ax.set_ylabel("device V_t (V)", fontsize=9)
    ax.set_title("Purify harder: more passes scrub the Na\n→ V_t recovers (residual B persists)", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")


def purification_figure(result):
    """Assemble the G4 artifact from a :class:`~fab_game.demo_purification.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _scrubbing_panel(axes[0], result)
    _vt_grade_panel(axes[1], result)
    _rework_panel(axes[2], result)
    trail = result.dead_trail.splitlines()[0] if result.dead_trail else ""
    fig.suptitle("G4 — bad purification → mobile-ion (Na) contamination → V_t out of spec → a dead "
                 "wafer; rework = purify harder\n" + trail, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


# --------------------------------------------------------------------------- #
# G4b — deep-level metals → killed lifetime → a leaky diode (scaling + isolated kill + rework)
# --------------------------------------------------------------------------- #
def _lifetime_scaling_panel(ax, result) -> None:
    """τ (µs) and junction leakage (nA/cm²) vs [Fe] — the cited 1/τ = σ_n·v_th·N_t scaling."""
    fe = np.asarray(result.fe_sweep)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.plot(fe, result.tau_us_sweep, color="#2f6db5", lw=1.6, label="lifetime τ (µs)")
    ax.set_xlabel("dissolved iron [Fe] (cm⁻³)", fontsize=9)
    ax.set_ylabel("minority-carrier lifetime τ (µs)", fontsize=9, color="#2f6db5")
    ax.tick_params(axis="y", labelcolor="#2f6db5")
    ax2 = ax.twinx()
    ax2.set_yscale("log")
    ax2.plot(fe, result.leak_sweep, color="#d62728", lw=1.6, label="leakage (nA/cm²)")
    ax2.axhline(result.leak_spec_hi, color="#d62728", ls="--", lw=1.0, alpha=0.7)
    ax2.set_ylabel("junction leakage (nA/cm²)", fontsize=9, color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax.set_title("Metals destroy lifetime → raise leakage\n(clean FZ ~ms/pA; [Fe]~1e12 → µs)", fontsize=10)


def _leakage_ladder_panel(ax, result) -> None:
    """Leakage per feed grade (one pass, log) vs spec — only the metal feed blows the window; V_t flat."""
    x = np.arange(len(result.ladder))
    hi = result.leak_spec_hi
    colors = ["#d62728" if lk > hi else "#2ca02c" for lk in result.leak_by_grade]
    ax.bar(x, result.leak_by_grade, width=0.6, color=colors, zorder=2)
    ax.axhline(hi, color="#d62728", ls="--", lw=1.1, label=f"leakage spec ≤ {hi:.0f} nA/cm²")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(result.ladder, fontsize=9)
    ax.set_ylabel("junction leakage (nA/cm²)", fontsize=9)
    ax.set_title("Only the metal-laden feed blows the leakage\nwindow — and V_t stays in spec throughout",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    for i, (lk, vt) in enumerate(zip(result.leak_by_grade, result.vt_by_grade)):
        ax.text(i, lk * 1.4, f"V_t {vt:.2f}", ha="center", fontsize=7, color="0.3")


def _leakage_rework_panel(ax, result) -> None:
    """Leakage vs zone passes (metal feed, log) — the tiny-k metals scrub fast → leakage recovers."""
    hi = result.leak_spec_hi
    p = list(result.metal_passes)
    ax.plot(p, result.leak_by_pass, color="0.4", lw=1.2, zorder=2)
    colors = ["#d62728" if lk > hi else "#2ca02c" for lk in result.leak_by_pass]
    ax.scatter(p, result.leak_by_pass, c=colors, s=46, zorder=3)
    ax.axhline(hi, color="#d62728", ls="--", lw=1.1, label=f"leakage spec ≤ {hi:.0f} nA/cm²")
    ax.set_yscale("log")
    ax.set_xticks(p)
    ax.set_xlabel("zone-refining passes (the rework)", fontsize=9)
    ax.set_ylabel("junction leakage (nA/cm²)", fontsize=9)
    ax.set_title("Purify harder: one extra pass (k² at the lead)\nscrubs the metals → leakage recovers",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper right")


def lifetime_figure(result):
    """Assemble the G4b artifact from a :class:`~fab_game.demo_lifetime.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _lifetime_scaling_panel(axes[0], result)
    _leakage_ladder_panel(axes[1], result)
    _leakage_rework_panel(axes[2], result)
    trail = result.dead_trail.splitlines()[0] if result.dead_trail else ""
    fig.suptitle("G4b — deep-level metals → killed minority-carrier lifetime → a leaky diode "
                 "(V_t can't see it); rework = purify harder\n" + trail, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


# --------------------------------------------------------------------------- #
# G5 — etch & deposition: CD transfer (etch bias) + the void map + the rework
# --------------------------------------------------------------------------- #
def _etch_bias_panel(ax, result) -> None:
    """Gate CD vs over-etch, per anisotropy — a real etch undercuts; the seam (A=1) is flat."""
    oe = np.asarray(result.over_etch)
    colors = {result.etch_curves[0]: "#2ca02c", result.etch_curves[1]: "#2f6db5",
              result.etch_curves[2]: "#d62728"}
    for A in result.etch_curves:
        label = "A = 1.0 (ideal — seam)" if A == 1.0 else f"A = {A:.2f}"
        ax.plot(oe, result.cd_by_aniso[A], lw=1.7, color=colors.get(A, "0.4"), marker="o", ms=3,
                label=label)
    ax.axhspan(result.cd_lo, result.cd_hi, color="#2ca02c", alpha=0.10, zorder=0)
    ax.axhline(result.cd_lo, color="#2ca02c", ls="--", lw=1.0, alpha=0.7)
    ax.set_xlabel("over-etch fraction (past endpoint)", fontsize=9)
    ax.set_ylabel("gate CD (nm)", fontsize=9)
    ax.set_title("Etch bias: over-etch undercuts → CD shrinks\n(out the bottom of its window → I_Dsat ↑)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")


def _void_panel(ax, result) -> None:
    """Max void-free aspect ratio vs step coverage, with the gate gap + the CVD/PVD points."""
    sc = np.asarray(result.step_coverages)
    ax.plot(sc, result.ar_crit_curve, color="0.35", lw=1.7, zorder=2,
            label="max void-free AR = SC/(1−SC)")
    ax.axhline(result.gate_gap_ar, color="#7f3fbf", ls="--", lw=1.2,
               label=f"gate-gap AR ≈ {result.gate_gap_ar:.2f}")
    # The two process points (AR_crit values come from compute() — plots never recompute physics): PVD
    # sits below the gap line (voids), CVD above (fills, clamped into view).
    top = result.gate_gap_ar * 6
    ax.scatter([result.pvd_sc], [result.pvd_ar_crit], s=70, zorder=4,
               color="#d62728", label=f"PVD ({result.pvd_sc:.1f}) → void")
    ax.scatter([result.cvd_sc], [min(result.cvd_ar_crit, top)], s=70, zorder=4,
               color="#2ca02c", label=f"CVD ({result.cvd_sc:.1f}) → fills")
    ax.set_ylim(0, top)
    ax.set_xlabel("deposition step coverage (sidewall / top)", fontsize=9)
    ax.set_ylabel("aspect ratio", fontsize=9)
    ax.set_title("Step coverage: a non-conformal fill voids the\ngap a conformal one fills (functional kill)",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="upper left")


def _etch_rework_panel(ax, result) -> None:
    """Yield before/after re-deposit: the void recovers, the over-etched CD does not (irreversible)."""
    x = np.arange(2)
    width = 0.36
    before = [result.void_yield_before * 100, result.overetch_yield_before * 100]
    after = [result.void_yield_after * 100, result.overetch_yield_after * 100]
    ax.bar(x - width / 2, before, width, color="#d62728", label="before rework", zorder=2)
    ax.bar(x + width / 2, after, width, color="#2ca02c", label="after re-deposit (CVD)", zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(["PVD void\n(strippable)", "over-etch\n(irreversible)"], fontsize=9)
    ax.set_ylabel("wafer yield (%)", fontsize=9)
    ax.set_ylim(0, 108)
    ax.set_title("Rework: a depo void re-deposits clean;\nan over-etched CD cannot be undone", fontsize=10)
    ax.legend(fontsize=8, loc="upper center")
    for xi, (b, a) in enumerate(zip(before, after)):
        ax.text(xi - width / 2, b + 2, f"{b:.0f}", ha="center", fontsize=8, color="0.3")
        ax.text(xi + width / 2, a + 2, f"{a:.0f}", ha="center", fontsize=8, color="0.3")


def etch_figure(result):
    """Assemble the G5 artifact from a :class:`~fab_game.demo_etch.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _etch_bias_panel(axes[0], result)
    _void_panel(axes[1], result)
    _etch_rework_panel(axes[2], result)
    trail = result.void_trail.splitlines()[0] if result.void_trail else ""
    fig.suptitle("G5 — mid-line etch & deposition: over-etch shrinks the gate CD; a non-conformal fill "
                 "voids the gap; rework recovers the void, not the etch\n" + trail, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


# --------------------------------------------------------------------------- #
# G6 — packaging & test: the assembly-yield funnel + speed binning + the outcome map
# --------------------------------------------------------------------------- #
def _funnel_panel(ax, result) -> None:
    """The cumulative assembly-yield funnel: a part must survive every back-end step (Π yᵢ narrows)."""
    x = np.arange(len(result.funnel_labels))
    vals = [100 * c for c in result.funnel_cumulative]
    # Colour the bond step (the narrow neck) red, the rest steel blue.
    colors = ["#2f6db5"] * len(x)
    for i, lab in enumerate(result.funnel_labels):
        if "bond" in lab:
            colors[i] = "#d62728"
    ax.bar(x, vals, color=colors, width=0.62, zorder=2)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.0, f"{v:.1f}%", ha="center", fontsize=8, color="0.25")
    ax.axhline(100 * result.funnel_assembly_yield, color="0.35", ls="--", lw=1.0)
    ax.text(0.0, 100 * result.funnel_assembly_yield + 1.2,
            f"cited Π yᵢ = {result.funnel_assembly_yield:.1%}  "
            f"(realized {result.funnel_empirical:.1%})", fontsize=8, color="0.35")
    ax.set_xticks(x)
    ax.set_xticklabels([lab.replace("\n", " ") for lab in result.funnel_labels], fontsize=8, rotation=20)
    ax.set_ylabel("surviving fraction of front-end-good parts (%)", fontsize=9)
    ax.set_ylim(0, 108)
    ax.set_title("Assembly-yield funnel: every back-end step\nmultiplies (the wire-bond is the neck)",
                 fontsize=10)


def _binning_panel(ax, result) -> None:
    """I_Dsat sorted into speed bins: a tight process fills the premium bin, a loose one spreads + bins out."""
    edges = sorted(result.bin_edges_mA)            # the sellable-bin lower edges (ascending)
    lo = min(min(result.loose_idsat), min(result.tight_idsat)) - 0.05
    hi = max(max(result.loose_idsat), max(result.tight_idsat)) + 0.05
    bins = np.linspace(lo, hi, 28)
    ax.hist(result.loose_idsat, bins=bins, color="#d62728", alpha=0.55,
            label=f"loose process (σ={result.loose_sigma:.0f} nm)", zorder=2)
    ax.hist(result.tight_idsat, bins=bins, color="#2ca02c", alpha=0.75,
            label=f"tight process (σ={result.tight_sigma:.0f} nm)", zorder=3)
    for e in edges:
        ax.axvline(e, color="0.35", ls="--", lw=1.0, zorder=1)
    # Shade the reject (bin-out) region — below the slowest sellable edge.
    ax.axvspan(lo, edges[0], color="0.6", alpha=0.18, zorder=0)
    ax.text(edges[0] - 0.005, ax.get_ylim()[1] * 0.0 + 1, "reject\n(too slow)", fontsize=7,
            color="0.4", ha="right", va="bottom")
    ax.set_xlabel("I_Dsat (mA) — the speed proxy", fontsize=9)
    ax.set_ylabel("die count", fontsize=9)
    ax.set_title("Speed binning: process control sets the bin mix\n(loose → spread + a bin-out tail)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


_OUTCOME_COLORS = {
    "premium": "#1a7a1a", "typical": "#2ca02c", "value": "#9acd32",
    "bin-out": "#ff7f0e", "assembly scrap": "#8b0000", "front-end fail": "#7f7f7f",
}


def _die_outcome(d) -> str:
    """Classify one die's final outcome (the four-way packaging partition + the grade)."""
    if d.assembled is None:
        return "front-end fail"
    if d.assembled is False:
        return "assembly scrap"
    if d.bin == "reject":
        return "bin-out"
    return d.bin if d.bin in ("premium", "typical", "value") else "value"


def _outcome_map_panel(ax, wafer, title: str) -> None:
    """The packaged wafer: each die coloured by its final outcome (grade / scrap / bin-out / fe-fail)."""
    import matplotlib.pyplot as plt

    xs, ys = _die_xy(wafer)
    n = _grid_n(wafer)
    size = (2.0 / n) * 0.92
    seen: dict[str, bool] = {}
    for x, y, d in zip(xs, ys, wafer.dies):
        outcome = _die_outcome(d)
        color = _OUTCOME_COLORS.get(outcome, "#7f7f7f")
        ax.add_patch(plt.Rectangle((x - size / 2, y - size / 2), size, size,
                                   facecolor=color, edgecolor="white", linewidth=0.5,
                                   label=outcome if outcome not in seen else None))
        seen[outcome] = True
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.4", linewidth=1.2))
    ax.set_title(title, fontsize=10)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(fontsize=7, loc="upper right", framealpha=0.9, ncol=1)


def packaging_figure(result):
    """Assemble the G6 artifact from a :class:`~fab_game.demo_packaging.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    _funnel_panel(axes[0], result)
    _binning_panel(axes[1], result)
    _outcome_map_panel(axes[2], result.outcome_wafer,
                       "The packaged wafer (loose process + a degraded bond)")
    trail = result.dead_trail.splitlines()[0] if result.dead_trail else ""
    fig.suptitle("G6 — the back end: the assembly-yield funnel (Π yᵢ) + speed binning → a binned, "
                 "packaged chip (and the three ways to die)\n" + trail, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


# --------------------------------------------------------------------------- #
# CG-1 — pull rate → effective segregation k_eff(v) → a flatter Scheil boule
# --------------------------------------------------------------------------- #
_CG1_COLORS = ("#1c2530", "#2f6db5", "#d62728")     # equilibrium / realistic / fast(illustrative)


def _keff_panel(ax, result) -> None:
    """k_eff vs pull rate (the BPS curve): k₀ at zero pull → 1 as pull → ∞; realistic-Si band shaded."""
    v = np.asarray(result.pull_sweep)
    ax.plot(v, result.keff_sweep, color="#2f6db5", lw=2.0, zorder=3, label="k_eff(v)  (Burton–Prim–Slichter)")
    ax.axhline(result.k0, color="0.5", ls=":", lw=1.1, label=f"k₀ = {result.k0:.2f} (well-mixed Scheil)")
    ax.axhline(1.0, color="0.5", ls="--", lw=1.0, label="k_eff → 1 (complete trapping)")
    ax.axvspan(0.0, result.realistic_pull_max, color="#2ca02c", alpha=0.12,
               label=f"realistic Si pull (≤ {result.realistic_pull_max:.0f} mm/min)")
    for pull, keff, c in zip(result.demo_pulls, result.demo_keffs, _CG1_COLORS):
        if pull is not None:
            ax.scatter([pull], [keff], color=c, s=40, zorder=4)
    ax.set_xlabel("pull rate (mm/min)", fontsize=9)
    ax.set_ylabel("effective segregation k_eff", fontsize=9)
    ax.set_title("Pull rate lifts k_eff toward 1\n(boron barely moves at realistic pull — modest)",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="lower right")


def _profile_panel(ax, result) -> None:
    """N_A(z) down the boule at the representative pull rates — flatter as pull rises (seed pinned)."""
    z = np.asarray(result.na_z)
    for (label, na), c, pull in zip(result.n_a_by_pull.items(), _CG1_COLORS, result.demo_pulls):
        illustrative = pull is not None and pull > result.realistic_pull_max
        ax.plot(z, np.asarray(na) / 1e17, color=c, lw=1.8,
                ls="--" if illustrative else "-",                    # dashed = beyond realistic Si pull
                label=f"{label} (illustrative)" if illustrative else label)
    ax.set_xlabel("axial position z (down the boule)", fontsize=9)
    ax.set_ylabel("substrate N_A (1e17 cm⁻³)", fontsize=9)
    ax.set_title("Faster pull flattens the axial doping\n(the seed end is pinned; the tail pulls down)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def _vt_walk_panel(ax, result) -> None:
    """V_t(z) down the boule (the real pipeline) at each pull rate, with the spec window shaded."""
    z = np.asarray(result.z_positions)
    ax.axhspan(result.v_t_lo, result.v_t_hi, color="#2ca02c", alpha=0.12,
               label=f"V_t spec [{result.v_t_lo:.2f}, {result.v_t_hi:.2f}]")
    for (label, vt), c, pull in zip(result.v_t_by_pull.items(), _CG1_COLORS, result.demo_pulls):
        illustrative = pull is not None and pull > result.realistic_pull_max
        ax.plot(z, vt, color=c, lw=1.8, marker="o", ms=3,
                ls="--" if illustrative else "-",                    # dashed = beyond realistic Si pull
                label=f"{label} (illustrative)" if illustrative else label)
    ax.set_xlabel("axial position z (down the boule)", fontsize=9)
    ax.set_ylabel("device V_t (V)", fontsize=9)
    ax.set_title("Consequence: a faster pull keeps the tail in spec\n(benefit only — the cost is CG-2, unmodelled)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def crystal_growth_figure(result):
    """Assemble the CG-1 artifact from a :class:`~fab_game.demo_crystal_growth.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _keff_panel(axes[0], result)
    _profile_panel(axes[1], result)
    _vt_walk_panel(axes[2], result)
    fig.suptitle("CG-1 — pull rate → effective segregation k_eff(v) (Burton–Prim–Slichter): pulling "
                 "faster flattens the Scheil boule\n"
                 "boron barely segregates (k₀=0.80) → modest at realistic Si pull; the cost of fast pull "
                 "(microvoids/striations = CG-2) is the deferred, unmodelled brake",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# G7 — the roguelike run down one boule: the Scheil V_t drift + scored strategies
# --------------------------------------------------------------------------- #
def _drift_panel(ax, result) -> None:
    """V_t vs slice_z: the naive recipe walks out of spec; the adaptive oxide trim holds it in."""
    z = np.asarray(result.z_curve)
    ax.axhspan(result.vt_lo, result.vt_hi, color="#2ca02c", alpha=0.12,
               label=f"V_t spec [{result.vt_lo:.2f}, {result.vt_hi:.2f}]")
    ax.plot(z, result.vt_naive, color="#d62728", lw=1.8, label="naive (fixed recipe)")
    ax.plot(z, result.vt_adaptive, color="#2f6db5", lw=1.8, label="adapt (thin the oxide)")
    ax.set_xlabel("axial position z (down the boule)", fontsize=9)
    ax.set_ylabel("device V_t (V)", fontsize=9)
    ax.set_title("The difficulty curve: Scheil drift walks V_t up\n(naive exits the ceiling; adapt holds)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def _score_panel(ax, result) -> None:
    """Budget vs wafer (turn) for the three strategies — the roguelike payoff: the lines diverge."""
    for traj, color, name in ((result.naive_budget, "#d62728", "naive"),
                              (result.scrap_budget, "#ff7f0e", "scrap the tail"),
                              (result.adaptive_budget, "#2f6db5", "adapt (thin oxide)")):
        x = range(1, len(traj) + 1)
        ax.plot(x, traj, color=color, lw=1.8, marker="o", ms=4, label=name)
    ax.axhline(result.naive.config.starting_budget, color="0.5", ls=":", lw=1.0,
               label=f"start ${result.naive.config.starting_budget:.0f}")
    ax.set_xlabel("wafer (turn down the boule)", fontsize=9)
    ax.set_ylabel("budget ($, house)", fontsize=9)
    ax.set_title("Scored playthrough: a worse strategy banks less\n(adapt's win = premium upgrade, not tail rescue)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def _profit_panel(ax, result) -> None:
    """Per-wafer profit down the boule: naive collapses at the tail where adaptive climbs (premium)."""
    x = np.arange(len(result.wafer_z))
    width = 0.4
    ax.bar(x - width / 2, result.naive_profit, width, color="#d62728", label="naive", zorder=2)
    ax.bar(x + width / 2, result.adaptive_profit, width, color="#2f6db5", label="adapt", zorder=2)
    ax.axhline(0.0, color="0.3", lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{z:.2f}" for z in result.wafer_z], fontsize=8)
    ax.set_xlabel("wafer slice z", fontsize=9)
    ax.set_ylabel("per-wafer profit ($, house)", fontsize=9)
    ax.set_title("Where the money is made/lost down the boule\n(naive bleeds the tail; adapt banks premium)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")


def game_figure(result):
    """Assemble the G7 artifact from a :class:`~fab_game.demo_game.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _drift_panel(axes[0], result)
    _score_panel(axes[1], result)
    _profit_panel(axes[2], result)
    fig.suptitle("G7 — a roguelike run down one boule: the Scheil V_t drift is the difficulty curve; "
                 "three strategies, scored\n"
                 f"naive ${result.naive.score:+.0f} < scrap ${result.scrap.score:+.0f} < "
                 f"adapt ${result.adaptive.score:+.0f}  ·  adapt's win is a premium UPGRADE of in-spec "
                 "wafers (double-braked: I_Dsat ceiling + unmodeled oxide reliability), not a tail rescue",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


def fab_game_figure(result):
    """Assemble the 2×2 G1 artifact figure from a :class:`~fab_game.demo_fab_game.DemoResult`."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    _wafer_map(axes[0, 0], result.good.wafer, "GOOD recipe — in focus")
    _wafer_map(axes[0, 1], result.bad.wafer, f"BAD recipe — one knob: defocus")
    _nils_vs_radius(axes[1, 0], result.bad.wafer)
    _wafer_map(axes[1, 1], result.reworked,
               f"After litho rework — re-expose at\ncorrected focus")

    trail = result.dead_trail.splitlines()[0] if result.dead_trail else ""
    fig.suptitle("The fab line: one bad knob (defocus) → a dead edge ring → rework recovers it\n"
                 + trail, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig
