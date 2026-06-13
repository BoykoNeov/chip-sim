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
from chip.purification import FEEDSTOCK_GRADES, Contamination, zone_refine


@dataclass(frozen=True)
class PurificationKnobs:
    """Silicon-purification knobs → :mod:`chip.purification` (G4) — the feedstock grade + zone passes.

    ``grade`` is a :data:`chip.purification.FEEDSTOCK_GRADES` key (``"MGS"``/``"solar"``/``"EGS"``/
    ``"clean"``); zone refining then scrubs that starting impurity vector by each species' cited ``k``
    over ``zone_passes`` passes (the costly rework knob — more passes, cleaner feed). The purified
    impurity vector becomes the wafer's wafer-level :class:`chip.purification.Contamination` (uniform
    across the die map — it composes orthogonally with the boule axial story, like ``slice_z``).

    ``grade`` defaults to **``"clean"``** (the idealized pristine baseline — all-zero impurities) so the
    seam *and* the G1/G2/G3 banked demos are byte-for-byte unchanged: a clean feed yields a clean
    contamination vector for any ``zone_passes``, so ``Q_ox = 0`` and the net-doping shift is 0 (the
    device is the ideal-oxide ``demo_device``). The G4 demo dials in a dirty grade to introduce the
    mobile-ion (Na→V_t) and residual-dopant stories.
    """

    grade: str = "clean"               # FEEDSTOCK_GRADES key — "clean" idealized baseline (the seam)
    zone_passes: int = 1               # zone-refining passes (more = cleaner feed; the costly rework knob)


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
class WaferPrepKnobs:
    """Wafer-prep knobs → :mod:`chip.wafer_prep` (G3) — the geometry + the killer-defect density.

    Geometry (exact bookkeeping): ``incoming_thickness_um`` from the saw, ``slice_ttv_um`` /
    ``slice_bow_um`` the as-sliced flatness, ``cmp_removal_um`` the lap+CMP material removal (eats
    thickness), ``cmp_ttv_improvement`` ∈ ``[0, 1]`` the planarizing fraction (improves TTV; bow is
    *not* fixed by CMP). ``defect_density`` (cm⁻²) is the line's **killer**-particle level — the
    :data:`chip.wafer_prep.DEFECT_DENSITY_BANDS` knob.

    ``defect_density`` defaults to **0.0** (a defect-free line) so the seam *and* the G1/G2 banked
    demos are unchanged — a zero density places no particles and consumes no RNG, and defect placement
    is anyway gated by the stochastic layer (``NO_VARIATION`` → no particles regardless). The G3 demo
    dials in a :data:`~chip.wafer_prep.DEFECT_DENSITY_BANDS` level to introduce the killer-defect
    story. The geometry defaults sit comfortably **in** the geometry spec (the seam wafer is never
    scrapped). ``wafer_diameter_mm`` sets the die-map physical scale (the single
    :func:`fab_game.state.die_area_cm2`).
    """

    incoming_thickness_um: float = 800.0   # as-sliced wafer thickness (µm)
    slice_ttv_um: float = 2.0              # as-sliced total thickness variation (µm)
    slice_bow_um: float = 25.0             # as-sliced bow (µm) — CMP does not fix this
    cmp_removal_um: float = 60.0           # lap + CMP material removed (µm)
    cmp_ttv_improvement: float = 0.85      # TTV planarized by 85 % (fraction ∈ [0, 1])
    defect_density: float = 0.0            # cm⁻² killer-defect density (0 ⇒ clean line; G3 demo dials it up)
    wafer_diameter_mm: float = 200.0       # die-map physical scale (→ die area)


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
class EtchDepositionKnobs:
    """Etch & deposition knobs → :mod:`chip.etch_deposition` (G5) — the mid-line gate-pattern transfer.

    The etch transfers the resist CD into the gate film: ``anisotropy`` ∈ ``[0, 1]`` (1 = perfectly
    anisotropic; <1 undercuts the mask → an etch bias that **shrinks** the CD), ``over_etch_frac`` the
    extra etch past endpoint (deepens the etch → widens the undercut → more CD loss, and consumes the
    underlayer by ``OE·film/selectivity``), ``film_thickness_nm`` the gate film etched through (sets
    the standing gate height the deposition's gap aspect ratio reads), ``selectivity`` to the
    underlayer. The deposition then fills the gaps between gate lines: ``conformality`` (step coverage)
    ∈ ``[0, 1]`` (1 = conformal CVD; a poor PVD voids high-aspect-ratio gaps → a **functional** kill).

    Defaults are the **idealized seam baseline** — ``anisotropy = 1`` (zero bias → the etched CD equals
    the printed CD bit-for-bit) and ``conformality = 1`` (never voids) — so the seam *and* the G1–G4
    banked demos are byte-for-byte unchanged (the etch step is the identity at the default recipe). The
    G5 demo dials a realistic ``anisotropy < 1`` + over-etch (CD collapse) and a poor PVD coverage (the
    void kill).
    """

    film_thickness_nm: float = 150.0   # gate film etched through (sets the standing gate height)
    anisotropy: float = 1.0            # 1 = perfectly anisotropic (the seam); <1 → etch bias → CD shrinks
    over_etch_frac: float = 0.0        # over-etch past endpoint (0 = none; deepens etch → more undercut)
    selectivity: float = 20.0          # etch selectivity to the underlayer (over-etch underlayer loss)
    conformality: float = 1.0          # deposition step coverage (1 = conformal CVD seam; <1 voids high-AR gaps)


