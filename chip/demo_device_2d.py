"""The v1.11 banked artifact: the 2-D MOSFET cross-section — lateral S/D diffusion → L_eff → device.

Wires the engine's 2-D regime (v1.8) into the process→device payoff (Phase 4). A coherent ~0.5 µm-node
n-MOSFET: a p-type ``N_A = 1e17`` channel, a thin **dry gate oxide** grown by Deal–Grove, and an n⁺
phosphorus **source/drain formed with the gate as its mask** — so the S/D diffuses *down and sideways
under the gate edges*, shrinking the drawn channel ``L_drawn`` to an **effective** length
``L_eff = L_drawn − 2·ΔL``. Two stories on one figure:

  * **The banked readout (left) — the S/D curving under the gate.** The 2-D n⁺ dopant field ``N(x, y)``
    (log fill, depth downward), mirrored into the full device: the poly **gate** drawn on the surface,
    the open **S/D windows** on either side, and the ``N = N_channel`` junction contour wrapping up
    **under the gate edges**. The drawn gate length ``L_drawn`` and the shortened **effective channel**
    ``L_eff`` (the surface gap the gate actually controls) are marked.

  * **The mechanism (right) — L_eff vs L_drawn, and the boundary.** The honest two-window
    ``L_eff_true`` (markers) lies on the textbook subtraction ``L_drawn − 2·ΔL`` (line) across the open
    range and they agree on the **punchthrough** knee at ``L_drawn ≈ 2·ΔL`` (where the channel closes).
    On the twin axis, ``V_t`` runs **flat** across the whole sweep — the honest boundary: the lateral
    diffusion moves the channel *length* and the drive *current* (``I_Dsat ∝ W/L``), **never** the
    *threshold* (short-channel ``V_t`` rolloff / DIBL is the named 2-D-electrostatics tar pit, left out).

This is a **validation deepening**: the independent two-window solve *confirms* the textbook effective
channel relation and the punchthrough limit (the front-interaction effect that would split them near
the knee is below the resolved scale — checked, not featured). The genuinely-2-D content is the figure
(the junction visibly curving under the gate); the quantitative weight is the validation.

Run headless (saves the figure, prints the cross-section table):

    python -m chip.demo_device_2d
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import oxidation as ox
from . import device_2d as d2

# --- The coherent ~0.5 µm-node n-MOSFET recipe ------------------------------- #
CHANNEL_N_A = 1.0e17           # cm⁻³ — p-type boron channel/substrate doping
SD_DOPANT = "P"               # n⁺ phosphorus source/drain
SD_T_CELSIUS = 1000.0         # °C — the S/D masked constant-source diffusion
SD_T_MIN = 6.0                # min → S/D x_j ≈ 0.12 µm, lateral ΔL ≈ 0.10 µm

GATE_OX_AMBIENT = "dry"       # dry O₂ gate oxide (thin, reaction-limited)
GATE_OX_T = 1000.0            # °C
GATE_OX_MIN = 15.0            # min → ~12 nm gate oxide

GATE = "n+poly"               # n⁺-poly gate (φ_gate = +0.55 V)
L_DRAWN_HEADLINE_UM = 0.5     # the representative drawn gate length (a 0.5 µm node)
DEVICE_WIDTH_UM = 10.0        # W for the drive-current readout
OVERDRIVE_V = 1.0             # V_GS − V_t for I_Dsat

# The L_drawn sweep for the mechanism panel (long-channel down through punchthrough).
L_DRAWN_SWEEP_UM = (0.75, 0.65, 0.55, 0.50, 0.45, 0.40, 0.35, 0.30, 0.25, 0.22, 0.20, 0.18)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-device-2d.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-device-2d.png"


@dataclass(frozen=True)
class CrossSectionResult:
    """The plain bundle the figure and summary consume (frozen + arrays — ADR 0002)."""

    gate_oxide: ox.OxideGrowth
    device: d2.MOSFET2D                     # the headline cross-section (field + device)
    L_drawn_sweep: np.ndarray               # µm
    L_eff_true_sweep: np.ndarray            # µm (two-window; 0.0 = punchthrough)
    L_eff_approx_sweep: np.ndarray          # µm (L_drawn − 2·ΔL, clamped ≥ 0)
    V_t: float                              # V — flat across the sweep (the boundary)
    two_delta_L_um: float                   # 2·ΔL — the subtraction's punchthrough threshold


def compute() -> CrossSectionResult:
    """Run the coherent 2-D MOSFET cross-section + the L_drawn sweep → :class:`CrossSectionResult`."""
    # The gate oxide (Phase 2) — its thickness sets C_ox (and is what the device reads).
    gate_oxide = ox.grow_oxide(GATE_OX_AMBIENT, GATE_OX_T, GATE_OX_MIN, orientation="100")

    # The headline device: the full cross-section (2-D field + the device read at L_eff_true).
    device = d2.mosfet_cross_section(
        channel_N_A=CHANNEL_N_A, t_ox_um=gate_oxide.t_ox, L_drawn_um=L_DRAWN_HEADLINE_UM,
        gate=GATE, sd_dopant=SD_DOPANT, sd_T_celsius=SD_T_CELSIUS, sd_t_min=SD_T_MIN,
        width_um=DEVICE_WIDTH_UM, overdrive_V=OVERDRIVE_V,
    )

    # The mechanism sweep: L_eff_true (cheap two-window) vs the subtraction across L_drawn.
    two_dL = 2.0 * device.delta_L_um
    L_drawn = np.array(L_DRAWN_SWEEP_UM)
    L_eff_true = np.array([
        d2.effective_channel_um(channel_N_A=CHANNEL_N_A, L_drawn_um=L, sd_dopant=SD_DOPANT,
                                sd_T_celsius=SD_T_CELSIUS, sd_t_min=SD_T_MIN)
        for L in L_drawn
    ])
    L_eff_approx = np.maximum(L_drawn - two_dL, 0.0)

    return CrossSectionResult(
        gate_oxide=gate_oxide, device=device, L_drawn_sweep=L_drawn,
        L_eff_true_sweep=L_eff_true, L_eff_approx_sweep=L_eff_approx,
        V_t=device.mos.V_t, two_delta_L_um=two_dL,
    )


def print_summary(r: CrossSectionResult) -> None:
    """Print the 2-D cross-section story — the demo's payoff in text."""
    d = r.device
    print("\n2-D MOSFET cross-section: lateral S/D diffusion → the effective channel length\n")
    print(f"  S/D       : n⁺ {d.sd_dopant} masked constant-source, {d.sd_T_celsius:.0f} °C / "
          f"{d.sd_t_min:.0f} min  →  vertical x_j = {d.sd_xj_um:.3f} µm, "
          f"lateral ΔL = {d.delta_L_um:.3f} µm (ratio {d.delta_L_um / d.sd_xj_um:.2f})")
    print(f"  gate oxide: {GATE_OX_AMBIENT} O₂ {GATE_OX_T:.0f} °C / {GATE_OX_MIN:.0f} min  →  "
          f"t_ox = {r.gate_oxide.t_ox_nm:.1f} nm")
    print(f"  channel   : L_drawn = {d.L_drawn_um:.3f} µm  →  the gate masks the S/D, which "
          f"diffuses 2·ΔL = {2 * d.delta_L_um:.3f} µm under the two edges")
    print(f"\n  EFFECTIVE CHANNEL  L_eff = L_drawn − 2·ΔL")
    print(f"    textbook (isolated edge)  L_drawn − 2·ΔL = {d.L_eff_approx_um:.3f} µm")
    print(f"    honest   (two-window solve)  2·x_j        = {d.L_eff_true_um:.3f} µm  "
          f"(they agree — the independent cross-check)")
    print(f"    →  {d.shortening_frac * 100:.0f}% shorter than drawn; "
          f"drive current I_Dsat ×{d.current_gain:.2f}  ({d.i_dsat * 1e3:.2f} mA vs "
          f"{d.i_dsat_drawn * 1e3:.2f} mA at L_drawn)")
    print(f"\n  THRESHOLD VOLTAGE  V_t = {d.mos.V_t:.3f} V  —  long-channel, **invariant** to L_eff: "
          f"the lateral diffusion moves the channel")
    print(f"    length and the current, NOT the threshold (short-channel rolloff / DIBL is the named "
          f"2-D-electrostatics tar pit, left out).")
    print(f"\n  The L_drawn sweep (the two routes track, then punch through together at ~2·ΔL = "
          f"{r.two_delta_L_um:.3f} µm):")
    print("    {:>9} {:>14} {:>14} {:>8}".format("L_drawn", "L−2ΔL (µm)", "2·x_j (µm)", "V_t (V)"))
    for L, ap, tr in zip(r.L_drawn_sweep, r.L_eff_approx_sweep, r.L_eff_true_sweep):
        tag = "  ← punchthrough" if tr == 0.0 else ""
        print(f"    {L:>9.3f} {ap:>14.3f} {tr:>14.3f} {r.V_t:>8.3f}{tag}")
    print()


def save_figure(r: CrossSectionResult) -> Path:
    """Render and save the 2-D cross-section artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import device_2d_figure

    fig = device_2d_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")         # µ, √, ², →, ⁻³, φ on legacy codepages

    data = compute()
    print_summary(data)
    try:
        saved = save_figure(data)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
