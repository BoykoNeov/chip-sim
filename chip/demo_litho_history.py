"""The historical-modes A2 banked artifact: the wavelength/lens ladder & proximity-gap printing.

Two period lithography modes, each landing on the CD/contrast the sim already computes — one figure, two
panels (orthogonal: the projection model re-parameterised vs the pre-projection shadow-print regime):

  * **Left — the wavelength / lens ladder (the Rayleigh CD floor, §A).** The *same* line/space feature imaged
    at each era's optics — g-line 436 → i-line 365 → KrF 248 → ArF 193 → ArF-immersion → EUV 13.5. Each
    node's contrast-vs-pitch curve is :func:`chip.litho_history.image_at_node` (= the existing projection
    model), and its resolution wall ``λ/NA`` marches left down the ladder. A fixed target feature that is a
    flat blur at g/i-line prints crisply at ArF/EUV — the contrast that drove the wavelength race. *Modern
    node = ArF, bit-for-bit :mod:`chip.demo_litho` (the seam).*
  * **Right — contact/proximity shadow printing (the √(λg) gap wall, §B).** Before steppers, a mask printed
    in **contact** (``gap = 0``, sharp) or at a **proximity gap** ``g`` blurred by near-field diffraction on
    a length ``σ = √(λg)`` (:func:`chip.litho_history.proximity_print`, riding the diffusion engine in BE
    mode). Contrast/NILS of a multi-micron feature collapse toward the
    :func:`chip.litho_history.proximity_resolution_gap` — why proximity aligners hit a resolution wall, and
    why projection (a lens, §A) replaced them.

Tight legs: the ArF seam (= :func:`chip.litho.expose_grating`), the ``R = k₁λ/NA`` formula-monotonicity, the
``gap = 0`` contact seam, and the blur's mean conservation. Flagged: the per-node NA table + the ``√(λg)``
prefactor (see :mod:`chip.litho_history`). Run headless:

    python -m chip.demo_litho_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import litho
from . import litho_history as lh

# --- §A the wavelength/lens ladder: contrast vs pitch, one curve per node ------------------------- #
LADDER = ["g-line", "i-line", "KrF", "ArF", "ArFi", "EUV"]
PITCHES_NM = np.logspace(np.log10(30.0), np.log10(2000.0), 80)   # spans EUV → g-line resolution
TARGET_PITCH_NM = 300.0            # the fixed feature: unresolved g/i-line/KrF, crisp ArF/ArFi/EUV

# --- §B contact/proximity shadow printing: contrast/NILS vs gap ---------------------------------- #
PROX_WAVELENGTH_NM = 436.0         # g-line — the classic broadband contact/proximity-aligner line
PROX_PITCH_NM = 8000.0             # a realistic 4 µm line / 4 µm space proximity feature
GAPS_UM = np.linspace(0.0, 50.0, 121)   # mask-to-wafer proximity gap sweep (contact → far)
GAP_MARKS_UM = (0.0, 10.0, 25.0, 40.0)  # annotated points

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-litho-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-litho-history.png"


@dataclass(frozen=True)
class LithoHistoryResult:
    """The A2 bundle the figure and summary consume."""

    # §A — the wavelength/lens ladder
    pitches_nm: np.ndarray
    contrast_by_node: dict[str, np.ndarray]     # node key → contrast vs pitch
    resolution_by_node: dict[str, float]        # node key → λ/NA resolution wall (nm)
    target_pitch_nm: float
    target_resolved: dict[str, bool]            # node key → does it resolve TARGET_PITCH_NM
    # §B — proximity gap blur
    gaps_um: np.ndarray
    contrast_vs_gap: np.ndarray
    nils_vs_gap: np.ndarray
    blur_vs_gap: np.ndarray                      # σ = √(λg) (nm) vs gap
    gap_marks: tuple[lh.ProximityPrint, ...]
    resolution_gap_um: float                     # the √(λg) wall for PROX_PITCH_NM


def compute() -> LithoHistoryResult:
    """Run both period modes → :class:`LithoHistoryResult`."""
    # §A — contrast vs pitch for each node (= the projection model at that era's Imaging)
    contrast_by_node, resolution_by_node, target_resolved = {}, {}, {}
    for key in LADDER:
        node = lh.NODES[key]
        contrast_by_node[key] = np.array(
            [lh.image_at_node(node, float(p)).contrast for p in PITCHES_NM])
        resolution_by_node[key] = node.imaging.pitch_min_coherent    # λ/NA (min resolved pitch)
        target_resolved[key] = lh.image_at_node(node, TARGET_PITCH_NM).resolved

    # §B — contrast/NILS vs proximity gap for a multi-micron feature
    prints = [lh.proximity_print(PROX_PITCH_NM, float(g), wavelength_nm=PROX_WAVELENGTH_NM)
              for g in GAPS_UM]
    contrast_vs_gap = np.array([p.contrast for p in prints])
    nils_vs_gap = np.array([p.nils for p in prints])
    blur_vs_gap = np.array([lh.fresnel_blur_length(PROX_WAVELENGTH_NM, float(g)) for g in GAPS_UM])
    marks = tuple(lh.proximity_print(PROX_PITCH_NM, g, wavelength_nm=PROX_WAVELENGTH_NM)
                  for g in GAP_MARKS_UM)
    res_gap = lh.proximity_resolution_gap(PROX_PITCH_NM, PROX_WAVELENGTH_NM)

    return LithoHistoryResult(
        pitches_nm=PITCHES_NM, contrast_by_node=contrast_by_node,
        resolution_by_node=resolution_by_node, target_pitch_nm=TARGET_PITCH_NM,
        target_resolved=target_resolved,
        gaps_um=GAPS_UM, contrast_vs_gap=contrast_vs_gap, nils_vs_gap=nils_vs_gap,
        blur_vs_gap=blur_vs_gap, gap_marks=marks, resolution_gap_um=res_gap,
    )


def print_summary(r: LithoHistoryResult) -> None:
    """Print the A2 story — the two period lithography walls, on resolution and on the proximity gap."""
    print("\nHistorical-modes A2: the wavelength/lens ladder & proximity-gap printing "
          "(two period modes, one CD observable)\n")

    print(f"  §A  The wavelength/lens ladder → the Rayleigh floor R = k₁·λ/NA (does a {r.target_pitch_nm:.0f} "
          f"nm pitch resolve?):")
    for key in LADDER:
        node = lh.NODES[key]
        wall = r.resolution_by_node[key]
        ok = "resolves" if r.target_resolved[key] else "FLAT — unresolved"
        print(f"    {node.era:>6}  {node.name:<14} λ={node.wavelength_nm:>5.1f} nm  NA={node.NA:.2f}  "
              f"→  min pitch λ/NA = {wall:>6.0f} nm   ({r.target_pitch_nm:.0f} nm {ok})")
    flat = [lh.NODES[k].name for k in LADDER if not r.target_resolved[k]]
    crisp = [lh.NODES[k].name for k in LADDER if r.target_resolved[k]]
    print(f"    → same feature, finer optics: {', '.join(flat)} leave it a flat blur; "
          f"{', '.join(crisp)} print it (the wavelength race).")
    print(f"    [ArF node = demo_litho bit-for-bit (seam); R∝λ/NA monotone (tight); per-node NA FLAGGED]\n")

    print(f"  §B  Contact/proximity shadow printing → the √(λg) gap wall "
          f"(a {PROX_PITCH_NM*1e-3:.0f} µm feature, {PROX_WAVELENGTH_NM:.0f} nm):")
    for h in r.gap_marks:
        tag = "  ← contact (sharp, σ=0)" if h.gap_um == 0.0 else ""
        print(f"    gap = {h.gap_um:>4.0f} µm   blur σ = {h.blur_length_nm:>6.0f} nm   "
              f"contrast = {h.contrast:.3f}   NILS = {h.nils:>5.2f}{tag}")
    print(f"    → contrast/NILS collapse toward the √(λg) resolution gap ≈ {r.resolution_gap_um:.0f} µm "
          f"(where σ = half-pitch).")
    print(f"    [contact (gap=0) = sharp mask bit-for-bit (seam); blur conserves the mean; √(λg) prefactor "
          f"FLAGGED]\n")


def save_figure(r: LithoHistoryResult) -> Path:
    """Render and save the A2 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))
    cmap = plt.get_cmap("viridis")
    node_colors = {key: cmap(i / (len(LADDER) - 1)) for i, key in enumerate(LADDER)}

    # --- Left: the wavelength/lens ladder — contrast vs pitch, one wall per era ------------------- #
    ax = axes[0]
    for key in LADDER:
        node = lh.NODES[key]
        color = node_colors[key]
        ax.semilogx(r.pitches_nm, r.contrast_by_node[key], "-", color=color, lw=2.0,
                    label=f"{node.name}  ({node.wavelength_nm:.0f} nm, NA {node.NA:.2f})")
    ax.axvline(r.target_pitch_nm, color="0.35", ls="--", lw=1.4)
    n_ok = sum(r.target_resolved.values())
    ax.annotate(f"target feature\n{r.target_pitch_nm:.0f} nm pitch\n({n_ok}/{len(LADDER)} nodes resolve)",
                xy=(r.target_pitch_nm, 0.5), xytext=(r.target_pitch_nm * 1.15, 0.62),
                fontsize=7.6, color="0.25", va="center",
                arrowprops=dict(arrowstyle="->", color="0.35", lw=1))
    ax.set_xlabel("grating pitch  (nm, log)")
    ax.set_ylabel("aerial-image contrast")
    ax.set_ylim(-0.03, 1.05)
    ax.set_title("Wavelength/lens ladder: the resolution wall marches left (g-line → EUV)", fontsize=9.5)
    ax.legend(fontsize=7.0, loc="lower right", ncol=1)
    ax.grid(True, which="both", alpha=0.18)
    ax.text(0.03, 0.05, "ArF node = demo_litho (seam);\nR = k₁λ/NA monotone (tight); NA table FLAGGED",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=6.8, color="0.4")

    # --- Right: the proximity gap wall — contrast/NILS collapse with √(λg) ------------------------ #
    ax = axes[1]
    ax.plot(r.gaps_um, r.contrast_vs_gap, "-", color="tab:blue", lw=2.2, label="contrast")
    ax.set_xlabel("mask-to-wafer proximity gap  g  (µm)")
    ax.set_ylabel("aerial-image contrast", color="tab:blue")
    ax.tick_params(axis="y", labelcolor="tab:blue")
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlim(0.0, 50.0)
    for h in r.gap_marks:
        ax.plot(h.gap_um, h.contrast, "o", color="tab:blue", ms=5)
    ax.axvline(r.resolution_gap_um, color="tab:red", ls=":", lw=1.6)
    ax.annotate(f"√(λg) wall ≈ {r.resolution_gap_um:.0f} µm\n(σ = half-pitch)",
                xy=(r.resolution_gap_um, 0.28), xytext=(r.resolution_gap_um - 21.0, 0.42),
                fontsize=7.6, color="tab:red", va="center",
                arrowprops=dict(arrowstyle="->", color="tab:red", lw=1))
    ax.annotate("contact (g=0):\nsharp mask replica", xy=(0.0, 1.0), xytext=(4.0, 0.86),
                fontsize=7.6, color="tab:green", va="top",
                arrowprops=dict(arrowstyle="->", color="tab:green", lw=1))
    # NILS on a twin axis (the second live discriminator)
    ax2 = ax.twinx()
    ax2.plot(r.gaps_um, r.nils_vs_gap, "--", color="tab:orange", lw=1.8, label="NILS")
    ax2.axhline(litho.NILS_PRINTABLE, color="tab:orange", ls=":", lw=1.0, alpha=0.7)
    ax2.set_ylabel("NILS  (printable ≳ 2)", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")
    ax2.set_ylim(0.0, 4.0)                            # cap: the contact step's NILS is off-scale (a delta)
    ax.set_title(f"Proximity shadow printing: contrast/NILS collapse as √(λg) "
                 f"({PROX_PITCH_NM*1e-3:.0f} µm feature)", fontsize=9.5)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=7.6, loc="upper right")

    fig.suptitle("Historical-modes A2 — period lithography: the wavelength race broke the Rayleigh floor, "
                 "projection broke the √(λg) proximity wall", fontsize=11.5)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ⁻³, →, √, λ on legacy codepages

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
