"""The recipe — the continuous process knobs the player sets, per step (the plan §1/§4).

A :class:`Recipe` is the full set of recipe knobs for one run of the line: one frozen
dataclass per process step plus the substrate doping. ``step(state, knobs, rng)`` reads its own
knob slice; the pipeline holds the whole recipe and dispatches each step its slice.

:data:`DEFAULT_RECIPE` is **exactly** the coherent n-MOSFET recipe of
:mod:`chip.demo_device` — the same numbers, so a nominal, zero-variation run reproduces that
demo's device bit-for-bit (the seam). The knob names mirror the back end's call signatures
(``T_predep``/``t_predep_min`` → :func:`chip.diffusion_dopant.two_step`; ``ambient``/``minutes``
→ :func:`chip.oxidation.grow_oxide`; ``defocus_nm`` → :func:`chip.litho.expose_grating`).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiffusionKnobs:
    """Source/drain two-step diffusion knobs → :func:`chip.diffusion_dopant.two_step`."""

    dopant: str = "P"                  # n⁺ phosphorus S/D into the p-type channel
    T_predep_C: float = 950.0          # °C
    t_predep_min: float = 10.0         # min
    T_drivein_C: float = 950.0         # °C
    t_drivein_min: float = 8.0         # min → shallow x_j ≈ 0.10 µm
    length_um: float = 2.0             # substrate depth domain


@dataclass(frozen=True)
class OxidationKnobs:
    """Gate-oxide growth knobs → :func:`chip.oxidation.grow_oxide` (thin dry-O₂ gate oxide)."""

    ambient: str = "dry"               # dry O₂ — the controllable thin/reaction-limited gate ambient
    T_celsius: float = 1000.0          # °C
    minutes: float = 20.0              # min → ~14 nm gate oxide
    orientation: str = "100"           # wafer orientation


@dataclass(frozen=True)
class LithoKnobs:
    """Gate-litho aerial-image knobs → :func:`chip.litho.expose_grating`. ``defocus_nm`` is the bad knob."""

    wavelength_nm: float = 193.0       # ArF
    NA: float = 0.85
    sigma: float = 0.5                 # partial-coherence factor
    pitch_nm: float = 300.0            # gate line/space pitch → CD ≈ 167 nm
    defocus_nm: float = 0.0            # **the dramatic-win knob**: focus error → CD → L → I_Dsat


@dataclass(frozen=True)
class DeviceKnobs:
    """Device-read knobs → :func:`chip.device.threshold_voltage` / :func:`chip.device.saturation_current`."""

    gate: str = "n+poly"               # n⁺-poly gate (φ_gate = +0.55 V)
    width_um: float = 10.0             # device width W for the I_Dsat readout
    overdrive_V: float = 1.0           # V_GS − V_t for I_Dsat


@dataclass(frozen=True)
class Recipe:
    """A full line recipe: the substrate doping + one knob slice per process step.

    ``channel_N_A`` (cm⁻³) is the p-type substrate doping — read by both the junction analysis
    (S/D into the channel) and the device (the channel doping that sets ``V_t``), exactly as
    :mod:`chip.demo_device` uses its ``CHANNEL_N_A``.
    """

    channel_N_A: float = 1.0e17
    diffusion: DiffusionKnobs = field(default_factory=DiffusionKnobs)
    oxidation: OxidationKnobs = field(default_factory=OxidationKnobs)
    litho: LithoKnobs = field(default_factory=LithoKnobs)
    device: DeviceKnobs = field(default_factory=DeviceKnobs)


# The default recipe IS chip.demo_device's coherent n-MOSFET recipe (the seam anchor).
DEFAULT_RECIPE = Recipe()
