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
from chip.diffusion_dopant import ThermalProgram
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
    zone_passes: float = 1             # zone-refining passes/effort (more = cleaner feed; the costly rework
    #                                    knob). CONTINUOUS — a fractional pass is a partial refining effort
    #                                    (front_purity's k^n is smooth in n), so the residual Na can be dialed
    #                                    into the marginal band instead of leaping ~1/k per integer pass.


@dataclass(frozen=True)
class CzochralskiKnobs:
    """Czochralski boule knobs → :class:`chip.czochralski.Boule` — the substrate is **grown**, not set.

    ``dopant`` the p-type substrate species; ``N_seed`` (cm⁻³) the seed-end (``z=0``) doping — equal
    to ``demo_device``'s ``CHANNEL_N_A`` at the default, so the seed slice reproduces the demo
    bit-for-bit (the seam). ``slice_z`` ∈ ``[0, 1)`` is the axial fraction-solidified for **this**
    wafer (0 = seed end); :func:`fab_game.pipeline.run_batch` sweeps it down the boule.
    ``length_mm``/``diameter_mm`` are narrative geometry.

    ``pull_rate_mm_min`` (CG-1) turns the **pull rate** into a live knob: a thin diffusion boundary
    layer at the freezing interface makes the *effective* segregation coefficient rise toward 1 with
    pull rate (Burton–Prim–Slichter, :func:`chip.czochralski.effective_segregation_coefficient`), so
    **pulling faster flattens the Scheil drift** down the boule. It defaults to **``None``** — the
    well-mixed Scheil idealization (``k_eff = k₀``, the cited Trumbore value) — so the seam *and* the
    G2/G7 banked boule demos are byte-for-byte unchanged (CG-1 is opt-in; the boule's ``k`` is the
    equilibrium ``k₀`` until a pull rate is set). Honest magnitude: for boron (``k₀=0.80``) realistic
    Si pull (~0.5–2 mm/min) only *modestly* flattens the drift.

    ``thermal_gradient_K_per_mm`` (CG-2) supplies the interface thermal gradient ``G`` that turns pull
    rate's one-sided CG-1 benefit into a real trade-off: the **Voronkov ratio** ``ξ = V/G`` against the
    critical ``ξ_t`` (:func:`chip.czochralski.voronkov_ratio`) decides the grown-in defect regime, and
    a vacancy-rich (``ξ > ξ_t``) growth seeds COP/void killer defects — :attr:`grown_in_defect_density`
    (cm⁻²), which **adds to the wafer-prep killer-defect density** (so pulling faster, or running a
    cooler hot zone, costs yield through the G3 defect map). It defaults to **``None``** — CG-2 off, no
    grown-in defects → the seam (and the G1–G7 banked demos byte-for-byte unchanged). ``G`` is a
    **flagged house knob** (or, deferred, the shipped Robin heat mode); only the criterion + ``ξ_t``
    are cited, the void→density coefficient is house. Setting ``G`` **requires** a ``pull_rate`` (you
    cannot form ``V/G`` without ``V``).

    ``melt_gradient_K_per_mm`` (CG-3) **derives** that interface gradient instead of setting it
    directly: at the moving freezing front the latent heat couples the crystal-side gradient to the
    pull rate via the **Stefan balance** ``G_s = (L·ρ·V + k_l·G_l)/k_s``
    (:func:`chip.czochralski.stefan_interface_gradient`), so you dial the *melt-side* gradient ``G_l``
    (the hot-zone superheat) and ``V``, and ``G_s`` follows. THE consequence: ``ξ = V/G_s`` **saturates**
    at ``ξ_max = k_s/(L·ρ) ≈ 0.3`` — latent heat caps the vacancy supersaturation (correcting CG-2's
    unbounded fixed-``G`` picture). It defaults to **``None``** (CG-3 off → the seam). Provide **either**
    ``thermal_gradient_K_per_mm`` (CG-2 direct ``G``) **or** ``melt_gradient_K_per_mm`` (CG-3 Stefan-
    derived), not both. ``G_l`` is still a house number (CG-3 adds the coupling + cap, not first
    principles).

    ``radial_gradient_boost`` (A2, the **OSF ring** — CG-2 made *radial*) turns the single interface
    gradient into a **radial profile** ``G(r) = G_center·(1 + boost·r²)``
    (:func:`chip.czochralski.radial_thermal_gradient`), reinterpreting ``thermal_gradient_K_per_mm`` as
    the **centre** gradient ``G_center`` (so it requires the direct CG-2 ``G`` + a pull rate, and is
    **incompatible** with CG-3's ``melt_gradient_K_per_mm`` — the two-``G`` guard). With ``G`` rising
    toward the edge, ``ξ(r) = V/G(r)`` **falls** outward, so the centre can be **vacancy**-rich (COP
    voids) and the edge **interstitial**-rich, with the **OSF ring** at ``ξ(r) = ξ_t``
    (:attr:`osf_ring_radius`). The killer (vacancy) density is then **per die** keyed on ``radius_frac``
    (:meth:`grown_in_defect_density_at`): the pipeline scatters a **COP-degraded vacancy core + a clean
    rim** — the edge-vs-centre yield **non-uniformity**. THE honest finding: the void density is monotone
    in ξ, so it peaks at the centre (a *modest* core kill rate — the same capped coefficient as CG-2) and
    is **zero at the ring** — the ring is the *boundary* where the kills **stop**, not a band of kills. It defaults to **``None``** (uniform ``G`` ⇒ **CG-2 byte-for-byte**,
    the seam). The ``G(r)`` profile, the ``boost``, and the ring's on-wafer existence are flagged house
    numbers; only the ring *location* + the topology signs are tight.

    **A1** completes CG-2's symmetry on the other side of ``ξ_t``: a too-slow pull / over-steep ``G``
    (``ξ < ξ_t``) freezes in **interstitial-rich** silicon → grown-in **dislocations**
    (:attr:`interstitial_dislocation_density`), which are recombination centres → they raise the junction
    **leakage** (the G4b :mod:`chip.lifetime` channel, ``1/τ += K·ρ_disl``), **not** the yield map. So
    too-fast costs yield (COP voids) and too-slow costs leakage (dislocations), with the defect-free
    optimum **at** ``ξ_t``. There is **no new knob** — A1 reads the *existing* ``(V, G)``: it switches on
    automatically when a CG-2/CG-3 recipe lands on the interstitial side, and is ``0`` (the seam) for any
    vacancy/boundary growth or with CG-2 off. With the A2 radial profile on it is **per die**
    (:meth:`interstitial_dislocation_density_at`) — the dislocation-leaky **rim** complementing the
    void-killed core (the OSF ring is the one annulus clean of both). Honest magnitude: realistic CZ is
    vacancy-side, so the dislocation cost is a **corner** (its value is that slow pull is no longer free).

    ``oxygen_conc_cm3`` (C1) + ``thermal_donor_anneal_min`` (C1) add the **electrical** crystal-growth
    deepening: a CZ boule dissolves interstitial oxygen ``[O_i]`` from the quartz crucible, and a
    ~450 °C **donor anneal** nucleates **thermal donors** (n-type) that **compensate** the p-substrate —
    so the device sees a *reduced* net ``N_A`` → a lower ``V_t`` and higher resistivity (the same
    net-doping chain as G4a's residual dopant). ``oxygen_conc_cm3`` is the incorporated ``[O_i]`` (cm⁻³,
    a flagged input *level* — :data:`chip.czochralski.OXYGEN_BANDS`; the incorporation-vs-pull model is a
    named deferred edge), and ``thermal_donor_anneal_min`` the ~450 °C anneal time. The donor density is
    :func:`chip.czochralski.thermal_donor_density` (the cited Kaiser–Frisch–Reiss fourth-power initial
    rate; saturating form + magnitudes flagged). BOTH default to the seam — ``oxygen_conc_cm3 = None``
    (no oxygen) **or** ``thermal_donor_anneal_min = 0`` (no anneal) → ``N_TD = 0`` exactly → the
    substrate is byte-for-byte the pre-C1 boule slice (donors form at the anneal, not during growth).
    Subtracted from the net doping by :attr:`Recipe.effective_channel_N_A`; over-compensation
    (``N_TD ≥ N_A`` → type inversion) is a guarded named edge (it raises — keep the oxygen/anneal in the
    p-type range).

    ``forming_gas_anneal_min`` (S4) is the **dual-use** counterpart: the same incorporated ``[O_i]`` that
    costs ``V_t`` (donors) also **getters** the deep-level metals (:attr:`internal_gettering_efficiency`
    → :func:`chip.purification.getter_metals`, the leakage channel), so more oxygen is *good for the
    diode, bad for the threshold*. To keep the donor cost non-skippable (you cannot getter for free), the
    universal final ~450 °C **forming-gas/sinter** — which sits in the thermal-donor window — adds its
    time to the donor budget: the effective donor anneal is ``thermal_donor_anneal_min +
    forming_gas_anneal_min``. It defaults to ``0`` so every pre-S4 recipe is byte-for-byte (the C1 seam
    untouched); the gettering wiring sets it (~30 min) when oxygen is engaged. Gettering itself touches
    **Fe/Cu only** — never the Na→``Q_ox``→``V_t`` chain — so the two oxygen channels stay orthogonal.
    """

    dopant: str = "B"                  # p-type boron substrate
    N_seed: float = 1.0e17             # cm⁻³ seed-end doping = demo_device CHANNEL_N_A (the seam)
    slice_z: float = 0.0               # axial fraction solidified for THIS wafer (0 = seed end)
    pull_rate_mm_min: float | None = None  # CG-1 pull rate; None = well-mixed k_eff=k₀ (the seam)
    thermal_gradient_K_per_mm: float | None = None  # CG-2 direct interface gradient G; None = off (seam)
    melt_gradient_K_per_mm: float | None = None     # CG-3 melt-side G_l → Stefan-derived G_s; None = off (seam)
    radial_gradient_boost: float | None = None      # A2 OSF ring: G(r)=G_center·(1+boost·r²); None = uniform (CG-2 seam)
    oxygen_conc_cm3: float | None = None   # C1 incorporated [O_i] (cm⁻³); None = oxygen-free (the seam)
    thermal_donor_anneal_min: float = 0.0  # C1 ~450 °C donor-anneal time (min); 0 = no anneal (the seam)
    forming_gas_anneal_min: float = 0.0    # S4 universal final ~450 °C sinter (min); 0 = off (C1 seam, by default)
    length_mm: float = 200.0           # boule length (narrative geometry only)
    diameter_mm: float = 200.0         # boule diameter (narrative geometry only)

    @property
    def k_eff(self) -> float | None:
        """The effective segregation coefficient for the boule, or ``None`` (use the equilibrium ``k₀``).

        ``None`` when ``pull_rate_mm_min`` is ``None`` (the well-mixed idealization → :class:`Boule`
        falls back to the cited Trumbore ``k₀`` — the seam). Otherwise the Burton–Prim–Slichter
        ``k_eff(Δ)`` at this pull rate (``Δ`` from the flagged boundary-layer/diffusivity), which the
        boule uses in place of ``k₀`` to flatten the axial profile.
        """
        if self.pull_rate_mm_min is None:
            return None
        from chip.czochralski import (
            effective_segregation_coefficient,
            normalized_growth_velocity,
            segregation_coefficient,
        )
        k0 = segregation_coefficient(self.dopant)
        return effective_segregation_coefficient(k0, normalized_growth_velocity(self.pull_rate_mm_min))

    @property
    def interface_gradient_K_per_mm(self) -> float | None:
        """The crystal-side interface gradient ``G`` (K/mm) CG-2's Voronkov ratio consumes, or ``None`` (off).

        Resolution: ``melt_gradient_K_per_mm`` set → **CG-3** Stefan-derived ``G_s =
        stefan_interface_gradient(V, G_l)`` (needs a pull rate — the front velocity ``V``); elif
        ``thermal_gradient_K_per_mm`` set → that **CG-2** direct house value; else ``None`` (both off →
        the seam). Setting **both** is a misconfiguration (two competing ``G`` sources) → raises.
        """
        if self.melt_gradient_K_per_mm is not None and self.thermal_gradient_K_per_mm is not None:
            raise ValueError(
                "set either thermal_gradient_K_per_mm (CG-2 direct G) OR melt_gradient_K_per_mm "
                "(CG-3 Stefan-derived G), not both")
        if self.melt_gradient_K_per_mm is not None:
            if self.pull_rate_mm_min is None:
                raise ValueError(
                    "melt_gradient_K_per_mm (CG-3) requires a pull_rate_mm_min — the Stefan balance "
                    "needs the front velocity V")
            from chip.czochralski import stefan_interface_gradient
            return stefan_interface_gradient(self.pull_rate_mm_min, self.melt_gradient_K_per_mm)
        return self.thermal_gradient_K_per_mm

    @property
    def voronkov_ratio(self) -> float | None:
        """The Voronkov ratio ``ξ = V/G`` (mm²/(K·min)), or ``None`` when no interface gradient is set.

        ``None`` when neither gradient knob is set (CG-2/CG-3 off → the seam). ``G`` is the resolved
        :attr:`interface_gradient_K_per_mm` (CG-2 direct, or CG-3 Stefan-derived). Raises if a gradient
        is set without a ``pull_rate_mm_min`` (no ``V`` → no ``V/G``).
        """
        g = self.interface_gradient_K_per_mm
        if g is None:
            return None
        if self.pull_rate_mm_min is None:
            raise ValueError(
                "an interface gradient requires a pull_rate_mm_min — cannot form the Voronkov "
                "ratio V/G without a pull rate V")
        from chip.czochralski import voronkov_ratio
        return voronkov_ratio(self.pull_rate_mm_min, g)

    @property
    def grown_in_defect_regime(self) -> str | None:
        """The CG-2 grown-in defect regime (``"vacancy"``/``"interstitial"``/``"osf"``), or ``None`` (off)."""
        ratio = self.voronkov_ratio
        if ratio is None:
            return None
        from chip.czochralski import grown_in_defect_regime
        return grown_in_defect_regime(ratio)

    @property
    def grown_in_defect_density(self) -> float:
        """The CG-2 grown-in COP/void killer-defect density (cm⁻²) — **0.0 when CG-2 is off (the seam)**.

        ``0.0`` when ``thermal_gradient_K_per_mm`` is ``None`` (CG-2 not engaged) **and** for any
        interstitial/boundary growth (``ξ ≤ ξ_t``). Otherwise the flagged vacancy-side void density at
        this ``(V, G)`` — added to the wafer-prep killer density (:attr:`Recipe.effective_defect_density`)
        so the G3 defect map scatters the extra COPs. Pulling faster / a cooler hot zone raises it.

        With the A2 **radial** profile on (``radial_gradient_boost`` set), this scalar is the **centre**
        value (it reads ``G = thermal_gradient_K_per_mm = G_center``, the lowest ``G`` → highest ξ → the
        *worst* density). The radial pipeline branch does **not** use it (nor the scalar
        :attr:`Recipe.effective_defect_density`); it scatters the per-die
        :meth:`grown_in_defect_density_at` instead. The scalar stays defined as the centre/worst case.
        """
        ratio = self.voronkov_ratio
        if ratio is None:
            return 0.0
        from chip.czochralski import void_defect_density
        return void_defect_density(ratio)

    # --- A2: the OSF ring — CG-2 made radial (G(r) keyed on each die's radius_frac) --- #
    @property
    def is_osf_radial(self) -> bool:
        """True when the OSF-ring radial gradient is engaged (``radial_gradient_boost`` is set)."""
        return self.radial_gradient_boost is not None

    def _center_gradient_K_per_mm(self) -> float:
        """The centre gradient ``G_center`` the radial profile builds on — the direct CG-2 ``G``.

        Raises if misconfigured: the radial profile reinterprets ``thermal_gradient_K_per_mm`` as
        ``G_center`` (so it must be set) and is **incompatible** with CG-3's ``melt_gradient_K_per_mm``
        (a Stefan-derived ``G`` is a single number, not a radial profile — the two-``G`` guard).
        """
        if self.melt_gradient_K_per_mm is not None:
            raise ValueError(
                "radial_gradient_boost (the A2 OSF ring) is incompatible with melt_gradient_K_per_mm "
                "(CG-3 Stefan-derived G) — the radial profile reinterprets the direct "
                "thermal_gradient_K_per_mm as the centre gradient G_center, not both")
        if self.thermal_gradient_K_per_mm is None:
            raise ValueError(
                "radial_gradient_boost (the A2 OSF ring) requires thermal_gradient_K_per_mm — it is the "
                "centre interface gradient G_center the radial profile G(r)=G_center·(1+boost·r²) builds on")
        if self.pull_rate_mm_min is None:
            raise ValueError(
                "the A2 OSF radial gradient requires a pull_rate_mm_min — no V → no ξ(r)=V/G(r)")
        return self.thermal_gradient_K_per_mm

    def grown_in_defect_density_at(self, radius_frac: float) -> float:
        """Per-die grown-in COP/void killer density (cm⁻²) at this die's ``radius_frac`` — the OSF field.

        When ``radial_gradient_boost`` is ``None`` → the **uniform** :attr:`grown_in_defect_density`
        (radius-independent — the CG-2 seam). When set → the vacancy-side
        :func:`chip.czochralski.void_defect_density` at the radial ``G(r)``: the **vacancy core** (small
        ``r``, low ``G``, high ξ) catches COPs, and the **interstitial rim** (large ``r``) is clean
        (``0.0`` at and beyond the ring). The pipeline adds the (uniform) wafer-prep particle level and
        scatters the sum per die through the same G3 Poisson map.
        """
        if self.radial_gradient_boost is None:
            return self.grown_in_defect_density          # uniform — CG-2 (radius-independent; the seam)
        from chip.czochralski import (
            radial_thermal_gradient,
            void_defect_density,
            voronkov_ratio,
        )
        g_r = radial_thermal_gradient(
            radius_frac, self._center_gradient_K_per_mm(), boost=self.radial_gradient_boost)
        return void_defect_density(voronkov_ratio(self.pull_rate_mm_min, g_r))

    @property
    def osf_ring_radius(self) -> float | None:
        """The normalized radius of the OSF (V/I) ring, or ``None`` (radial off **or** no on-wafer boundary).

        ``None`` when ``radial_gradient_boost`` is unset (the seam) or when the boundary is off-wafer
        (all-vacancy / all-interstitial). The two off-wafer cases are told apart by
        :attr:`osf_zone_regimes`, not by the ``None`` (advisor: don't conflate no-kills with all-kills).
        """
        if self.radial_gradient_boost is None:
            return None
        from chip.czochralski import osf_ring_radius
        return osf_ring_radius(
            self.pull_rate_mm_min, self._center_gradient_K_per_mm(), boost=self.radial_gradient_boost)

    @property
    def osf_zone_regimes(self) -> tuple[str, str] | None:
        """``(centre_regime, edge_regime)`` for the radial wafer, or ``None`` (radial off).

        The topology-sign leg: a ring on-wafer ⇒ ``("vacancy", "interstitial")``. Also disambiguates the
        off-wafer cases — ``("vacancy", "vacancy")`` is all-vacancy, ``("interstitial", "interstitial")``
        all-interstitial — which the bare :attr:`osf_ring_radius` ``None`` cannot.
        """
        if self.radial_gradient_boost is None:
            return None
        from chip.czochralski import radial_defect_regime
        g_center, v, boost = self._center_gradient_K_per_mm(), self.pull_rate_mm_min, self.radial_gradient_boost
        return (radial_defect_regime(0.0, v, g_center, boost),
                radial_defect_regime(1.0, v, g_center, boost))

    # --- A1: the interstitial side — grown-in dislocations → junction leakage (the COP mirror) --- #
    @property
    def interstitial_dislocation_density(self) -> float:
        """The A1 grown-in interstitial-side dislocation density (cm⁻²) — **0.0 when CG-2 off or vacancy**.

        The interstitial mirror of :attr:`grown_in_defect_density` (the *uniform* value): ``0.0`` when no
        interface gradient is set (CG-2/CG-3 off) and for any vacancy/boundary growth (``ξ ≥ ξ_t``);
        otherwise the flagged :func:`chip.czochralski.dislocation_defect_density` at this ``(V, G)``. It
        feeds the junction-**leakage** channel (:func:`chip.lifetime.device_leakage`, ``1/τ += K·ρ_disl``),
        **not** the Poisson yield map — voids → yield, dislocations → leakage are distinct device outputs.
        With the A2 radial profile on, the dislocations live on the **rim** (large ``r``), not at the
        centre this scalar's ``G = G_center`` reads — so there use the per-die
        :meth:`interstitial_dislocation_density_at` (this scalar reads the vacancy core → ``0.0``).
        """
        ratio = self.voronkov_ratio
        if ratio is None:
            return 0.0
        from chip.czochralski import dislocation_defect_density
        return dislocation_defect_density(ratio)

    def interstitial_dislocation_density_at(self, radius_frac: float) -> float:
        """Per-die A1 grown-in dislocation density (cm⁻²) at this die's ``radius_frac`` — the interstitial rim.

        The leakage-channel companion to :meth:`grown_in_defect_density_at` (the void/yield core). When
        ``radial_gradient_boost`` is ``None`` → the **uniform** :attr:`interstitial_dislocation_density`
        (radius-independent — a whole-wafer interstitial growth gives every die the same density). When
        set → the interstitial-side :func:`chip.czochralski.dislocation_defect_density` at the radial
        ``G(r)``: the **vacancy core** (small ``r``, high ξ) is dislocation-free (``0.0``) and the
        **interstitial rim** (large ``r``, low ξ, past the ring) carries the dislocations — the exact
        complement of the void core, so the OSF ring is the one annulus clean of *both*. Fed to
        :func:`chip.lifetime.device_leakage` per die (the rim's leakage), **not** the Poisson yield map.
        """
        if self.radial_gradient_boost is None:
            return self.interstitial_dislocation_density
        from chip.czochralski import (
            dislocation_defect_density,
            radial_thermal_gradient,
            voronkov_ratio,
        )
        g_r = radial_thermal_gradient(
            radius_frac, self._center_gradient_K_per_mm(), boost=self.radial_gradient_boost)
        return dislocation_defect_density(voronkov_ratio(self.pull_rate_mm_min, g_r))

    @property
    def thermal_donor_density(self) -> float:
        """The C1 active thermal-donor density (cm⁻³) compensating the substrate — **0.0 off (the seam)**.

        ``0.0`` when ``oxygen_conc_cm3`` is ``None`` (no incorporated oxygen) **or** the **effective
        donor anneal** ``thermal_donor_anneal_min + forming_gas_anneal_min`` is ``0`` (no ~450 °C
        excursion) — donors form at the anneal, not during growth, so a boule with oxygen but no anneal
        of either kind is the unchanged substrate (both default to ``0`` → the C1 seam byte-for-byte).
        Otherwise the cited-fourth-power / flagged-saturation :func:`chip.czochralski.thermal_donor_density`
        at this ``([O_i], t_eff)`` — the S4 forming-gas/sinter adds its time so engaging oxygen carries an
        unavoidable donor budget — subtracted from the net doping by :attr:`Recipe.effective_channel_N_A`.
        """
        if self.oxygen_conc_cm3 is None:
            return 0.0
        from chip.czochralski import thermal_donor_density
        return thermal_donor_density(
            self.oxygen_conc_cm3, self.thermal_donor_anneal_min + self.forming_gas_anneal_min)

    @property
    def internal_gettering_efficiency(self) -> float:
        """The S4 oxygen-precipitate internal-gettering efficiency — fraction of Fe/Cu removed, **0.0 off**.

        ``0.0`` when ``oxygen_conc_cm3`` is ``None`` (no oxygen) **or** the ``[O_i]`` is below the cited
        precipitation threshold (~12 ppma ≈ 6e17 cm⁻³) — the wafer does not precipitate enough to getter
        (the seam: :func:`chip.purification.getter_metals` then leaves the Fe/Cu untouched → the G4b
        leakage is byte-for-byte). Otherwise the flagged-magnitude
        :func:`chip.czochralski.internal_gettering_efficiency` at this ``[O_i]`` — consumed in the device
        step by gettering the wafer's deep-level metals before the leakage read (Fe/Cu only, never
        ``Na``/``V_t``). The dual-use mirror of :attr:`thermal_donor_density`.
        """
        if self.oxygen_conc_cm3 is None:
            return 0.0
        from chip.czochralski import internal_gettering_efficiency
        return internal_gettering_efficiency(self.oxygen_conc_cm3)


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
    """Source/drain two-step diffusion knobs → :func:`chip.diffusion_dopant.two_step`.

    ``drivein_program`` (E1, optional) swaps the isothermal drive-in for a **transient**
    spike/RTA anneal :class:`chip.diffusion_dopant.ThermalProgram` ``T(t)``. When set,
    ``T_drivein_C``/``t_drivein_min`` are **bypassed** — the program governs the schedule *and* the
    duration (``program.duration``). ``None`` (default) is the isothermal step, byte-for-byte
    unchanged (the seam). The spike's junction depth is set by the *budget* ``∫D(T(t))dt`` — for a
    fast ramp far less than the clock time would suggest (Arrhenius collapse near the peak), which
    is why RTA gives shallow junctions.

    ``sd_contact_squares`` (the diffusion-journey consumer) turns the S/D sheet resistance ``R_s``
    into a **device consequence**: the parasitic **source** series resistance is ``R_series = R_s·sd_contact_squares``
    (the contact-to-channel square count ``n_□ = L_access/W`` — a flagged layout-geometry number), which
    the device step feeds to :func:`chip.device.saturation_current` as source degeneration → a shallow,
    **under-diffused** junction (high ``R_s``) starves ``I_Dsat``. Without it the diffusion knobs move
    ``x_j``/``R_s`` but **nothing scored** (the device reads ``N_A``/``t_ox``/CD, never ``R_s``), so the
    dose is inert — this is the wire that makes the predep dose a real decision. It defaults to **``0.0``**
    → ideal contact, ``R_series = 0`` → the device call is byte-for-byte the ideal closed form (the seam,
    G1–G7 banked demos unchanged); the journey dials in the flagged house value (a wide ``W = 10 µm``
    device → ``n_□ ≈ 0.15``, so nominal ``R_series ≈ 12 Ω`` sits comfortably inside the ``I_Dsat`` window
    and an under-diffused predep walks it out). One-sided by construction: *more* dose only lowers ``R_s``
    (over-diffusion's harm is the short-channel tar pit the device model deliberately omits).
    """

    dopant: str = "P"                  # n⁺ phosphorus S/D into the p-type channel
    T_predep_C: float = 950.0          # °C
    t_predep_min: float = 10.0         # min
    T_drivein_C: float = 950.0         # °C
    t_drivein_min: float = 8.0         # min → shallow x_j ≈ 0.10 µm
    drivein_program: "ThermalProgram | None" = None  # E1 spike/RTA T(t); None = isothermal (the seam)
    sd_contact_squares: float = 0.0    # S/D series-R geometry n_□ = R_series/R_s; 0 = ideal contact (the seam)
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

    ``under_etch_frac`` (D1) is the **mirror** of ``over_etch_frac``: an *incomplete* clear that stops
    before the film is fully etched, leaving **residual film** (``residual = UE·film_thickness``) in the
    gaps that **bridges** adjacent gate lines into a functional **short** once it exceeds the (flagged)
    bridge threshold (:func:`chip.etch_deposition.under_etch`) — a second functional kill, parallel to
    the deposition void (an *open*; this is a *short*). Over- and under-etch are **mutually exclusive**
    (one etch either runs past, or stops short of, endpoint), so setting **both** ``over_etch_frac`` and
    ``under_etch_frac`` non-zero raises (a recipe misconfiguration, like CzochralskiKnobs' two-``G``
    guard).

    Defaults are the **idealized seam baseline** — ``anisotropy = 1`` (zero bias → the etched CD equals
    the printed CD bit-for-bit), ``conformality = 1`` (never voids), and ``under_etch_frac = 0`` (a full
    clear → no residual, no bridge) — so the seam *and* the G1–G4 banked demos are byte-for-byte
    unchanged (the etch step is the identity at the default recipe). The G5 demo dials a realistic
    ``anisotropy < 1`` + over-etch (CD collapse) and a poor PVD coverage (the void kill); the D1 demo
    dials an ``under_etch_frac`` (the bridging short).
    """

    film_thickness_nm: float = 150.0   # gate film etched through (sets the standing gate height)
    anisotropy: float = 1.0            # 1 = perfectly anisotropic (the seam); <1 → etch bias → CD shrinks
    over_etch_frac: float = 0.0        # over-etch past endpoint (0 = none; deepens etch → more undercut)
    under_etch_frac: float = 0.0       # D1 incomplete clear (0 = full clear, the seam; >0 → residual → bridge)
    selectivity: float = 20.0          # etch selectivity to the underlayer (over-etch underlayer loss)
    conformality: float = 1.0          # deposition step coverage (1 = conformal CVD seam; <1 voids high-AR gaps)

    def __post_init__(self) -> None:
        # Over- and under-etch are mutually exclusive (one etch either over- or under-shoots endpoint).
        if self.over_etch_frac > 0.0 and self.under_etch_frac > 0.0:
            raise ValueError(
                "set either over_etch_frac (etch past endpoint → CD undercut) OR under_etch_frac "
                "(incomplete clear → residual bridge), not both — one etch cannot do both")


@dataclass(frozen=True)
class DeviceKnobs:
    """Device-read knobs → :func:`chip.device.threshold_voltage` / :func:`chip.device.saturation_current`.

    ``vt_adjust_dose`` (§5, the ion-implant consumer) is the areal dose (cm⁻²) of a shallow **V_t-adjust
    implant** — the honest, dose-controlled source of the threshold adjust the device model previously
    *faked* with a uniform substrate offset. It shifts ``V_t`` by ``±q·Q/C_ox`` (:func:`chip.device.vt_adjust_shift`)
    via :func:`chip.device.threshold_voltage`: ``vt_adjust_kind = "p"`` (acceptor, e.g. boron) **raises**
    ``V_t``, ``"n"`` (donor) **lowers** it. The dose is physically that of a buried
    :class:`chip.diffusion_dopant.Implant` (the observable a surface-peaked predep cannot make — see
    :mod:`chip.demo_implant`); the *shift* needs only dose+type (the shallow-sheet approximation, peak-depth
    independent — the deep/retrograde effective-``N_A`` case is a deferred slice). Defaults to ``0.0`` /
    ``None`` → **no adjust implant**, byte-for-byte the prior ``V_t`` (the seam; the G1–G7 banked demos and
    the journey are untouched), and the ``vt_adjust`` record key is added only when engaged.

    ``contact_scheme`` (F2, the silicide/contact-resistance model) upgrades the source series resistance
    from the access-only ``R_series = die.R_s · sd_contact_squares`` to the **two-term** access + TLM
    contact model (:func:`chip.contact_resistance.series_resistance`): ``"direct-Al"`` adds a high-``ρ_c``
    contact term on the diffused sheet, ``"salicide"`` shunts the sheet with a low-resistivity TiSi₂ film
    so access collapses while the contact term lingers (the bottleneck flips access→contact). It feeds the
    *same* ``R_series_ohm`` source-degeneration seam :func:`chip.device.saturation_current` already
    consumes — ``device.py`` is untouched. Defaults to ``None`` → the access-only value **byte-for-byte**
    (the seam; the G1–G7 banked demos and the journey are unchanged, since ``die.R_s · sd_contact_squares``
    is exactly :func:`chip.contact_resistance.access_resistance`).
    """

    gate: str = "n+poly"               # n⁺-poly gate (φ_gate = +0.55 V)
    width_um: float = 10.0             # device width W for the I_Dsat readout
    overdrive_V: float = 1.0           # V_GS − V_t for I_Dsat
    vt_adjust_dose: float = 0.0        # §5 V_t-adjust implant dose (cm⁻²); 0 = no adjust implant (the seam)
    vt_adjust_kind: str | None = None  # "p" acceptor (raises V_t) | "n" donor (lowers) | None
    contact_scheme: str | None = None  # F2 silicide/contact model ("direct-Al"|"salicide"); None = access-only (the seam)


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
        """The :class:`chip.czochralski.Boule` grown from the Czochralski knobs (cited Scheil profile).

        Uses the CG-1 Burton–Prim–Slichter ``k_eff`` when a ``pull_rate_mm_min`` is set (pulling faster
        flattens the axial drift); ``k=None`` otherwise → the boule defaults to the equilibrium Trumbore
        ``k₀`` (the well-mixed Scheil seam — the G2/G7 demos are byte-for-byte unchanged when CG-1 is off).
        """
        cz = self.czochralski
        return Boule(dopant=cz.dopant, N_seed=cz.N_seed, k=cz.k_eff,
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
    def effective_defect_density(self) -> float:
        """The total killer-defect density (cm⁻²) the wafer sees: wafer-prep particles **+** grown-in COPs.

        ``wafer_prep.defect_density`` (the line's particle level, G3) plus the CG-2
        :attr:`CzochralskiKnobs.grown_in_defect_density` (vacancy-rich growth's voids). Two Poisson
        killer-defect processes superpose into one Poisson process at the summed density — so the
        grown-in COPs scatter through the **same** cited G3 defect map. At the default (no thermal
        gradient set) the grown-in term is ``0.0``, so this equals ``wafer_prep.defect_density``
        **exactly** (``+ 0.0``) — the G3 seam, byte-for-byte.
        """
        return self.wafer_prep.defect_density + self.czochralski.grown_in_defect_density

    @property
    def channel_N_A(self) -> float:
        """The boule's substrate doping (cm⁻³) at this wafer's slice — exactly ``N_seed`` at ``slice_z=0``.

        The *intentional* Scheil doping (no contamination). The device sees :attr:`effective_channel_N_A`.
        """
        return float(self.boule.axial_doping(self.czochralski.slice_z))

    @property
    def effective_channel_N_A(self) -> float:
        """The channel doping the device sees: the boule slice, the residual-dopant shift, **less donors** (cm⁻³).

        ``channel_N_A + contamination.net_doping_shift − thermal_donor_density``: residual ``B`` raises it
        / ``P`` lowers it (G4a), and **C1 thermal donors** (n-type, from crucible oxygen + the ~450 °C
        anneal) **compensate** it down (:func:`chip.czochralski.net_doping_after_donors`, exact). At a
        clean grade *and* no oxygen/anneal both terms are 0, so this equals :attr:`channel_N_A` (exactly
        ``N_seed`` at the seed slice — the seam). Fed to *both* the S/D junction (``N_background``) and the
        device ``V_t``, so the two stay coherent. Over-compensation (``N_TD ≥ N_A`` → type inversion)
        raises (the guarded named edge — keep the oxygen/anneal in the p-type range).
        """
        from chip.czochralski import net_doping_after_donors
        net_of_residual = self.channel_N_A + self.contamination.net_doping_shift
        return net_doping_after_donors(net_of_residual, self.czochralski.thermal_donor_density)

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
