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
# The guided slider-driven slice (the §9 UX step) — the live wafer map
# --------------------------------------------------------------------------- #
def dashboard_figure(result):
    """The guided-slice wafer map — the live render the notebook slider drives (one panel).

    A thin reuse of the G1 die map (:func:`_wafer_map`) over a
    :class:`~fab_game.pipeline.LineResult`: pass dies green, fail red, on the wafer circle, titled
    with the recipe + yield. The map is the **spatial** story (the focus bowl's edge ring, the
    scattered particle kills); the rich readout + the failure trail are the text companion
    :func:`fab_game.dashboard.dashboard_summary`. "Builds without error" is all the viz layer asserts
    (ADR 0002/0005 — a figure is never in the correctness path).
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.0, 5.0))
    _wafer_map(ax, result.wafer, result.label)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# The terminal wafer map — the headless renderer the deferred Textual TUI drives
# --------------------------------------------------------------------------- #
WAFER_PASS_GLYPH = "O"      # a die that printed in spec
WAFER_FAIL_GLYPH = "X"      # a die that failed its verdict (or was never tested)
WAFER_EMPTY_GLYPH = " "     # a grid cell outside the wafer's edge-exclusion circle (no die)


def wafer_map_text(wafer: WaferState, *, color: bool = False) -> str:
    """An ASCII die map of ``wafer`` — pass dies ``O``, fail dies ``X``, on the wafer circle.

    The terminal twin of :func:`dashboard_figure`'s wafer-map panel: it reuses the **same** per-die
    placement (the ``grid_n × grid_n`` lattice clipped to the circle — :func:`_grid_n` and the
    :class:`~fab_game.state.Die` ``site`` index), emitting one glyph per cell instead of a matplotlib
    patch. A cell with no die (outside the edge-exclusion ring) renders as :data:`WAFER_EMPTY_GLYPH`,
    so the wafer's round footprint emerges; rows are laid top-to-bottom with *y* increasing upward
    (matplotlib's orientation — cosmetic on a symmetric map, but it keeps the text and the figure
    consistent). A die counts as a pass only with a passing :class:`~fab_game.state.Verdict` (mirrors
    :func:`_wafer_map`); an untested or failed die is the fail glyph.

    This is a **pure function with no matplotlib / Textual import** — the load-bearing, independently
    testable core the deferred Textual front-end drives. (The §9 discipline: the validated
    string-building lives *outside* the interactive surface, which — like ``ipywidgets.interact`` —
    can swallow a callback exception and still look green.) With ``color=True`` the pass/fail glyphs
    are wrapped in Rich console markup (``[green]``/``[red]``) for the TUI's markup-rendering panel;
    the default is plain ASCII (what the test pins).
    """
    n = _grid_n(wafer)
    grid = [[WAFER_EMPTY_GLYPH] * n for _ in range(n)]
    for d in wafer.dies:
        passed = d.verdict is not None and d.verdict.passed
        glyph = WAFER_PASS_GLYPH if passed else WAFER_FAIL_GLYPH
        if color:
            glyph = f"[green]{glyph}[/]" if passed else f"[red]{glyph}[/]"
        i, j = d.site                                          # site[0] → column (x), site[1] → row (y)
        grid[j][i] = glyph
    return "\n".join(" ".join(row) for row in reversed(grid))  # reversed: higher y on top


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
# The journey (phase 1) — refine a feed step by step: the scrub, the consequence arc, the graded ring
# --------------------------------------------------------------------------- #
def _journey_trajectory_panel(ax, result) -> None:
    """Impurity vector vs refining effort (log) — Na/Fe fall fast, boron barely moves (the contrast)."""
    efforts = [e for e, _ in result.trajectory]
    na = [c.Na for _, c in result.trajectory]
    fe = [c.Fe for _, c in result.trajectory]
    b = [c.B for _, c in result.trajectory]
    ax.set_yscale("log")
    ax.plot(efforts, na, color="#d62728", lw=1.8, marker="o", ms=4, label="Na (mobile ion → V_t)")
    ax.plot(efforts, fe, color="#7f7f7f", lw=1.4, marker="s", ms=3, label="Fe (metal → leakage)")
    ax.plot(efforts, b, color="#2f6db5", lw=1.4, marker="^", ms=3, label="B (dopant, k≈0.8)")
    ax.set_xlabel("refining effort (zone passes)", fontsize=9)
    ax.set_ylabel("impurity concentration (cm⁻³)", fontsize=9)
    ax.set_title("Refine step by step: Na/Fe fall fast,\nboron barely (segregation can't purify dopants)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper right")


def _journey_arc_panel(ax, result) -> None:
    """Forecast yield vs effort, banded — the ok→rework→fail spectrum you refine across (dead→ring→clean)."""
    e = list(result.efforts)
    y = [100.0 * v for v in result.yields]
    ax.axhspan(0, 5, color="#d62728", alpha=0.10)
    ax.axhspan(5, 95, color="#ff7f0e", alpha=0.10)
    ax.axhspan(95, 100, color="#2ca02c", alpha=0.10)
    ax.plot(e, y, color="0.2", lw=1.7, marker="o", ms=5, zorder=3)
    ax.axvline(result.ring_effort, color="#ff7f0e", ls="--", lw=1.1,
               label=f"the ring ({result.ring_forecast.yield_:.0%}) at effort {result.ring_effort:g}")
    ax.set_xlabel("refining effort (zone passes)", fontsize=9)
    ax.set_ylabel("forecast yield (%)", fontsize=9)
    ax.set_ylim(-3, 103)
    ax.set_title("The consequence forecast: dead → ring → clean\n(the band the player refines across)",
                 fontsize=10)
    ax.text(e[-1], 2, "dead", color="#d62728", fontsize=8, ha="right", va="bottom")
    ax.text(e[-1], 50, "ring (rework)", color="#cc6600", fontsize=8, ha="right", va="center")
    ax.text(e[-1], 98, "clean", color="#2ca02c", fontsize=8, ha="right", va="top")
    ax.legend(fontsize=8, loc="center left")


def _journey_boule_panel(ax, result) -> None:
    """Axial V_t down the boule (seed→tail) at a slow vs the optimum pull — CG-1 flattens the Scheil drift."""
    ax.plot([z for z, _ in result.boule_slow], [v for _, v in result.boule_slow],
            color="#d62728", lw=1.6, marker="o", ms=4, label="slow pull (steep drift)")
    ax.plot([z for z, _ in result.boule_opt], [v for _, v in result.boule_opt],
            color="#2ca02c", lw=1.6, marker="s", ms=4, label=f"optimum pull {result.growth_optimum_pull:g}")
    ax.set_xlabel("axial position z (seed → tail)", fontsize=9)
    ax.set_ylabel("mean V_t (V)", fontsize=9)
    ax.set_title("Watch the boule develop: Scheil walks V_t up\nthe boule; a faster pull flattens it (CG-1)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def _journey_growth_arc_panel(ax, result) -> None:
    """Forecast yield vs pull rate, banded — the two-sided Voronkov window (leakage rim ↔ void core)."""
    p = list(result.growth_pulls)
    y = [100.0 * v for v in result.growth_yields]
    ax.axhspan(0, 5, color="#d62728", alpha=0.10)
    ax.axhspan(5, 90, color="#ff7f0e", alpha=0.10)
    ax.axhspan(90, 100, color="#2ca02c", alpha=0.10)
    ax.plot(p, y, color="0.2", lw=1.7, marker="o", ms=5, zorder=3)
    ax.axvline(result.growth_optimum_pull, color="#2ca02c", ls="--", lw=1.1,
               label=f"optimum {result.growth_optimum_pull:g} mm/min")
    ax.set_xlabel("pull rate (mm/min)", fontsize=9)
    ax.set_ylabel("forecast yield (%)", fontsize=9)
    ax.set_ylim(-3, 103)
    ax.set_title("Two-sided window: slow → leakage rim,\nfast → void core, clean ring between (graded both)",
                 fontsize=10)
    ax.text(p[0], 48, "leakage\nrim", color="#cc6600", fontsize=8, ha="left", va="center")
    ax.text(p[-1], 48, "void\ncore", color="#cc6600", fontsize=8, ha="right", va="center")
    ax.legend(fontsize=8, loc="lower center")


def _journey_slice_arc_panel(ax, result) -> None:
    """Forecast yield vs cut depth (axial z), banded — clean near the seed → a graded V_t centre core → dead."""
    z = list(result.slice_zs)
    y = [100.0 * v for v in result.slice_yields]
    ax.axhspan(0, 5, color="#d62728", alpha=0.10)
    ax.axhspan(5, 90, color="#ff7f0e", alpha=0.10)
    ax.axhspan(90, 100, color="#2ca02c", alpha=0.10)
    ax.plot(z, y, color="0.2", lw=1.7, marker="o", ms=5, zorder=3)
    ax.axvline(result.slice_commit_z, color="#2ca02c", ls="--", lw=1.1,
               label=f"deepest clean cut z={result.slice_commit_z:g}")
    ax.axvline(result.slice_ring_z, color="#ff7f0e", ls=":", lw=1.2,
               label=f"the V_t core ({result.slice_ring_forecast.yield_:.0%}) at z={result.slice_ring_z:g}")
    ax.set_xlabel("cut position z (seed → tail)", fontsize=9)
    ax.set_ylabel("forecast yield (%)", fontsize=9)
    ax.set_ylim(-3, 103)
    ax.set_title("Where to cut: clean near the seed → a graded\nV_t centre core → dead (Scheil walks V_t up)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")


def _journey_coupling_panel(ax, result) -> None:
    """The phase-2 → phase-3 coupling: the same cut sweep on a flat (fast-pull) vs a slow-pulled boule."""
    z = list(result.slice_zs)
    ax.axhspan(90, 100, color="#2ca02c", alpha=0.08)
    ax.plot(z, [100.0 * v for v in result.slice_yields], color="#2ca02c", lw=1.7, marker="s", ms=4,
            label=f"flat boule (pull {result.growth_optimum_pull:g}) — cut deep")
    ax.plot(z, [100.0 * v for v in result.slice_yields_slow], color="#d62728", lw=1.7, marker="o", ms=4,
            label=f"slow pull {result.slow_pull:g} — lost to its leakage rim")
    ax.set_xlabel("cut position z (seed → tail)", fontsize=9)
    ax.set_ylabel("forecast yield (%)", fontsize=9)
    ax.set_ylim(-3, 103)
    ax.set_title("The coupling: a flat boule can be cut deep; a slow\npull is dead before the cut "
                 "(can't slice it away)", fontsize=10)
    ax.legend(fontsize=8, loc="center right")


def _journey_diffusion_panel(ax, result) -> None:
    """Watch the dose set the junction: predep dose (time) → R_s up, I_Dsat down (the series-R consumer)."""
    t = [pt for pt, _, _, _ in result.diffusion_traj]
    rs = [r for _, r, _, _ in result.diffusion_traj]
    idsat = [i for _, _, _, i in result.diffusion_traj]
    ax.plot(t, rs, color="#7f3fbf", lw=1.8, marker="o", ms=4, label="sheet resistance R_s (Ω/sq)")
    ax.set_xlabel(f"predep time at {result.diffusion_predep_C:g}°C (dose) — less →", fontsize=9)
    ax.set_ylabel("S/D sheet resistance R_s (Ω/sq)", fontsize=9, color="#7f3fbf")
    ax.tick_params(axis="y", labelcolor="#7f3fbf")
    ax.invert_xaxis()                                            # less dose to the right (the failing direction)
    ax2 = ax.twinx()
    ax2.plot(t, idsat, color="#2f6db5", lw=1.6, marker="s", ms=3, label="I_Dsat (mA)")
    ax2.set_ylabel("drive current I_Dsat (mA)", fontsize=9, color="#2f6db5")
    ax2.tick_params(axis="y", labelcolor="#2f6db5")
    ax.set_title("Watch the dose set the junction: less predep dose\n→ higher R_s → series R starves I_Dsat",
                 fontsize=10)


def _journey_diffusion_arc_panel(ax, result) -> None:
    """Forecast yield vs predep dose (time), banded — clean → a graded I_Dsat centre-weighted core → dead."""
    t = list(result.diffusion_times)
    y = [100.0 * v for v in result.diffusion_yields]
    ax.axhspan(0, 5, color="#d62728", alpha=0.10)
    ax.axhspan(5, 90, color="#ff7f0e", alpha=0.10)
    ax.axhspan(90, 100, color="#2ca02c", alpha=0.10)
    ax.plot(t, y, color="0.2", lw=1.7, marker="o", ms=5, zorder=3)
    ax.invert_xaxis()                                            # less dose → right (toward failure)
    ax.axvline(result.diffusion_commit_time, color="#2ca02c", ls="--", lw=1.1,
               label=f"shortest clean predep {result.diffusion_commit_time:g} min")
    ax.axvline(result.diffusion_ring_time, color="#ff7f0e", ls=":", lw=1.2,
               label=f"the I_Dsat core ({result.diffusion_ring_forecast.yield_:.0%}) at "
                     f"{result.diffusion_ring_time:g} min")
    ax.set_xlabel(f"predep time at {result.diffusion_predep_C:g}°C (dose) — less →", fontsize=9)
    ax.set_ylabel("forecast yield (%)", fontsize=9)
    ax.set_ylim(-3, 103)
    ax.set_title("Under-diffuse → I_Dsat starved: clean → a graded\nI_Dsat centre-weighted core → dead (one-sided)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")


def _journey_oxidation_panel(ax, result) -> None:
    """Watch the oxide set the device: gate-oxide time → t_ox up, V_t up AND I_Dsat down (the two-sided read)."""
    m = [pt for pt, _, _, _ in result.oxide_traj]
    vt = [v for _, _, v, _ in result.oxide_traj]
    idsat = [i for _, _, _, i in result.oxide_traj]
    ax.plot(m, vt, color="#b5651d", lw=1.8, marker="o", ms=4, label="V_t (V)")
    ax.set_xlabel("gate-oxide time (min) — thicker →", fontsize=9)
    ax.set_ylabel("threshold V_t (V)", fontsize=9, color="#b5651d")
    ax.tick_params(axis="y", labelcolor="#b5651d")
    ax2 = ax.twinx()
    ax2.plot(m, idsat, color="#2f6db5", lw=1.6, marker="s", ms=3, label="I_Dsat (mA)")
    ax2.set_ylabel("drive current I_Dsat (mA)", fontsize=9, color="#2f6db5")
    ax2.tick_params(axis="y", labelcolor="#2f6db5")
    ax.set_title("Watch the oxide set the device: thicker t_ox →\nV_t up AND I_Dsat down (read two ways at once)",
                 fontsize=10)


def _journey_oxidation_arc_panel(ax, result) -> None:
    """Forecast yield vs gate-oxide time, banded — the two-sided window (thin edge ring ↔ thick centre core)."""
    m = list(result.oxide_minutes)
    y = [100.0 * v for v in result.oxide_yields]
    ax.axhspan(0, 5, color="#d62728", alpha=0.10)
    ax.axhspan(5, 90, color="#ff7f0e", alpha=0.10)
    ax.axhspan(90, 100, color="#2ca02c", alpha=0.10)
    ax.plot(m, y, color="0.2", lw=1.7, marker="o", ms=5, zorder=3)
    ax.axvline(result.oxide_commit_min, color="#2ca02c", ls="--", lw=1.1,
               label=f"committed clean oxide {result.oxide_commit_min:g} min")
    ax.axvline(result.oxide_ring_min, color="#ff7f0e", ls=":", lw=1.2,
               label=f"the thin edge ring ({result.oxide_ring_forecast.yield_:.0%}) at {result.oxide_ring_min:g} min")
    ax.set_xlabel(f"gate-oxide time (min) — thicker →  (shown at a z={result.oxide_showcase_z:g} mid cut)",
                  fontsize=9)
    ax.set_ylabel("forecast yield (%)", fontsize=9)
    ax.set_ylim(-3, 103)
    ax.set_title("Two-sided window (no economics): too thin → edge\nring, too thick → centre core (graded both)",
                 fontsize=10)
    ax.text(m[0], 48, "thin\nedge ring", color="#cc6600", fontsize=8, ha="left", va="center")
    ax.text(m[-1], 48, "thick\ncentre core", color="#cc6600", fontsize=8, ha="right", va="center")
    ax.legend(fontsize=8, loc="lower center")


def journey_figure(result):
    """Assemble the journey artifact from a :class:`~fab_game.demo_journey.JourneyDemoResult` (5×3 panels).

    Row 1 — **purification**: the refining scrub, the dead→ring→clean consequence arc, and the wafer map at
    the graded Na ring. Row 2 — **crystal growth**: the axial boule drift (CG-1 flattening), the two-sided
    Voronkov pull window (leakage rim ↔ void core), and the wafer map at the optimum (the clean OSF ring).
    Row 3 — **slice/cut**: where-to-cut (clean → V_t centre core → dead down the boule), the phase-2 coupling
    (a flat boule cuts deep; a slow pull is dead before the cut), and the wafer map at the V_t centre core.
    Row 4 — **S/D diffusion**: the dose → R_s → I_Dsat read, the clean → I_Dsat-core → dead arc, and the
    wafer map at the I_Dsat centre-weighted core. Row 5 — **oxidation**: the t_ox → V_t/I_Dsat two-way read,
    the two-sided gate-oxide-time window (thin edge ring ↔ thick centre core), and the wafer map at the
    under-oxidized **edge ring** (the opposite-radii bookend to the stage-3/4 cores; echoes the Na ring).
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(5, 3, figsize=(15, 22.5))
    _journey_trajectory_panel(axes[0][0], result)
    _journey_arc_panel(axes[0][1], result)
    _wafer_map(axes[0][2], result.ring_forecast.result.wafer,
               f"stage 1: the graded Na ring — refine ×{result.ring_effort:g}")
    _journey_boule_panel(axes[1][0], result)
    _journey_growth_arc_panel(axes[1][1], result)
    _wafer_map(axes[1][2], result.growth_optimum_forecast.result.wafer,
               f"stage 2: the clean OSF ring — pull {result.growth_optimum_pull:g} mm/min")
    _journey_slice_arc_panel(axes[2][0], result)
    _journey_coupling_panel(axes[2][1], result)
    _wafer_map(axes[2][2], result.slice_ring_forecast.result.wafer,
               f"stage 3: the V_t centre core — cut z={result.slice_ring_z:g}")
    _journey_diffusion_panel(axes[3][0], result)
    _journey_diffusion_arc_panel(axes[3][1], result)
    _wafer_map(axes[3][2], result.diffusion_ring_forecast.result.wafer,
               f"stage 4: the I_Dsat centre-weighted core — predep {result.diffusion_ring_time:g} min")
    _journey_oxidation_panel(axes[4][0], result)
    _journey_oxidation_arc_panel(axes[4][1], result)
    _wafer_map(axes[4][2], result.oxide_ring_forecast.result.wafer,
               f"stage 5: the under-oxidized edge ring — oxide {result.oxide_ring_min:g} min "
               f"(z={result.oxide_showcase_z:g} baseline)")
    fig.suptitle("The journey — purify (Na edge ring)  →  grow (Voronkov window)  →  cut (Scheil V_t core)  "
                 "→  diffuse (series-R I_Dsat core)  →  oxidize (the two-sided gate-oxide window)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
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
# CG-2 — the Voronkov V/G criterion: the in-model brake on pulling faster
# --------------------------------------------------------------------------- #
_VACANCY_C = "#d62728"     # vacancy/void (the COP killer)
_INTERSTITIAL_C = "#2ca02c"  # interstitial / defect-free


def _criterion_panel(ax, result) -> None:
    """The criterion (G-sweep at fixed pull): the analytic defect yield crosses at G* = V/ξ_t, with the
    V/G ratio on a twin axis so the ξ_t boundary is visible. Below G* (cool zone) → vacancy/voids."""
    g = np.asarray(result.g_sweep)
    ax.plot(g, result.defect_yield_vs_g, color="#2f6db5", lw=2.0, zorder=3,
            label="defect yield exp(−D_void·A)")
    ax.axvline(result.g_boundary, color="0.4", ls="--", lw=1.2,
               label=f"V/I boundary G* = V/ξ_t ≈ {result.g_boundary:.1f} K/mm")
    ax.axvspan(g.min(), result.g_boundary, color=_VACANCY_C, alpha=0.10)      # cool zone → voids
    ax.axvspan(result.g_boundary, g.max(), color=_INTERSTITIAL_C, alpha=0.10)  # hot zone → defect-free
    ax.set_xlabel("interface thermal gradient G (K/mm)", fontsize=9)
    ax.set_ylabel("grown-in defect yield", fontsize=9)
    ax.set_ylim(-0.03, 1.05)
    ax.set_title(f"The criterion (fixed pull V={result.v_fixed:.0f} mm/min)\n"
                 "cool zone → vacancy/voids; hot zone → defect-free", fontsize=10)
    # Twin axis: the V/G ratio + the cited ξ_t line (the crossing the yield reads).
    ax2 = ax.twinx()
    ax2.plot(g, result.ratio_vs_g, color="0.55", lw=1.3, ls=":")
    ax2.axhline(result.xi_t, color="0.55", lw=1.0, ls=":")
    ax2.set_ylabel("ξ = V/G  (mm²/K·min)", fontsize=8.5, color="0.4")
    ax2.tick_params(axis="y", labelsize=7.5, colors="0.4")
    ax2.annotate(f"ξ_t = {result.xi_t:.2f}", (g.max(), result.xi_t), fontsize=7.5, color="0.4",
                 ha="right", va="bottom")
    ax.legend(fontsize=7.5, loc="center right")


def _brake_panel(ax, result) -> None:
    """The brake (pull-sweep at two hot zones): pulling faster drops the analytic defect yield; the
    engineered hot zone tolerates a faster pull before the voids switch on."""
    v = np.asarray(result.pull_sweep)
    ax.plot(v, result.defect_yield_baseline, color="#2f6db5", lw=2.0,
            label=f"baseline hot zone (G={result.g_baseline:.1f} K/mm)")
    ax.plot(v, result.defect_yield_hotzone, color="#2f6db5", lw=2.0, ls="--",
            label=f"engineered hot zone (G={result.g_hotzone:.1f} K/mm)")
    ax.set_xlabel("pull rate V (mm/min)", fontsize=9)
    ax.set_ylabel("grown-in defect yield", fontsize=9)
    ax.set_ylim(-0.03, 1.05)
    ax.set_title("The brake CG-1 lacked: faster pull → voids → yield↓\n"
                 "(a hotter zone tolerates a faster pull)", fontsize=10)
    ax.legend(fontsize=8, loc="lower left")


def _unifier_panel(ax, result) -> None:
    """CG-1 + CG-2 together (pull-sweep at the hot-zone G): the combined yield is maximized on the
    defect-free plateau V ≤ V*=ξ_t·G, then falls. CG-1's parametric fraction is FLAT across this range,
    so the two do not trade off — CG-2's criterion alone sets the pull (the plateau location is the cited
    ξ_t; only the fall-off depth is the flagged coefficient; the boundary's edge is throughput, unmodeled)."""
    v = np.asarray(result.pull_unifier)
    ax.axvline(result.v_boundary_unifier, color="0.4", ls="--", lw=1.2,
               label=f"V/I boundary V*=ξ_t·G ≈ {result.v_boundary_unifier:.1f} mm/min")
    ax.plot(v, result.parametric_fraction, color=_INTERSTITIAL_C, lw=1.8, marker="o", ms=4,
            label="CG-1 parametric in-spec (flat here)")
    ax.plot(v, result.defect_survival, color=_VACANCY_C, lw=1.8, marker="s", ms=4,
            label="CG-2 defect survival ↓")
    ax.plot(v, result.combined_yield, color="#1c2530", lw=2.2, marker="D", ms=4,
            label="combined (product)")
    ax.set_xlabel("pull rate V (mm/min)", fontsize=9)
    ax.set_ylabel("fraction / yield", fontsize=9)
    ax.set_ylim(-0.03, 1.05)
    ax.set_title(f"CG-1 + CG-2 (hot zone G={result.g_unifier:.1f} K/mm): CG-2 sets the pull\n"
                 "max on the defect-free plateau V≤V* (CG-1 flat → no trade-off)", fontsize=10)
    ax.legend(fontsize=7.5, loc="center left")


def voronkov_figure(result):
    """Assemble the CG-2 artifact from a :class:`~fab_game.demo_voronkov.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _criterion_panel(axes[0], result)
    _brake_panel(axes[1], result)
    _unifier_panel(axes[2], result)
    fig.suptitle("CG-2 — the Voronkov V/G criterion (J. Cryst. Growth 59:625, 1982): the in-model brake "
                 "on pulling faster\n"
                 "fast pull / cool hot zone → vacancy-rich → COP killers (gate-oxide integrity); CG-2's "
                 "criterion (cited ξ_t) sets the optimal pull — CG-1's doping benefit is flat in range, "
                 "so the two do not trade off",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# CG-3 — the Stefan interface balance: the latent-heat cap on the Voronkov ratio
# --------------------------------------------------------------------------- #
_CG3_FAMILY = ("#1c2530", "#2f6db5", "#7aa8d6")    # melt-gradient family (dark → light)
_CG2_CONTRAST = "#d62728"                          # the CG-2 fixed-G "what if G didn't couple" line


def _saturation_panel(ax, result) -> None:
    """ξ vs pull: the Stefan-coupled ξ(V) caps at ξ_max for every melt gradient, while CG-2's fixed-G
    ξ=V/G diverges. The headline — latent heat bounds the vacancy supersaturation."""
    v = np.asarray(result.pull_sweep)
    ax.axhline(result.xi_max, color="0.4", ls="--", lw=1.2, label=f"ξ_max = k_s/(L·ρ) ≈ {result.xi_max:.2f}")
    ax.axhline(result.xi_t, color="0.5", ls=":", lw=1.1, label=f"ξ_t = {result.xi_t:.2f} (V/I boundary)")
    for g_l, c in zip(result.melt_grads, _CG3_FAMILY):
        ax.plot(v, result.xi_by_melt[g_l], color=c, lw=1.8, label=f"Stefan, G_l={g_l:.1f} K/mm")
    ax.plot(v, result.xi_cg2_fixed, color=_CG2_CONTRAST, lw=1.8, ls="--",
            label=f"CG-2 fixed G={result.g_fixed:.1f} (unbounded)")
    ax.set_xlabel("pull rate V (mm/min)", fontsize=9)
    ax.set_ylabel("Voronkov ratio ξ = V/G", fontsize=9)
    ax.set_ylim(0.0, max(0.5, result.xi_max * 1.6))
    ax.set_title("ξ saturates at ξ_max (latent-heat cap)\nvs CG-2's unbounded fixed-G ξ=V/G", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")


def _coupling_panel(ax, result) -> None:
    """G_s vs pull: the crystal-side gradient rises linearly with pull (the latent term L·ρ·V/k_s) for
    each melt gradient — why ξ saturates — vs CG-2's frozen, flat G."""
    v = np.asarray(result.pull_sweep)
    for g_l, c in zip(result.melt_grads, _CG3_FAMILY):
        ax.plot(v, result.gs_by_melt[g_l], color=c, lw=1.8, label=f"G_s(V), G_l={g_l:.1f} K/mm")
    ax.axhline(result.g_fixed, color=_CG2_CONTRAST, lw=1.6, ls="--",
               label=f"CG-2 fixed G = {result.g_fixed:.1f} K/mm")
    ax.set_xlabel("pull rate V (mm/min)", fontsize=9)
    ax.set_ylabel("crystal-side gradient G_s (K/mm)", fontsize=9)
    ax.set_title("The coupling: G_s rises linearly with pull\n(latent heat L·ρ·V/k_s) — vs CG-2's frozen G",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="upper left")


def _bounded_cost_panel(ax, result) -> None:
    """Defect yield vs pull: the CG-2 grown-in COP yield FLOORS under the Stefan coupling (a worst-case
    COP yield) while CG-2's fixed-G collapses it to 0 — the in-model cost of fast pull is capped."""
    v = np.asarray(result.pull_sweep)
    ax.axhline(result.yield_floor, color="0.4", ls=":", lw=1.1,
               label=f"Stefan floor ≈ {result.yield_floor:.2f}")
    ax.plot(v, result.yield_cg3_ref, color="#2f6db5", lw=2.0,
            label=f"CG-3 Stefan (G_l={result.g_l_ref:.1f})")
    ax.plot(v, result.yield_cg2_fixed, color=_CG2_CONTRAST, lw=2.0, ls="--",
            label=f"CG-2 fixed G={result.g_fixed:.1f}")
    ax.set_xlabel("pull rate V (mm/min)", fontsize=9)
    ax.set_ylabel("grown-in COP defect yield", fontsize=9)
    ax.set_ylim(-0.03, 1.05)
    ax.set_title("The bounded cost: the COP yield floors (Stefan)\nvs collapses to 0 (CG-2 fixed G)",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="center right")


def stefan_figure(result):
    """Assemble the CG-3 artifact from a :class:`~fab_game.demo_stefan.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _saturation_panel(axes[0], result)
    _coupling_panel(axes[1], result)
    _bounded_cost_panel(axes[2], result)
    fig.suptitle("CG-3 — the Stefan interface balance (latent heat couples G to the pull rate): ξ = V/G_s "
                 "saturates at ξ_max = k_s/(L·ρ)\n"
                 "so CG-2's fixed-G runaway is capped — the cost of fast pull is bounded; G_l (hot-zone "
                 "superheat) is still house, the coupling + cap are the value (no engine touch, no ADR)",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# A2 — the OSF ring: CG-2 made radial (a radial G(r) → the across-wafer non-uniformity)
# --------------------------------------------------------------------------- #
def _osf_criterion_panel(ax, result) -> None:
    """ξ(r) vs radius: the radial gradient makes ξ=V/G(r) fall from centre to edge, crossing the cited
    ξ_t at the OSF ring r_OSF — the three zones (vacancy core | OSF ring | interstitial rim)."""
    r = np.asarray(result.r_grid)
    ax.plot(r, result.xi_of_r, color="#2f6db5", lw=2.0, zorder=3, label="ξ(r) = V / G(r)")
    ax.axhline(result.xi_t, color="0.4", ls=":", lw=1.2, label=f"ξ_t = {result.xi_t:.2f} (V/I boundary)")
    ax.axvline(result.ring_radius, color="0.4", ls="--", lw=1.2,
               label=f"OSF ring r_OSF = {result.ring_radius:.2f}")
    ax.axvspan(0.0, result.ring_radius, color=_VACANCY_C, alpha=0.10)        # vacancy core
    ax.axvspan(result.ring_radius, 1.0, color=_INTERSTITIAL_C, alpha=0.10)   # interstitial rim
    ax.set_xlabel("die radius r (centre → edge)", fontsize=9)
    ax.set_ylabel("Voronkov ratio ξ = V/G", fontsize=9)
    ax.set_xlim(0.0, 1.0)
    ax.set_title("The radial criterion: ξ(r) falls outward\nvacancy core | OSF ring | interstitial rim",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="upper right")


def _osf_consequence_panel(ax, result) -> None:
    """The kills STOP at the ring: the per-die survival exp(−D(r)·A) climbs from the degraded vacancy core
    to a clean interstitial rim, the void density D(r) (twin axis) peaking at the centre and zero past r_OSF."""
    r = np.asarray(result.r_grid)
    ax.plot(r, result.survival_of_r, color="#2f6db5", lw=2.0, zorder=3,
            label="per-die survival exp(−D(r)·A)")
    ax.axvline(result.ring_radius, color="0.4", ls="--", lw=1.2,
               label=f"OSF ring r_OSF = {result.ring_radius:.2f}")
    ax.set_xlabel("die radius r (centre → edge)", fontsize=9)
    ax.set_ylabel("grown-in defect survival", fontsize=9)
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlim(0.0, 1.0)
    ax.set_title("The kills STOP at the ring\nCOP-degraded core → clean interstitial rim", fontsize=10)
    ax2 = ax.twinx()
    ax2.plot(r, result.density_of_r, color=_VACANCY_C, lw=1.4, ls=":")
    ax2.set_ylabel("void density D(r) (cm⁻²)", fontsize=8.5, color=_VACANCY_C)
    ax2.tick_params(axis="y", labelsize=7.5, colors=_VACANCY_C)
    ax.legend(fontsize=7.5, loc="center left")


def _osf_wafer_map_panel(ax, result) -> None:
    """The G3 consumer: the seeded wafer map, each die shaded by its grown-in void density, killer-COP
    deaths marked (×) — they fall **only** in the vacancy core; the rim is clean. The OSF ring is dashed."""
    import matplotlib.pyplot as plt

    wafer = result.wafer
    xs, ys = _die_xy(wafer)
    geom_r = np.hypot(xs, ys)
    rad_frac = np.array([d.radius_frac for d in wafer.dies])
    dens = np.interp(rad_frac, result.r_grid, result.density_of_r)          # per-die void density
    killed = np.array([bool(d.killed_by_defect) for d in wafer.dies])
    n = _grid_n(wafer)
    size = (2.0 / n) * 0.92
    dmax = max(float(dens.max()), 1e-12)
    cmap = plt.get_cmap("Reds")
    for x, y, dn, kl in zip(xs, ys, dens, killed):
        face = cmap(0.18 + 0.82 * dn / dmax) if dn > 0.0 else "#eef3ee"      # red core → pale clean rim
        ax.add_patch(plt.Rectangle((x - size / 2, y - size / 2), size, size, facecolor=face,
                                   edgecolor="black" if kl else "white", linewidth=1.6 if kl else 0.6))
        if kl:                                                              # a killer-COP death (×)
            h = size / 2.6
            ax.plot([x - h, x + h], [y - h, y + h], color="black", lw=1.3)
            ax.plot([x - h, x + h], [y + h, y - h], color="black", lw=1.3)
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.4", linewidth=1.2))
    # The OSF ring drawn at the geometric radius (radius_frac is normalized by edge-exclusion).
    pos = rad_frac > 0.05
    edge_excl = float(np.median(geom_r[pos] / rad_frac[pos])) if np.any(pos) else 0.95
    ax.add_patch(plt.Circle((0, 0), result.ring_radius * edge_excl, fill=False,
                            color="#1c2530", linewidth=1.6, ls="--"))
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"Wafer map (seed {result.map_seed}): COPs kill the core, the rim survives\n"
                 f"core {result.core_killed}/{result.core_dies} killed · rim {result.rim_killed}/"
                 f"{result.rim_dies} killed  (× = COP death, dashed = OSF ring)", fontsize=9.5)


def osf_ring_figure(result):
    """Assemble the A2 artifact from a :class:`~fab_game.demo_osf_ring.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _osf_criterion_panel(axes[0], result)
    _osf_consequence_panel(axes[1], result)
    _osf_wafer_map_panel(axes[2], result)
    fig.suptitle("A2 — the OSF ring: CG-2 made radial (a radial G(r) → ξ(r) → the V/I boundary made "
                 "visible on the wafer)\n"
                 "the ring is the BOUNDARY where the vacancy-core COP kills STOP — a COP-degraded core "
                 "(modest) + a provably-clean rim (edge-vs-centre non-uniformity), NOT a ring of kills; "
                 "the ring's existence is a flagged house profile",
                 fontsize=10.0)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    return fig


# --------------------------------------------------------------------------- #
# A1 — the interstitial side: slow pull → grown-in dislocations → junction leakage
# --------------------------------------------------------------------------- #
_DISLOC_C = "#2f6db5"      # interstitial dislocation / leakage (the slow-pull cost)


def _two_sided_window_panel(ax, result) -> None:
    """The two-sided Voronkov window: leakage rises below ξ_t (dislocations), the COP void density rises
    above it (voids) — the defect-free optimum AT ξ_t, a cost on both sides."""
    xi = np.asarray(result.xi_of_g)
    ax.plot(xi, result.leak_of_xi, color=_DISLOC_C, lw=2.0, zorder=3, label="junction leakage (nA/cm²)")
    ax.axhline(result.leak_spec_hi, color=_DISLOC_C, ls="--", lw=1.0, alpha=0.7)
    ax.text(xi.min(), result.leak_spec_hi * 1.15, f"leakage spec ≤ {result.leak_spec_hi:.0f}",
            fontsize=7.5, color=_DISLOC_C)
    ax.axvline(result.xi_t, color="0.35", ls=":", lw=1.3, zorder=2)
    ax.text(result.xi_t, result.leak_spec_hi * 3.0,
            f" ξ_t = {result.xi_t:.2f}\n (optimum)", fontsize=7.5, color="0.3")
    ax.axvspan(xi.min(), result.xi_t, color=_DISLOC_C, alpha=0.08)            # interstitial (leakage)
    ax.axvspan(result.xi_t, xi.max(), color="#d62728", alpha=0.08)           # vacancy (voids)
    ax.set_yscale("log")
    ax.set_xlabel("Voronkov ratio ξ = V/G  (slow pull → low ξ)", fontsize=9)
    ax.set_ylabel("junction leakage (nA/cm²)", fontsize=9, color=_DISLOC_C)
    ax.tick_params(axis="y", labelsize=7.5, colors=_DISLOC_C)
    ax.set_title("The two-sided window: leakage (slow) | voids (fast)\nclean only at the ξ_t optimum",
                 fontsize=10)
    ax2 = ax.twinx()
    ax2.plot(xi, result.void_of_xi, color="#d62728", lw=1.5, ls=":", label="COP void density")
    ax2.set_ylabel("COP void density (cm⁻²)", fontsize=8.5, color="#d62728")
    ax2.tick_params(axis="y", labelsize=7.5, colors="#d62728")
    ax.legend(fontsize=7.5, loc="upper center")


def _leakage_ladder_bystander_panel(ax, result) -> None:
    """The clean-feed pull ladder: leakage climbs on the slow side (out of spec), while V_t (twin axis) is
    flat across the whole ladder — slow pull leaks the diode, it does not move the threshold."""
    x = np.arange(len(result.ladder_labels))
    leak = np.asarray(result.leak_by_step)
    colors = [("#d62728" if lk > result.leak_spec_hi else _DISLOC_C) for lk in leak]
    ax.bar(x, leak, width=0.6, color=colors, zorder=2)
    ax.axhline(result.leak_spec_hi, color="0.3", ls="--", lw=1.0)
    ax.text(x[0] - 0.4, result.leak_spec_hi * 1.25, f"leakage spec ≤ {result.leak_spec_hi:.0f}",
            fontsize=7.5, color="0.3")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(result.ladder_labels, fontsize=8)
    ax.set_ylabel("junction leakage (nA/cm²)", fontsize=9)
    ax.set_title("Leakage ladder — V_t is a bystander\nslow pull leaks the diode, not the threshold",
                 fontsize=10)
    for xi_, lk in zip(x, leak):
        ax.text(xi_, lk * 1.25, f"{lk:.2g}", ha="center", fontsize=7.5, color="0.3")
    # V_t on a twin axis — a flat line across the ladder (the isolation: the same value everywhere).
    ax2 = ax.twinx()
    vt = np.asarray(result.vt_by_step)
    ax2.plot(x, vt, color="#2ca02c", lw=1.8, marker="o", ms=4, zorder=4, label="V_t (flat)")
    ax2.axhspan(result.v_t_lo, result.v_t_hi, color="#2ca02c", alpha=0.08)
    ax2.set_ylabel("device V_t (V)", fontsize=8.5, color="#2ca02c")
    ax2.set_ylim(result.v_t_lo - 0.02, result.v_t_hi + 0.02)
    ax2.tick_params(axis="y", labelsize=7.5, colors="#2ca02c")
    ax2.legend(fontsize=7.5, loc="upper left")


def _dislocation_wafer_map_panel(ax, result) -> None:
    """The A2 completion: the radial wafer — a void-prone vacancy core (red), a dislocation-leaky rim
    (blue, × = a leakage scrap), and the clean OSF-ring annulus between (the one band clean of both)."""
    import matplotlib.pyplot as plt

    wafer = result.wafer
    xs, ys = _die_xy(wafer)
    geom_r = np.hypot(xs, ys)
    rad_frac = np.array([d.radius_frac for d in wafer.dies])
    void = np.asarray(result.void_density_of_die)
    leak = np.asarray(result.leak_of_die)
    failed = np.array([bool(d.verdict is not None and d.verdict.failed
                            and any("leakage" in r for r in d.verdict.reasons)) for d in wafer.dies])
    n = _grid_n(wafer)
    size = (2.0 / n) * 0.92
    vmax = max(float(void.max()), 1e-12)
    lmax = max(float(leak.max()), 1e-12)
    reds = plt.get_cmap("Reds")
    blues = plt.get_cmap("Blues")
    for x, y, vd, lk, fl in zip(xs, ys, void, leak, failed):
        if vd > 0.0:                                                         # vacancy core → void (red)
            face = reds(0.18 + 0.82 * vd / vmax)
        elif lk > result.leak_spec_hi * 0.15:                               # interstitial rim → leakage (blue)
            face = blues(0.18 + 0.82 * min(lk / lmax, 1.0))
        else:                                                               # the clean ring annulus
            face = "#eef3ee"
        ax.add_patch(plt.Rectangle((x - size / 2, y - size / 2), size, size, facecolor=face,
                                   edgecolor="black" if fl else "white", linewidth=1.6 if fl else 0.6))
        if fl:                                                              # a leakage scrap (×)
            h = size / 2.6
            ax.plot([x - h, x + h], [y - h, y + h], color="black", lw=1.3)
            ax.plot([x - h, x + h], [y + h, y - h], color="black", lw=1.3)
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.4", linewidth=1.2))
    pos = rad_frac > 0.05
    edge_excl = float(np.median(geom_r[pos] / rad_frac[pos])) if np.any(pos) else 0.95
    ax.add_patch(plt.Circle((0, 0), result.ring_radius * edge_excl, fill=False,
                            color="#1c2530", linewidth=1.6, ls="--"))
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"Radial map: void core (red) + leaky rim (blue, × = scrap)\n"
                 f"the OSF ring (dashed, r={result.ring_radius:.2f}) is the one clean annulus  "
                 f"(rim {result.rim_leak_failed}/{result.rim_dies} scrapped)", fontsize=9.5)


def dislocation_figure(result):
    """Assemble the A1 artifact from a :class:`~fab_game.demo_dislocation.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _two_sided_window_panel(axes[0], result)
    _leakage_ladder_bystander_panel(axes[1], result)
    _dislocation_wafer_map_panel(axes[2], result)
    trail = result.dead_trail.splitlines()[0] if result.dead_trail else ""
    fig.suptitle("A1 — the interstitial side of Voronkov: too-slow a pull → grown-in dislocations → a "
                 "leaky diode (V_t can't see it)\n"
                 "the criterion is now two-sided — fast costs yield (COP), slow costs leakage; the OSF "
                 "ring is the one clean annulus. A corner (realistic CZ is vacancy-side); the leakage "
                 "depth is flagged\n" + trail, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
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


# --------------------------------------------------------------------------- #
# D1 — under-etch: the residual film + the bridging cliff + the etch process window
# --------------------------------------------------------------------------- #
_D1_FILM_COLORS = ("#2ca02c", "#2f6db5", "#d62728")   # film thicknesses (thin → thick)


def _residual_panel(ax, result) -> None:
    """Residual vs under-etch fraction per film, with the (flagged) bridge threshold — UE=0 is the seam."""
    ue = np.asarray(result.ue_sweep)
    for h, c in zip(result.films_nm, _D1_FILM_COLORS):
        ax.plot(ue, result.residual_by_film[h], color=c, lw=1.8, label=f"film {h:.0f} nm")
    ax.axhline(result.bridge_threshold_nm, color="0.3", ls="--", lw=1.1)
    ax.text(0.01, result.bridge_threshold_nm + 1.5,
            f"bridge threshold ≈ {result.bridge_threshold_nm:.0f} nm (short)", fontsize=8, color="0.3")
    ax.set_xlabel("under-etch fraction UE (incomplete clear)", fontsize=9)
    ax.set_ylabel("residual film (nm)", fontsize=9)
    ax.set_title("Residual = UE·film: above the threshold a\nstringer bridges the lines (UE=0 ⇒ 0, the seam)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def _bridge_cliff_panel(ax, result) -> None:
    """Yield vs under-etch fraction (pipeline): a clean functional cliff as the residual crosses threshold."""
    ue = np.asarray(result.ue_sweep)
    ax.plot(ue, [100 * y for y in result.yield_vs_ue], color="#1c2530", lw=1.8, marker="o", ms=3, zorder=3)
    ax.axvline(result.ue_bridge_onset, color="#d62728", ls="--", lw=1.1)
    ax.text(result.ue_bridge_onset + 0.005, 50,
            f"residual crosses threshold\nUE ≈ {result.ue_bridge_onset:.2f}", fontsize=8, color="#d62728")
    ax.set_xlabel("under-etch fraction UE", fontsize=9)
    ax.set_ylabel("wafer yield (%)", fontsize=9)
    ax.set_ylim(-5, 105)
    ax.set_title(f"The bridging cliff (film {result.nominal_film_nm:.0f} nm): a\nFUNCTIONAL short — the CD is untouched",
                 fontsize=10)


def _process_window_panel(ax, result) -> None:
    """Yield vs the signed etch axis: under-etch (left) shorts, over-etch (right) collapses CD — a window."""
    x = np.asarray(result.etch_axis)
    ax.axvspan(result.window_lo, result.window_hi, color="#2ca02c", alpha=0.14,
               label=f"in-spec window [{result.window_lo:+.2f}, {result.window_hi:+.2f}]")
    ax.axvline(0.0, color="0.5", ls=":", lw=1.0)
    ax.text(0.0, 104, "endpoint", fontsize=7.5, color="0.4", ha="center")
    ax.plot(x, [100 * y for y in result.yield_vs_etch], color="#1c2530", lw=1.8, zorder=3)
    ax.text(result.etch_axis[0], 8, "under-etch\n→ SHORT", fontsize=8, color="#d62728", ha="left")
    ax.text(result.etch_axis[-1], 8, "over-etch\n→ OPEN (CD)", fontsize=8, color="#d62728", ha="right")
    ax.set_xlabel("signed etch (under-etch ← 0 → over-etch)", fontsize=9)
    ax.set_ylabel("wafer yield (%)", fontsize=9)
    ax.set_ylim(-5, 112)
    ax.set_title(f"The etch process window (A={result.process_anisotropy:.2f}):\nbracketed by a short and an open",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower center")


def under_etch_figure(result):
    """Assemble the D1 artifact from a :class:`~fab_game.demo_under_etch.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _residual_panel(axes[0], result)
    _bridge_cliff_panel(axes[1], result)
    _process_window_panel(axes[2], result)
    fig.suptitle("D1 — under-etch: an incomplete clear leaves residual film that bridges the gate lines "
                 "into a functional SHORT (the mirror of G5's over-etch OPEN)\n"
                 "the residual algebra + the cited 'thicker → bridge' direction are tight; the bridge "
                 "threshold is a flagged house number — endpoint control is bracketed by a short and an open",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# C1 — crucible oxygen → thermal donors: the kinetics + the V_t walk + the cited power laws
# --------------------------------------------------------------------------- #
_C1_FAMILY = ("#2ca02c", "#2f6db5", "#d62728")     # oxygen levels: low / typical / high (clean → scrap)


def _td_kinetics_panel(ax, result) -> None:
    """N_TD vs anneal time at the three oxygen levels (saturating exponentials; more oxygen → faster+higher)."""
    t = np.asarray(result.anneal_fine)
    for label, c in zip(result.oxygen_labels, _C1_FAMILY):
        ax.plot(t, np.asarray(result.n_td_by_oxygen[label]) / 1e16, color=c, lw=1.8, label=f"[O_i] {label}")
        ax.axhline(result.saturation_by_oxygen[label] / 1e16, color=c, ls=":", lw=1.0, alpha=0.7)
    ax.set_xlabel("~450 °C donor anneal (min)", fontsize=9)
    ax.set_ylabel("thermal donors N_TD (1e16 cm⁻³)", fontsize=9)
    ax.set_title("Donor kinetics: N_TD saturates with anneal\n(more oxygen → faster and higher; t=0 ⇒ 0, the seam)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower right")


def _td_vt_panel(ax, result) -> None:
    """V_t vs anneal time (real pipeline) at the three oxygen levels, spec shaded — high oxygen scraps."""
    t = np.asarray(result.anneal_sweep)
    lo, hi = result.v_t_lo, result.v_t_hi
    ax.axhspan(lo, hi, color="#2ca02c", alpha=0.12, label=f"V_t spec [{lo:.2f}, {hi:.2f}]")
    for label, c in zip(result.oxygen_labels, _C1_FAMILY):
        vt = result.vt_by_oxygen[label]
        ax.plot(t, vt, color=c, lw=1.8, marker="o", ms=3, label=f"[O_i] {label}")
    ax.set_xlabel("~450 °C donor anneal (min)", fontsize=9)
    ax.set_ylabel("device V_t (V)", fontsize=9)
    ax.set_title("Donors compensate the substrate → V_t walks down\n(high oxygen exits the floor → a scrap)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper right")


def _td_powerlaw_panel(ax, result) -> None:
    """Log–log vs [O_i]: the cited fourth-power initial rate and the flagged cube-law saturation ceiling."""
    o = np.asarray(result.oxygen_sweep)
    rate = np.asarray(result.formation_rate_sweep)
    sat = np.asarray(result.saturation_sweep)
    ax.loglog(o, rate / rate[0], color="#d62728", lw=2.0,
              label=f"initial rate ∝ [O_i]^{result.rate_exponent:.0f}  (cited KFR)")
    ax.loglog(o, sat / sat[0], color="#2f6db5", lw=2.0, ls="--",
              label=f"saturation ∝ [O_i]^{result.sat_exponent:.0f}  (flagged)")
    ax.axvline(result.oxygen_ref, color="0.5", ls=":", lw=1.0)
    ax.text(result.oxygen_ref, ax.get_ylim()[0] * 1.5, " ref 1e18", fontsize=7.5, color="0.4")
    ax.set_xlabel("interstitial oxygen [O_i] (cm⁻³)", fontsize=9)
    ax.set_ylabel("relative to the reference [O_i]", fontsize=9)
    ax.set_title("The cited power laws: rate ∝ [O_i]⁴ (four-oxygen\ncore), ceiling ∝ [O_i]³ — oxygen control matters",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def thermal_donor_figure(result):
    """Assemble the C1 artifact from a :class:`~fab_game.demo_thermal_donors.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _td_kinetics_panel(axes[0], result)
    _td_vt_panel(axes[1], result)
    _td_powerlaw_panel(axes[2], result)
    fig.suptitle("C1 — crucible oxygen → thermal donors (Kaiser–Frisch–Reiss, Phys. Rev. 112, 1546, 1958): "
                 "the ~450 °C anneal compensates the p-substrate → V_t drifts down\n"
                 "the cited fourth-power initial rate ∝ [O_i]⁴ is the only anchor; the saturating form, the "
                 "cube-law ceiling, and every magnitude are flagged house numbers (opt-in, seam-safe)",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# S4 — crucible oxygen's dual-use: donors (V_t down) vs internal gettering (leakage down)
# --------------------------------------------------------------------------- #
def _ig_two_faces_panel(ax, result) -> None:
    """The two faces of the SAME oxygen: the gettering efficiency η([O_i]) (the asset) and the
    thermal-donor density N_TD([O_i]) (the liability), both switched on by more oxygen."""
    o = np.asarray(result.oxygen_fine)
    eff = np.asarray(result.efficiency_fine)
    ntd = np.asarray(result.donor_fine)
    ax.plot(o, eff, color="#2ca02c", lw=2.1, label="gettering η([O_i]) — asset")
    ax.axvline(result.critical_oxygen, color="0.45", ls=":", lw=1.2)
    ax.text(result.critical_oxygen, 0.04, "  precip.\n  threshold\n  ~12 ppma", fontsize=7.5, color="0.35",
            va="bottom", ha="left")
    ax.set_xlabel("incorporated oxygen [O_i] (cm⁻³)", fontsize=9)
    ax.set_ylabel("internal-gettering efficiency η", fontsize=9, color="#2ca02c")
    ax.tick_params(axis="y", labelcolor="#2ca02c")
    ax.set_ylim(-0.03, 1.03)
    ax2 = ax.twinx()
    ax2.plot(o, ntd, color="#d62728", lw=2.0, label="donors N_TD([O_i]) — liability")
    ax2.set_ylabel("thermal-donor density N_TD (cm⁻³)", fontsize=9, color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax.set_title("The two faces of the same oxygen:\ngettering switches on at the threshold; donors keep "
                 "rising", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax2.legend(fontsize=8, loc="lower right")


def _ig_goldilocks_panel(ax, result) -> None:
    """The headline: leakage([O_i]) falls (gettering) while V_t([O_i]) falls (donors); the band where
    BOTH pass their spec is the dual-use sweet spot."""
    o = np.asarray(result.oxygen_pipe)
    leak = np.asarray(result.leak_pipe)
    vt = np.asarray(result.vt_pipe)
    ax.plot(o, leak, color="#2f6db5", lw=2.1, marker="o", ms=3.5, label="leakage (gettering)")
    ax.axhline(result.leak_hi, color="#2f6db5", ls="--", lw=1.1, alpha=0.8)
    ax.text(o[0], result.leak_hi * 1.1, f"  leakage spec ≤ {result.leak_hi:.0f}", fontsize=7.5,
            color="#2f6db5", va="bottom")
    ax.set_yscale("log")
    ax.set_xlabel("incorporated oxygen [O_i] (cm⁻³)", fontsize=9)
    ax.set_ylabel("junction leakage (nA/cm²)", fontsize=9, color="#2f6db5")
    ax.tick_params(axis="y", labelcolor="#2f6db5")
    ax2 = ax.twinx()
    ax2.plot(o, vt, color="#e08a1e", lw=2.1, marker="s", ms=3.5, label="V_t (donors)")
    ax2.axhline(result.v_t_lo, color="#e08a1e", ls="--", lw=1.1, alpha=0.8)
    ax2.text(o[-1], result.v_t_lo, f"V_t floor {result.v_t_lo:.2f}  ", fontsize=7.5, color="#e08a1e",
             va="bottom", ha="right")
    ax2.set_ylabel("threshold V_t (V)", fontsize=9, color="#e08a1e")
    ax2.tick_params(axis="y", labelcolor="#e08a1e")
    if result.pass_lo is not None:
        ax.axvspan(result.pass_lo, result.pass_hi, color="#2ca02c", alpha=0.12)
        mid = (result.pass_lo + result.pass_hi) / 2
        ax.text(mid, ax.get_ylim()[1], "Goldilocks\n(both pass)", fontsize=8, color="#1a7a1a",
                ha="center", va="top")
    ax.set_title("The Goldilocks: too little O leaks, too much craters V_t\n(one knob, two opposite "
                 "consequences — a trade-off, not one optimum)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    ax2.legend(fontsize=8, loc="lower left")


def _ig_yield_panel(ax, result) -> None:
    """The two-sided window as a single yield hump: 0 on the low-O (leakage) side, 0 on the high-O
    (V_t) side, the dual-use window in between."""
    o = np.asarray(result.oxygen_pipe)
    y = np.asarray(result.yield_pipe)
    ax.plot(o, y * 100, color="#6a3d9a", lw=2.2, marker="o", ms=3.5)
    if result.pass_lo is not None:
        ax.axvspan(result.pass_lo, result.pass_hi, color="#2ca02c", alpha=0.12)
    ax.annotate("leakage\nscraps", xy=(o[0], 2), fontsize=8, color="#2f6db5", va="bottom")
    ax.annotate("V_t\nscraps", xy=(o[-1], 2), fontsize=8, color="#e08a1e", va="bottom", ha="right")
    ax.set_xlabel("incorporated oxygen [O_i] (cm⁻³)", fontsize=9)
    ax.set_ylabel("wafer yield (%)", fontsize=9)
    ax.set_ylim(-4, 108)
    ax.set_title(f"The two-sided window (a {result.feed_grade} feed,\nbase leakage "
                 f"{result.base_leak:.0f} nA/cm² un-gettered)", fontsize=10)


def internal_gettering_figure(result):
    """Assemble the S4 artifact from a :class:`~fab_game.demo_internal_gettering.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _ig_two_faces_panel(axes[0], result)
    _ig_goldilocks_panel(axes[1], result)
    _ig_yield_panel(axes[2], result)
    fig.suptitle("S4 — crucible oxygen's DUAL-USE: internal gettering (Tan–Gardner–Tice, Phys. Rev. Lett. "
                 "64, 196, 1990) traps the deep-level metals (leakage down)\n"
                 "while the SAME oxygen makes thermal donors (C1) that pull V_t down — a process-trade-off "
                 "within ONE device; the precipitation threshold is cited, the efficiency magnitude flagged",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# S5 — the lifetime inversion: one τ read two ways (leakage killer ↔ recovery feature)
# --------------------------------------------------------------------------- #
def _rr_two_faces_panel(ax, result) -> None:
    """The two faces of one τ: leakage J_gen(τ) ∝ 1/τ (the logic killer) + t_rr(τ) ∝ τ (the rectifier
    feature), with the two ceilings carving out DISJOINT pass bands on the same lifetime axis."""
    tau_us = np.asarray(result.tau_fine_s) * 1e6
    leak = np.asarray(result.leak_fine)
    t_rr = np.asarray(result.t_rr_fine_ns)
    ax.plot(tau_us, leak, color="#d62728", lw=2.0, label="leakage J_gen ∝ 1/τ (logic killer)")
    ax.axhline(result.leak_ceil, color="#d62728", ls=":", lw=1.1, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("minority-carrier lifetime τ (µs)", fontsize=9)
    ax.set_ylabel("junction leakage (nA/cm²)", fontsize=9, color="#d62728")
    ax.tick_params(axis="y", labelcolor="#d62728")
    ax2 = ax.twinx()
    ax2.plot(tau_us, t_rr, color="#2f6db5", lw=2.0, label="reverse recovery t_rr ∝ τ (rectifier)")
    ax2.axhline(result.t_rr_ceil, color="#2f6db5", ls=":", lw=1.1, alpha=0.7)
    ax2.set_yscale("log")
    ax2.set_ylabel("reverse recovery t_rr (ns)", fontsize=9, color="#2f6db5")
    ax2.tick_params(axis="y", labelcolor="#2f6db5")
    # The two DISJOINT pass bands (the cross): rectifier ships at short τ, logic at long τ.
    trr_edge, leak_edge = result.tau_trr_edge_s * 1e6, result.tau_leak_edge_s * 1e6
    ax.axvspan(tau_us[0], trr_edge, color="#2f6db5", alpha=0.10)
    ax.axvspan(leak_edge, tau_us[-1], color="#2ca02c", alpha=0.10)
    ax.axvline(trr_edge, color="#2f6db5", ls="--", lw=1.0, alpha=0.7)
    ax.axvline(leak_edge, color="#2ca02c", ls="--", lw=1.0, alpha=0.7)
    ax.text(trr_edge * 0.55, leak[0] * 0.25, "rectifier\nτ short", color="#2f6db5", fontsize=8,
            ha="center", va="center")
    ax.text(leak_edge * 2.2, leak[0] * 0.25, "logic\nτ long", color="#2ca02c", fontsize=8,
            ha="center", va="center")
    ax.set_title("One τ, two faces: a SHORT lifetime is a leaky logic reject\nbut a FAST rectifier "
                 "— the pass bands are disjoint", fontsize=10)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc="upper center")


def _rr_optimum_panel(ax, result) -> None:
    """The declaration moves the optimum: sweeping the feed cleanliness (zone passes → longer τ), the
    native-MOSFET revenue rises while the power-rectifier revenue falls — the best SKU flips."""
    passes = np.asarray(result.zone_passes)
    ax.plot(passes, result.native_rev, color="#2ca02c", lw=2.0, marker="o", ms=3.5,
            label="high-res native MOSFET (wants clean)")
    ax.plot(passes, result.rectifier_rev, color="#2f6db5", lw=2.0, marker="s", ms=3.5,
            label="power rectifier (wants killed τ)")
    ax.set_xlabel("zone-refining passes (→ cleaner feed → longer τ)", fontsize=9)
    ax.set_ylabel("wafer revenue ($, flagged)", fontsize=9)
    ax2 = ax.twinx()
    ax2.plot(passes, result.tau_pipe_us, color="0.55", ls="--", lw=1.3, label="τ (µs)")
    ax2.set_yscale("log")
    ax2.set_ylabel("lifetime τ (µs)", fontsize=9, color="0.45")
    ax2.tick_params(axis="y", labelcolor="0.45")
    ax.set_title("The declaration moves the optimum: clean feed → native part,\n"
                 "lifetime-killed feed → rectifier (the best SKU flips)", fontsize=10)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="center right")


def _rr_substrate_panel(ax, result) -> None:
    """The rectifier needs the light boule too: BV(N_substrate) crosses the blocking-voltage floor only at
    the lighter (high-res) substrate — a short τ is necessary but not sufficient (the substrate commit)."""
    n = np.asarray(result.n_seed_sweep)
    ax.plot(n, result.bv_sweep, color="#7b3fbf", lw=2.0, marker="o", ms=3.5, label="BV(N_substrate)")
    ax.axhline(result.bv_floor, color="#d62728", ls="--", lw=1.2, label=f"rectifier BV floor ({result.bv_floor:.0f} V)")
    ax.axvspan(n[0], result.n_seed_bv_edge, color="#7b3fbf", alpha=0.10)
    ax.axvline(result.n_seed_bv_edge, color="#7b3fbf", ls=":", lw=1.0, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("substrate doping N_A (cm⁻³)", fontsize=9)
    ax.set_ylabel("junction breakdown BV (V)", fontsize=9)
    ax.text(result.n_seed_bv_edge * 0.45, result.bv_floor * 1.25, "light boule\n(BV clears)",
            color="#7b3fbf", fontsize=8, ha="center", va="bottom")
    ax.set_title("A short τ is not enough: the rectifier needs the LIGHT boule\nfor blocking voltage "
                 "(its own declared run, not a logic harvest)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")


def reverse_recovery_figure(result):
    """Assemble the S5 artifact from a :class:`~fab_game.demo_reverse_recovery.DemoResult` (3 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    _rr_two_faces_panel(axes[0], result)
    _rr_optimum_panel(axes[1], result)
    _rr_substrate_panel(axes[2], result)
    fig.suptitle("S5 — the LIFETIME inversion: reverse recovery t_rr ∝ τ (charge-control, Sze) reads the "
                 "SAME minority-carrier lifetime the junction leakage does, in the opposite direction\n"
                 "the lifetime killer (Fe/Cu / short τ) is the rectifier's FEATURE — a power rectifier is its "
                 "own declared run (light boule + killed τ); the form is cited, the operating point flagged",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return fig


# --------------------------------------------------------------------------- #
# E1 — spike/RTA thermal budget: the budget accrues near the peak → shallower x_j
# --------------------------------------------------------------------------- #
def _budget_accrual_panel(ax, result) -> None:
    """T(t) (left) + the cumulative ∫D dt fraction (right) for the representative spike — the budget
    is deposited in a narrow window near the peak (the Arrhenius collapse)."""
    t = np.asarray(result.t_profile)
    T = np.asarray(result.T_profile)
    frac = np.asarray(result.cumulative_budget_frac)
    ax.plot(t, T, color="#d62728", lw=1.8, label="T(t) — the spike")
    ax.axhline(result.peak_C, color="#d62728", ls=":", lw=1.0, alpha=0.6)
    ax.set_xlabel("anneal time (s)", fontsize=9)
    ax.set_ylabel("temperature T (°C)", fontsize=9, color="#d62728")
    ax.tick_params(axis="y", labelcolor="#d62728")
    ax2 = ax.twinx()
    ax2.plot(t, frac, color="#2f6db5", lw=2.0, label="cumulative ∫D dt")
    ax2.set_ylabel("budget ∫₀ᵗ D dt  (fraction of total)", fontsize=9, color="#2f6db5")
    ax2.tick_params(axis="y", labelcolor="#2f6db5")
    ax2.set_ylim(-0.02, 1.02)
    ax.set_title(f"Budget accrues near the peak: a {result.ref_duration_s:.0f} s spike deposits the\n"
                 f"diffusion of only ~{result.ref_t_eq_s:.1f} s at {result.peak_C:.0f} °C "
                 f"({result.ref_duration_s / result.ref_t_eq_s:.0f}× collapse)", fontsize=10)
    ax.legend(fontsize=8, loc="center left")
    ax2.legend(fontsize=8, loc="center right")


def _ramp_sweep_panel(ax, result) -> None:
    """x_j (left) vs ramp rate + the equivalent isothermal time t_eq, exact vs the Laplace closed form
    (right) — faster ramp → less budget → shallower junction."""
    rates = np.asarray(result.ramp_rates)
    ax.plot(rates, np.asarray(result.x_j_um) * 1e3, color="#2ca02c", lw=1.9, marker="o", ms=4,
            label="spike x_j")
    ax.axhline(result.x_j_iso_um * 1e3, color="0.45", ls="--", lw=1.2,
               label=f"isothermal baseline ({result.T_iso_C:.0f} °C/{result.t_iso_min:.0f} min)")
    ax.set_xlabel("ramp rate |dT/dt| (°C/s)", fontsize=9)
    ax.set_ylabel("junction depth x_j (nm)", fontsize=9, color="#2ca02c")
    ax.tick_params(axis="y", labelcolor="#2ca02c")
    ax.set_xscale("log")
    ax2 = ax.twinx()
    ax2.plot(rates, result.t_eq_laplace_s, color="#9467bd", lw=2.0,
             label="t_eq — Laplace closed form")
    ax2.plot(rates, result.t_eq_numeric_s, color="#9467bd", ls="none", marker="s", ms=4.5,
             mfc="none", label="t_eq — exact ∫D dt")
    ax2.set_ylabel("equivalent isothermal time t_eq (s)", fontsize=9, color="#9467bd")
    ax2.tick_params(axis="y", labelcolor="#9467bd")
    ax.set_title("Faster ramp → smaller budget → shallower x_j\n(t_eq ∝ 1/β; the D0-independent Laplace "
                 "form tracks the exact budget)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    ax2.legend(fontsize=8, loc="center right")


def thermal_budget_figure(result):
    """Assemble the E1 artifact from a :class:`~fab_game.demo_thermal_budget.DemoResult` (2 panels)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.0))
    _budget_accrual_panel(axes[0], result)
    _ramp_sweep_panel(axes[1], result)
    fig.suptitle("E1 — spike/RTA anneal: D(T(t)) → the ∫D dt thermal budget sets the junction depth "
                 "(heat-mode FALSIFIED, √(D/α)≈1e-6 → T is the setpoint; the OED effective_Dt twin, no engine)\n"
                 "the τ=∫D dt substitution + the Laplace asymptotics are the anchors; the spike recipe "
                 "numbers are illustrative — opt-in, seam-safe (drivein_program=None → isothermal)",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
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
