"""Strained silicon — the one ``I_Dsat`` factor no process in this simulator had ever moved (F5).

The **backward axis** (``docs/plans/strained-silicon-f5.md``): every factor in

    ``I_Dsat = ½·µ·C_ox·(W/L)·(V_GS − V_t)²``

has been a *process outcome* here since Phase 4 — ``C_ox`` from the oxide furnace (P2) and then the
dielectric (F3), ``W/L`` from the litho CD (P3), ``V_t`` from channel doping (P1a), ``Q_ox`` (G4a) and the
adjust implant (F1) — **except ``µ``**, which has been the module constant
:data:`chip.device.MU_N_EFF` = 450 cm²/V·s, flagged "illustrative", since the day it was written. F5
makes the channel material itself a process outcome: strain is a **mechanical** state, not a chemical
one, so this is the first device number in the sim that moves without changing a dopant, a thickness or a
length. That is the observable the model could not previously produce.

What this module emits — an enhancement **factor**, not a mobility, and not a current
-------------------------------------------------------------------------------------
A mobility *enhancement factor* is a **material/carrier property**, and that is deliberate. The era's two
mechanisms want **opposite strain signs**, because electrons and holes respond to opposite stresses:
Intel's 90 nm node put **compressive** uniaxial strain into the pMOS channel (SiGe source/drain) and
**tensile** strain into the nMOS channel (a silicon-nitride capping layer). The simulator has only an
n-channel device (:mod:`chip.device` — "textbook long-channel n-MOSFET, p-type substrate"; there is no
polarity switch), so:

  * the registry is **carrier-generic** and carries **both** signs as cited data — the hole leg is honest
    material data that needs no p-MOSFET to exist;
  * the **wired** leg is the carrier the simulator has: :data:`TENSILE_CESL`, nMOS, tensile, +20% µ;
  * :func:`nmos_mobility` **refuses** the hole mechanism by name rather than returning a number for it.
    That refusal is load-bearing and is the era's actual teaching point — *the two carriers want opposite
    strain signs, which is why the strain era needed two different processes* (the structural analogue of
    :mod:`chip.interconnect` refusing aluminium on the narrow-wire axis).

No absolute mobility is emitted, and that is forced: ``MU_N_EFF`` is a **house lump** this module
inherits rather than fixes. A **ratio against it cancels the lump; an absolute µ does not.**

The magnitude trap — the model's µ→I elasticity is 1, and the source measures ≈0.5
-----------------------------------------------------------------------------------
:func:`chip.device.saturation_current` is **explicitly long-channel**, so it carries ``I ∝ µ``: an
elasticity of exactly **1** by construction (asserted in the tests against the real ``device.py``). The
90 nm strain-era device is **velocity-saturated** — ``I_Dsat ≈ W·C_ox·v_sat·(V_GS − V_t)``, and ``v_sat``
is nearly strain-independent — so the real elasticity is well under 1, and the cited source *measures* it
on both carriers:

===========  ==========================  ==========  =============  ==============
carrier      mechanism (Intel 90 nm)     mobility    drive current  **elasticity**
===========  ==========================  ==========  =============  ==============
holes        SiGe S/D, 17% Ge, compr.    **>50%**    **+25%**       **0.500**
electrons    tensile nitride cap         **+20%**    **+10%**       **0.500**
===========  ==========================  ==========  =============  ==============

so *"the long-channel read overstates the drive win by ~2× at 90 nm"* is **arithmetic on cited numbers**,
not an estimate this module has to defend (:func:`drive_overstatement`). **Read the 0.500-on-both as a
coincidence, not a law:** two different mechanisms landing on the same ratio is a numerical accident of
two rounded pairs, and the independent short-channel point below sits at **0.35**.

The elasticity is a **ratio of fractional gains**, ``(drive − 1)/(µ − 1)`` (:func:`elasticity`) — the
ratio of the *factors* (1.10/1.20 = 0.917) is not the quantity and would silently pass a wrong test.

**Therefore: headline the mobility, and label the drive read an upper bound.** There is deliberately
**no elasticity knob defaulting to 1** — that would be inflating an unrelated variable to buy back a
number the model has not earned. The bound is a *documented limit*, not a tunable, and it is enforced
where the claim is made: a test pins each registry entry's cited ``drive_factor`` against its cited
``mobility_factor``, so a later slice that starts treating the long-channel read as *the* drive result
confronts the ratio head-on.

The seam — and it predates the slice
-------------------------------------
``saturation_current(mos, V_GS, width_um, mu_eff=MU_N_EFF, R_series_ohm=0.0)`` has taken a **defaulted**
``mu_eff`` since P4. F5 does not add a seam; it *uses* one written before the slice existed. Passing
nothing → ``MU_N_EFF`` → **byte-for-byte** today's numbers; passing ``MU_N_EFF · factor`` → the strained
rung. **:mod:`chip.device` is untouched — the fourth consecutive slice** (F2 rode ``R_series_ohm``, F3 the
EOT identity, F4 read ``I_Dsat`` as a loose scalar).

**Multiply and pass — never rescale ``MU_N_EFF`` in place.** ``test_device.py`` recomputes
``β = ½·MU_N_EFF·C_ox·(W/L)`` by hand; mutating the constant would silently re-baseline that test instead
of failing it.

The honesty ladder (per the F5 plan + the ``historical-modes.md`` triad)
------------------------------------------------------------------------
* **Tight — the seam.** No mechanism ⇒ nothing multiplies: the unstrained factor is exactly ``1.0`` and
  ``mu_eff`` is never passed (:func:`strained_mobility` at ``mechanism=None`` is the identity).
* **Tight — the model's own elasticity is 1.** Long-channel ``I ∝ µ`` exactly, on the ideal-contact
  closed form. Asserted against the real :mod:`chip.device`, which is *why* the drive read is a bound.
  (It holds on the ``R_series_ohm = 0`` path only: source degeneration sub-linearizes µ→I on its own.)
* **Tight — the cited elasticity.** ``(drive−1)/(µ−1)`` = **0.500 exactly** on both carriers, from one
  paper. Hence :func:`drive_overstatement` = **2.0**: the model's ``I ∝ µ`` is twice the measured gain.
* **Cross-check (non-circular).** The cited drive-current enhancements are an **independent measured
  quantity this module does not compute** — the model has no route to them (it would need velocity
  saturation, which F5 does not build). They are the leg that bounds the model from *outside* it.
* **Flagged — the direction of the bound's looseness.** An independent short-geometry point
  (L = 25 nm, W = 77 nm): **100%** mobility enhancement → **35%** drive enhancement, i.e. elasticity
  **0.35** (:data:`SHORT_CHANNEL_CROSSCHECK`). The elasticity **falls as ``L`` shrinks** — strain
  increasingly acts through *injection velocity* rather than mobility in the quasi-ballistic regime — so
  the long-channel 1 is an upper bound **whose looseness grows** as the era advances.
* **Flagged — the hole leg's mobility is a floor.** The source says ">50%", so 1.50 is a **lower** bound
  on the numerator (never round a win up — F4's ``floor_decades`` rule in µ's currency), which makes the
  hole elasticity derived from it an **upper** bound. It points the same way as everything above.

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **Velocity saturation: NAMED, NOT BUILT.** It is the mechanism that makes the drive read a bound.
  Building it means replacing the long-channel ``I_Dsat`` — a *device-model* change, not a *process* one,
  and four consecutive slices have left :mod:`chip.device` alone.
* **A p-MOSFET: NOT BUILT.** The enhancement-factor design exists precisely so the hole leg needs none.
* **A stress → mobility physical model: NOT BUILT.** Deformation potentials, band warping, a GPa→µ curve.
  The sourced quantity is the **enhancement factor per cited mechanism**; a GPa figure for a given Ge% is
  **not** pinned at this project's sourcing bar, so this module carries **no stress field at all** rather
  than an invented one. ``ge_percent`` is cited *data* on the SiGe entry, not the input to a function.
* **Strain relaxation / misfit dislocations / SiGe critical thickness: NOT BUILT.** A yield and
  reliability currency, not a drive-current one (the same reason F4 kept electromigration out).
* **Vertical-field erosion: DELIBERATELY ABSENT, and the obvious caveat is the wrong one.** "Strain
  enhancement erodes at the high vertical fields scaled devices run at" is a **biaxial** result and does
  **not** transfer: the cited uniaxial S/D work states the hole-mobility enhancement *is present at large
  vertical electric fields in nanoscale transistors*. Both registry entries are **uniaxial**; carrying a
  field dependence the sources deny would be recalling instead of citing.
* **The dual stress liner** — compressive CESL over pMOS *and* tensile CESL over nMOS on the same die —
  is the generalization of the 2003 pair and a **named later rung**, not a registry entry here. What is
  built is the single 2003 tensile nitride cap.

Units — dimensionless factors in and out; mobilities in cm²/V·s only where a caller supplies the base
------------------------------------------------------------------------------------------------------
Enhancement factors are **dimensionless** (1.0 = unstrained). :func:`strained_mobility` takes the base
mobility as a **required** argument in cm²/V·s (the :mod:`chip.device` currency) and never defaults it:
a hole mechanism silently inheriting an *electron* surface mobility would be exactly the incoherent pair
:mod:`chip.high_k` refuses for (φ_B, m*). Ge content in **atomic %**.
"""
from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Carriers and strain signs — the fork this module exists to keep straight
# --------------------------------------------------------------------------- #
ELECTRONS = "electrons"                # the carrier chip.device has (n-channel)
HOLES = "holes"                        # cited data only — no p-MOSFET exists here

