"""Chemical–mechanical polishing — the step that gave the wire a spread of its own (F8, slice 1).

The **backward axis** (``docs/plans/cmp-planarity-f8.md``): F4 shipped a law and stated it sharply
(:meth:`chip.interconnect.Delay.sensitivity`) —

    ``∂ln f / ∂ln I_Dsat = 1 − wire_share``, because ``τ_wire`` is a **common-mode** additive floor: it
    shifts every die's delay by the same amount and **contributes no spread of its own**.

That clause is true of the tree, but not because of physics. It is true because
``fab_game/steps.py`` reads ``ic.delay(ic.WireGeometry(), …)`` — a *default-constructed* cross-section,
the same ``W`` and ``H`` on every die of every wafer. The wire's zero spread is an artifact of there being
no process step upstream of it.

**CMP is that step.** Polishing is where wire thickness is actually set, and it is set *non-uniformly*.
So the observable F8 exists for is **a chip-speed spread with a non-transistor source** — something no
current knob can produce, since every existing per-die number (``V_t``, ``I_Dsat``, ``j_leak``, ``bv``,
``t_rr``, ``j_gate``) is downstream of the device, and ``τ_wire`` is provably not
(``∂τ_wire/∂I_Dsat = 0``, enforced by construction in :func:`chip.interconnect.delay`).

Why the copper era needed this step at all (the enabling claim, from the source's own first paragraph)
-------------------------------------------------------------------------------------------------------
*"Copper has lower resistivity and higher electromigration immunity compared to Al. However, unlike Al,
copper can not be easily plasma etched, and one must resort to a damascene process and use CMP …
to remove the excess copper and barrier materials, thereby accurately defining the copper lines in the
trenches."* Aluminium lines were **subtractively etched**; copper cannot be. So the trenches are cut
first, flooded with copper, and the excess is **polished off** — polishing is what defines the wire.
**F4's copper era does not exist without F8**, which is the reverse of the usual roadmap dependency:
the later slice is the earlier one's precondition, not its refinement.

The two-sided window — and why dishing is not a defect
--------------------------------------------------------
The source's motivating requirement, near-verbatim: *to ensure there is no residual copper between the
trenches, and hence **no shorting of any two copper lines**, requires that one clears excess copper
**everywhere** on the die and wafer. This requirement typically implies **overpolish** in some regions,
leading to dishing of copper and erosion of oxide.*

So the two failure directions read the **same** removal number:

* **Under-polish** → residual copper bridges adjacent trenches → **functional short**.
* **Over-polish** → dishing + erosion → thinner trench copper → ``R ∝ 1/(W·H)`` rises → **slower part**.

Dishing is therefore **the price of not shorting**, not a defect to be engineered away — and that makes
the wall structural rather than calibrated (:func:`forced_overpolish_ratio`, :func:`polish_window_um`).

The headline closed form — the overpolish you are *forced* into
----------------------------------------------------------------
Let the across-wafer removal spread be ``s`` (local removal ∈ ``R̄·[1−s, 1+s]``) and let ``t_over`` be the
copper overburden that must come off to clear. Clearing the **slowest** site requires ``R̄(1−s) ≥ t_over``,
so the *typical* site is overpolished by ``R̄ − t_over``, and at the cheapest admissible ``R̄``:

    **``overpolish / t_over = s / (1 − s)``**    (:func:`forced_overpolish_ratio`)

**No house constant appears.** At ``s = 0`` the forced overpolish is exactly zero — a perfectly uniform
polish dishes nothing, ever — and it diverges as ``s → 1``. Every gram of dishing in this module is
**bought by non-uniformity**, which is the sharpest statement of the wall and the F3/F4 prefactor-free
discipline in the polish's own currency.

The window then closes in closed form (:func:`critical_nonuniformity`): with a loss budget
``L ≡ loss_max·H₀/(η·t_over)`` in units of the clearing removal, a polish that both clears everywhere and
stays inside budget exists **iff** ``s/(1−s) ≤ L/2``, i.e. ``s ≤ L/(2+L)``. Past that, **no polish time
exists** — clearing the slow region necessarily over-thins the fast one. That is the F8 wall.

Why the across-wafer signature is a *pressure* story (the tight leg, DERIVED not recalled)
--------------------------------------------------------------------------------------------
**Preston's equation** (cited, glass-polishing origin, standard in CMP): ``RR = K·P·V`` — removal rate is
linear in down-force ``P`` and in pad–wafer relative speed ``V``. Two factors; only one of them can carry
a centre-to-edge signature, and it is **not** the obvious one.

In the standard rotary configuration the platen spins at ``ω_p`` about ``O``; the carrier spins at ``ω_w``
about its own centre ``C``, held at distance ``d`` from ``O``. For a wafer point at ``r`` from ``C``
(``ω`` along ẑ, so ``ẑ×`` preserves magnitude):

    ``v_rel = ω_w ẑ×r − ω_p ẑ×(d + r) = ẑ × [(ω_w − ω_p)·r − ω_p·d]``

At **matched speeds** ``ω_w = ω_p`` the ``r`` term vanishes **identically**:

    ``|v_rel| = ω·d`` — **the same at every point on the wafer**, independent of position.

(:func:`relative_speed_m_s`, asserted in the tests.) Real tools run near-matched for exactly this reason.
⇒ **Preston's ``V`` is structurally barred from producing a radial profile; ``P`` must carry it.** The
cited mechanism is the wafer-edge contact "hot spot" — the wafer edge cuts into the pad, so local pressure
exceeds the average — plus retaining-ring pressure mismatch. This is the same shape as F4's *"the
crossover is an R story, not a C story"*: one factor of a product is disqualified by construction.

**Flagged, loudly:** the *sign and existence* of the edge effect are cited; the **amplitude** is a house
number and lives in the consumer (slice 2), not here. The source deliberately **averaged nine dies per
wafer** to remove within-wafer variation, so it supplies no radial profile at all.

The trap this module was nearly built on
------------------------------------------
Secondary summaries state a tidy split: *dishing depends on line **width**, erosion on pattern
**density***. It is memorable, and it is the shape this repo likes (F2's two ``R_sh`` exponents, F3's two
currencies, F4's two terms). **The primary source refutes it in two places** — its Fig. 4b shows dishing
vs *density* is strong **and non-monotonic** (peaking at 60–70 % then falling sharply), and its Fig. 6
shows erosion depends on *pitch*, flagged explicitly as *"different than Steigerwald et al. … where oxide
line space or pitch dependence of erosion is not observed or explored."*

What is built here rides each mechanism on its **primary measured axis** — dishing on pitch (Fig. 5, at
fixed 50 % density) and erosion on density (Fig. 7, at fixed 250 µm pitch), both direct measurements —
and **drops the cross terms by name**, exactly as F4 drops the two Elmore cross terms. The difference
between "modelled on the primary axis, cross terms named" and "the clean split is the physics" is the
whole distinction, and it is why this paragraph exists.

Scale honesty — the part that must NOT be ported, and what it turns into
-------------------------------------------------------------------------
The source's masks are **2–1000 µm** pitch with blocks to **3 mm**, and its break point is an oxide line
space of **~100 µm**. The sim's global wire is a **250 nm** line on a ~0.5 µm pitch, and the paper names
this gap itself in its future work (*"…features at sub-micron dimensions … not apparent with the large
features used in this study"*).

**But the gap is not one number, and that is what decides which legs port.** The smallest *measured*
pitch (2 µm) is only ≈ **4×** the sim's pitch — a short extrapolation, which is why the monotone
log-linear dishing trend may be run down to its zero crossing at ~1 µm. The **break point** sits at an
oxide space ≈ **400×** the sim's, and the density mask's fixed 250 µm pitch ≈ **500×**. So the 60–70 %
dishing peak and the 100 µm break point are **cited observations at the source's scale and are not
extrapolated into any number that reaches a device**, while the near-scale monotone legs are.
(:meth:`CitedExperiment.scale_gap` computes both ratios rather than asserting either.)

That refusal is not a hole; it produces a finding. Fig. 5's dishing trend is ≈ linear in log(pitch) from
~0.1 at 2 µm to ~1.0 at 1000 µm, and **extrapolating it downward crosses zero below ≈ 1 µm pitch**.
:func:`dishing_efficiency` therefore returns **exactly zero** for a sub-micron signal line rather than a
clamped small number — and the consequence is the module's second finding:

    **At the sim's dimensions the loss is an EROSION story, not a dishing story.** Dishing is a
    *wide-feature* problem (bond pads, power rails, the source's own test blocks); a 250 nm signal wire in
    a dense array loses its copper to **erosion of the oxide holding it up**.

The honesty ladder
-------------------
* **Tight — the premise change.** ``τ_wire`` gains a per-die spread, so F4's ``1 − wire_share`` law loses
  the clause it was derived under. Structural, prefactor-free.
* **Tight — the forced-overpolish law** ``s/(1−s)``, and the window collapse ``s ≤ L/(2+L)``. No constants.
* **Tight — ``R ∝ 1/H`` exactly** ⇒ :func:`resistance_factor` = ``1/(1−loss)``. No constants.
* **Tight — the Preston kinematic identity.** ``V`` is *exactly* position-independent at matched speeds.
* **Cited, monotone legs only.** Dishing ↑ with pitch; erosion ↑ with density; total trench-copper loss
  ≈ linear in log(pitch), spanning **25–90 %** across the source's processes and pitches — measured at a
  *targeted* **0 % overpolish**, which is itself the two-sided window's whole point: "just cleared" on the
  wafer already means heavily overpolished somewhere on it.
* **Shape-fitted, FLAGGED — the erosion divergence.** ``η_erode ∝ d/(1−d)`` reproduces Fig. 7's
  near-flat-then-steep rise and has the source's own stated mechanism behind it (beyond the break point
  *"the oxide is able to support the physical pressure of pad"*; below it the standing oxide cannot, so it
  polishes fast). It is a **shape fit to a mechanism**, not a cited law, and is flagged as such.
* **Flagged — the magnitudes.** :data:`PRESTON_K`, :data:`DISH_DECADE_SLOPE`, :data:`DISH_ZERO_PITCH_UM`,
  :data:`EROSION_COEFF`, and the pattern the caller supplies. As in F4, **absolute nanometres of dishing
  are not a claim this module makes** — only fractions, ratios, and the two closed forms above.

The calibration, named as one (and the flattering reading it would otherwise get)
----------------------------------------------------------------------------------
Run the module at the source's own scale (250 µm pitch, 50 % density, its 0.7 µm overburden and 0.8 µm
trench) and sweep across-wafer non-uniformity: ``s`` = 7 % → 27 % trench copper lost, 10 % → 40 %,
15 % → 63 %, 20 % → 89 %. That reproduces the source's measured **25–90 %** band (Fig. 8) across a
**realistic** CMP non-uniformity range, and the temptation is to report it as the module predicting the
paper's headline from the clear-everywhere requirement alone.

**It is not a prediction, and must never be quoted as one.** :data:`DISH_SCALE` is a free multiplier that
the source does not pin — its dishing axis is *normalized*, so nothing in the paper fixes the conversion
from "normalized dishing" to "fraction of trench copper". ``DISH_SCALE`` was **chosen so that the cited
loss band lands on a realistic non-uniformity band.** One free parameter, one matched band: that is a
**calibration**, and calling it a cross-check would be the F5-S3 flattering-direction trap arriving one
layer down — a number that agrees with the literature because it was set to.

What *is* free of the calibration, and therefore what may be quoted: the ``s/(1−s)`` law, the
``s ≤ L/(2+L)`` window collapse, ``1/(1−loss)``, the velocity identity, and the **ordering** results
(dishing dies below ~1 µm pitch; erosion takes over and diverges as density → 1). None of those move when
``DISH_SCALE`` moves.

Named scope edges (honest ceilings, stated so the omission isn't silent)
-------------------------------------------------------------------------
* **Slurry chemistry, pad mechanics, pad conditioning, dishing-model fitting: NOT BUILT.** The module
  takes a removal and a pattern and returns a thickness. Preston + the pattern dependence is the physics.
* **The cross terms (dishing↔density, erosion↔pitch): NAMED, NOT BUILT** — see the trap above.
* **The sub-micron regime the source could not measure: NOT EXTRAPOLATED** — see the scale note.
* **``W`` does not move.** Erosion thins the oxide *between* lines and dishing thins the copper *in* them;
  neither redefines the trench sidewalls, which the etch set. Modelling ``H`` alone is the honest minimum,
  and it is also the only axis :func:`chip.interconnect.wire_resistance` needs from here.
* **``C`` is not touched.** F4's cited ``c_pul`` invariance says capacitance per length does not read
  ``W``/``H``; letting dishing move ``C`` would silently contradict the F4 source.
* **Multi-level stacking / cumulative planarity: NOT BUILT.** One metal level, one polish.

Units — µm for every thickness, psi for pressure, m/s for speed, fractions dimensionless
------------------------------------------------------------------------------------------
Thicknesses, removals and pitches are **µm** (the ``chip`` house length currency); pressure **psi** (the
source's own unit, Table 1a); speed **m/s**; pattern density, spread and loss are **dimensionless
fractions in [0, 1)**. Efficiencies (``η``) are dimensionless and may exceed 1 — that is what dishing
*is*: the pad dips into soft wide copper and the trench recedes **faster** than the surrounding field.

Cited source
-------------
Park, Tugbawa, Yoon, Boning, Chung (MIT EECS); Muralidhar, Hymes (SEMATECH); Gotkis, Alamgir, Walesa,
Shumway (IPEC/Planar); Wu, Zhang (Rodel); Kistler, Hawkins (Cabot), **"Pattern and Process Dependencies
in Copper Damascene Chemical Mechanical Polishing Processes"**, VLSI Multilevel Interconnect Conference
(VMIC), Santa Clara CA, June 1998. Read in full 2026-08-19. Preston's equation: standard CMP form
``RR = K·P·V`` (glass-polishing origin; modified-exponent variants exist and are named, not used).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# House constants — every one of these is FLAGGED (see the honesty ladder)
# --------------------------------------------------------------------------- #
PRESTON_K = 1.67e-2        # FLAGGED — Preston coefficient, µm/(s·psi·(m/s)); scales removal, no headline
DISH_ZERO_PITCH_UM = 1.0   # FLAGGED — pitch at which the cited log-linear dishing trend reaches zero
DISH_DECADE_SLOPE = 0.33   # FLAGGED — normalized dishing gained per decade of pitch (Fig. 5: ~0.9/2.7)
DISH_SCALE = 5.0           # CALIBRATED (see `the calibration, named as one` in the docstring) — converts
#                            the source's NORMALIZED dishing into a trench-recession efficiency
EROSION_COEFF = 0.12       # FLAGGED — shape-fit prefactor on d/(1−d) (Fig. 7)

# --------------------------------------------------------------------------- #
# The cited experiment, kept as data so the demo and tests quote rather than recall
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CitedExperiment:
    """The source's stack, masks and headline numbers — quoted, never fitted.

    Carried as data for the same reason :mod:`chip.strain` carries both the mobility *and* the drive
    factor: it makes "what the paper measured" a computable object rather than a claim in prose, and it
    keeps the **scale gap** (``mask_pitch_um`` vs a 250 nm wire) visible at the point of use.
    """

    oxide_um: float = 0.8              # TEOS deposited on bare silicon
    trench_depth_um: float = 0.8       # etched all the way to silicon ⇒ the nominal copper thickness
    barrier_nm: float = 25.0           # deposited before the seed
    plated_copper_um: float = 1.5      # electroplated copper
    wafer_mm: float = 200.0            # 8" wafers
    mask_pitch_um: tuple[float, float] = (2.0, 1000.0)
    mask_density: tuple[float, float] = (0.04, 1.00)
    density_mask_pitch_um: float = 250.0
    trench_loss_fraction: tuple[float, float] = (0.25, 0.90)   # Fig. 8, at a TARGETED 0% overpolish
    dishing_density_peak: tuple[float, float] = (0.60, 0.70)   # Fig. 4b — NOT modelled (scale)
    break_point_oxide_space_um: float = 100.0                  # NOT modelled (scale)
    planarization_length_um: tuple[float, float] = (50.0, 100.0)   # vs 3–5 mm for conventional oxide CMP
    dies_averaged: int = 9             # ⇒ the paper supplies NO within-wafer radial profile

    @property
    def overburden_um(self) -> float:
        """Copper standing above the field oxide that must come off to clear (plated − trench depth)."""
        return self.plated_copper_um - self.trench_depth_um

    def scale_gap(self, pitch_um: float) -> tuple[float, float]:
        """``(nearest, break_point)`` ratios between this experiment's scale and a pitch of interest.

        The first is the smallest *measured* pitch over ``pitch_um`` — how far the monotone trends must be
        extrapolated to reach the caller (≈ 4× for the sim's ~0.5 µm pitch: short). The second is the
        break-point oxide space over ``pitch_um`` — how far the *break point* would have to be carried
        (≈ 200–400×: refused). **Two numbers, because "the scale gap" is not one number**, and which legs
        may be ported is decided by the first while which may not is decided by the second.
        """
        if pitch_um <= 0.0:
            raise ValueError(f"pitch_um must be > 0, got {pitch_um}")
        return (self.mask_pitch_um[0] / pitch_um, self.break_point_oxide_space_um / pitch_um)


CITED = CitedExperiment()


# --------------------------------------------------------------------------- #
# 1. Preston's equation, and the kinematic identity that disqualifies V
# --------------------------------------------------------------------------- #
def preston_removal_um(pressure_psi: float, speed_m_s: float, time_s: float,
                       k: float = PRESTON_K) -> float:
    """Blanket removal ``K·P·V·t`` (µm) — Preston's equation, linear in pressure and in speed.

    The **linearity in ``P``** is what makes the across-wafer pressure profile map straight onto a removal
    profile in slice 2 (no exponent to soften it). Modified forms with ``P^(5/6)``/``V^(1/2)`` exponents
    exist in the literature and are **named, not used** — a fractional exponent would change magnitudes
    without touching a single structural claim here, and this module makes no magnitude claims.
    """
    if pressure_psi < 0.0:
        raise ValueError(f"pressure_psi must be ≥ 0, got {pressure_psi}")
    if speed_m_s < 0.0:
        raise ValueError(f"speed_m_s must be ≥ 0, got {speed_m_s}")
    if time_s < 0.0:
        raise ValueError(f"time_s must be ≥ 0, got {time_s}")
    if k < 0.0:
        raise ValueError(f"k must be ≥ 0, got {k}")
    return k * pressure_psi * speed_m_s * time_s


def relative_speed_m_s(omega_carrier: float, omega_platen: float, offset_m: float,
                       radius_m: float, angle_rad: float = 0.0) -> float:
    """Pad–wafer relative speed at a point ``radius_m`` from the wafer centre (rad/s in, m/s out).

    ``|v_rel| = |(ω_w − ω_p)·r − ω_p·d|`` with the vectors laid out in the module docstring. **At matched
    speeds (``ω_w == ω_p``) the ``r`` term cancels identically and this returns ``ω·d`` for every point on
    the wafer** — which is the leg that disqualifies Preston's ``V`` from carrying any centre-to-edge
    signature and hands the whole radial story to ``P``.

    ``angle_rad`` is the angle between the point's radius vector and the carrier-to-platen offset; it
    matters only off-match (where it produces the few-percent spread the kinematic literature reports).
    """
    if offset_m < 0.0:
        raise ValueError(f"offset_m must be ≥ 0, got {offset_m}")
    if radius_m < 0.0:
        raise ValueError(f"radius_m must be ≥ 0, got {radius_m}")
    d_omega = omega_carrier - omega_platen
    # |(Δω)r − ω_p d|, law of cosines on the two contributions
    a = d_omega * radius_m
    b = omega_platen * offset_m
    return math.sqrt(a * a + b * b - 2.0 * a * b * math.cos(angle_rad))


def velocity_is_uniform(omega_carrier: float, omega_platen: float) -> bool:
    """Whether the kinematics make ``|v_rel|`` position-independent over the whole wafer (``ω_w == ω_p``).

    The predicate form exists so a caller can *assert* the identity rather than trust a comment: when this
    is ``True``, :func:`relative_speed_m_s` is constant in ``radius_m`` and ``angle_rad`` exactly.
    """
    return omega_carrier == omega_platen


# --------------------------------------------------------------------------- #
# 2. The pattern — and the two efficiencies, each on its primary measured axis
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PatternGeometry:
    """The layout the polish sees: line pitch (µm) and metal pattern density (fraction of area copper).

    ``density`` is the source's definition — *copper line width divided by pitch* — so the line width and
    the oxide space between lines both follow from the pair. Density must stay **below 1**: at ``d = 1``
    there is no oxide left standing to carry the pad load, which is the divergence
    :func:`erosion_efficiency` is built around, not a case to be clamped.
    """

    pitch_um: float
    density: float = 0.5

    def __post_init__(self) -> None:
        if self.pitch_um <= 0.0:
            raise ValueError(f"pitch_um must be > 0, got {self.pitch_um}")
        if not 0.0 <= self.density < 1.0:
            raise ValueError(
                f"density must be in [0, 1), got {self.density} — at density = 1 no oxide remains to "
                "carry the pad load and the erosion model diverges by construction"
            )

    @property
    def line_width_um(self) -> float:
        """Copper line width ``pitch·density`` (µm) — the axis dishing is measured against."""
        return self.pitch_um * self.density

    @property
    def oxide_space_um(self) -> float:
        """Oxide space between lines ``pitch·(1−density)`` (µm) — what must hold the pad up."""
        return self.pitch_um * (1.0 - self.density)

    @property
    def sub_micron(self) -> bool:
        """Whether the pitch is below the cited dishing trend's zero crossing (⇒ an erosion-only regime)."""
        return self.pitch_um < DISH_ZERO_PITCH_UM


def dishing_efficiency(pattern: PatternGeometry) -> float:
    """Trench recession per unit overpolish from **dishing**, on its primary axis (pitch). Dimensionless.

    Rides Fig. 5's log-linear trend (``≈0.1`` at 2 µm to ``≈1.0`` at 1000 µm, at 50 % density) and
    **returns exactly 0.0 at or below** :data:`DISH_ZERO_PITCH_UM`, where that trend crosses zero, rather
    than clamping a small positive number. The zero is the point: dishing is a **wide-feature** problem —
    bond pads, power rails, the source's own 3 mm test blocks — and a sub-micron signal line does not have
    it. What such a line loses instead is :func:`erosion_efficiency`.

    Values above 1 are physical and expected for wide features: dishing *is* the trench receding faster
    than the surrounding field, because the pad dips into the soft copper.
    """
    if pattern.pitch_um <= DISH_ZERO_PITCH_UM:
        return 0.0
    return DISH_SCALE * DISH_DECADE_SLOPE * math.log10(pattern.pitch_um / DISH_ZERO_PITCH_UM)


def erosion_efficiency(pattern: PatternGeometry) -> float:
    """Trench recession per unit overpolish from **oxide erosion**, on its primary axis (density).

    ``η_erode = EROSION_COEFF · d/(1−d)``. The **divergence at ``d → 1`` is the mechanism, not a fitting
    artifact**: the standing oxide is what carries the pad load, so as its area fraction ``(1−d)`` goes to
    zero the pressure on it — and therefore its removal rate — goes up without bound, and the oxide
    receding takes the copper's floor down with it. That is the source's own stated explanation of its
    break point, one scale up.

    **FLAGGED as a shape fit to a mechanism, not a cited law.** It reproduces Fig. 7's near-flat rise to
    ~50–60 % density followed by a steep climb toward 100 %; the source publishes *normalized* erosion, so
    no absolute calibration is available or claimed.
    """
    d = pattern.density
    return EROSION_COEFF * d / (1.0 - d)


def loss_efficiency(pattern: PatternGeometry) -> float:
    """Total trench recession per unit overpolish — **dishing + erosion**, the source's own sum.

    *"By adding copper dishing to oxide erosion, we get the total amount of copper loss in the trenches"*
    — the two mechanisms are additive in the paper and additive here. Both remove copper thickness from
    the trench; they differ in which surface goes down (the copper's top vs the oxide holding it up), and
    that distinction has no consequence for ``R ∝ 1/(W·H)``, which reads only the remaining thickness.
    """
    return dishing_efficiency(pattern) + erosion_efficiency(pattern)


# --------------------------------------------------------------------------- #
# 3. The headline — the overpolish non-uniformity forces on you
# --------------------------------------------------------------------------- #
def forced_overpolish_ratio(nonuniformity: float) -> float:
    """``s/(1−s)`` — overpolish forced by the clear-everywhere requirement, in units of the overburden.

    **The module's headline, and it contains no house constant.** With local removal spread over
    ``R̄·[1−s, 1+s]``, clearing the slowest site needs ``R̄ = t_over/(1−s)``, so the typical site is
    overpolished by ``R̄ − t_over = t_over·s/(1−s)``.

    Read it in both directions:

    * ``s = 0`` ⇒ **exactly zero** forced overpolish. A perfectly uniform polish dishes *nothing*, at any
      pattern, for any time — every gram of dishing in this module is **bought by non-uniformity**.
    * ``s → 1`` ⇒ divergence. The fast region is polished arbitrarily far past clearing while the slow
      region is still just reaching it.

    This is why F8's wall is structural rather than calibrated, and why the fix for dishing is *polish
    uniformity*, never *polish less* — polishing less does not reduce ``s``, it only fails to clear.
    """
    if not 0.0 <= nonuniformity < 1.0:
        raise ValueError(
            f"nonuniformity must be in [0, 1), got {nonuniformity} — at s = 1 the slowest site removes "
            "nothing and no finite polish clears the wafer"
        )
    return nonuniformity / (1.0 - nonuniformity)


def critical_nonuniformity(loss_budget: float, trench_depth_um: float, overburden_um: float,
                           pattern: PatternGeometry) -> float:
    """The largest across-wafer spread ``s`` for which *some* polish both clears and stays in budget.

    Derivation (both bounds on the mean removal ``R̄``, then the condition that they do not cross):

    * clear the slowest site:  ``R̄ ≥ t_over/(1−s)``
    * hold the fastest site inside budget:  ``η·(R̄(1+s) − t_over)/H₀ ≤ loss_max``

    A window exists iff ``2·s·t_over ≤ (1−s)·loss_max·H₀/η``, i.e. with
    ``L ≡ loss_max·H₀/(η·t_over)``:  ``s/(1−s) ≤ L/2``  ⇒  **``s_crit = L/(2+L)``**.

    Returns 1.0 (no attainable spread is fatal) when the pattern loses nothing per unit overpolish —
    ``η = 0``, i.e. a sub-micron pitch at zero density — since then the budget cannot be spent.
    """
    if not 0.0 < loss_budget <= 1.0:
        raise ValueError(f"loss_budget must be in (0, 1], got {loss_budget}")
    if trench_depth_um <= 0.0:
        raise ValueError(f"trench_depth_um must be > 0, got {trench_depth_um}")
    if overburden_um <= 0.0:
        raise ValueError(f"overburden_um must be > 0, got {overburden_um}")
    eta = loss_efficiency(pattern)
    if eta <= 0.0:
        return 1.0
    budget = loss_budget * trench_depth_um / (eta * overburden_um)
    return budget / (2.0 + budget)


def polish_window_um(loss_budget: float, trench_depth_um: float, overburden_um: float,
                     nonuniformity: float, pattern: PatternGeometry) -> tuple[float, float] | None:
    """The admissible **mean removal** range (µm), or ``None`` when the window has closed.

    The lower bound clears the slowest site; the upper bound keeps the fastest site inside ``loss_budget``.
    ``None`` is returned — rather than an inverted or empty tuple — when ``nonuniformity`` exceeds
    :func:`critical_nonuniformity`: **there is no polish time at all**, and a caller that silently took a
    midpoint of a crossed interval would be reporting a recipe that shorts *and* over-thins.
    """
    if not 0.0 < loss_budget <= 1.0:
        raise ValueError(f"loss_budget must be in (0, 1], got {loss_budget}")
    if trench_depth_um <= 0.0:
        raise ValueError(f"trench_depth_um must be > 0, got {trench_depth_um}")
    if overburden_um <= 0.0:
        raise ValueError(f"overburden_um must be > 0, got {overburden_um}")
    if not 0.0 <= nonuniformity < 1.0:
        raise ValueError(f"nonuniformity must be in [0, 1), got {nonuniformity}")
    eta = loss_efficiency(pattern)
    lo = overburden_um / (1.0 - nonuniformity)
    if eta <= 0.0:
        return (lo, math.inf)       # nothing to over-thin: the upper bound is not binding
    hi = (overburden_um + loss_budget * trench_depth_um / eta) / (1.0 + nonuniformity)
    return (lo, hi) if hi >= lo else None


# --------------------------------------------------------------------------- #
# 4. The polish itself — one site, one removal, one thickness
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Polish:
    """What the polish did at **one site**: whether it cleared, and what thickness it left behind.

    ``residual_um`` copper still bridging the trenches (``> 0`` ⇒ a **short**, the under-polish side);
    ``overpolish_um`` removal beyond clearing; ``dish_loss``/``erosion_loss``/``loss_fraction`` the trench
    copper lost, as fractions of the nominal depth; ``thickness_um`` what the wire is actually made of.
    Plain scalars — the loose-coupling currency the rest of ``chip`` speaks.
    """

    removal_um: float
    residual_um: float
    overpolish_um: float
    dish_loss: float
    erosion_loss: float
    loss_fraction: float
    thickness_um: float

    @property
    def cleared(self) -> bool:
        """Whether the site cleared — ``False`` ⇒ residual copper bridges the lines ⇒ a functional short."""
        return self.residual_um <= 0.0

    @property
    def resistance_factor(self) -> float:
        """``R/R_nominal = 1/(1−loss)`` — exact, since ``R ∝ 1/(W·H)`` and only ``H`` moved.

        Prefactor-free: length, width, resistivity and ``c_pul`` all cancel. This is the number
        :func:`chip.interconnect.wire_resistance` would return with the polished thickness in place of
        the nominal one, and it is how the loss reaches ``τ_wire`` without this module importing F4.
        """
        return 1.0 / (1.0 - self.loss_fraction)


def polish(removal_um: float, overburden_um: float, trench_depth_um: float,
           pattern: PatternGeometry) -> Polish:
    """Polish one site by ``removal_um`` and report what is left (:class:`Polish`).

    Below clearing, nothing has reached the trench yet: the copper thickness is still nominal and the
    residual overburden is the failure. Above clearing, the excess ``removal − t_over`` is multiplied by
    the pattern's two efficiencies and comes out of the trench.

    **Raises** when the loss reaches 100 % — the trench has been polished out and there is no conductor
    left to have a resistance, the same refusal :func:`chip.interconnect.conductor_width_um` makes at its
    all-barrier floor rather than returning a zero that would divide downstream.
    """
    if removal_um < 0.0:
        raise ValueError(f"removal_um must be ≥ 0, got {removal_um}")
    if overburden_um <= 0.0:
        raise ValueError(f"overburden_um must be > 0, got {overburden_um}")
    if trench_depth_um <= 0.0:
        raise ValueError(f"trench_depth_um must be > 0, got {trench_depth_um}")

    residual = max(0.0, overburden_um - removal_um)
    overpolish = max(0.0, removal_um - overburden_um)
    dish = dishing_efficiency(pattern) * overpolish / trench_depth_um
    erode = erosion_efficiency(pattern) * overpolish / trench_depth_um
    loss = dish + erode
    if loss >= 1.0:
        raise ValueError(
            f"the trench is polished out: loss fraction {loss:.3f} ≥ 1 at removal_um={removal_um} on "
            f"pitch={pattern.pitch_um} µm / density={pattern.density} — no conductor remains, so no "
            "thickness or resistance exists to report (cf. chip.interconnect.conductor_width_um)"
        )
    return Polish(
        removal_um=removal_um, residual_um=residual, overpolish_um=overpolish,
        dish_loss=dish, erosion_loss=erode, loss_fraction=loss,
        thickness_um=trench_depth_um * (1.0 - loss),
    )
