"""The recipe — the continuous process knobs the player sets, per step (the plan §1/§4).

A :class:`Recipe` is the full set of recipe knobs for one run of the line: one frozen
dataclass per process step plus the **Czochralski boule** the substrate is grown from. ``step(state,
knobs, rng)`` reads its own knob slice; the pipeline holds the whole recipe and dispatches each step
its slice.

:data:`DEFAULT_RECIPE` is **exactly** the coherent n-MOSFET recipe of
:mod:`chip.demo_device` — the same numbers, so a nominal, zero-variation run reproduces that
demo's device bit-for-bit (the seam). The knob names mirror the back end's call signatures
(``T_predep``/``t_predep_min`` → :func:`chip.diffusion_dopant.two_step`; ``ambient``/``minutes``
→ :func:`chip.oxidation.grow_oxide`; ``defocus_nm`` → :func:`chip.litho.expose_grating`).

G2 — the substrate is **grown, not set.** The channel/substrate doping is no longer a free scalar:
:class:`CzochralskiKnobs` grows a :class:`chip.czochralski.Boule` and the wafer's
``channel_N_A`` is the **Scheil slice** at its axial position ``slice_z`` (so wafers down a boule
start different — the front-of-line cause of a V_t spread). At the default knobs (``N_seed = 1e17``,
``slice_z = 0``) the seed slice returns ``1e17`` *exactly*, so the seam to ``demo_device`` holds.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from chip.czochralski import Boule


@dataclass(frozen=True)
class CzochralskiKnobs:
    """Czochralski boule knobs → :class:`chip.czochralski.Boule` — the substrate is **grown**, not set.

    ``dopant`` the p-type substrate species; ``N_seed`` (cm⁻³) the seed-end (``z=0``) doping — equal
    to ``demo_device``'s ``CHANNEL_N_A`` at the default, so the seed slice reproduces the demo
    bit-for-bit (the seam). ``slice_z`` ∈ ``[0, 1)`` is the axial fraction-solidified for **this**
    wafer (0 = seed end); :func:`fab_game.pipeline.run_batch` sweeps it down the boule. ``k`` is the
    cited Trumbore segregation coefficient (looked up from ``dopant``); ``length_mm``/``diameter_mm``
    are narrative geometry. (Pull rate/rotation are the named ``k_eff`` scope edge — not knobs here.)
    """

    dopant: str = "B"                  # p-type boron substrate
    N_seed: float = 1.0e17             # cm⁻³ seed-end doping = demo_device CHANNEL_N_A (the seam)
    slice_z: float = 0.0               # axial fraction solidified for THIS wafer (0 = seed end)
    length_mm: float = 200.0           # boule length (narrative geometry only)
    diameter_mm: float = 200.0         # boule diameter (narrative geometry only)


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
    """A full line recipe: the Czochralski boule the substrate is grown from + one slice per step.

    The substrate doping is **derived**, not stored: :attr:`channel_N_A` is the Scheil slice of the
    grown :attr:`boule` at the wafer's ``slice_z`` — read by both the junction analysis (S/D into the
    channel) and the device (the channel doping that sets ``V_t``). At the default Czochralski knobs
    the seed slice is exactly ``1e17``, matching :mod:`chip.demo_device`'s ``CHANNEL_N_A`` (the seam).
    """

    czochralski: CzochralskiKnobs = field(default_factory=CzochralskiKnobs)
    diffusion: DiffusionKnobs = field(default_factory=DiffusionKnobs)
    oxidation: OxidationKnobs = field(default_factory=OxidationKnobs)
    litho: LithoKnobs = field(default_factory=LithoKnobs)
    device: DeviceKnobs = field(default_factory=DeviceKnobs)

    @property
    def boule(self) -> Boule:
        """The :class:`chip.czochralski.Boule` grown from the Czochralski knobs (cited Scheil profile)."""
        cz = self.czochralski
        return Boule(dopant=cz.dopant, N_seed=cz.N_seed,
                     length_mm=cz.length_mm, diameter_mm=cz.diameter_mm)

    @property
    def channel_N_A(self) -> float:
        """The substrate doping (cm⁻³) at this wafer's boule slice — exactly ``N_seed`` at ``slice_z=0``."""
        return float(self.boule.axial_doping(self.czochralski.slice_z))

    @property
    def substrate_resistivity_ohm_cm(self) -> float:
        """The substrate resistivity (Ω·cm) at this wafer's boule slice (Masetti ``μ(N)``)."""
        return float(self.boule.axial_resistivity(self.czochralski.slice_z))


# The default recipe IS chip.demo_device's coherent n-MOSFET recipe (the seam anchor): the seed-end
# boule slice (slice_z=0, N_seed=1e17) reproduces CHANNEL_N_A = 1e17 exactly.
DEFAULT_RECIPE = Recipe()