TENSILE = "tensile"                    # what electrons want
COMPRESSIVE = "compressive"            # what holes want

_CARRIERS = (ELECTRONS, HOLES)
_SIGNS = (TENSILE, COMPRESSIVE)


def elasticity(mobility_factor: float, drive_factor: float) -> float:
    """The µ→I **elasticity** ``(drive − 1)/(µ − 1)`` — a ratio of *fractional* gains, not of factors.

    How much of a mobility gain reaches the drive current. **The definition matters:** on the cited
    nMOS pair (1.20, 1.10) this is ``0.10/0.20`` = **0.500**, while the ratio of the factors themselves is
    ``1.10/1.20`` = 0.917 — a plausible-looking number that is not this quantity, and a test written on it
    would pass while asserting nothing.

    The long-channel model has elasticity **1** by construction (``I ∝ µ``); the cited 90 nm devices
    measure **0.5**; a cited 25 nm device measures **0.35** (:data:`SHORT_CHANNEL_CROSSCHECK`). Raises at
    ``mobility_factor == 1`` — no mobility gain, so there is no fraction of one to have reached the drive.
    """
    if mobility_factor <= 1.0:
        raise ValueError(
            f"elasticity is undefined without a mobility gain, got mobility_factor={mobility_factor} "
            "(it is the fraction of a gain that reaches the drive current)"
        )
    return (drive_factor - 1.0) / (mobility_factor - 1.0)


