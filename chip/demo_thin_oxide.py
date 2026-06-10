"""The v1.1 thin-oxide demo: the Massoud burst on the gate-oxide leg — before vs after.

Phase 2 named the **thin-dry (Massoud) anomaly** as its scope edge: plain Deal–Grove
*under*-predicts the first ~25 nm of dry-O₂ growth. This demo banks the promoted correction
(:mod:`oxidation` §5) exactly where it bites the project: the **Phase-4 gate-oxide recipe**
(dry O₂, 1000 °C, 20 min, (100)) sits squarely inside the anomaly band, so the chain's payoff
input was the least honest number in it. The headline, on one figure:

  * **before** — the v1 chain's plain Deal–Grove (1965 constants): gate oxide ≈ 14 nm;
  * **after** — the cited Massoud time-decay model: the same recipe really grows ≈ 23 nm
    (~1.5× the same linear-parabolic law without the burst — shown as the grey baseline);
  * **the device consequence** — feeding both oxides to the Phase-4 compact model moves the
    threshold voltage by ≈ +0.4 V (``Q_dep/C_ox`` scales with ``t_ox``): the thin-regime
    anomaly is not an oxidation footnote, it is a *V_t-sized* error in the process→device chain.

The mechanism panel shows *why*: the Massoud growth rate starts ~4× the Deal–Grove linear rate
and decays onto it with the two cited time constants (τ₁ ≈ 1.2 min, τ₂ ≈ 7.5 min at 1000 °C) —
a **finite** transient worth exactly ``M₁+M₂`` of extra ``x²+Ax``, after which growth is pure
linear-parabolic again.

Run headless (saves the figure, prints the table):

    python -m projects.chip.demo_thin_oxide
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np

from . import device as dev
from . import oxidation as ox

# The gate-oxide recipe (demo_device's step 2 — the chain this demo sharpens).
T_GATE = 1000.0                # °C — inside the cited Massoud fit range (800–1000 °C)
ORIENTATION = "100"            # the device face
GATE_MIN = 20.0                # min — the Phase-4 gate-oxide time
T_RANGE_MIN = (0.0, 40.0)      # the sweep: the whole anomaly transient (τ₂ ≈ 7.5 min)
N_T = 400

# The Phase-4 channel the V_t consequence is read with (demo_device's channel + gate).
CHANNEL_N_A = 1.0e17           # cm⁻³
GATE = "n+poly"

_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-thin-oxide.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-thin-oxide.png"


def compute():
    """Run the before/after sweeps; return ``(t_min, curves, rates, gate, vt)``.

    ``curves`` is ``{name: x_ox µm array}`` over ``t_min`` for the three thickness curves
    (``massoud``, ``plain_same_ba`` — the same B, A without the burst — and ``v1_dg1965``)
    plus the two rate curves in nm/min (``rate_massoud``, ``rate_plain``); ``rates`` the
    evaluated :class:`oxidation.MassoudRates`; ``gate`` the dict of the two
    :class:`oxidation.OxideGrowth` table points; ``vt`` the dict of the two Phase-4
    :class:`device.MOSDevice` readouts.
    """
    rates = ox.massoud_rate_constants(T_GATE, ORIENTATION)
    t_min = np.linspace(T_RANGE_MIN[0], T_RANGE_MIN[1], N_T)

    x_massoud = ox.oxide_thickness_massoud(t_min, rates)
    # The same linear-parabolic law with the burst switched off (K₁=K₂=0) — isolates the
    # enhancement itself, on Massoud's own coherent B, A.
    rates_off = dataclasses.replace(rates, K1=0.0, K2=0.0)
    x_plain = ox.oxide_thickness_massoud(t_min, rates_off)
    # The v1 chain's prediction: plain Deal–Grove on the 1965 cited constants.
    r_v1 = ox.oxide_rate_constants("dry", T_GATE, ORIENTATION)
    x_v1 = ox.oxide_thickness(t_min / ox.MIN_PER_HOUR, r_v1.B, r_v1.A)

    curves = {
        "massoud": x_massoud,
        "plain_same_ba": x_plain,
        "v1_dg1965": x_v1,
        "rate_massoud": ox.massoud_growth_rate(x_massoud, t_min, rates),
        "rate_plain": ox.massoud_growth_rate(x_plain, t_min, rates_off),
    }

    gate = {
        "massoud": ox.grow_oxide_massoud(T_GATE, GATE_MIN, ORIENTATION),
        "v1": ox.grow_oxide("dry", T_GATE, GATE_MIN, orientation=ORIENTATION),
    }
    vt = {name: dev.threshold_voltage(CHANNEL_N_A, g.t_ox, gate=GATE)
          for name, g in gate.items()}
    return t_min, curves, rates, gate, vt


def print_summary(rates, gate, vt) -> None:
    """Print the burst → gate oxide → V_t story — the demo's payoff in text."""
    print(f"\nMassoud thin-dry correction at {T_GATE:.0f} °C on ({ORIENTATION}) silicon "
          f"(cited fit range {ox.MASSOUD_T_RANGE_C[0]:.0f}–{ox.MASSOUD_T_RANGE_C[1]:.0f} °C, dry O₂)\n")
    print(f"  Massoud set : B = {rates.B:.0f} nm²/min,  B/A = {rates.B_over_A:.3f} nm/min,  "
          f"A = {rates.A:.0f} nm")
    print(f"  the burst   : K₁ = {rates.K1:.0f} nm²/min on τ₁ = {rates.tau1:.2f} min,  "
          f"K₂ = {rates.K2:.0f} nm²/min on τ₂ = {rates.tau2:.2f} min")
    print(f"                → worth a finite M₁+M₂ = {rates.M1 + rates.M2:.0f} nm² of extra x²+Ax, "
          f"then pure linear-parabolic again\n")
    g_m, g_v1 = gate["massoud"], gate["v1"]
    print(f"  gate recipe ({GATE_MIN:.0f} min):  v1 plain Deal–Grove → {g_v1.t_ox_nm:.1f} nm   "
          f"|   Massoud → {g_m.t_ox_nm:.1f} nm   (×{g_m.t_ox / g_v1.t_ox:.2f})")
    v_m, v_v1 = vt["massoud"], vt["v1"]
    print(f"  the Phase-4 consequence (N_A = {CHANNEL_N_A:.0e} cm⁻³, {GATE}):")
    print(f"      V_t({g_v1.t_ox_nm:.1f} nm) = {v_v1.V_t:.3f} V   →   "
          f"V_t({g_m.t_ox_nm:.1f} nm) = {v_m.V_t:.3f} V   (ΔV_t = {v_m.V_t - v_v1.V_t:+.3f} V)")
    print(f"      — the thin-dry anomaly was a V_t-sized error in the chain, not a footnote\n")


def save_figure(t_min, curves, rates, gate) -> Path:
    """Render and save the before/after artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import thin_oxide_figure

    fig = thin_oxide_figure(
        t_min, curves, rates, gate_t_min=GATE_MIN,
        gate_massoud_nm=gate["massoud"].t_ox_nm, gate_v1_nm=gate["v1"].t_ox_nm,
        T_celsius=T_GATE, orientation=ORIENTATION,
    )
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ₂, µ, → on legacy codepages

    t_min, curves, rates, gate, vt = compute()
    print_summary(rates, gate, vt)
    try:
        saved = save_figure(t_min, curves, rates, gate)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
