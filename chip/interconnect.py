"""BEOL interconnect RC delay — the chip speed the transistor does not set (F4, slice 1).

The **backward axis** (``docs/plans/beol-interconnect-f4.md``): chip delay is **two terms with no shared
variable**, and *no single scalar can move both*:

  * **Gate delay** ``τ_gate = C_load·V_dd / I_Dsat`` — the transistor's term (the CV/I metric).
    **Inversely ∝ ``I_Dsat``**, the number the whole existing chain already computes (CD → ``V_t`` →
    ``I_Dsat``, plus F2's ``R_series`` source degeneration).
  * **Wire delay** ``τ_wire = k·R_wire·C_wire``, ``R_wire = ρ·L/(W·H)``, ``C_wire = c_pul·L`` —
    the interconnect's term. **``∂τ_wire/∂I_Dsat = 0``**: it is blind to the transistor *entirely*.

``τ_total = τ_gate + τ_wire``. Past the **crossover** (``τ_wire > τ_gate``) **halving the gate delay less
than halves the chip delay** — the transistor stops setting speed. That is the discriminating observable
this module exists for, and it is the first output in the sim the transistor chain does not set. A scalar
"wires are slow" cannot produce it: the two terms must respond to *different* inputs.

The premise this falsifies is already in the tree, stated verbatim
-----------------------------------------------------------------
:class:`fab_game.spec.SpeedBin` bins parts by drive current as a speed proxy — "clock speed ∝ drive
current → ∝ ``I_Dsat``" — and :meth:`fab_game.spec.SpeedBins.assign` takes ``I_Dsat`` **directly**. That
premise is **era-appropriate and false**: it is the pre-1997 assumption, and it lives in the game layer as
a **house grading policy** (ADR 0005 §1 — binning is policy, not physics), which is exactly where an era
assumption belongs and exactly what a later era gets to overturn. The consumer (slice 2) re-bins on
``τ_total``; ``τ_wire`` is a **common-mode floor** on every die (it depends on the metal and the geometry,
never on that die's transistor), so past the crossover the across-wafer ``I_Dsat`` spread stops mapping to
a speed spread — **tightening CD control stops buying speed grades**.

Why the crossover is driven by R and not C (the cited invariance — the tight leg)
--------------------------------------------------------------------------------
``C`` per unit length is **~2 pF/cm for essentially any interconnect geometry**: a ~1 cm-diameter 50 Ω
coax is ~1.5 pF/cm and an **80 nm**-pitch on-chip line is ~2 pF/cm — *seven orders of magnitude of
geometry, the same* ``c_pul`` ("the capacitances per unit length of all electrical transmission or
interconnect lines are very similar, within factors of order unity"). This is **physics, not a lump**:
``C`` per length depends on **ratios** of dimensions, not absolute size, and on-chip the line-to-line
**coupling** capacitance rises as the area capacitance falls, holding the total roughly fixed.

So under scaling ``R ∝ 1/(W·H)`` **rises** while ``C ∝ L`` **sits still** ⇒ **the crossover is an R
story.** Two consequences this module is built around:

  * :func:`wire_capacitance` **must not read W or H** — it is the total (area + fringing + coupling) per
    length. An area-only parallel-plate ``C`` would omit coupling, understate ``C``, and *misplace the
    crossover* — fatal for the slice-3 demo whose whole point is "the crossover happened, ~250 nm".
  * **The scaling scenario is load-bearing.** Cited: *"if the interconnect length and interconnect pitch
    scale identically, the wire delay will remain constant with technology scaling."* So **local** wires
    (``L`` scales with pitch) ⇒ ``τ_wire`` ≈ flat; **global** wires (``L`` ~ chip-sized and *fixed* while
    the cross-section shrinks) ⇒ ``τ_wire`` **explodes**. **The crossover is a global-wire statement** —
    :data:`GLOBAL_WIRE_LENGTH_UM`, and any figure must say so or the crossover is an artifact.

The honesty ladder (per the F4 plan + the ``historical-modes.md`` triad)
-----------------------------------------------------------------------
* **Tight — the structural claim (the discriminator).** ``∂τ_wire/∂I_Dsat = 0`` exactly (``I_Dsat`` does
  not appear in the wire term) while ``τ_gate ∝ 1/I_Dsat`` — so the wire share rises monotonically as the
  transistor improves, for **any** geometry, metal, or house constant. This is the leg that survives every
  flagged magnitude below, and it is what the consumer asserts.
* **Tight — the cited ``c_pul`` invariance.** ``C`` is independent of ``W``/``H``; ``R`` is not. Hence the
  crossover exists and is an R story. Prefactor-free.
* **Tight — the prefactor-free era win.** :func:`wire_delay_ratio` (``ρ_a/ρ_b``) and
  :func:`crossover_width_ratio` (``√(ρ_a/ρ_b)``) contain **no house constant at all** — ``L``, ``c_pul``,
  ``V_dd``, ``C_load`` and the Elmore factor **cancel exactly**. This is the F3 ``leakage_decades_saved``
  discipline, and it is where the module's headline must live, because ``L`` is a lump (below).
* **The non-circular cross-check (unplanned, and the reason to keep ρ₀ cited rather than fitted).** The
  cited bulk resistivities — materials-handbook values, **never fitted to a delay curve** — *predict*
  IBM's independently reported **~40% resistance reduction** for the 1997 Al→Cu swap: ``ρ_Al/ρ_Cu`` =
  2.65/1.68 = 1.58 ⇒ **~37% less resistance** (and ~46% for a real Al–Cu alloy line at ρ ≈ 3.1). Same
  spirit as Irvin-vs-Masetti and F3's cited-(φ_B,m*)-predicts-the-2 Å-slope check.
* **Flagged — the magnitudes.** The wire length :data:`GLOBAL_WIRE_LENGTH_UM` (**nothing in the sim carries
  a wire length** — the analogue of F2's ``CONTACT_LENGTH_UM`` and B6's ``SPIKE_CONCENTRATION``; checked:
  B6's ``t_Al`` is a contact-metallization *thickness*, not a line length), the Elmore distributed-line
  factor :data:`ELMORE_FACTOR`, the supply :data:`V_DD_HOUSE`, and the aluminium ``ρ₀`` (handbook, and a
  real Al–Cu alloy line runs higher than pure Al). **Absolute picoseconds are therefore NOT a claim this
  module makes** — only ratios, shares, and the crossover's *shift* are.

Scope — this slice is BULK resistivity only (the S4 gate, stated so the omission is not silent)
-----------------------------------------------------------------------------------------------
``ρ_eff = ρ₀`` here, which is valid **only for wires much wider than the electron mean free path ``λ``**
(:meth:`Metal.bulk_regime_ok`) — precisely the Al→Cu era this slice serves (250 nm ≫ Cu's 39 nm). Below
``λ``, surface and grain-boundary scattering make ``ρ_eff ≈ ρ₀·(1 + C·λ/d)`` rise sharply, and the
material enters **only** through the product ``ρ₀λ`` — the cited screening figure of merit. **Ruthenium is
deliberately NOT in :data:`METALS`**: its bulk ``ρ₀`` is ~4× *higher* than copper's, so a bulk-only model
would rank it *last* — and "Ru is the worst wire metal" is the **sign error inverted**, the exact trap the
F4 plan exists to prevent. Ru arrives in slice 4 **with** the size-effect and barrier-fraction physics that
make its constants mean anything. ``λ`` is carried here **only as a validity guard** (an honesty device,
like F3's ladder cap) — slice 4 promotes it from a guard to a term.

Named scope edges (honest ceilings)
-----------------------------------
* **Repeater / buffer insertion — the big one.** Real chips break long wires with repeaters, which makes
  delay ∝ ``L`` and **not** ``L²``. Un-named, this model would silently claim wire delay is unfixable and
  **overstate the wall**; the ``L²`` growth here is the *un-repeated* wire (the F3 trap-limited-floor
  analogue — the mechanism that stops the extrapolation being real).
* **Low-κ ILD** — the C-side mirror of high-κ (F3 bought ``t_phys`` with κ; low-κ buys ``C_wire`` by
  *lowering* ε). Cited as real and arriving *with* Cu at 250 nm; a separate era knob, not modelled.
* **Electromigration** — Cu's *other* win over Al (and a real reason Al died): a **reliability** mechanism,
  the wrong currency for a delay observable (the same discipline that kept F3's gate leakage out of
  ``lifetime.py``).
* **No crosstalk, no inductance, no multi-level RC stack, no via resistance.** Single representative line.
* **CMP is NOT here** — ``future-steps.md`` gates F8 to unblock *after* F4. This slice's job is to give
  wire cross-section a consumer, not to model planarity.

Units — inherited from the consumed modules (no new currency)
-------------------------------------------------------------
Resistivity ``ρ₀`` in **µΩ·cm** and mean free path ``λ`` in **nm** (the materials-datasheet units, as F2
takes ``ρ_c`` in Ω·cm²); wire length/width/thickness in **µm** (the cross-module length currency);
capacitance per length in **pF/cm**; ``I_Dsat`` in **A** and ``C_load`` in **F** (the ``device.py``
currencies — plain scalars across the boundary, the F2/F3 loose-coupling discipline); delays in **s**
internally, with a ``_ps`` read at the surface.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

_UM_PER_CM = 1.0e4                     # µm per cm
_NM_PER_UM = 1.0e3                     # nm per µm

# --------------------------------------------------------------------------- #
# Cited constants + flagged house lumps (the honesty ladder — see the module docstring)
# --------------------------------------------------------------------------- #
# Total wire capacitance per unit length (pF/cm) — CITED, and TIGHT because of its INVARIANCE rather than
# its value: "the capacitances per unit length of all electrical transmission or interconnect lines are
# very similar, within factors of order unity" — a ~1 cm-diameter 50 Ω coax runs ~1.5 pF/cm while an
# 80 nm-pitch on-chip line runs ~2 pF/cm (≡ 200 aF/µm). Seven orders of magnitude of geometry, one c_pul.
# This is the TOTAL (area + fringing + line-to-line coupling), NOT an area-only parallel-plate value: on
# chip the coupling term rises as the area term falls, which is *why* the total barely moves under
# scaling. Using an area-only C would understate C and misplace the crossover.
C_PUL_PF_CM = 2.0                      # CITED — total wire capacitance per unit length (pF/cm)

# Elmore distributed-RC delay factor (dimensionless) — FLAGGED. A distributed RC line's 50% delay is
# ~0.38·RC (vs 0.69·RC for a lumped RC); the exact coefficient depends on the driver/load convention.
# It CANCELS in every ratio this module headlines, which is why it is allowed to be a house number.
ELMORE_FACTOR = 0.38                   # FLAGGED — distributed-line delay coefficient

# Representative GLOBAL wire length (µm) — FLAGGED, and the module's dominant lump. NOTHING in the sim
# carries a wire length (the analogue of F2's CONTACT_LENGTH_UM / B6's SPIKE_CONCENTRATION), so a
# representative chip-crossing line is a house choice: 1 mm. It is a *global* wire — fixed length while
# the cross-section scales — because that is the ONLY scenario in which a crossover exists at all (a
# local wire whose length scales with the pitch has a flat τ_wire; cited). τ_wire ∝ L², so absolute
# delays scale hard with this number: only ratios and the crossover's SHIFT are claims here.
GLOBAL_WIRE_LENGTH_UM = 1000.0         # FLAGGED — representative chip-crossing (global) wire length (µm)

# Supply voltage (V) — FLAGGED house lump. ~3.3 V is period-appropriate for the mid-1990s crossover era.
# Cancels in the τ_wire/τ_gate ratio's metal comparison and in every crossover ratio.
V_DD_HOUSE = 3.3                       # FLAGGED — house supply voltage (V)


# --------------------------------------------------------------------------- #
# 1. The metal registry — bulk ρ₀ (the era's currency) + λ (carried ONLY as a validity guard at S1)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Metal:
    """An interconnect metal: bulk resistivity ``ρ₀`` (µΩ·cm) and electron mean free path ``λ`` (nm).

    ``rho0_uohm_cm`` is what sets ``R_wire`` in this slice (``ρ_eff = ρ₀``, the wide-wire limit).
    ``mfp_nm`` is **not used in the resistance model here** — it is carried as the **validity guard**
    (:meth:`bulk_regime_ok`) that says where the bulk model may speak, and as the input to the ``ρ₀λ``
    figure of merit (:attr:`rho0_lambda`) that slice 4's size-effect model turns into physics.
    """

    name: str
    rho0_uohm_cm: float
    mfp_nm: float

    def __post_init__(self) -> None:
        if self.rho0_uohm_cm <= 0.0:
            raise ValueError(f"rho0_uohm_cm must be > 0, got {self.rho0_uohm_cm}")
        if self.mfp_nm <= 0.0:
            raise ValueError(f"mfp_nm must be > 0, got {self.mfp_nm}")

    @property
    def rho0_lambda(self) -> float:
        """The ``ρ₀·λ`` scaling figure of merit (µΩ·cm·nm) — **lower is better in the narrow-wire limit**.

        Below ``λ`` the size effect gives ``ρ_eff → C·ρ₀λ/d``, so the material enters *only* through this
        product — the cited screening FOM for interconnect metals. **The FOM ordering is not the bulk
        ordering**, which is the whole Cu→Ru story: buying a low ``ρ₀`` costs a long ``λ`` (structurally
        F3's κ↔band-gap inverse correlation). Reported here for the guard/FOM; slice 4 makes it a term.
        """
        return self.rho0_uohm_cm * self.mfp_nm

    def bulk_regime_ok(self, width_um: float, margin: float = 5.0) -> bool:
        """Whether a line of width ``width_um`` is wide enough for the **bulk** ``ρ_eff = ρ₀`` model.

        True when the linewidth exceeds ``margin × λ`` — the wide-wire limit where surface/grain-boundary
        scattering is a small correction. This slice's model is bulk-only, so this is the honest bound on
        where it may speak (the F3 ladder-cap discipline). ``margin=5`` keeps the size-effect correction
        at the ~10–20% level rather than the ~2× level. Slice 4 removes the need for the guard.
        """
        return width_um * _NM_PER_UM > margin * self.mfp_nm


# The two metals of the F4 era transition. RUTHENIUM IS DELIBERATELY ABSENT — see the module docstring's
# scope note: Ru's bulk ρ₀ (7.1) is ~4× copper's, so a bulk-only model ranks it LAST, which is the sign
# error inverted. Ru needs slice 4's size-effect + barrier-fraction physics before its constants mean
# anything, and it must not be plottable before then.
#
# CITED: Cu ρ₀ = 1.68 µΩ·cm, λ ≈ 38.7–39 nm. Al λ ≈ 22 nm and Al ρ₀ ≈ 2.65–2.7 µΩ·cm are FLAGGED (the Al
# ρ₀ is a handbook value not pinned by the source search, and real Al interconnect was an Al–Cu alloy at
# ρ ≈ 3.0–3.2, i.e. this pure-Al value UNDERSTATES the historical Cu win — the honest direction to err).
METALS: dict[str, Metal] = {
    "Al": Metal("aluminium (subtractive, pre-1997)", rho0_uohm_cm=2.65, mfp_nm=22.0),
    "Cu": Metal("copper (dual damascene, 1997)", rho0_uohm_cm=1.68, mfp_nm=38.7),
}


def _resolve(metal: Metal | str) -> Metal:
    """The registry lookup shared by the reads (a :class:`Metal` passes through unchanged)."""
    return METALS[metal] if isinstance(metal, str) else metal


# --------------------------------------------------------------------------- #
# 2. The two terms — R (scales with the cross-section) and C (cited: does NOT)
# --------------------------------------------------------------------------- #
def wire_resistance(
    rho_uohm_cm: float, length_um: float, width_um: float, thickness_um: float,
) -> float:
    """The wire resistance ``R = ρ·L/(W·H)`` (Ω) — **rises as the cross-section shrinks**.

    The term that produces the crossover: under scaling ``W`` and ``H`` fall while a *global* wire's ``L``
    does not, so ``R`` grows. ``rho_uohm_cm`` is the **effective** resistivity — in this slice always the
    bulk ``ρ₀`` (valid for ``W ≫ λ``; see :meth:`Metal.bulk_regime_ok`). Lengths in µm, converted to cm
    internally against the µΩ·cm resistivity.
    """
    if rho_uohm_cm <= 0.0:
        raise ValueError(f"rho_uohm_cm must be > 0, got {rho_uohm_cm}")
    if length_um < 0.0:
        raise ValueError(f"length_um must be ≥ 0, got {length_um}")
    if width_um <= 0.0:
        raise ValueError(f"width_um must be > 0, got {width_um}")
    if thickness_um <= 0.0:
        raise ValueError(f"thickness_um must be > 0, got {thickness_um}")
    rho_ohm_cm = rho_uohm_cm * 1.0e-6
    L_cm = length_um / _UM_PER_CM
    area_cm2 = (width_um / _UM_PER_CM) * (thickness_um / _UM_PER_CM)
    return rho_ohm_cm * L_cm / area_cm2


def wire_capacitance(length_um: float, c_pul_pf_cm: float = C_PUL_PF_CM) -> float:
    """The wire capacitance ``C = c_pul·L`` (F) — **independent of W and H** (the cited invariance).

    Note the signature: **there is no width or thickness argument, and that is the physics**, not a
    simplification. The total per-length capacitance (area + fringing + line-to-line coupling) is ~2 pF/cm
    across essentially every interconnect geometry — a 1 cm coax and an 80 nm-pitch on-chip line agree to
    within a factor of order unity — because ``C`` per length depends on *ratios* of dimensions, not
    absolute size, and on chip the coupling term rises as the area term falls. This is why the crossover
    is an **R** story: ``R`` scales, ``C`` does not.
    """
    if length_um < 0.0:
        raise ValueError(f"length_um must be ≥ 0, got {length_um}")
    if c_pul_pf_cm <= 0.0:
        raise ValueError(f"c_pul_pf_cm must be > 0, got {c_pul_pf_cm}")
    return (c_pul_pf_cm * 1.0e-12) * (length_um / _UM_PER_CM)


# --------------------------------------------------------------------------- #
# 3. The two delays — the wire's (blind to the transistor) and the gate's (the CV/I metric)
# --------------------------------------------------------------------------- #
def wire_delay(R_ohm: float, C_farad: float, elmore: float = ELMORE_FACTOR) -> float:
    """The distributed-RC wire delay ``τ_wire = k·R·C`` (s). **``∂τ_wire/∂I_Dsat = 0``** — the payload.

    ``elmore`` is the flagged distributed-line coefficient (~0.38·RC for a distributed line vs 0.69·RC
    lumped); it cancels in every ratio this module headlines. Nothing about the transistor appears in this
    function's signature — *that* is the discriminator, made structural rather than asserted.
    """
    if R_ohm < 0.0:
        raise ValueError(f"R_ohm must be ≥ 0, got {R_ohm}")
    if C_farad < 0.0:
        raise ValueError(f"C_farad must be ≥ 0, got {C_farad}")
    if elmore <= 0.0:
        raise ValueError(f"elmore must be > 0, got {elmore}")
    return elmore * R_ohm * C_farad


def gate_delay(c_load_farad: float, i_dsat_A: float, v_dd: float = V_DD_HOUSE) -> float:
    """The transistor's CV/I delay ``τ_gate = C_load·V_dd / I_Dsat`` (s) — **inversely ∝ ``I_Dsat``**.

    The standard drive-limited switching metric: the drive current charges the load through the supply
    swing. ``i_dsat_A`` is :func:`chip.device.saturation_current`'s output (A) — a plain scalar across the
    module boundary (the F2/F3 loose-coupling discipline; ``device.py`` is untouched). This is the *only*
    term the transistor moves, which is the whole point.
    """
    if c_load_farad < 0.0:
        raise ValueError(f"c_load_farad must be ≥ 0, got {c_load_farad}")
    if v_dd <= 0.0:
        raise ValueError(f"v_dd must be > 0, got {v_dd}")
    if i_dsat_A <= 0.0:
        raise ValueError(f"i_dsat_A must be > 0, got {i_dsat_A}")
    return c_load_farad * v_dd / i_dsat_A


def gate_load_capacitance(c_ox_F_cm2: float, width_um: float, channel_length_um: float) -> float:
    """A fan-out-1 gate load ``C_load = C_ox·W·L`` (F) from the **existing** device chain's ``C_ox``.

    Lets ``τ_gate`` be a genuine CV/I read of the real device (``c_ox_F_cm2`` =
    :func:`chip.device.oxide_capacitance`) rather than a house lump — the same "consume the real number"
    move F2 made with ``die.R_s`` and F3 with ``die.t_ox_um``. Fan-out 1 and no parasitics: a
    representative load, not a claim about a real cell.
    """
    if c_ox_F_cm2 <= 0.0:
        raise ValueError(f"c_ox_F_cm2 must be > 0, got {c_ox_F_cm2}")
    if width_um <= 0.0:
        raise ValueError(f"width_um must be > 0, got {width_um}")
    if channel_length_um <= 0.0:
        raise ValueError(f"channel_length_um must be > 0, got {channel_length_um}")
    return c_ox_F_cm2 * (width_um / _UM_PER_CM) * (channel_length_um / _UM_PER_CM)


# --------------------------------------------------------------------------- #
# 4. The bundled delay reading (the τ currency the consumer/demo read)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class WireGeometry:
    """A representative interconnect line: length, width, thickness (all µm).

    ``length_um`` is the flagged house lump (:data:`GLOBAL_WIRE_LENGTH_UM` for a global wire — the only
    scenario with a crossover). ``width_um``/``thickness_um`` are the cross-section that scales with the
    node; they set ``R`` and, per the cited invariance, **do not touch ``C``**.
    """

    length_um: float = GLOBAL_WIRE_LENGTH_UM
    width_um: float = 0.25
    thickness_um: float = 0.5

    def __post_init__(self) -> None:
        if self.length_um < 0.0:
            raise ValueError(f"length_um must be ≥ 0, got {self.length_um}")
        if self.width_um <= 0.0:
            raise ValueError(f"width_um must be > 0, got {self.width_um}")
        if self.thickness_um <= 0.0:
            raise ValueError(f"thickness_um must be > 0, got {self.thickness_um}")

    @property
    def aspect_ratio(self) -> float:
        """The line aspect ratio ``H/W`` — held fixed as the node scales (the ladder's convention)."""
        return self.thickness_um / self.width_um


@dataclass(frozen=True)
class Delay:
    """The decomposed chip delay: the wire term, the gate term, and the share that says who is in charge.

    ``metal`` the interconnect metal; ``R_wire_ohm``/``C_wire_F`` the two wire parasitics;
    ``tau_wire_s``/``tau_gate_s`` the two delay terms. Plain scalars — the loose-coupling currency.
    """

    metal: str
    R_wire_ohm: float
    C_wire_F: float
    tau_wire_s: float
    tau_gate_s: float

    @property
    def tau_total_s(self) -> float:
        """The chip delay ``τ_total = τ_gate + τ_wire`` (s) — the binning consumer's input."""
        return self.tau_gate_s + self.tau_wire_s

    @property
    def tau_total_ps(self) -> float:
        """:attr:`tau_total_s` in picoseconds (the display currency)."""
        return self.tau_total_s * 1.0e12

    @property
    def wire_share(self) -> float:
        """The wire term's fraction of ``τ_total`` — the graded readout of who sets the speed.

        Rises monotonically as ``I_Dsat`` rises (``τ_gate`` falls, ``τ_wire`` does not move **at all**),
        for any geometry/metal/house constant. The tight leg, and a
        :doc:`gradual-failure-preferred`-style graded observable rather than a cliff.
        """
        total = self.tau_total_s
        return self.tau_wire_s / total if total > 0.0 else 0.0

    @property
    def wire_limited(self) -> bool:
        """Whether the wire term is the majority of ``τ_total`` — i.e. the transistor no longer sets speed."""
        return self.wire_share > 0.5


def delay(
    geometry: WireGeometry,
    i_dsat_A: float,
    c_load_farad: float,
    *,
    metal: Metal | str = "Cu",
    v_dd: float = V_DD_HOUSE,
    c_pul_pf_cm: float = C_PUL_PF_CM,
    elmore: float = ELMORE_FACTOR,
) -> Delay:
    """Decompose the chip delay ``τ_total = τ_gate(I_Dsat) + τ_wire(metal, geometry)`` into :class:`Delay`.

    The two terms share **no** variable: ``i_dsat_A`` reaches only :func:`gate_delay`, and ``metal`` /
    ``geometry`` reach only :func:`wire_delay`. That separation is the discriminator, and it is enforced
    here by construction rather than asserted in a docstring.

    ``i_dsat_A`` is the existing chain's drive current (A) and ``c_load_farad`` the switched load (F, e.g.
    from :func:`gate_load_capacitance`). The bulk-``ρ₀`` model is valid for ``W ≫ λ``
    (:meth:`Metal.bulk_regime_ok`) — this slice does **not** guard on it (the caller owns the regime;
    slice 3's ladder must cap itself, the F3 discipline), but the guard is available.
    """
    m = _resolve(metal)
    R = wire_resistance(m.rho0_uohm_cm, geometry.length_um, geometry.width_um, geometry.thickness_um)
    C = wire_capacitance(geometry.length_um, c_pul_pf_cm)
    return Delay(
        metal=m.name, R_wire_ohm=R, C_wire_F=C,
        tau_wire_s=wire_delay(R, C, elmore),
        tau_gate_s=gate_delay(c_load_farad, i_dsat_A, v_dd),
    )


# --------------------------------------------------------------------------- #
# 5. The crossover — and the prefactor-free ratios that are the module's actual headline
# --------------------------------------------------------------------------- #
def crossover_width_um(
    i_dsat_A: float,
    c_load_farad: float,
    *,
    metal: Metal | str = "Cu",
    length_um: float = GLOBAL_WIRE_LENGTH_UM,
    aspect_ratio: float = 2.0,
    v_dd: float = V_DD_HOUSE,
    c_pul_pf_cm: float = C_PUL_PF_CM,
    elmore: float = ELMORE_FACTOR,
) -> float:
    """The linewidth ``W`` at which ``τ_wire = τ_gate`` (µm) — **the crossover**, in closed form.

    Scaling the cross-section at a fixed aspect ratio ``AR = H/W`` gives ``W·H = AR·W²``, so
    ``τ_wire = K/W²`` with ``K = k·ρ·L²·c_pul/AR`` (unit factors folded in) — hence

        ``W_x = √(K / τ_gate)``

    Above ``W_x`` the transistor sets the speed; **below it the wire does**, and the sim's whole
    ``I_Dsat``-is-speed premise stops being true. The **absolute** value carries the flagged ``L`` (it
    scales ∝ ``L``, since ``τ_wire ∝ L²``), so it is **not** a claim on its own — the claims are
    :func:`crossover_width_ratio` (how the metal *shifts* it) and the existence/monotonicity of the
    crossing. A *global* wire is assumed (fixed ``L``): a local wire whose length scales with the pitch
    has a flat ``τ_wire`` and **no crossover at all** (cited).
    """
    if aspect_ratio <= 0.0:
        raise ValueError(f"aspect_ratio must be > 0, got {aspect_ratio}")
    m = _resolve(metal)
    tau_gate = gate_delay(c_load_farad, i_dsat_A, v_dd)          # validates C_load, I_Dsat, V_dd
    if tau_gate <= 0.0:
        raise ValueError("tau_gate must be > 0 to have a crossover (C_load = 0 ⇒ no gate delay)")
    C = wire_capacitance(length_um, c_pul_pf_cm)                 # validates L, c_pul
    # τ_wire(W) = elmore · [ρ·L/(AR·W²)] · C  ⇒  K = elmore·ρ·L·C/AR with the µm→cm factors of
    # wire_resistance folded in. Evaluate R at W = H = 1 µm and rescale: R(W) = R(1)·1/(AR·W²)·1.
    R_unit = wire_resistance(m.rho0_uohm_cm, length_um, 1.0, 1.0)   # ρ·L with unit cross-section
    K = elmore * (R_unit / aspect_ratio) * C
    return math.sqrt(K / tau_gate)


def wire_delay_ratio(metal_a: Metal | str, metal_b: Metal | str) -> float:
    """``τ_wire(a)/τ_wire(b) = ρ₀(a)/ρ₀(b)`` at a fixed geometry — **prefactor-free**.

    Every house constant cancels: ``L``, ``c_pul``, the Elmore factor, the cross-section, ``V_dd`` and
    ``C_load`` are all common to both sides. This is where the era win may be stated (the F3
    ``leakage_decades_saved`` discipline). For Al→Cu it returns **1.58**, i.e. copper cuts wire delay (and
    resistance) by **~37%** — which the independently reported ~40% of the 1997 IBM swap corroborates
    **without this model having been fitted to it**.
    """
    return _resolve(metal_a).rho0_uohm_cm / _resolve(metal_b).rho0_uohm_cm


def crossover_width_ratio(metal_a: Metal | str, metal_b: Metal | str) -> float:
    """``W_x(a)/W_x(b) = √(ρ₀(a)/ρ₀(b))`` — **prefactor-free**: how far the metal *shifts* the crossover.

    Since ``W_x = √(K/τ_gate)`` and ``K ∝ ρ₀``, everything else cancels — ``L``, ``c_pul``, ``V_dd``,
    ``C_load``, the aspect ratio and the Elmore factor. Al→Cu returns **1.26**: copper pushes the
    crossover **~21% further down** in linewidth (``1/1.26``), i.e. it *buys roughly one node* of scaling
    before the wire takes over. That "one node" is the honest size of the 1997 escape — and, unlike the
    absolute crossover width, it contains no house constant at all.
    """
    return math.sqrt(wire_delay_ratio(metal_a, metal_b))