# --------------------------------------------------------------------------- #
# 1. The mechanism registry — cited factors, both signs, no stress field
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StrainMechanism:
    """A cited strain mechanism: which carrier it helps, which sign it needs, and what it measured.

    ``mobility_factor`` the cited **mobility** enhancement (1.20 = +20%) — *the headline*;
    ``drive_factor`` the cited **saturated drive-current** enhancement measured on the same devices, which
    this module does **not** compute and could not (see :attr:`cited_elasticity`); ``carrier`` and
    ``sign`` the fork; ``ge_percent`` cited composition where the source pins one, else ``None``.

    **Both factors are stored because the pair is the payload.** The mobility alone would let a reader
    take the long-channel ``I ∝ µ`` inference for a result; carrying the measured drive beside it makes
    the model's overstatement a computable number rather than a caveat in prose.

    **There is no stress field.** A GPa figure per Ge% is not sourced at this project's bar, and an empty
    or invented one is exactly how an unsourced number leaks back in — so it is absent, not ``None``.
    """

    name: str
    carrier: str
    sign: str
    mobility_factor: float
    drive_factor: float
    mechanism: str
    ge_percent: float | None = None
    mobility_is_floor: bool = False

    def __post_init__(self) -> None:
        if self.carrier not in _CARRIERS:
            raise ValueError(f"carrier must be one of {_CARRIERS}, got {self.carrier!r}")
        if self.sign not in _SIGNS:
            raise ValueError(f"sign must be one of {_SIGNS}, got {self.sign!r}")
        if self.mobility_factor <= 1.0:
            raise ValueError(f"mobility_factor must be > 1 (1.0 = unstrained), got {self.mobility_factor}")
        if self.drive_factor <= 1.0:
            raise ValueError(f"drive_factor must be > 1 (1.0 = unstrained), got {self.drive_factor}")
        if self.ge_percent is not None and not 0.0 < self.ge_percent < 100.0:
            raise ValueError(f"ge_percent must be in (0, 100) or None, got {self.ge_percent}")

    @property
    def mobility_gain(self) -> float:
        """The fractional mobility gain, ``µ_factor − 1`` (0.20 = +20%)."""
        return self.mobility_factor - 1.0

    @property
    def drive_gain(self) -> float:
        """The **cited** fractional drive-current gain, ``I_factor − 1`` (0.10 = +10%)."""
        return self.drive_factor - 1.0

    @property
    def cited_elasticity(self) -> float:
        """This mechanism's **measured** µ→I elasticity — :func:`elasticity` on its own cited pair.

        **0.500 on both cited mechanisms**, which is the coincidence the module docstring says to report
        as a coincidence. It is an *independent* number: nothing here computes it, because computing it
        would take the velocity saturation F5 names and does not build.
        """
        return elasticity(self.mobility_factor, self.drive_factor)

    @property
    def long_channel_drive_factor(self) -> float:
        """What :func:`chip.device.saturation_current` **infers**: ``I ∝ µ``, so the drive factor *is* µ's.

        Elasticity 1 by construction — the long-channel form has no other option. This is the number the
        wired path produces, and :attr:`drive_factor` is what the real devices did.
        """
        return self.mobility_factor

    @property
    def drive_overstatement(self) -> float:
        """How many times the long-channel read overstates the cited drive gain — ``1/elasticity``.

        **2.0 on both cited mechanisms.** The honest way to read a wired ``I_Dsat``: an **upper bound**,
        loose by about this factor at 90 nm and looser as ``L`` shrinks
        (:data:`SHORT_CHANNEL_CROSSCHECK`).
        """
        return self.mobility_gain / self.drive_gain

    @property
    def wired(self) -> bool:
        """Whether the simulator has a device this mechanism can drive (i.e. it is an **electron** leg)."""
        return self.carrier == ELECTRONS