@dataclass(frozen=True)
class DeviceKnobs:
    """Device-read knobs → :func:`chip.device.threshold_voltage` / :func:`chip.device.saturation_current`."""

    gate: str = "n+poly"               # n⁺-poly gate (φ_gate = +0.55 V)
    width_um: float = 10.0             # device width W for the I_Dsat readout
    overdrive_V: float = 1.0           # V_GS − V_t for I_Dsat


@dataclass(frozen=True)
class PackagingKnobs:
    """Back-end (assembly) yield knobs → :mod:`chip.packaging` (G6) — the per-step survival yields.

    After wafer sort decides which dies work, the good dies are diced, attached, wire-bonded, and
    encapsulated; each operation can lose a part, so the **assembly yield** is the product of the
    per-step survival probabilities (the cited funnel, :func:`chip.packaging.assembly_yield`). The
    back-end loss is **stochastic** — a per-die Bernoulli draw against :attr:`assembly_yield` (drawn
    only when the back end is lossy *and* the stochastic layer is on), so it lives with the variation
    layer (like the killer-particle scatter), not the deterministic core.

    All four default to **1.0** (a perfect back end loses nothing) so the seam *and* the G1–G5 banked
    demos are byte-for-byte unchanged: ``assembly_yield = 1.0`` ⇒ no draw ⇒ every front-end-good die is
    packaged. The G6 demo dials in :data:`chip.packaging.ASSEMBLY_STEPS` (a realistic mature back end)
    or degrades one step (e.g. a bad wire-bond) to narrow the funnel. Cracked/scrapped parts are
    irreversible (the plan's "cracked die = scrap"); rebond is a named, deferred edge.
    """

    dice_yield: float = 1.0            # wafer dicing/singulation survival (1.0 = no saw loss; the seam)
    attach_yield: float = 1.0          # die-attach survival
    bond_yield: float = 1.0            # wire-bond survival (the lossiest back-end step when degraded)
    encapsulate_yield: float = 1.0     # mold/encapsulation survival

    @property
    def step_yields(self) -> tuple[float, ...]:
        """The four per-step survival yields in funnel order (dice → attach → bond → encapsulate)."""
        return (self.dice_yield, self.attach_yield, self.bond_yield, self.encapsulate_yield)

    @property
    def assembly_yield(self) -> float:
        """The cumulative back-end yield ``Π step_yields`` — the per-die back-end survival probability.

        Exactly ``1.0`` at the default (perfect) knobs (the seam): a part is then packaged with
        certainty and the stochastic kill never draws.
        """
        from chip.packaging import assembly_yield
        return assembly_yield(*self.step_yields)


