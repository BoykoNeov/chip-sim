"""BEOL interconnect RC delay — the chip speed the transistor does not set (F4, complete: slices 1–4).

The **backward axis** (``docs/plans/beol-interconnect-f4.md``): chip delay is **two terms with no shared
variable**, and *no single scalar can move both*:

  * **Gate delay** ``τ_gate = C_load·V_dd / I_Dsat`` — the transistor's term (the CV/I metric).
    **Inversely ∝ ``I_Dsat``**, the number the whole existing chain already computes (CD → ``V_t`` →
    ``I_Dsat``, plus F2's ``R_series`` source degeneration).
  * **Wire delay** ``τ_wire = k·R_wire·C_wire``, ``R_wire = ρ·L/(W·H)``, ``C_wire = c_pul·L`` — the
    wire's **intrinsic** RC. **``∂τ_wire/∂I_Dsat = 0``**: the transistor does not appear in it.

**The precise claim (bounded — read this before quoting the headline).** What is modelled here is the
wire's **intrinsic** ``R_w·C_w``, and *that* is the term no transistor can touch. The full single-stage
Elmore delay is ``R_d·(C_w + C_L) + R_w·(C_w/2 + C_L)``; this module carries ``R_d·C_L`` (as ``τ_gate``,
the CV/I form) and ``R_w·C_w`` (as ``τ_wire``), and **drops the two cross terms** — see the scope edges.
One of those, ``R_driver·C_wire``, *is* weakly ``I_Dsat``-dependent, so the honest statement is **"the
wire's intrinsic RC is a common-mode floor"**, not "the transistor cannot touch the wire at all". The
discriminator is unharmed — an ``I_Dsat``-independent floor still exists, and it still ends the
``I_Dsat``-is-speed premise — but the stronger phrasing would be a claim this model has not earned.

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
* **A consistency check on the constants (deliberately NOT called non-circular — it is weaker than F3's).**
  The cited bulk resistivities reproduce IBM's independently reported **~40% resistance reduction** for the
  1997 Al→Cu swap: ``ρ_Al/ρ_Cu`` = 2.65/1.68 = 1.58 ⇒ **~37% less** (and ~46% for a real Al–Cu alloy line
  at ρ ≈ 3.1, so the report is bracketed). **Its honest status:** at a fixed geometry ``R_Al/R_Cu`` **is**
  ``ρ_Al/ρ_Cu`` identically, so this checks that the handbook ratio matches the reported ratio — it does
  **not** validate a structural form. F3's (φ_B, m*)-predicts-the-2 Å-slope check was stronger because it
  ran through the *exponential*, so cited inputs predicted a **different functional form's** slope. This
  one is a sanity check on the inputs, and must not be quoted as more.
* **Tight — the two S4 impossibility results (the narrow-wire era's headline).** Below ``λ`` the ranking
  metal changes, and *which mechanism* flips Cu→Ru is settled by two closed forms that use **only cited
  constants** — no ``C``, no barrier thickness, no geometry. **(a) The size effect alone can never flip
  the sign, at any width whatsoever**: :func:`resistance_ratio` without a barrier falls monotonically from
  ``ρ₀(Ru)/ρ₀(Cu)`` = 4.23 to the asymptote ``ρ₀λ(Ru)/ρ₀λ(Cu)`` = **1.179**, and 1.179 > 1. So "ruthenium
  wins because its mean free path is short" is false not approximately but **in the limit** — the cited
  FOM says *parity*, and parity is not a win. **(b) The barrier alone, on bulk ``ρ``, cannot flip it
  either**, except in a window no fab could use: ``ρ₀(Ru)/ρ₀(Cu)·(W − 2t_b)/W < 1`` needs
  ``W < 2t_b/(1 − ρ₀(Cu)/ρ₀(Ru))`` = **5.2 nm** at ``t_b`` = 2 nm — barely a nanometre above ``W = 2t_b``
  = 4.0 nm, the width at which copper stops having a conductor **at all**. Only the two *together* get the
  sign right, which is the F3-IL structure exactly.
* **Tight — the geometric conductor floor.** ``W_eff = W − 2·t_b`` with a **fixed** ``t_b`` has a hard zero
  at ``W = 2·t_b`` (4–6 nm over the cited 2–3 nm barrier range): a copper line narrower than its own two
  liners is **all barrier and no conductor**, for any resistivity, any length, any ``C``. This is F3's
  "``EOT > t_IL`` for **any** κ" in the wire's currency — prefactor-free, and inside the roadmap.
  :func:`conductor_width_um` raises below it rather than extrapolating through.
* **Flagged — the magnitudes.** The wire length :data:`GLOBAL_WIRE_LENGTH_UM` (**nothing in the sim carries
  a wire length** — the analogue of F2's ``CONTACT_LENGTH_UM`` and B6's ``SPIKE_CONCENTRATION``; checked:
  B6's ``t_Al`` is a contact-metallization *thickness*, not a line length), the Elmore distributed-line
  factor :data:`ELMORE_FACTOR`, the supply :data:`V_DD_HOUSE`, the aluminium ``ρ₀`` (handbook, and a
  real Al–Cu alloy line runs higher than pure Al), and the size-effect coefficient
  :data:`SIZE_EFFECT_C`. **Absolute picoseconds are therefore NOT a claim this module makes** — only
  ratios, shares, the crossover's *shift*, and the two closed forms above are.

The narrow-wire era (slice 4): where ρ_eff = ρ₀ stops being true, and the ranking metal changes
-------------------------------------------------------------------------------------------------
Slices 1–3 are **bulk-``ρ`` only** — ``ρ_eff = ρ₀``, valid for wires much wider than the electron mean free
path ``λ`` (:meth:`Metal.bulk_regime_ok`), which is precisely the Al→Cu era they serve (250 nm ≫ Cu's
39 nm). Slice 4 adds the two mechanisms that take over below that, and **promotes ``λ`` from a validity
guard to a term**. (The guard is *not* retired: it still bounds where :func:`delay` and
:func:`crossover_width_um` — the bulk functions — may speak. Slice 4 adds a second, narrow-wire path
beside them rather than widening the first.)

* **The size effect.** Below ``λ``, surface and grain-boundary scattering give
  ``ρ_eff ≈ ρ₀·(1 + C·λ/d)`` (:func:`effective_resistivity`), so in the narrow limit ``ρ_eff → C·ρ₀λ/d``
  and the material enters **only** through the product ``ρ₀λ`` — the cited screening figure of merit
  (:attr:`Metal.rho0_lambda`). **The FOM ordering is not the bulk ordering**, structurally the same finding
  as F3's "buying κ costs barrier" and F2's two ``R_sh`` exponents. But see the honesty ladder: the FOM
  buys ruthenium *parity*, never a win.
* **The barrier — the BEOL's interfacial layer.** Copper needs a Ta/TaN diffusion barrier with a cited
  **~2–3 nm minimum thickness that does not scale**; ruthenium needs **none**. So a **fixed** thickness
  eats a **shrinking** budget: ``W_eff = W − 2·t_b``, with the hard floor above. This is what tips an
  already-near-parity metal over, and it is **geometric, not a materials ride** (A4's lesson).

**The honest Ru claim is therefore two steps, both load-bearing**, and the three-rung ladder
(:func:`resistance_ratio`, whose ``size_effect``/``barrier`` switches exist to *run* it) is the proof at a
12 nm line: bulk ``ρ`` alone ranks Ru **4.23× worse**; adding the size effect takes that to **1.90×** —
better, still losing; adding the barrier on top lands **0.92×**, a win. Neither alone suffices — the
barrier on *bulk* ``ρ`` is still 2.82× worse at that width. **The metal with the worst bulk ``ρ`` and the
worst ``ρ₀λ`` of the three wins anyway, and only both currencies together get that sign right.** Do not
collapse this to "Ru wins because of the liner" (drops the necessary condition) or to "Ru has a shorter
mean free path" (the sign error this module exists to prevent).

**Aluminium is refused in this regime, and the refusal is load-bearing** (:data:`NARROW_WIRE_METALS`).
Al's ``ρ₀λ`` ≈ 58 would *screen better than copper's 65* — and printing that number would be a claim this
module cannot support: aluminium's disqualifier is **electromigration**, a reliability currency this module
does not carry (a named ceiling, below). So :attr:`Metal.barrier_nm` is ``None`` for Al and the narrow-wire
reads raise rather than return a competitive-looking figure. That is S3's "the cap is binding, not
cosmetic", applied to a metal instead of a width.

**Where the crossing lands is a bracketed CONSISTENCY check, never a prediction — and it is a band.**
:func:`equal_resistance_width_nm` puts Cu→Ru at **12.9 nm** at ``t_b`` = 2 nm and **17.1 nm** at
``t_b`` = 3 nm — i.e. the *cited* barrier range alone moves it by about a node, which is the finding rather
than an error bar: **where ruthenium wins is set by the thickness of the layer that stopped scaling.**
Widening the flagged ``C`` over [0.375 (pure Fuchs–Sondheimer, fully diffuse) … 2.0] spans ~9.7–21.1 nm.
The literature's crossing is **<~20 nm**; this model's band sits a node or two *inside* it, and the two
named biases below both push that way, so the direction is understood rather than tuned away. Status: the
IBM ~40% check's, not F3's.

**The four simplifications, with their directions named** (the module must say which way each errs, since
the slice's whole conclusion is a sign):

* ``C`` = 1.0 is a round house number, **not fitted** — and it **errs against ruthenium**. It puts copper
  at **6.3 µΩ·cm** in an 18 nm line, where the measurement is **~9** (a ~5× bulk degradation): the model
  *understates* copper's narrow-line penalty, making Ru's win harder to earn. A single coefficient also
  cannot span both ends of the measured range (it over-corrects at 80 nm, where real lines are near bulk);
  the real model needs a separate grain-boundary term whose grain size tracks the linewidth. Named, not
  built — splitting ``C`` in two would add a second lump and no new claim.
* ``W_eff = W − 2·t_b`` takes the barrier off the **width only**, though a damascene liner coats the trench
  bottom too. That gives copper *more* conductor than it really has ⇒ **also errs against ruthenium**.
* **The scattering dimension ``d`` is the conductor width alone, not a cross-section.** Scattering in a
  real rectangular wire sees both surface pairs, and the rates add: the standard form is
  ``1/d = 1/W_eff + 1/H``. Two reasons this module uses ``d = W_eff`` anyway, and the second is why it is
  not a free choice: (i) it **errs against ruthenium** — switching to ``1/W_eff + 1/H`` at the featured
  12 nm rung moves the ratio 0.917 → **0.889** (ruthenium wins by *more*) and the crossing 12.9 → 13.4 nm,
  and it also lands copper's 18 nm resistivity at 8.1 µΩ·cm against the measured ~9, closer than this
  module's 6.3; (ii) bringing ``H`` into the scattering would put the **flagged aspect ratio into the
  headline ratio**, and :func:`resistance_ratio`'s whole value is that ``H`` and ``AR`` cancel exactly.
  A prefactor-free claim that errs against its own conclusion is worth more here than a better-calibrated
  one that does not. [Checked, since the conclusion is a sign: the *harmonic mean* ``2WH/(W+H)`` — twice
  the reciprocal-sum ``d``, and therefore not the additive-rate form — would put the 12 nm rung at 1.12,
  i.e. Ru losing. It also lands the 18 nm resistivity at 4.9 µΩ·cm, furthest of the three from the
  measurement, which is what breaks the tie between the conventions on evidence rather than on taste.]
* The barrier is treated as **perfectly dead area** (TaN is highly resistive but not an insulator), which
  is the one simplification that **errs in ruthenium's favour**.

**Where the bulk model stops being valid — and a slice-1 claim slice 2 had to correct.** *Where* the
crossover lands is a statement about the **load**, not a fixed property of this module. At the **game's
own** operating point — the fan-out-1 load off the real chain (``C_ox`` at the grown ``t_ox`` ≈ 14 nm,
``W`` = 10 µm, ``L`` = the printed ~167 nm CD ⇒ ``C_load`` ≈ 4.1 fF) — Cu's crossover sits at
**~0.395 µm**, which is **comfortably inside** the bulk regime (Cu wants ``W`` > ~0.19 µm at
``margin=5``). A **heavier** load pushes it down: at ``C_load`` ≈ 23 fF (a 1 µm channel, or fan-out > 1)
it lands at ~0.167 µm, *outside* the regime, and :meth:`Metal.bulk_regime_ok` fires. **Slice 1 asserted
that second case as "this slice's own operating point"; it was a test-local load, and the first is the
one the game actually runs** — so the honest reading is that this slice's Al→Cu era (250 nm, ``W`` ≫ Cu's
39 nm ``λ``) is **inside** the bulk model's competence, exactly as claimed.

**Slice 4 is still motivated for copper, not only for ruthenium** — but for the *right* reason: not
because the operating point is already outside the bulk regime (it is not), but because the size-effect
correction **grows without bound as ``W`` scales below ~0.19 µm**, and that is cited history — the size
effect became a **copper** problem at sub-200 nm, long before ruthenium was on anyone's roadmap.

Named scope edges (honest ceilings)
-----------------------------------
* **The driver↔wire cross terms — the omission a student asks about first.** The full single-stage Elmore
  delay is ``R_d·(C_w + C_L) + R_w·(C_w/2 + C_L)``. This module keeps ``R_d·C_L`` (≡ ``τ_gate``, in CV/I
  form) and ``R_w·C_w`` (≡ ``τ_wire``) and **drops ``R_driver·C_wire`` and ``R_wire·C_load``**. *"Doesn't
  the transistor still have to charge the wire capacitance?"* — **yes, and that is the dropped
  ``R_d·C_w``.** It matters for framing: ``R_d ~ V/I``, so ``R_d·C_w`` **is** weakly ``I_Dsat``-dependent,
  which is why the licensed claim is "the wire's **intrinsic** RC is a common-mode floor" and not "the
  transistor cannot touch the wire". The intrinsic ``R_w·C_w`` floor is real and ``I_Dsat``-free, so the
  discriminator stands; the two-term split is a *decomposition*, not a full delay model. Building the
  cross terms is a candidate deepening, not a correction.
* **Repeater / buffer insertion — the big one.** Real chips break long wires with repeaters, which makes
  delay ∝ ``L`` and **not** ``L²``. Un-named, this model would silently claim wire delay is unfixable and
  **overstate the wall**; the ``L²`` growth here is the *un-repeated* wire (the F3 trap-limited-floor
  analogue — the mechanism that stops the extrapolation being real).
* **Low-κ ILD** — the C-side mirror of high-κ (F3 bought ``t_phys`` with κ; low-κ buys ``C_wire`` by
  *lowering* ε). Cited as real and arriving *with* Cu at 250 nm; a separate era knob, not modelled.
* **Electromigration** — Cu's *other* win over Al (and a real reason Al died): a **reliability** mechanism,
  the wrong currency for a delay observable (the same discipline that kept F3's gate leakage out of
  ``lifetime.py``). It is also **aluminium's disqualifier in the narrow-wire regime**, which is why this
  module refuses Al there instead of reporting its flattering ``ρ₀λ``.
* **Thinner liners rather than none** — cited and not modelled: RuCo liners cut the barrier ~33% (to 20 Å)
  for ~25% lower resistance. That is a *third* option between "2–3 nm of TaN" and "nothing", and it moves
  the crossing the same way ``t_b`` does in the band above (which is the point of reporting a band).
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

# The Fuchs–Sondheimer / Mayadas–Shatzkes size-effect coefficient in ρ_eff = ρ₀·(1 + C·λ/d) — FLAGGED, and
# deliberately NOT fitted. 1.0 is a round number; pure FS with fully diffuse surfaces would give 0.375, and
# grain-boundary scattering (MS, with the grain size tracking the linewidth) pushes it above 1. The choice
# matters only for the crossing WIDTH, never for the two impossibility results, which are C-free.
#
# ITS DIRECTION IS NAMED, because the slice's conclusion is a sign: C = 1.0 puts copper at 6.3 µΩ·cm in an
# 18 nm line where the measurement is ~9 µΩ·cm, so this UNDERSTATES copper's narrow-line penalty and makes
# ruthenium's win HARDER to earn. A single coefficient cannot also reproduce the wide end (~80 nm lines run
# near bulk while this form gives ~3 µΩ·cm) — that is the named grain-boundary limitation, not a fit error.
SIZE_EFFECT_C = 1.0                    # FLAGGED — the FS/MS coefficient; errs AGAINST the Ru conclusion

# The copper diffusion-barrier thickness per sidewall (nm) — CITED as a ~2–3 nm floor that DOES NOT SCALE,
# which is the entire mechanism: a fixed thickness eating a shrinking budget. The default is the thin end,
# i.e. the value most favourable to copper and least favourable to the ruthenium conclusion. The range is
# reported as a BAND rather than collapsed to a point, because the band IS the finding — where ruthenium
# wins is set by the thickness of the layer that stopped scaling.
BARRIER_NM_CITED_RANGE = (2.0, 3.0)    # CITED — the Ta/TaN minimum-thickness range (nm, per sidewall)


# --------------------------------------------------------------------------- #
# 1. The metal registry — bulk ρ₀ (the era's currency) + λ (carried ONLY as a validity guard at S1)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Metal:
    """An interconnect metal: bulk ``ρ₀`` (µΩ·cm), mean free path ``λ`` (nm), barrier need ``t_b`` (nm).

    ``rho0_uohm_cm`` sets ``R_wire`` in the **bulk** path (``ρ_eff = ρ₀``, the wide-wire limit — slices
    1–3). ``mfp_nm`` is unused there; it is the **validity guard** (:meth:`bulk_regime_ok`) saying where
    the bulk model may speak, and in the **narrow-wire** path (slice 4) it becomes a term, entering through
    :func:`effective_resistivity` and, in the narrow limit, only through ``ρ₀λ`` (:attr:`rho0_lambda`).

    ``barrier_nm`` is the diffusion barrier this metal needs **per sidewall** — copper's cited ~2–3 nm
    Ta/TaN floor, and **0.0 for a barrierless metal** such as ruthenium. ``None`` means *this metal is not
    a narrow-wire candidate at all*, and the narrow-wire reads **refuse** it rather than returning a
    number: that is aluminium's case, and the refusal is load-bearing (see the module docstring — Al's
    ``ρ₀λ`` flatters it, while its real disqualifier is electromigration, a currency this module does not
    carry). ``None`` is the gap-vs-fake-zero rule: a barrierless metal (0.0) and a metal with no modelled
    narrow-wire case (``None``) are different statements and must not share a value.
    """

    name: str
    rho0_uohm_cm: float
    mfp_nm: float
    barrier_nm: float | None = None

    def __post_init__(self) -> None:
        if self.rho0_uohm_cm <= 0.0:
            raise ValueError(f"rho0_uohm_cm must be > 0, got {self.rho0_uohm_cm}")
        if self.mfp_nm <= 0.0:
            raise ValueError(f"mfp_nm must be > 0, got {self.mfp_nm}")
        if self.barrier_nm is not None and self.barrier_nm < 0.0:
            raise ValueError(f"barrier_nm must be ≥ 0 or None, got {self.barrier_nm}")

    @property
    def rho0_lambda(self) -> float:
        """The ``ρ₀·λ`` scaling figure of merit (µΩ·cm·nm) — **lower is better in the narrow-wire limit**.

        Below ``λ`` the size effect gives ``ρ_eff → C·ρ₀λ/d``, so the material enters *only* through this
        product — the cited screening FOM for interconnect metals. **The FOM ordering is not the bulk
        ordering**, which is the whole Cu→Ru story: buying a low ``ρ₀`` costs a long ``λ`` (structurally
        F3's κ↔band-gap inverse correlation). **It ranks metals; it does not locate a crossing** — see
        :func:`equal_resistance_width_um` on why the deep-limit closed form built from it is ~4× wrong.
        """
        return self.rho0_uohm_cm * self.mfp_nm

    def bulk_regime_ok(self, width_um: float, margin: float = 5.0) -> bool:
        """Whether a line of width ``width_um`` is wide enough for the **bulk** ``ρ_eff = ρ₀`` model.

        True when the linewidth exceeds ``margin × λ`` — the wide-wire limit where surface/grain-boundary
        scattering is a small correction. ``margin=5`` keeps the size-effect correction at the ~10–20%
        level rather than the ~2× level, and this is the honest bound on where the **bulk** path (
        :func:`delay`, :func:`crossover_width_um`, :func:`wire_delay_ratio`) may speak — the F3 ladder-cap
        discipline. **Slice 4 does not retire this guard**: it adds a *second*, narrow-wire path
        (:func:`narrow_line_resistance`) beside the bulk one rather than widening it, so the guard still
        marks exactly the same boundary — it just now has somewhere to point.
        """
        return width_um * _NM_PER_UM > margin * self.mfp_nm

    @property
    def narrow_wire_candidate(self) -> bool:
        """Whether this metal has a modelled narrow-wire case (i.e. a barrier need, possibly zero)."""
        return self.barrier_nm is not None


# The three metals of the F4 arc, with the barrier need that decides the second transition.
#
# CITED: Cu ρ₀ = 1.68 µΩ·cm, λ ≈ 38.7–39 nm, and a Ta/TaN barrier with a ~2–3 nm floor that does not scale.
# Ru ρ₀ = 7.1 µΩ·cm, λ = 10.8 nm, and it needs NO barrier — which is the whole slice-4 story, because its
# bulk ρ₀ is ~4× copper's and no bulk model could ever rank it anything but last.
#
# Al λ ≈ 22 nm and Al ρ₀ ≈ 2.65–2.7 µΩ·cm are FLAGGED (the Al ρ₀ is a handbook value not pinned by the
# source search, and real Al interconnect was an Al–Cu alloy at ρ ≈ 3.0–3.2, i.e. this pure-Al value
# UNDERSTATES the historical Cu win — the honest direction to err). Al's barrier_nm is None ON PURPOSE:
# its ρ₀λ ≈ 58 would screen BETTER than copper's 65, and this module cannot support that comparison
# because aluminium's actual disqualifier — electromigration — is a reliability currency it does not
# carry. The narrow-wire reads refuse Al rather than print the flattering number.
METALS: dict[str, Metal] = {
    "Al": Metal("aluminium (subtractive, pre-1997)", rho0_uohm_cm=2.65, mfp_nm=22.0, barrier_nm=None),
    "Cu": Metal("copper (dual damascene, 1997)", rho0_uohm_cm=1.68, mfp_nm=38.7,
                barrier_nm=BARRIER_NM_CITED_RANGE[0]),
    "Ru": Metal("ruthenium (barrierless, ~3 nm node)", rho0_uohm_cm=7.1, mfp_nm=10.8, barrier_nm=0.0),
}

# The metals the BULK path may be offered for — and specifically the set the game's `interconnect` knob
# (fab_game.recipe.DeviceKnobs, slice 2) accepts. THIS IS A GUARD, NOT A TASTE: the game runs ONE house
# geometry, a 250 nm-era global line, through the bulk-ρ model. Ruthenium at 250 nm really is ~4× worse
# than copper — the bulk answer is *correct* and reads as a verdict on the metal, which is exactly the
# sign inversion this module exists to prevent. Ru's case is a sub-20 nm claim; there is no node in the
# game to make it at. So the knob refuses it by name, with the reason, rather than binning a plausible-
# looking number. (The narrow-wire reads below have the mirror-image guard in NARROW_WIRE_METALS.)
BULK_ERA_METALS: tuple[str, ...] = ("Al", "Cu")

# The metals with a modelled narrow-wire case — derived, never hand-maintained, so a metal added to
# METALS with a barrier_nm can never be silently missing from here (and Al can never silently appear).
NARROW_WIRE_METALS: tuple[str, ...] = tuple(k for k, m in METALS.items() if m.narrow_wire_candidate)


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

    @property
    def drive_sensitivity(self) -> float:
        """``∂ln f / ∂ln I_Dsat = 1 − wire_share`` — what a drive improvement is still worth. **Exact.**

        The clock rate is ``f = 1/τ_total = I/(A + τ_wire·I)`` with ``A = C_load·V_dd`` (so
        ``τ_gate = A/I``). Differentiating, ``∂ln f/∂ln I = 1 − τ_wire/(τ_gate + τ_wire) = 1 −
        wire_share`` — **exact at every ``I_Dsat``**, not a small-signal linearization, and structurally
        prefactor-free (every house constant enters only through ``wire_share``, which is a *readout*,
        not a claim).

        This is the law the binning consumer turns into money, and the sharpest form of the
        discriminator. Under the pre-1997 premise (``speed ∝ I_Dsat``, which
        :class:`fab_game.spec.SpeedBin` still encodes) this sensitivity is **1**: a 3%-faster transistor
        is a 3%-faster part. Here it is ``1 − wire_share``, because ``τ_wire`` is a **common-mode**
        additive floor — it shifts every die's delay by the same amount and contributes **no spread of
        its own**. So the across-wafer ``I_Dsat`` spread maps to a speed spread damped by exactly this
        factor while the transistor histogram is *untouched*, and as ``wire_share → 1`` it → **0**:
        **tightening CD control stops buying speed grades.**

        Note the damping is **symmetric** — it compresses the *whole* speed distribution toward typical,
        pulling the slow tail up exactly as it pulls the fast tail down. The wire costs the **premium
        grade** (the margin), not the die count: this is a *grading* loss, never a yield loss.
        """
        return 1.0 - self.wire_share


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
    ``C_load``, the aspect ratio and the Elmore factor. **Argument order is the trap: the CHALLENGER goes
    first**, since ``ratio(a, b)`` is ``W_x(a)/W_x(b)`` and a value **< 1 means ``a`` is the better wire**.
    ``crossover_width_ratio("Cu", "Al")`` = **0.796** — copper pushes the crossover ~20% further down in
    linewidth before the wire takes over. Spelling it the other way round and reciprocating gives the same
    number here and the *reciprocal* for a metal that loses, which is how slice 3 first shipped silver as
    a negative (see :mod:`chip.demo_beol_history`).

    **Read the size of that win in node units, and do not round it up.** A technology node is a **0.7×**
    linear step, so 0.796× is ``ln(0.796)/ln(0.7)`` = **0.64 of a node** — the celebrated 1997 escape
    bought about *two-thirds of one generation*, not "roughly one node" (which this docstring claimed
    until slice 3 did the arithmetic). Overstating a win is the one direction this module never rounds,
    exactly as F3's ``floor_decades`` refuses it in the leakage currency. What is honest — and unlike the
    absolute crossover width, free of every house constant — is that copper **shifted the line without
    bending it**: ``W_x ∝ √ρ₀`` is the same √ for every metal, so a *second* node would need ``ρ`` halved
    again to ~0.82 µΩ·cm, and no elemental conductor is there (silver, the best there is, is 1.59). The
    bulk-``ρ₀`` **axis** is exhausted — which is precisely why slice 4 changes axis rather than shopping
    for a better conductor.
    """
    return math.sqrt(wire_delay_ratio(metal_a, metal_b))


# --------------------------------------------------------------------------- #
# 6. The narrow-wire era (slice 4) — the size effect, the barrier, and the metal that wins by losing
# --------------------------------------------------------------------------- #
# Everything below is about a DIFFERENT crossing from section 5's. Section 5's crossover_* pair is the
# gate↔wire crossing (a linewidth at which two DELAY TERMS are equal); these are metal↔metal equal
# RESISTANCE (a linewidth at which two METALS are equal). Same units, unrelated statements — hence the
# deliberately different name. Conflating them is the same collision class as Die.tau (the carrier
# lifetime) vs the F4 delay, which slice 2 had to rename around.
def _narrow(metal: Metal | str) -> Metal:
    """Resolve a metal for a **narrow-wire** read, refusing one with no modelled narrow-wire case.

    The refusal is the point, not defensive coding: aluminium's ``ρ₀λ`` ≈ 58 screens *better* than
    copper's 65, and returning that comparison would be a claim this module cannot support — Al's real
    disqualifier is electromigration, a reliability currency it does not carry. See
    :data:`NARROW_WIRE_METALS` and the module docstring.
    """
    m = _resolve(metal)
    if m.barrier_nm is None:
        raise ValueError(
            f"{m.name!r} has no modelled narrow-wire case (barrier_nm is None), so the size-effect "
            f"reads refuse it. Aluminium is the live instance: its ρ₀λ ≈ "
            f"{m.rho0_lambda:.0f} µΩ·cm·nm would screen better than copper's "
            f"{METALS['Cu'].rho0_lambda:.0f}, but its disqualifier is electromigration — a reliability "
            f"currency this module does not carry. Narrow-wire metals: {NARROW_WIRE_METALS}."
        )
    return m


def conductor_floor_width_um(metal: Metal | str, *, barrier_nm: float | None = None) -> float:
    """``W = 2·t_b`` (µm) — the width at which the line is **all barrier and no conductor**.

    The hard geometric floor, and one of the module's two prefactor-free narrow-wire claims: a fixed
    barrier thickness eating a shrinking budget reaches zero conductor at twice the liner thickness —
    **4.0 nm** at the cited ``t_b`` = 2 nm, 6.0 nm at 3 nm — regardless of resistivity, length, aspect
    ratio or ``C``. This is F3's "``EOT > t_IL`` for any κ" in the wire's currency, and it sits *inside*
    the published roadmap rather than at some asymptote. Barrierless metals return 0.0: they have no floor.
    """
    m = _narrow(metal)
    t_b = m.barrier_nm if barrier_nm is None else barrier_nm
    if t_b < 0.0:
        raise ValueError(f"barrier_nm must be ≥ 0, got {t_b}")
    return 2.0 * t_b / _NM_PER_UM


def conductor_width_um(width_um: float, metal: Metal | str, *, barrier_nm: float | None = None) -> float:
    """``W_eff = W − 2·t_b`` (µm) — the conductor left once the barrier has taken its fixed cut.

    **Raises at or below the floor** (:func:`conductor_floor_width_um`) rather than returning zero or a
    negative width: below it the object being described does not exist, and extrapolating through would
    be F3's magnitude trap. The barrier is taken off the **width only** — a real damascene liner coats the
    trench bottom too, so this leaves copper *more* conductor than it has, which errs **against** the
    ruthenium conclusion (the direction is named in the module docstring).
    """
    if width_um <= 0.0:
        raise ValueError(f"width_um must be > 0, got {width_um}")
    floor_um = conductor_floor_width_um(metal, barrier_nm=barrier_nm)
    if width_um <= floor_um:
        raise ValueError(
            f"width_um = {width_um*_NM_PER_UM:.3g} nm is at or below the conductor floor "
            f"2·t_b = {floor_um*_NM_PER_UM:.3g} nm for {_resolve(metal).name!r}: the line is all barrier "
            f"and no conductor. There is no resistance to report, at any resistivity."
        )
    return width_um - floor_um


def effective_resistivity(metal: Metal | str, d_um: float, *, c: float = SIZE_EFFECT_C) -> float:
    """``ρ_eff = ρ₀·(1 + C·λ/d)`` (µΩ·cm) — the size effect, with ``d`` the **conducting** dimension.

    Below the mean free path, surface and grain-boundary scattering lift the resistivity without bound.
    Note the narrow limit: ``ρ_eff → C·ρ₀λ/d``, so the material enters **only** through the product
    ``ρ₀λ`` (:attr:`Metal.rho0_lambda`) — the cited screening figure of merit, and the reason *the metric
    that ranks metals at 3 nm is not the metric that ranked them at 250 nm*.

    ``d_um`` is the **conductor** width (i.e. after :func:`conductor_width_um`), not the drawn linewidth:
    the barrier both removes area and narrows what is left, and the second effect is real. It is a
    *width*, not a cross-section — the module docstring's fourth simplification, where that choice is
    priced and its direction (against the ruthenium conclusion) is checked rather than assumed.
    """
    m = _narrow(metal)
    if d_um <= 0.0:
        raise ValueError(f"d_um must be > 0, got {d_um}")
    if c < 0.0:
        raise ValueError(f"c must be ≥ 0, got {c}")
    return m.rho0_uohm_cm * (1.0 + c * m.mfp_nm / (d_um * _NM_PER_UM))


def narrow_line_resistance(
    metal: Metal | str,
    geometry: WireGeometry,
    *,
    c: float = SIZE_EFFECT_C,
    barrier_nm: float | None = None,
    size_effect: bool = True,
    barrier: bool = True,
) -> float:
    """The line resistance (Ω) with the size effect and the barrier — the narrow-wire path.

    ``R = ρ_eff(W_eff)·L/(W_eff·H)``. The two switches are not conveniences: they exist so that
    :func:`resistance_ratio` can walk the **three-rung ladder** that is this slice's whole argument
    (bulk → +size effect → +barrier), and so that a test can pin that *neither mechanism alone* flips the
    Cu→Ru sign. With both off this reduces exactly to :func:`wire_resistance` at the bulk ``ρ₀``.
    """
    m = _narrow(metal)
    w_eff = (conductor_width_um(geometry.width_um, m, barrier_nm=barrier_nm) if barrier
             else geometry.width_um)
    rho = effective_resistivity(m, w_eff, c=c) if size_effect else m.rho0_uohm_cm
    return wire_resistance(rho, geometry.length_um, w_eff, geometry.thickness_um)


def resistance_ratio(
    challenger: Metal | str,
    incumbent: Metal | str,
    width_um: float,
    *,
    c: float = SIZE_EFFECT_C,
    barrier_nm: float | None = None,
    size_effect: bool = True,
    barrier: bool = True,
) -> float:
    """``R(challenger)/R(incumbent)`` at a drawn linewidth — **prefactor-free**, and **< 1 is a win**.

    Length, thickness, aspect ratio, ``c_pul``, the Elmore factor, ``V_dd`` and ``C_load`` all cancel: at
    a common drawn ``W`` and a common ``H``, only the resistivities and the barrier-reduced widths
    survive. **The CHALLENGER goes first** — the same argument order as :func:`crossover_width_ratio`, and
    for the same reason: slice 3 shipped silver as a win-turned-loss from an incumbent-first call, and the
    reciprocal of a plausible number is another plausible number. Only the sign gives it away.

    **The three-rung ladder this exists to run** (Cu → Ru at a 12 nm line, cited constants plus the
    flagged ``C`` = 1 and ``t_b`` = 2 nm):

    ========================================  ======  ===================================================
    rung                                       ratio   what it says
    ========================================  ======  ===================================================
    ``size_effect=False, barrier=False``        4.23   bulk ``ρ`` alone: ruthenium is hopeless
    ``size_effect=True,  barrier=False``        1.90   the size effect closes most of it — still losing
    ``size_effect=False, barrier=True``         2.82   the barrier on bulk ``ρ``: also still losing
    ``size_effect=True,  barrier=True``         0.92   **both together: ruthenium wins**
    ========================================  ======  ===================================================

    That is the payload, and the two middle rows are why it cannot be shortened to one mechanism. See
    :func:`size_effect_ratio_limit` and :func:`barrier_only_flip_width_um` for the two closed forms that
    turn "still losing at 12 nm" into "can never win, at any manufacturable width", using cited constants
    only.
    """
    a, b = _narrow(challenger), _narrow(incumbent)
    geom = WireGeometry(length_um=1.0, width_um=width_um, thickness_um=1.0)   # L and H cancel exactly
    kw = dict(c=c, size_effect=size_effect, barrier=barrier)
    # A barrierless metal keeps its 0.0 under a barrier_nm sweep: the sweep is over the CITED Ta/TaN
    # range, which is a statement about copper's liner and says nothing about a metal that needs none.
    r_a = narrow_line_resistance(a, geom, barrier_nm=0.0 if a.barrier_nm == 0.0 else barrier_nm, **kw)
    r_b = narrow_line_resistance(b, geom, barrier_nm=0.0 if b.barrier_nm == 0.0 else barrier_nm, **kw)
    return r_a / r_b


def size_effect_ratio_limit(challenger: Metal | str, incumbent: Metal | str) -> float:
    """The ``W → 0`` limit of :func:`resistance_ratio` **with no barrier** — i.e. ``ρ₀λ(a)/ρ₀λ(b)``.

    **Impossibility result (a), and it needs no house constant at all:** with the barrier switched off,
    ``ρ_eff → C·ρ₀λ/d`` for both metals, ``C`` and ``d`` cancel, and the ratio asymptotes to the cited
    figure-of-merit ratio. For Cu → Ru that is **1.179**, and the approach is monotone from
    ``ρ₀(Ru)/ρ₀(Cu)`` = 4.23 above — so the ratio is **> 1 at every width**. The size effect alone can
    therefore **never** flip the sign: not at 20 nm, not at 2 nm, not in the limit. The cited FOM buys
    ruthenium *parity*, and parity is a necessary condition, never a sufficient one. "Ruthenium wins
    because its mean free path is short" is false — and this is the function that says so exactly rather
    than approximately.
    """
    a, b = _narrow(challenger), _narrow(incumbent)
    return a.rho0_lambda / b.rho0_lambda


def barrier_only_flip_width_um(
    challenger: Metal | str, incumbent: Metal | str, *, barrier_nm: float | None = None,
) -> float:
    """The width below which the **barrier alone, on bulk ``ρ``**, would flip the sign (µm).

    **Impossibility result (b), also cited-constants-only.** With no size effect, a barrierless challenger
    wins when ``ρ₀(a)/ρ₀(b)·(W − 2t_b)/W < 1``, i.e.

        ``W < 2·t_b / (1 − ρ₀(b)/ρ₀(a))``

    For Cu → Ru at the cited ``t_b`` = 2 nm that is **5.2 nm** — and copper's conductor floor
    (:func:`conductor_floor_width_um`) is **4.0 nm**. So the barrier acting on bulk resistivity opens a
    window barely **1.2 nm** wide, immediately above the width at which copper ceases to be a conductor at
    all. No fab has ever been there. Together with :func:`size_effect_ratio_limit` this closes the
    argument: **neither mechanism alone gets the sign right, at any manufacturable width** — the F3-IL
    structure, where the better barrier is still a pure loss until the other currency is counted too.

    Raises if the challenger's bulk ``ρ₀`` is not the *higher* one (there is then nothing to flip).
    """
    a, b = _narrow(challenger), _narrow(incumbent)
    if a.rho0_uohm_cm <= b.rho0_uohm_cm:
        raise ValueError(
            f"{a.name!r} already has the lower bulk ρ₀ ({a.rho0_uohm_cm} vs {b.rho0_uohm_cm}), so there "
            f"is no bulk-ρ deficit for a barrier to overcome — this read is for the sign-inverted case."
        )
    t_b = (b.barrier_nm if barrier_nm is None else barrier_nm) / _NM_PER_UM
    return 2.0 * t_b / (1.0 - b.rho0_uohm_cm / a.rho0_uohm_cm)


def equal_resistance_width_um(
    challenger: Metal | str,
    incumbent: Metal | str,
    *,
    c: float = SIZE_EFFECT_C,
    barrier_nm: float | None = None,
    search_max_um: float = 1.0,
) -> float:
    """The drawn linewidth at which the two metals have **equal resistance** (µm) — below it, ``a`` wins.

    Solved numerically on :func:`resistance_ratio`, and **deliberately not in closed form**: the tempting
    closed form uses the deep-limit ``ρ_eff → C·ρ₀λ/d`` for *both* metals and is **wrong here by a factor
    of four** (it puts Cu→Ru at ~50 nm against the full form's ~13). The reason is worth keeping: at the
    crossing, ruthenium is **not in its own deep limit** — ``C·λ/W`` ≈ 0.84, not ≫ 1 — because its short
    mean free path is exactly what keeps it near-bulk. **The cited ``ρ₀λ`` figure of merit ranks metals but
    does not locate the crossing**; its domain of validity does not contain the width where the sign
    flips. A test pins the disagreement so a later slice cannot "simplify" to the wrong one.

    **Report this as a band, never a point.** Over the *cited* ``t_b`` = 2–3 nm range it spans
    **12.9 → 17.1 nm**, and that spread is the finding rather than an error bar: where ruthenium wins is
    set by the thickness of the layer that stopped scaling. Over the flagged ``C`` ∈ [0.375, 2] it spans
    ~9.7–21.1 nm. The literature's crossing is <~20 nm; this band sits a node or two inside it, and both
    of the module's Ru-conservative simplifications push that way. A **consistency check on the constants**
    with the IBM ~40% check's status — not a prediction.
    """
    def f(w_um: float) -> float:
        return resistance_ratio(challenger, incumbent, w_um, c=c, barrier_nm=barrier_nm) - 1.0

    floor_um = conductor_floor_width_um(incumbent, barrier_nm=barrier_nm)
    lo = floor_um * 1.0001 + 1.0e-9
    hi = search_max_um
    if f(lo) >= 0.0 or f(hi) <= 0.0:
        raise ValueError(
            f"no equal-resistance width bracketed in ({lo*_NM_PER_UM:.3g}, {hi*_NM_PER_UM:.3g}) nm: the "
            f"ratio is {f(lo)+1.0:.3f} at the floor and {f(hi)+1.0:.3f} at the top of the search range."
        )
    for _ in range(200):                                   # bisection — the ratio is monotone in W here
        mid = 0.5 * (lo + hi)
        if f(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def equal_resistance_width_nm(
    challenger: Metal | str,
    incumbent: Metal | str,
    *,
    c: float = SIZE_EFFECT_C,
    barrier_nm: float | None = None,
) -> float:
    """:func:`equal_resistance_width_um` in **nm** — the display currency for a sub-50 nm claim.

    Mirrors the ``tau_total_s``/``tau_total_ps`` pair: µm is the module's length currency, nm is what a
    3 nm-node statement is legible in.
    """
    return equal_resistance_width_um(challenger, incumbent, c=c, barrier_nm=barrier_nm) * _NM_PER_UM