# --- Cited constants -------------------------------------------------------- #
# BOTH legs come from ONE source: the Intel 90 nm logic technology (IEDM 2003 and the associated uniaxial
# strain papers) — which is why the unwired hole leg is sourced no worse than the wired electron one.
#
# CITED: SiGe source/drain selective epitaxy, 17% Ge → longitudinal UNIAXIAL COMPRESSIVE channel stress →
# hole mobility >50% and saturated pMOS drive +25% (record 700 µA/µm at high V_t / 800 µA/µm at low V_t,
# 1.2 V) · a tensile silicon-nitride capping layer → UNIAXIAL TENSILE strain in the nMOS → electron
# mobility +20% and nMOS drive +10% · the hole enhancement PERSISTS at large vertical fields (so the
# biaxial erosion caveat is not imported — see the module docstring).
#
# NOT CITED, therefore ABSENT: the channel stress in GPa for a given Ge%, and whether mobility vs Ge% is
# linear over the useful range. No stress field exists on StrainMechanism for that reason.
TENSILE_CESL = StrainMechanism(
    name="tensile nitride capping layer (nMOS, 2003)",
    carrier=ELECTRONS,
    sign=TENSILE,
    mobility_factor=1.20,               # CITED — +20% electron mobility
    drive_factor=1.10,                  # CITED — +10% saturated nMOS drive current
    mechanism=(
        "A high-tensile silicon-nitride film deposited over the finished nMOS transistor puts the channel "
        "into uniaxial tensile strain. This is the 2003 single-cap process; the later DUAL STRESS LINER "
        "(compressive CESL over pMOS, tensile over nMOS on the same die) generalizes it and is a NAMED "
        "later rung, not built here."
    ),
)

# The hole leg — cited data, no p-MOSFET required, and DELIBERATELY not wired (see nmos_mobility).
# mobility_is_floor: the source says ">50%", so 1.50 is a LOWER bound on the numerator (never round a win
# up), which makes the elasticity derived from it an UPPER bound — the same direction as every other
# flag here.
SIGE_SD = StrainMechanism(
    name="SiGe source/drain (pMOS, 2003)",
    carrier=HOLES,
    sign=COMPRESSIVE,
    mobility_factor=1.50,               # CITED — ">50%" hole mobility, stored as the floor it is
    drive_factor=1.25,                  # CITED — +25% saturated pMOS drive current
    mechanism=(
        "Selective epitaxial SiGe grown in etched source/drain recesses. The larger Ge lattice constant "
        "compresses the channel longitudinally — uniaxial COMPRESSIVE strain, the opposite sign to the "
        "nMOS cap, because holes and electrons respond to opposite stresses."
    ),
    ge_percent=17.0,                    # CITED — 17% Ge in the source/drain
    mobility_is_floor=True,
)

MECHANISMS: dict[str, StrainMechanism] = {"tensile_cesl": TENSILE_CESL, "sige_sd": SIGE_SD}

