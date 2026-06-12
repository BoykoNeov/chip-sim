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
