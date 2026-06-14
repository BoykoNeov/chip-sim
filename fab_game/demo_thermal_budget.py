"""The E1 banked artifact: a spike/RTA anneal's thermal budget → a shallower junction.

The diffusion deepening on the **transient-anneal** axis (the scope-edge backlog E1). A spike /
rapid-thermal anneal ramps the wafer through a temperature schedule ``T(t)`` instead of holding one
setpoint. The verify-at-build gate — *"is T emergent or just the setpoint?"* — resolves to
**setpoint**: in silicon the dopant/thermal diffusivity ratio ``√(D/α) ≈ 1.2e-6``, so at a
junction's length scale the thermal field is always flat (``T(t)`` is spatially uniform over the
diffusion domain). So this is **not** a heat-mode engine consumer (that premise is falsified, the
same way Robin-`G` was — heat-mode stays Steel-program-only); it is the engine's already-shipped
**time-dependent ``D(t)``** path, the twin of OED's ``coupling.effective_Dt``.

The finding (two panels, one thesis — *budget, not clock time, sets the depth*):

1. **The budget accrues in a narrow window near the peak.** Plotting ``T(t)`` and the cumulative
   ``∫₀ᵗ D(T(t'))dt'`` for a representative spike: the Arrhenius ``D`` collapses away from the peak,
   so almost all of the diffusion budget is deposited in the top ~50 °C — the long shoulders through
   600 → 1000 °C contribute almost nothing.
2. **Faster ramp → shallower junction (the pipeline consequence).** Sweeping the ramp rate, the
   spike's junction depth ``x_j`` falls (and ``R_s`` rises) as the ramp steepens, because the
   equivalent isothermal time ``t_eq = budget / D(T_peak)`` shrinks like ``1/β`` — the
   ``D0``-independent Laplace closed form ``t_eq ≈ hold + (k·T_peak²/Ea)·(1/β_up + 1/β_down)``
   tracks the exact (trapezoid) budget to a few %. *This* is why RTA gives shallow junctions: a
   13 s spike can deposit the diffusion of barely ~1 s at the peak.

The honesty ladder (the repo's bar): the **cited/engine** legs are the ``τ = ∫D dt`` time-
substitution (``engines.diffusion test_variable_d``) and the Laplace asymptotics of the Arrhenius
integral; the spike *recipe* numbers (peak, ramp rates, hold) are illustrative house settings. Opt-in
and seam-safe — ``drivein_program=None`` ⇒ the isothermal drive-in, the G1–G7 banked demos
byte-for-byte unchanged.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_thermal_budget
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.diffusion_dopant import (
    ThermalProgram,
    diffusivity,
    equivalent_isothermal_time,
    spike_budget_time_laplace,
    thermal_budget,
)

from .recipe import DiffusionKnobs, Recipe
from .steps import diffusion_junction

# --- The demo settings (illustrative house numbers — mechanics, not magnitudes) --- #
DOPANT = "P"                                       # the n⁺ S/D dopant (DiffusionKnobs default)
CHANNEL_N_A = 1.0e17                               # the p-substrate the junction forms against
PEAK_C = 1050.0                                    # spike peak temperature (°C)
HOLD_S = 1.0                                       # peak dwell (s)
BASE_C = 600.0                                     # ramp endpoints (°C; below this D is negligible)
RAMP_REF_C_PER_S = 50.0                            # the representative ramp for the budget panel
RAMP_SWEEP_C_PER_S = (10.0, 20.0, 35.0, 60.0, 100.0, 175.0, 300.0)  # the x_j / t_eq sweep
N_PROFILE = 400                                    # points along the representative T(t)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-e1.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-e1.png"


@dataclass(frozen=True)
class DemoResult:
    """The budget-accrual profile + the ramp-rate sweep (x_j / R_s / t_eq) — no score."""

    dopant: str
    peak_C: float
    base_C: float
    hold_s: float
    # Panel 1 — the representative spike: T(t) and the cumulative budget (normalized 0→1):
    ramp_ref: float
    t_profile: tuple[float, ...]                    # s
    T_profile: tuple[float, ...]                    # °C
    cumulative_budget_frac: tuple[float, ...]       # ∫₀ᵗ D dt / ∫₀^dur D dt (0→1)
    ref_duration_s: float
    ref_t_eq_s: float
    # Panel 2 — the ramp-rate sweep (the pipeline consequence + the t_eq collapse):
    ramp_rates: tuple[float, ...]                   # °C/s
    x_j_um: tuple[float, ...]                        # spike junction depth (µm)
    R_s: tuple[float, ...]                           # spike sheet resistance (Ω/sq)
    t_eq_numeric_s: tuple[float, ...]               # equivalent isothermal time (exact, trapezoid)
    t_eq_laplace_s: tuple[float, ...]               # the D0-independent Laplace closed form
    durations_s: tuple[float, ...]                  # the spike clock time (for the collapse factor)
    # The isothermal baseline (the seam reference — DiffusionKnobs defaults):
    x_j_iso_um: float
    R_s_iso: float
    T_iso_C: float
    t_iso_min: float


def _spike(ramp_C_per_s: float) -> ThermalProgram:
    return ThermalProgram(T_peak=PEAK_C, ramp_up_C_per_s=ramp_C_per_s,
                          ramp_down_C_per_s=ramp_C_per_s, hold_s=HOLD_S, T_base=BASE_C)


def compute() -> DemoResult:
    """Build the budget-accrual profile and the ramp-rate sweep (x_j / R_s / t_eq vs ramp rate)."""
    # Panel 1 — the representative spike: T(t) and the cumulative ∫D dt (normalized).
    ref = _spike(RAMP_REF_C_PER_S)
    t = np.linspace(0.0, ref.duration, N_PROFILE)
    T = np.array([ref(ti) for ti in t])
    D = np.array([diffusivity(DOPANT, ti) for ti in T])
    cum = np.concatenate(([0.0], np.cumsum(0.5 * (D[1:] + D[:-1]) * np.diff(t))))  # cumulative trapezoid
    cum_frac = cum / cum[-1]
    ref_budget = thermal_budget(DOPANT, ref)
    ref_t_eq = equivalent_isothermal_time(DOPANT, PEAK_C, ref_budget)

    # Panel 2 — the ramp-rate sweep: the pipeline x_j/R_s (diffusion_junction IS the line's diffusion
    # step, die-independent) and the equivalent isothermal time (exact vs the Laplace closed form).
    x_j, R_s, t_eq_num, t_eq_lap, durations = [], [], [], [], []
    for rate in RAMP_SWEEP_C_PER_S:
        spike = _spike(rate)
        _, out = diffusion_junction(DiffusionKnobs(dopant=DOPANT, drivein_program=spike), CHANNEL_N_A)
        x_j.append(float(out["x_j_um"]))
        R_s.append(float(out["R_s"]))
        t_eq_num.append(float(equivalent_isothermal_time(DOPANT, PEAK_C, thermal_budget(DOPANT, spike))))
        t_eq_lap.append(float(spike_budget_time_laplace(DOPANT, spike)))
        durations.append(float(spike.duration))

    # The isothermal baseline (the seam — DiffusionKnobs defaults, no program).
    base_knobs = DiffusionKnobs(dopant=DOPANT)
    _, base_out = diffusion_junction(base_knobs, CHANNEL_N_A)

    return DemoResult(
        dopant=DOPANT, peak_C=PEAK_C, base_C=BASE_C, hold_s=HOLD_S,
        ramp_ref=RAMP_REF_C_PER_S,
        t_profile=tuple(float(v) for v in t), T_profile=tuple(float(v) for v in T),
        cumulative_budget_frac=tuple(float(v) for v in cum_frac),
        ref_duration_s=float(ref.duration), ref_t_eq_s=float(ref_t_eq),
        ramp_rates=RAMP_SWEEP_C_PER_S,
        x_j_um=tuple(x_j), R_s=tuple(R_s),
        t_eq_numeric_s=tuple(t_eq_num), t_eq_laplace_s=tuple(t_eq_lap),
        durations_s=tuple(durations),
        x_j_iso_um=float(base_out["x_j_um"]), R_s_iso=float(base_out["R_s"]),
        T_iso_C=base_knobs.T_drivein_C, t_iso_min=base_knobs.t_drivein_min,
    )


def print_summary(r: DemoResult) -> None:
    """Print the budget-collapse → shallow-junction story — the demo's payoff in text (no score)."""
    print("\nDiffusion E1: a spike/RTA anneal's thermal budget → a shallower junction\n")

    print("  The verify-at-build gate ('is T emergent or just the setpoint?') resolves to SETPOINT:")
    print("  √(D_dopant/α_thermal) ≈ 1.2e-6 in Si → T is flat over the junction → D(T(t)) is the")
    print("  engine's already-shipped D(t) (the OED effective_Dt twin), NOT a heat-mode engine build.")
    print("  Heat-mode is falsified here (joins Robin-G) → Steel-program-only.\n")

    collapse = r.ref_duration_s / r.ref_t_eq_s
    print(f"  A {r.ramp_ref:.0f} °C/s spike to {r.peak_C:.0f} °C ({r.base_C:.0f}→peak→{r.base_C:.0f}, "
          f"{r.hold_s:.0f} s hold):")
    print(f"     clock time   = {r.ref_duration_s:5.1f} s")
    print(f"     budget t_eq  = {r.ref_t_eq_s:5.2f} s at the peak   → an {collapse:.1f}× COLLAPSE")
    print(f"     (the Arrhenius D collapses off the peak — only the top ~50 °C of the ramp counts)\n")

    print(f"  Faster ramp → less budget → shallower junction (n⁺ {r.dopant}, the pipeline diffusion step):")
    print(f"     {'ramp (°C/s)':>11}  {'clock (s)':>9}  {'t_eq (s)':>8}  {'Laplace':>7}  {'x_j (µm)':>8}  {'R_s (Ω/sq)':>10}")
    for i, rate in enumerate(r.ramp_rates):
        print(f"     {rate:>11.0f}  {r.durations_s[i]:>9.1f}  {r.t_eq_numeric_s[i]:>8.2f}  "
              f"{r.t_eq_laplace_s[i]:>7.2f}  {r.x_j_um[i]:>8.4f}  {r.R_s[i]:>10.1f}")
    print(f"\n  Isothermal baseline (the seam — {r.T_iso_C:.0f} °C / {r.t_iso_min:.0f} min drive-in): "
          f"x_j = {r.x_j_iso_um:.4f} µm, R_s = {r.R_s_iso:.1f} Ω/sq")
    print(f"     → the spike trades a hotter peak for a far smaller budget: a shallower, more abrupt "
          f"junction.\n")

    lap_err = max(abs(n - l) / l for n, l in zip(r.t_eq_numeric_s, r.t_eq_laplace_s))
    print(f"  New: the D(T(t)) → ∫D dt budget path (chip.diffusion_dopant, triad-tested); the "
          f"D0-independent\n  Laplace t_eq closed form tracks the exact budget to {lap_err:.0%}. "
          f"Opt-in (drivein_program=None → seam).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the E1 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import thermal_budget_figure

    fig = thermal_budget_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, →, ≈ on legacy codepages

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