# The mechanisms the simulator can actually WIRE — derived from the registry, never hand-maintained, so a
# hole mechanism can never silently appear here and an electron one can never silently go missing (the
# NARROW_WIRE_METALS pattern). This is the carrier fork made mechanical: chip.device is n-channel-only.
WIRED_MECHANISMS: tuple[str, ...] = tuple(k for k, m in MECHANISMS.items() if m.wired)

# --- The independent short-channel cross-check (the bound's DIRECTION) ------- #
# CITED, and from a different source than the 90 nm pair: at L = 25 nm / W = 77 nm, a 100% long-and-wide
# mobility enhancement yields a 35% saturation drive enhancement — elasticity 0.35, well below the 90 nm
# 0.50. The µ→I elasticity FALLS with L (strain acting increasingly through injection velocity in the
# quasi-ballistic regime), so the long-channel elasticity of 1 is an upper bound whose looseness GROWS as
# the era advances. Named, not built — this is data about the bound, not a mechanism, so it is not in
# MECHANISMS.
SHORT_CHANNEL_L_NM = 25.0               # nm — the cited geometry's channel length
SHORT_CHANNEL_W_NM = 77.0               # nm — and its width
SHORT_CHANNEL_MOBILITY_FACTOR = 2.00    # CITED — 100% mobility enhancement (long/wide)
SHORT_CHANNEL_DRIVE_FACTOR = 1.35       # CITED — 35% saturation drive enhancement at that geometry
SHORT_CHANNEL_CROSSCHECK = elasticity(SHORT_CHANNEL_MOBILITY_FACTOR, SHORT_CHANNEL_DRIVE_FACTOR)  # 0.35


def _resolve(mechanism: StrainMechanism | str) -> StrainMechanism:
    """Registry key → :class:`StrainMechanism` (or pass one straight through)."""
    return MECHANISMS[mechanism] if isinstance(mechanism, str) else mechanism


# --------------------------------------------------------------------------- #
# 2. The factor a consumer multiplies by — and the seam at "no strain"
# --------------------------------------------------------------------------- #
def mobility_factor(mechanism: StrainMechanism | str | None) -> float:
    """The dimensionless mobility enhancement factor — **``1.0`` when there is no strain (the seam)**.

    ``None`` returns exactly ``1.0``, so a consumer that multiplies unconditionally still reproduces
    today's numbers **byte-for-byte** (``MU_N_EFF · 1.0 == MU_N_EFF``, and the F5 game knob's ``None``
    path skips passing ``mu_eff`` at all).
    """
    return 1.0 if mechanism is None else _resolve(mechanism).mobility_factor


def strained_mobility(mu_base_cm2_Vs: float, mechanism: StrainMechanism | str | None) -> float:
    """``µ_base · factor`` (cm²/V·s) — the number to **pass** to :func:`chip.device.saturation_current`.

    ``mu_base_cm2_Vs`` is **required and positional on purpose**: this module is carrier-generic, and a
    hole mechanism silently defaulting to :data:`chip.device.MU_N_EFF` — an *electron* surface mobility —
    would be the incoherent pair :mod:`chip.high_k` refuses for (φ_B, m*). The caller owns the base.

    **Multiply and pass; never write the result back.** ``mu_eff`` is a read-time argument, exactly as F2
    passed ``R_series_ohm`` and F3 passed an EOT — :data:`chip.device.MU_N_EFF` is not mutated (a
    hand-computed ``β`` in the device tests would be silently re-baselined rather than fail).
    """
    if mu_base_cm2_Vs <= 0.0:
        raise ValueError(f"mu_base_cm2_Vs must be positive, got {mu_base_cm2_Vs}")
    return mu_base_cm2_Vs * mobility_factor(mechanism)


def nmos_mobility(mu_base_cm2_Vs: float, mechanism: StrainMechanism | str | None) -> float:
    """:func:`strained_mobility` for the **n-channel** device — and it **refuses** a hole mechanism.

    The refusal is the point, not a guard rail. :mod:`chip.device` is n-channel-only, and the strain era's
    two mechanisms want **opposite signs**: applying the SiGe source/drain's *compressive* strain to an
    electron channel would degrade it, not enhance it, so returning ``1.50`` for it would invert the
    physics while looking like a result. The simulator has no pMOS to be right about, so this raises
    instead — the mirror of :mod:`chip.interconnect` refusing aluminium on the narrow-wire axis.

    ``None`` passes straight through to the seam (``µ_base`` unchanged).
    """
    if mechanism is not None:
        mech = _resolve(mechanism)
        if not mech.wired:
            raise ValueError(
                f"{mech.name} strains the channel {mech.sign}ly to help {mech.carrier} — it is a pMOS "
                f"technique, and chip.device is n-channel-only, so its factor would have the WRONG SIGN "
                f"on an electron channel. That the two carriers need opposite strain is the era's point, "
                f"not an oversight: the strain era needed two different processes. Wired mechanisms: "
                f"{WIRED_MECHANISMS}."
            )
    return strained_mobility(mu_base_cm2_Vs, mechanism)


