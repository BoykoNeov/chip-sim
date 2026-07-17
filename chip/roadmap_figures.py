"""Roadmap schematic previews — the banked figures for the PLANNED, not-yet-built slices.

Draws one figure per unbuilt roadmap slice of ``docs/plans/future-steps.md`` (F4 BEOL, F5 SiGe,
F6 epitaxy, F7 STI remainder, F8 CMP, F9 FinFET/GAA, F10 EUV) into ``docs/figures/roadmap-*.png``,
for the ``docs/roadmap.html`` page (:mod:`chip.roadmap_gallery`) to display.

A slice that **ships** loses its schematic here and its card on the page (F3 high-κ graduated
2026-07-17) — the drawing is a promise, and once the real demo exists the banked artifact on the
history gallery is the honest picture. Deleting the draw function is what keeps the two in step:
the manifest guard pins ``FIGURES`` against the page's ``SLICES``.

**These are illustrations, not results — the honesty rules:**

  * every figure carries a **"PLANNED — schematic preview, not simulator output"** stamp baked
    into the image itself (not just the page around it), so a saved/hot-linked copy can never
    impersonate a banked demo artifact;
  * the drawings are **structural/qualitative only** — device cross-sections, era contrasts,
    trend directions. The few numbers that appear are *cited era landmarks* (λ = 13.5 nm EUV,
    the ~1.2 nm SiO₂ tunneling wall, 2007/45 nm), never a computed model output;
  * nothing here imports the simulator's physics — there is nothing to compute yet. When a slice
    is built, its real demo banks a real figure and its card graduates off the roadmap page
    (the drift guard in ``chip/tests/test_roadmap_gallery.py`` keeps the two sets in sync).

Colors are the validated data-viz reference palette (categorical slots + chrome ink on the light
surface), each colored region direct-labeled in ink so color never carries meaning alone.

Matplotlib is imported lazily inside :func:`main` (the standing demo-module convention), so
importing this module stays viz-free for the gallery/tests fast lane. Regenerate (then commit
the PNGs) with:

    python -m chip.roadmap_figures
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = _REPO_ROOT / "docs" / "figures"

# --- the validated reference palette (dataviz skill), light surface -------------------------- #
INK = "#0b0b0b"        # primary ink — titles, direct labels
INK2 = "#52514e"       # secondary ink — captions
MUTED = "#898781"      # muted — de-emphasized structure
GRID = "#e1e0d9"       # hairline
BLUE = "#2a78d6"       # categorical 1 — the modern / planned element
AQUA = "#1baf7a"       # categorical 2
YELLOW = "#eda100"     # categorical 3
VIOLET = "#4a3aa7"     # categorical 5
RED = "#e34948"        # categorical 6 — the wall / the problem
ORANGE = "#eb6834"     # categorical 8
BLUE_PALE = "#cde2fb"  # sequential 100 — light dielectric fills
BLUE_LT = "#9ec5f4"    # sequential 200
SI_GRAY = "#deddd6"    # neutral structural fill (substrate silicon)
GATE_GRAY = "#b9b8b0"  # neutral structural fill (poly/metal bodies)
STAMP_INK = "#8a5a00"  # the planned-stamp ink / box (the page's .status.part pair)
STAMP_BG = "#fdf3dd"


def figure_path(fid: str) -> Path:
    """The banked PNG for roadmap slice ``fid`` (e.g. ``"F3"`` → ``docs/figures/roadmap-f3.png``)."""
    return FIGURES_DIR / f"roadmap-{fid.lower()}.png"


def _chrome(fig, title: str) -> None:
    """The shared figure chrome: the title (top-left) + the PLANNED stamp (top-right, in-image)."""
    fig.text(0.012, 0.975, title, ha="left", va="top", fontsize=11.5, fontweight="bold", color=INK)
    fig.text(0.988, 0.975, "PLANNED — schematic preview, not simulator output",
             ha="right", va="top", fontsize=8, fontweight="bold", color=STAMP_INK,
             bbox=dict(boxstyle="round,pad=0.35", facecolor=STAMP_BG, edgecolor=STAMP_INK, linewidth=0.8))


def _bare(ax, xlim=(0.0, 10.0), ylim=(0.0, 6.0)):
    """A drawing canvas: fixed data coords, no axes chrome."""
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("auto")
    ax.axis("off")
    return ax


def _rect(ax, x, y, w, h, fc, ec=INK2, lw=0.9, z=2):
    import matplotlib.patches as mp
    ax.add_patch(mp.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))


# --------------------------------------------------------------------------------------------- #
# F4 — BEOL interconnect RC (Al → Cu damascene 1997 → Ru)
# --------------------------------------------------------------------------------------------- #
def _draw_f4(fig) -> None:
    _chrome(fig, "F4 — BEOL interconnect: chip speed set by wire RC, not the transistor")
    ax = _bare(fig.add_axes((0.02, 0.02, 0.96, 0.84)), xlim=(0, 12), ylim=(0, 6.4))

    # period: one wide subtractive-Al wire, relaxed pitch
    _rect(ax, 0.6, 1.0, 4.0, 0.9, SI_GRAY)
    ax.text(2.6, 1.45, "oxide", ha="center", va="center", fontsize=8.5, color=MUTED)
    _rect(ax, 1.3, 1.9, 2.6, 1.1, GATE_GRAY)
    ax.text(2.6, 2.45, "Al wire (subtractive)", ha="center", va="center", fontsize=9, color=INK)
    ax.text(2.6, 3.6, "wide, far apart —\nR and C both easy", ha="center", va="bottom",
            fontsize=9, color=INK2)

    # successor: narrow, dense Cu damascene wires with a barrier liner
    _rect(ax, 6.8, 1.0, 4.6, 0.9, SI_GRAY)
    ax.text(9.1, 1.45, "low-κ dielectric", ha="center", va="center", fontsize=8.5, color=MUTED)
    for i in range(4):
        x = 7.15 + i * 1.05
        _rect(ax, x, 1.9, 0.62, 1.35, VIOLET, lw=0.8)            # barrier liner (Ta/TaN → Ru)
        _rect(ax, x + 0.09, 1.99, 0.44, 1.26, ORANGE, ec=VIOLET, lw=0.6, z=3)   # the Cu core
    ax.text(9.1, 3.55, "Cu dual-damascene (1997) → Ru (3 nm):\n"
                       "narrow wire → R = ρL/A rises;  tight pitch → C rises",
            ha="center", va="bottom", fontsize=9, color=INK)
    ax.text(7.05, 1.62, "barrier liner", ha="left", va="top", fontsize=8, color=VIOLET)

    ax.annotate("", xy=(6.5, 2.5), xytext=(5.1, 2.5),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.4))
    ax.text(5.8, 2.75, "scaling", ha="center", va="bottom", fontsize=9, color=INK2)
    ax.text(5.95, 5.9, "the would-be observable is NEW to the sim: delay ∝ R_wire·C_wire —\n"
                       "the first output the transistor chain does not set (also the step that finally\n"
                       "gives CMP (F8) a consumer: a layer thickness something reads)",
            ha="center", va="top", fontsize=9, color=INK2, style="italic")


# --------------------------------------------------------------------------------------------- #
# F5 — SiGe strained source/drain (~2004, 90 nm)
# --------------------------------------------------------------------------------------------- #
def _draw_f5(fig) -> None:
    _chrome(fig, "F5 — SiGe strained S/D (~2004, 90 nm): strain → mobility → I_Dsat")
    ax = _bare(fig.add_axes((0.02, 0.02, 0.96, 0.84)), xlim=(0, 12), ylim=(0, 6.4))

    _rect(ax, 1.2, 0.8, 9.6, 1.9, SI_GRAY)                        # substrate
    ax.text(10.55, 1.1, "Si substrate", ha="right", va="center", fontsize=9, color=INK2)
    # embedded SiGe pockets (recessed, refilled epitaxially)
    for x0, xd in ((2.2, 4.4), (7.6, 9.8)):
        import matplotlib.patches as mp
        ax.add_patch(mp.Polygon([(x0, 2.7), (xd, 2.7), (xd - 0.35, 1.75), (x0 + 0.35, 1.75)],
                                closed=True, facecolor=ORANGE, edgecolor=INK2, linewidth=0.9, zorder=3))
    ax.text(3.3, 3.0, "SiGe S/D (~20% Ge)", ha="center", va="bottom", fontsize=9, color=INK)
    ax.text(8.7, 3.0, "SiGe S/D", ha="center", va="bottom", fontsize=9, color=INK)
    # the channel + gate stack
    _rect(ax, 4.4, 2.7, 3.2, 0.16, BLUE_PALE)                     # gate oxide
    _rect(ax, 4.75, 2.86, 2.5, 1.15, GATE_GRAY)                   # gate
    ax.text(6.0, 3.43, "gate", ha="center", va="center", fontsize=9, color=INK)
    ax.text(6.0, 2.35, "p-channel", ha="center", va="center", fontsize=8.5, color=INK2)
    # the strain arrows — the pockets squeeze the channel
    ax.annotate("", xy=(5.35, 2.25), xytext=(4.35, 2.25),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=2.0))
    ax.annotate("", xy=(6.65, 2.25), xytext=(7.65, 2.25),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=2.0))
    ax.text(6.0, 1.35, "the larger Ge atom squeezes the channel —\ncompressive strain ~2 GPa",
            ha="center", va="top", fontsize=9, color=RED)
    ax.text(6.0, 5.9, "the would-be observable: hole mobility µ↑ (up to ~2× at ~20% Ge) → I_Dsat ↑ —\n"
                      "gated on a strain-aware mobility model µ(strain) in device.py (none exists yet)",
            ha="center", va="top", fontsize=9, color=INK2, style="italic")


# --------------------------------------------------------------------------------------------- #
# F6 — epitaxy: buried layer / retrograde well (coupled to F1)
# --------------------------------------------------------------------------------------------- #
def _draw_f6(fig) -> None:
    import numpy as np
    _chrome(fig, "F6 — epitaxy: buried layer / retrograde well (coupled to F1)")
    ax = fig.add_axes((0.09, 0.16, 0.86, 0.62))
    x = np.linspace(0.0, 1.0, 400)
    surface = np.exp(-(x / 0.28) ** 2)                            # surface-peaked (predep-like), qualitative
    retro = 0.15 + 0.85 * np.exp(-((x - 0.55) / 0.16) ** 2)       # buried peak, qualitative
    ax.plot(x, surface, color=BLUE, lw=2.0)
    ax.plot(x, retro, color=VIOLET, lw=2.0)
    ax.text(0.10, 1.02, "surface-peaked (what the sim's predep\nand implant both already make)",
            ha="left", va="bottom", fontsize=9, color=BLUE)
    ax.text(0.62, 0.88, "retrograde well / buried layer\n(what an epi step would grow)",
            ha="left", va="bottom", fontsize=9, color=VIOLET)
    ax.set_xlabel("depth into the wafer  →", fontsize=9, color=INK2)
    ax.set_ylabel("doping N  (qualitative)", fontsize=9, color=INK2)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_ylim(0, 1.45)
    ax.text(0.5, 1.32, "COUPLED to F1: the buried-peak contrast is exactly what ion implantation\n"
                       "(BUILT) already delivers — a standalone epi slice stays deferred",
            ha="center", va="top", fontsize=9, color=INK2, style="italic", transform=ax.transData)


# --------------------------------------------------------------------------------------------- #
# F7 — isolation remainder: STI process + latchup (bird's beak itself is BUILT as B5)
# --------------------------------------------------------------------------------------------- #
def _draw_f7(fig) -> None:
    import matplotlib.patches as mp
    _chrome(fig, "F7 — isolation: the beak is BUILT (B5); STI + latchup remain")
    ax = _bare(fig.add_axes((0.02, 0.02, 0.96, 0.84)), xlim=(0, 12), ylim=(0, 6.4))

    # LOCOS side — the field oxide with tapering beaks under the nitride pads
    _rect(ax, 0.6, 0.8, 4.8, 1.7, SI_GRAY)
    ax.text(3.0, 1.15, "Si", ha="center", va="center", fontsize=9, color=INK2)
    ax.add_patch(mp.Polygon([(1.5, 2.5), (2.3, 2.5), (2.65, 2.9), (3.35, 2.9), (3.7, 2.5),
                             (4.5, 2.5), (3.9, 2.15), (2.1, 2.15)],
                            closed=True, facecolor=BLUE_PALE, edgecolor=INK2, linewidth=0.9, zorder=3))
    _rect(ax, 0.8, 2.5, 1.2, 0.35, GATE_GRAY, z=4)                # nitride pads
    _rect(ax, 4.0, 2.5, 1.2, 0.35, GATE_GRAY, z=4)
    ax.text(1.4, 3.05, "nitride", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.text(3.0, 2.65, "field oxide", ha="center", va="center", fontsize=8, color=INK2)
    ax.annotate("", xy=(1.6, 2.42), xytext=(2.4, 2.42),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
    ax.annotate("", xy=(4.4, 2.42), xytext=(3.6, 2.42),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
    ax.text(3.0, 3.55, "LOCOS — the bird's beak eats active width\n(modelled: history-mode B5, the 2-D engine)",
            ha="center", va="bottom", fontsize=9, color=INK)

    # STI side — a vertical trench, no lateral oxidant path
    _rect(ax, 6.6, 0.8, 4.8, 1.7, SI_GRAY)
    ax.text(7.4, 1.15, "Si", ha="center", va="center", fontsize=9, color=INK2)
    _rect(ax, 8.5, 1.15, 1.0, 1.7, BLUE_LT, z=3)                  # the filled trench
    _rect(ax, 6.8, 2.5, 1.5, 0.35, GATE_GRAY, z=4)
    _rect(ax, 9.7, 2.5, 1.5, 0.35, GATE_GRAY, z=4)
    ax.text(9.0, 2.0, "oxide-filled\ntrench", ha="center", va="center", fontsize=8, color=INK)
    ax.text(9.0, 3.55, "STI (1998) — vertical walls, no beak:\nactive width = drawn width",
            ha="center", va="bottom", fontsize=9, color=INK)

    ax.annotate("", xy=(6.3, 1.9), xytext=(5.6, 1.9),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.4))
    ax.text(6.0, 5.9, "the unbuilt remainder: the STI process itself (trench etch/fill) and a latchup\n"
                      "electrical observable — the beak physics + the pitch wall already shipped as B5",
            ha="center", va="top", fontsize=9, color=INK2, style="italic")


# --------------------------------------------------------------------------------------------- #
# F8 — CMP / dishing / erosion (deferred; unblocks after F4)
# --------------------------------------------------------------------------------------------- #
def _draw_f8(fig) -> None:
    import numpy as np
    _chrome(fig, "F8 — CMP planarity: dishing & erosion — deferred until a thickness has a reader (F4)")
    ax = _bare(fig.add_axes((0.02, 0.02, 0.96, 0.84)), xlim=(0, 12), ylim=(0, 6.4))

    # the polished stack: a dense Cu array (left) + one wide Cu line (right) in oxide
    _rect(ax, 0.8, 1.0, 10.4, 2.2, SI_GRAY)
    ax.text(1.35, 1.35, "oxide", ha="center", va="center", fontsize=8.5, color=MUTED)
    for i in range(6):
        _rect(ax, 1.9 + i * 0.75, 1.9, 0.45, 1.3, ORANGE, z=3)    # dense array
    _rect(ax, 7.6, 1.9, 2.9, 1.3, ORANGE, z=3)                    # wide line
    ax.text(3.9, 1.55, "dense Cu array", ha="center", va="center", fontsize=8.5, color=INK2)
    ax.text(9.05, 1.55, "wide Cu line", ha="center", va="center", fontsize=8.5, color=INK2)

    # ideal flat vs the actual post-CMP surface (erosion over dense, dishing over wide)
    xs = np.linspace(0.8, 11.2, 500)
    ideal = np.full_like(xs, 3.2)
    erosion = -0.35 * np.exp(-((xs - 3.9) / 1.3) ** 2)
    dishing = -0.55 * np.exp(-((xs - 9.05) / 1.1) ** 2)
    ax.plot(xs, ideal, color=MUTED, lw=1.2, ls=(0, (5, 3)))
    ax.plot(xs, ideal + erosion + dishing, color=BLUE, lw=2.2)
    ax.text(11.15, 3.32, "ideal flat", ha="right", va="bottom", fontsize=8.5, color=MUTED)
    ax.text(3.9, 3.42, "erosion (dense pattern\npolishes faster)", ha="center", va="bottom",
            fontsize=9, color=INK)
    ax.text(9.05, 2.5, "dishing (the soft wide\nCu bows out)", ha="center", va="top",
            fontsize=9, color=INK, zorder=5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.75))
    ax.text(6.0, 5.9, "the missing consumer: nothing in the sim reads a layer thickness — CMP only earns\n"
                      "a build after BEOL (F4) makes wire cross-section an electrical (RC) observable",
            ha="center", va="top", fontsize=9, color=INK2, style="italic")


# --------------------------------------------------------------------------------------------- #
# F9 — FinFET / GAA (deferred; gated on the 3-D engine, backlog B1)
# --------------------------------------------------------------------------------------------- #
def _draw_f9(fig) -> None:
    _chrome(fig, "F9 — FinFET (2011) / GAA (2022): the gate wraps the channel — a genuinely 3-D field")
    labels = ("planar (today's model)\ngate on 1 side", "FinFET 2011\ngate wraps 3 sides",
              "GAA nanosheets 2022\ngate on all 4 sides")
    for i, lab in enumerate(labels):
        ax = _bare(fig.add_axes((0.035 + i * 0.325, 0.14, 0.29, 0.66)), xlim=(0, 6), ylim=(0, 6))
        if i == 0:
            _rect(ax, 0.8, 0.8, 4.4, 1.6, SI_GRAY)
            _rect(ax, 1.6, 2.4, 2.8, 0.22, BLUE_PALE)
            _rect(ax, 1.6, 2.62, 2.8, 1.5, GATE_GRAY)
            ax.text(3.0, 3.37, "gate", ha="center", va="center", fontsize=9, color=INK)
            ax.text(3.0, 1.6, "channel at the surface", ha="center", va="center", fontsize=8, color=INK2)
        elif i == 1:
            _rect(ax, 0.8, 0.8, 4.4, 1.0, SI_GRAY)
            _rect(ax, 1.4, 1.8, 3.2, 2.6, GATE_GRAY)              # the wrapping gate
            _rect(ax, 2.55, 1.8, 0.9, 1.9, SI_GRAY, z=4)          # the fin through it
            ax.text(3.0, 2.7, "fin", ha="center", va="center", fontsize=9, color=INK, zorder=5)
            ax.text(3.0, 4.75, "gate", ha="center", va="bottom", fontsize=9, color=INK)
        else:
            _rect(ax, 0.8, 0.8, 4.4, 1.0, SI_GRAY)
            _rect(ax, 1.4, 1.8, 3.2, 2.9, GATE_GRAY)
            for k in range(3):
                _rect(ax, 2.2, 2.15 + k * 0.85, 1.6, 0.5, SI_GRAY, z=4)
            ax.text(3.0, 5.05, "gate", ha="center", va="bottom", fontsize=9, color=INK)
            ax.text(4.05, 2.4, "nanosheets", ha="left", va="center", fontsize=8, color=INK2)
        ax.text(0.5, 1.03, lab, ha="center", va="bottom", fontsize=9, color=INK2,
                transform=ax.transAxes)
    fig.text(0.5, 0.03, "gated on the 3-D engine (backlog B1): the dopant/potential field around a wrapped "
                        "channel is non-separable in 3-D — deferred until such a device consumer exists",
             ha="center", va="bottom", fontsize=9, color=INK2, style="italic")


# --------------------------------------------------------------------------------------------- #
# F10 — EUV / multipatterning (deferred; no new observable)
# --------------------------------------------------------------------------------------------- #
def _draw_f10(fig) -> None:
    import numpy as np
    _chrome(fig, "F10 — EUV (2019) & multipatterning: the ladder's last rung — no new observable")

    # left: the exposure-wavelength ladder (cited era landmarks, nm)
    axl = fig.add_axes((0.075, 0.16, 0.38, 0.62))
    rungs = [("g-line", 436.0), ("i-line", 365.0), ("KrF", 248.0), ("ArF", 193.0), ("EUV", 13.5)]
    y = np.arange(len(rungs))[::-1]
    for yi, (name, lam) in zip(y, rungs):
        color = BLUE if name == "EUV" else BLUE_LT
        axl.barh(yi, lam, height=0.55, color=color, edgecolor="none")
        axl.text(lam + 8, yi, f"{name}  {lam:g} nm", ha="left", va="center", fontsize=8.5, color=INK)
    axl.set_xlim(0, 560)
    axl.set_yticks([])
    axl.set_xticks([])
    for s in axl.spines.values():
        s.set_color(GRID)
    axl.set_title("exposure wavelength λ (already modelled\ndown this whole ladder)", fontsize=9, color=INK2)

    # right: pitch-splitting — one target grating printed as two interleaved exposures
    axr = _bare(fig.add_axes((0.52, 0.10, 0.45, 0.68)), xlim=(0, 10), ylim=(0, 6))
    for i in range(8):
        x = 0.9 + i * 1.05
        color = BLUE if i % 2 == 0 else AQUA
        _rect(axr, x, 1.2, 0.55, 2.6, color, ec="none")
    axr.text(5.0, 4.25, "LELE double patterning: two interleaved exposures\nat pitch 2p print the target pitch p",
             ha="center", va="bottom", fontsize=9, color=INK)
    axr.text(2.5, 0.75, "exposure A", ha="center", va="top", fontsize=8.5, color=BLUE)
    axr.text(6.7, 0.75, "exposure B", ha="center", va="top", fontsize=8.5, color=AQUA)
    fig.text(0.5, 0.03, "deferred: litho.py already computes the aerial image, R = k₁λ/NA, defocus, PEB and CAR — "
                        "a shorter λ or a split pitch adds no observable the model does not already have",
             ha="center", va="bottom", fontsize=9, color=INK2, style="italic")


# The registry the roadmap page + drift guard anchor on: slice id → its draw function.
FIGURES = {
    "F4": _draw_f4,
    "F5": _draw_f5,
    "F6": _draw_f6,
    "F7": _draw_f7,
    "F8": _draw_f8,
    "F9": _draw_f9,
    "F10": _draw_f10,
}


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # the → in the message, on legacy codepages
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for fid, draw in FIGURES.items():
        fig = plt.figure(figsize=(11.6, 4.6), facecolor="white")
        draw(fig)
        target = figure_path(fid)
        fig.savefig(target, dpi=130, facecolor="white")
        plt.close(fig)
        print(f"Roadmap schematic banked → {target.relative_to(_REPO_ROOT)}")


if __name__ == "__main__":
    main()
