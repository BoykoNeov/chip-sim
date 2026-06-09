"""The Phase-4 banked artifact: the whole process→device flow on one figure — recipe in, V_t out.

The chip's payoff demo and the counterpart of Steel's four-curves anchor. It chains **one coherent
n-MOSFET** through all three process modules and reads the device parameter off the end:

  1. **Diffusion** (Phase 1a, frozen engine) — an n⁺ phosphorus source/drain diffused into a
     **p-type, N_A = 1e17 channel**; the junction depth ``x_j`` is the S/D depth.
  2. **Oxidation** (Phase 2, Deal–Grove) — a thin **dry-O₂ gate oxide** (~14 nm, the reaction-limited
     thin regime — *not* the banked field oxide); its ``t_ox`` sets ``C_ox``.
  3. **Lithography** (Phase 3, Abbe aerial image) — the gate grating prints a **CD ≈ 0.17 µm**, the
     channel length ``L``.
  4. **Device** (Phase 4) — ``V_t = V_FB + 2φ_F + Q_dep/C_ox`` from the channel ``N_A`` and the gate
     ``t_ox``; the litho ``L`` sets the geometry (and an honest long-channel ``I_Dsat``), *not* ``V_t``.

The coherence is the point (and the advisor's flagged requirement): the three process outputs describe
**the same device**, so the final ``V_t`` is the genuine consequence of the recipe — not three unrelated
numbers on one canvas. ``V_t ≈ 0.55 V`` for this ~180 nm-node n-MOSFET (cf. the cited MIT worked example
at exactly 15 nm → 0.58 V; this demo's 14 nm oxide gives the slightly lower value).

Run headless (saves the figure, prints the flow):

    python -m projects.chip.demo_device
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import oxidation as ox
from . import litho
from . import device as dev
from . import diffusion_dopant as dd
from .junction import analyze_junction, Junction
from .diffusion_dopant import DopantProfile

# --- The coherent n-MOSFET recipe (one device through every step) ----------- #
CHANNEL_N_A = 1.0e17            # cm⁻³ — p-type boron channel/substrate doping (the Phase-1 wafer)
SD_DOPANT = "P"                # n⁺ phosphorus source/drain (types flipped from the Phase-1a banked demo)
SD_PREDEP = (950.0, 15.0)      # S/D predep: °C, minutes
SD_DRIVEIN = (1000.0, 30.0)    # S/D drive-in: °C, minutes
SUBSTRATE_LENGTH_UM = 2.0

GATE_OX_AMBIENT = "dry"        # dry O₂ — the controllable gate-oxide ambient (thin, reaction-limited)
GATE_OX_T = 1000.0             # °C
GATE_OX_MIN = 20.0             # min → ~14 nm gate oxide

LITHO_IMAGING = litho.Imaging(wavelength_nm=193.0, NA=0.85, sigma=0.5)   # 193 nm ArF, NA 0.85, σ 0.5
GATE_PITCH_NM = 300.0          # the gate line/space pitch → CD ≈ 167 nm gate length

GATE = "n+poly"                # n⁺-poly gate (φ_gate = +0.55 V)
DEVICE_WIDTH_UM = 10.0         # W for the long-channel drive-current readout
OVERDRIVE_V = 1.0              # V_GS − V_t for I_Dsat

_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-device.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-device.png"


@dataclass(frozen=True)
class FlowResult:
    """The chained process→device result — the plain bundle the figure and summary consume."""

    sd_predep: DopantProfile
    sd_drivein: DopantProfile
    sd_junction: Junction
    t_hours: np.ndarray
    oxide_curve: np.ndarray
    gate_oxide: ox.OxideGrowth
    litho_x_nm: np.ndarray
    litho_intensity: np.ndarray
    litho_threshold: float
    gate_feature: litho.PrintedFeature
    mos: dev.MOSDevice
    i_dsat: float


def compute() -> FlowResult:
    """Run the coherent n-MOSFET recipe end to end → :class:`FlowResult` (no plotting)."""
    # 1. Diffusion — n⁺ S/D into the p-type channel; the junction is the S/D depth.
    predep, drivein = dd.two_step(
        SD_DOPANT, T_predep=SD_PREDEP[0], t_predep_min=SD_PREDEP[1],
        T_drivein=SD_DRIVEIN[0], t_drivein_min=SD_DRIVEIN[1], length_um=SUBSTRATE_LENGTH_UM,
    )
    sd_junction = analyze_junction(drivein, SD_DOPANT, CHANNEL_N_A)

    # 2. Oxidation — the thin dry gate oxide (and its growth curve for the panel).
    t_hours = np.logspace(-2.0, 0.0, 150)
    r = ox.oxide_rate_constants(GATE_OX_AMBIENT, GATE_OX_T, "100")
    oxide_curve = ox.oxide_thickness(t_hours, r.B, r.A)
    gate_oxide = ox.grow_oxide(GATE_OX_AMBIENT, GATE_OX_T, GATE_OX_MIN, orientation="100")

    # 3. Lithography — the gate aerial image + printed CD (the channel length).
    orders = litho.grating_orders(GATE_PITCH_NM)
    litho_x = np.linspace(-GATE_PITCH_NM, GATE_PITCH_NM, 400)
    litho_I = litho.abbe_image(litho_x, orders, LITHO_IMAGING)
    litho_threshold = float(litho_I.mean())
    gate_feature = litho.expose_grating(imaging=LITHO_IMAGING, pitch_nm=GATE_PITCH_NM)

    # 4. Device — V_t from the channel N_A + the gate t_ox; litho CD sets the geometry (not V_t).
    mos = dev.threshold_voltage(
        CHANNEL_N_A, gate_oxide.t_ox, gate=GATE, channel_length_um=gate_feature.cd_um,
    )
    i_dsat = dev.saturation_current(mos, mos.V_t + OVERDRIVE_V, DEVICE_WIDTH_UM)

    return FlowResult(
        sd_predep=predep, sd_drivein=drivein, sd_junction=sd_junction,
        t_hours=t_hours, oxide_curve=oxide_curve, gate_oxide=gate_oxide,
        litho_x_nm=litho_x, litho_intensity=litho_I, litho_threshold=litho_threshold,
        gate_feature=gate_feature, mos=mos, i_dsat=i_dsat,
    )


def print_summary(r: FlowResult) -> None:
    """Print the recipe → device story — the demo's payoff in text."""
    m = r.mos
    print("\nProcess → device: a coherent n-MOSFET, recipe in → V_t out\n")
    print(f"  1. diffusion : n⁺ {SD_DOPANT} S/D into p-type N_A={CHANNEL_N_A:.0e} cm⁻³ channel"
          f"  →  S/D junction x_j = {r.sd_junction.x_j_um:.3f} µm")
    g = r.gate_oxide
    print(f"  2. oxidation : {GATE_OX_AMBIENT} O₂ {GATE_OX_T:.0f} °C / {GATE_OX_MIN:.0f} min"
          f"  →  gate oxide t_ox = {g.t_ox_nm:.1f} nm ({g.regime} regime)")
    f = r.gate_feature
    print(f"  3. litho     : 193 nm ArF, NA {LITHO_IMAGING.NA}, σ {LITHO_IMAGING.sigma}, "
          f"pitch {GATE_PITCH_NM:.0f} nm  →  gate length L = {f.cd_nm:.0f} nm "
          f"(CD = {f.cd_um:.3f} µm, NILS {f.nils:.2f})")
    print(f"  4. device    : V_t = V_FB({m.V_FB:+.3f}) + 2φ_F({m.two_phi_F:.3f}) "
          f"+ Q_dep/C_ox({m.body_term:.3f})")
    print(f"\n     →  C_ox = {m.C_ox:.3e} F/cm²,  γ = {m.gamma:.3f} V^½")
    print(f"     →  THRESHOLD VOLTAGE  V_t = {m.V_t:.3f} V   (n⁺-poly gate, {GATE_PITCH_NM:.0f} nm pitch)")
    print(f"     →  long-channel I_Dsat (V_ov={OVERDRIVE_V:.0f} V, W={DEVICE_WIDTH_UM:.0f} µm) "
          f"= {r.i_dsat * 1e3:.2f} mA   (the litho CD sets W/L, not V_t)\n")


def save_figure(r: FlowResult) -> Path:
    """Render and save the process→device flow artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import device_figure

    fig = device_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ₂, φ, → on legacy codepages

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