def drive_overstatement(mechanism: StrainMechanism | str) -> float:
    """How many times a long-channel ``I_Dsat`` read overstates this mechanism's **cited** drive gain.

    ``µ_gain / drive_gain`` = ``1/elasticity`` — **2.0** on both cited mechanisms. Module-level mirror of
    :attr:`StrainMechanism.drive_overstatement`, so the bound is reachable without unpacking the record.
    """
    return _resolve(mechanism).drive_overstatement


# --------------------------------------------------------------------------- #
# 3. The bundled reading (the record a demo or the game knob reports)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StrainedChannel:
    """A strained channel as read: the mobility it buys, and **both** drive currencies side by side.

    ``mu_unstrained_cm2_Vs``/``mu_strained_cm2_Vs`` the base and its enhancement;
    ``drive_factor_long_channel`` what :func:`chip.device.saturation_current` will infer (== the mobility
    factor, elasticity 1); ``drive_factor_cited`` what the real devices measured. **The two drive numbers
    sit in the same record on purpose** — the wired path *is* the optimistic one, so the only place the
    bound can live is beside it. Plain scalars: the loose-coupling currency.

    ``cited_elasticity``/``drive_overstatement`` are **``None`` at the seam**, not ``1.0``: with no
    mobility gain there is no fraction of one to have reached the drive current (:func:`elasticity`
    raises on exactly that input), and a fake ``1.0`` would read as "the model is exact here" — the
    gap-vs-fake-value rule (:attr:`chip.interconnect.Metal.barrier_nm`).
    """

    mechanism: str
    carrier: str
    sign: str
    mu_unstrained_cm2_Vs: float
    mu_strained_cm2_Vs: float
    mobility_factor: float
    drive_factor_long_channel: float
    drive_factor_cited: float
    cited_elasticity: float | None
    drive_overstatement: float | None
    mobility_is_floor: bool = False

    @property
    def is_strained(self) -> bool:
        """Whether any strain was applied — ``False`` is the seam (every factor exactly ``1.0``)."""
        return self.mobility_factor != 1.0


def strained_channel(
    mu_base_cm2_Vs: float, mechanism: StrainMechanism | str | None, *, nmos: bool = True,
) -> StrainedChannel:
    """Read a strained channel — the demo's and the game knob's unit of comparison.

    ``nmos=True`` (the default, and the simulator's only device) routes through :func:`nmos_mobility`, so
    a hole mechanism **raises** rather than returning an inverted-sign number. ``nmos=False`` reads the
    hole leg as the cited *material* data it is — no p-MOSFET is implied and no current is computed.

    ``mechanism=None`` is **the seam**: every factor is exactly ``1.0`` and ``mu_strained`` is
    ``mu_base``, byte-for-byte.
    """
    if mechanism is None:
        if mu_base_cm2_Vs <= 0.0:
            raise ValueError(f"mu_base_cm2_Vs must be positive, got {mu_base_cm2_Vs}")
        return StrainedChannel(
            mechanism="", carrier="", sign="",
            mu_unstrained_cm2_Vs=mu_base_cm2_Vs, mu_strained_cm2_Vs=mu_base_cm2_Vs,
            mobility_factor=1.0, drive_factor_long_channel=1.0, drive_factor_cited=1.0,
            cited_elasticity=None, drive_overstatement=None,
        )
    mech = _resolve(mechanism)
    mu = nmos_mobility(mu_base_cm2_Vs, mech) if nmos else strained_mobility(mu_base_cm2_Vs, mech)
    return StrainedChannel(
        mechanism=mech.name, carrier=mech.carrier, sign=mech.sign,
        mu_unstrained_cm2_Vs=mu_base_cm2_Vs, mu_strained_cm2_Vs=mu,
        mobility_factor=mech.mobility_factor,
        drive_factor_long_channel=mech.long_channel_drive_factor,
        drive_factor_cited=mech.drive_factor,
        cited_elasticity=mech.cited_elasticity,
        drive_overstatement=mech.drive_overstatement,
        mobility_is_floor=mech.mobility_is_floor,
    )