@dataclass(frozen=True)
class Recipe:
    """A full line recipe: the Czochralski boule the substrate is grown from + one slice per step.

    The substrate doping is **derived**, not stored: :attr:`channel_N_A` is the Scheil slice of the
    grown :attr:`boule` at the wafer's ``slice_z`` — read by both the junction analysis (S/D into the
    channel) and the device (the channel doping that sets ``V_t``). At the default Czochralski knobs
    the seed slice is exactly ``1e17``, matching :mod:`chip.demo_device`'s ``CHANNEL_N_A`` (the seam).
    """

    purification: PurificationKnobs = field(default_factory=PurificationKnobs)
    czochralski: CzochralskiKnobs = field(default_factory=CzochralskiKnobs)
    wafer_prep: WaferPrepKnobs = field(default_factory=WaferPrepKnobs)
    diffusion: DiffusionKnobs = field(default_factory=DiffusionKnobs)
    oxidation: OxidationKnobs = field(default_factory=OxidationKnobs)
    litho: LithoKnobs = field(default_factory=LithoKnobs)
    etch_deposition: EtchDepositionKnobs = field(default_factory=EtchDepositionKnobs)
    device: DeviceKnobs = field(default_factory=DeviceKnobs)
    packaging: PackagingKnobs = field(default_factory=PackagingKnobs)

    @property
    def boule(self) -> Boule:
        """The :class:`chip.czochralski.Boule` grown from the Czochralski knobs (cited Scheil profile)."""
        cz = self.czochralski
        return Boule(dopant=cz.dopant, N_seed=cz.N_seed,
                     length_mm=cz.length_mm, diameter_mm=cz.diameter_mm)

    @property
    def contamination(self) -> Contamination:
        """The wafer's purified impurity vector — the feedstock grade zone-refined ``zone_passes`` times.

        A clean grade (the default) → a clean (all-zero) vector for any number of passes (the seam). The
        device consumes it as: ``Na`` → gate-oxide ``Q_ox`` (the headline ``V_t`` shift) and ``B``/``P``
        → :attr:`effective_channel_N_A` (net doping); the metals ride along (the named G4b gap).
        """
        return zone_refine(FEEDSTOCK_GRADES[self.purification.grade], self.purification.zone_passes)

    @property
    def channel_N_A(self) -> float:
        """The boule's substrate doping (cm⁻³) at this wafer's slice — exactly ``N_seed`` at ``slice_z=0``.

        The *intentional* Scheil doping (no contamination). The device sees :attr:`effective_channel_N_A`.
        """
        return float(self.boule.axial_doping(self.czochralski.slice_z))

    @property
    def effective_channel_N_A(self) -> float:
        """The channel doping the device sees: the boule slice **plus** the residual-dopant net shift (cm⁻³).

        ``channel_N_A + contamination.net_doping_shift`` (residual ``B`` raises it, ``P`` lowers it). At a
        clean grade the shift is 0, so this equals :attr:`channel_N_A` (and is exactly ``N_seed`` at the
        seed slice — the seam). Fed to *both* the S/D junction (``N_background``) and the device ``V_t``,
        so the two stay coherent.
        """
        return self.channel_N_A + self.contamination.net_doping_shift

    @property
    def substrate_resistivity_ohm_cm(self) -> float:
        """The substrate resistivity (Ω·cm) of the wafer's **effective** doping (Masetti ``μ(N)``).

        Computed from :attr:`effective_channel_N_A` (the boule slice + the residual-dopant net shift),
        **not** the boule slice alone — so a wafer's reported resistivity is coherent with the doping
        the device actually sees (else a dirty feed would carry two silently-disagreeing doping-derived
        fields). At a clean grade the shift is 0, so this is exactly the boule-slice resistivity (the
        G2 seam — ``demo_boule`` byte-for-byte). The residual shift is small vs an intentional ~1e17
        substrate, so the net carrier type stays p (boron ``μ(N)`` valid)."""
        from chip.czochralski import resistivity
        return float(resistivity(self.effective_channel_N_A, self.czochralski.dopant))


# The default recipe IS chip.demo_device's coherent n-MOSFET recipe (the seam anchor): the seed-end
# boule slice (slice_z=0, N_seed=1e17) reproduces CHANNEL_N_A = 1e17 exactly.
DEFAULT_RECIPE = Recipe()
