"""Device targets — "good is application-relative": re-score the *same* wafer against multiple specs.

Today every wafer is judged against **one** notion of "good" (``DEFAULT_SPECS`` — a fast-logic MOSFET:
tight low-ish ``V_t``, high drive, thin oxide). This module adds the central DTCO lesson
(``docs/plans/device-targets.md``, slice 1): the *same* physical property that ruins a part for one product
is a *feature* for another. A high ``V_t`` is slow logic (reject) but a low-leakage low-power part
(premium); the *same* drifted wafer can be the wrong SKU for one target and the right SKU for its sibling.

Slice 1 was the **zero-new-physics spine** (``fast-logic`` ↔ ``low-power``): it added no device output, only
**grading** — a finished wafer's already-computed dies re-scored against a different :class:`DeviceTarget`'s
windows + bins (:func:`regrade`), never re-fabricated. **Slice 2 adds the ``hv-io`` flavor** and, with it,
the slice's *one* cited device output — the drain–body junction **avalanche breakdown** ``BV``
(:mod:`chip.breakdown`, computed in the device step, scored by the new optional ``bv`` spec window). The
grading machinery here is unchanged; what is new is that one target (HV-I/O) now reads an axis the logic
flavors leave open.

**Slice 3 adds the high-resistivity ``high-res`` native part** (:data:`HIGH_RES`, the slice-3 section below)
— and, again, **zero new physics**: it turns ``BV``'s *other* knob, the **substrate doping** itself
(``BV ∝ N_B^(−3/4)``, set at growth), where slice 2 turned the junction depth. The finding that shapes it
(verified on the line, mirroring slice 2's): in this single-doping model the substrate doping moves ``BV``
and ``V_t`` with **opposite signs, coupled** — so a light enough substrate to give a real high ``BV``
craters ``V_t`` below every logic window. The resolution is that the high-``BV`` part is the **native**
low-``V_t`` device (the MOSFET *without* a threshold implant) — the coupling *is* the inversion, a crossing
on **both** axes at once. Because the substrate is **committed at growth**, the high-res part is its own
declared run (a second up-front commitment alongside the device family — :attr:`DeviceTarget.substrate`),
**not** a same-wafer disposition sibling of the low-R flavors.

Why HV-I/O is its own slice (the junction-DEPTH axis — advisor 2026-06-15)
--------------------------------------------------------------------------
``BV`` depends on the junction **depth** ``x_j`` (cylindrical-edge field crowding — a shallow junction breaks
down early) as well as the body doping. Depth is set by the diffusion **drive-in**, and — crucially — it is
**independent of ``V_t``** (which reads N_A + t_ox, never x_j): two wafers with identical ``V_t`` but
different drive-in have different ``BV``. So HV-I/O is *not* a relabel of the thick-oxide low-power corner —
it adds a genuinely orthogonal acceptance axis (the BV floor), gated by a process knob the logic flavors
never had to care about. (Slice 3 will turn the *other* BV knob — a high-resistivity substrate, ``BV ∝
N_A^(−3/4)`` — for a genuine high-voltage part; here the BV floor is calibrated to the depth-reachable band
at the nominal substrate.)

The two-level declaration (the design's backbone, ``docs/plans/device-targets.md`` §"the real-world line")
----------------------------------------------------------------------------------------------------------
1. **Device family** — the mask / structure, **committed up front, never salvaged across.** A logic wafer is
   not a power rectifier; the mask set commits the device from lithography on. (The power-device family is a
   later slice — its own declared run, never a harvest of a logic wafer.)
2. **Flavor within a family** — ``fast-logic`` ↔ ``low-power`` ↔ ``hv-io`` share a base flow and differ only
   by where their windows sit (oxide / junction depth — *not* the mask). An off-target lot **can** be
   dispositioned to a sibling flavor (real *engineering disposition* / material-review-board: "use-as-is or
   re-grade rather than scrap"). This is where "harvest the tail" honestly lives, and it is what
   :func:`disposition` surfaces.

:data:`MOSFET_FLAVORS` is that one family's flavor set; re-grading **across** families is *not* offered (it
is not real). The dollar amounts and the window bands are **flagged house numbers** (ADR 0005 §5) — the
tests assert the *mechanics* (the windows genuinely **cross**; a declaration **moves** the recipe optimum;
the disposition bookkeeping closes), never the magnitudes.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .scoring import BIN_PRICES, WAFER_COST, ScoreCard, score_wafer
from .spec import DEFAULT_SPECS, SpecSet, SpecWindow, SpeedBin, SpeedBins
from .state import Die, Verdict, WaferState

# --------------------------------------------------------------------------- #
# The market — the multi-grade speed bins parts are graded into (FLAGGED house numbers).
# Positioned around the nominal fast-logic I_Dsat (~3.30 mA → typical); a thinned-oxide / short-channel
# wafer drives I_Dsat up into premium, a slow part down into value. The value floor sits at the front-end
# I_Dsat spec floor (2.8 mA), so a working fast-logic part is always sellable. (Lived in game.py through G7;
# moved here so a DeviceTarget can own its bins without a game↔targets import cycle.)
# --------------------------------------------------------------------------- #
MARKET_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.55),               # fast parts (a thinned-oxide / short-channel wafer)
    SpeedBin("typical", lo_mA=3.15, hi_mA=3.55),   # the nominal grade
    SpeedBin("value", lo_mA=2.80, hi_mA=3.15),     # slow but sellable (down to the I_Dsat spec floor)
))


@dataclass(frozen=True)
class DeviceTarget:
    """A named product target — a spec window set (with its speed bins) + a price curve + an optimum hint.

    A *target* is one notion of "good": its :attr:`specs` carries the per-die acceptance windows **and** the
    final-test speed bins (``specs.speed_bins``), and :attr:`prices` is the per-bin revenue curve. Two
    targets of the **same device family** differ only by where their windows sit — the *same* wafer scores
    differently against each (the "good is relative" lesson). :attr:`optimum_hint` is human guidance (which
    knob direction this target rewards) for the educational guide / disposition readout; it is **not** read
    by any scoring path (the optimum is proven empirically, not declared — see the slice-1 gates).

    :attr:`structure` (slice 5) names the **device family** — the mask / structure, the *first* level of the
    two-level declaration (``"mosfet"`` / ``"rectifier"``). It is committed up front at lithography and is
    **never salvaged across**: a MOSFET wafer is not a power diode, so :func:`disposition` is *within one
    device family* (a different family is its own declared run, never a harvest). The MOSFET flavors and the
    high-res native part are all ``"mosfet"``; the slice-5 power rectifier (:data:`POWER_RECTIFIER`) is the
    ``"rectifier"`` family. Defaults to ``"mosfet"`` (the incumbent), so the slice-1/2/3 targets are unchanged.

    :attr:`substrate` (slice 3) names the **substrate-resistivity class** the target is grown on
    (``"low-res"`` / ``"high-res"``). Unlike a flavor (oxide / junction depth — set *after* the substrate),
    the substrate resistivity is **committed at growth** (the boule): you cannot re-grade a finished wafer
    across substrate classes (a low-R logic wafer is not a high-res part), so it is a **second up-front
    commitment** alongside the device family — :func:`disposition` is *within one substrate class*. The
    low-R class is the dispositionable MOSFET family (:data:`MOSFET_FLAVORS`); the high-res class holds two
    *different-family* declared runs that share the light boule — the high-res native MOSFET
    (:data:`HIGH_RES`, slice 3) and the power rectifier (:data:`POWER_RECTIFIER`, slice 5) — so the
    :attr:`structure` guard, not the substrate one, is what keeps *those* two apart. Defaults to
    ``"low-res"`` (the incumbent), so the slice-1/2 flavors are unchanged.

    All numbers are flagged house values (ADR 0005 §5): only the *relationships* between targets (the
    windows cross; the optimum moves) carry meaning, never the bands or the dollars.
    """

    name: str
    specs: SpecSet
    prices: dict[str, float]
    optimum_hint: str = ""
    substrate: str = "low-res"   # slice-3 substrate-resistivity class — committed at growth (see above)
    structure: str = "mosfet"    # slice-5 device family — mask/structure, committed up front (see above)


# --------------------------------------------------------------------------- #
# The MOSFET family's flavors — same mask/structure, dispositionable between (FLAGGED bands + prices).
# The windows deliberately **cross** (the slice-1 gate): logic V_t [0.45, 0.68], low-power V_t [0.60, 0.85]
# overlap only on [0.60, 0.68]. A V_t = 0.50 wafer is logic-good / low-power-reject (too low → leaky for a
# mobile part); a V_t = 0.75 wafer is low-power-premium / logic-reject (too slow). The non-V_t windows
# (CD/NILS) and the I_Dsat ceiling are held common so V_t is the *sole* discriminator on the crossing axis;
# low-power lowers only the I_Dsat *floor* (a thick-oxide low-power part runs at lower drive — a feature,
# not a fail), so the V_t-band thick-oxide / deep-cut parts land in a sellable low-power bin, not a bin-out.
# --------------------------------------------------------------------------- #
FAST_LOGIC = DeviceTarget(
    name="fast-logic",
    specs=replace(DEFAULT_SPECS, speed_bins=MARKET_BINS),   # == today's specs (the seam: declaring this
    #                                                          reproduces the pre-targets game bit-for-bit)
    prices=BIN_PRICES,
    optimum_hint="thin gate oxide + shallow cut → low V_t, high drive (fast switching)",
    substrate="low-res",     # the incumbent low-resistivity (~1e17) logic substrate
)

# Low-power speed bins — positioned BELOW the fast-logic market: a low-power part trades drive for a high,
# low-leakage V_t, so its grades sit at lower I_Dsat (floor 2.0 mA, well under the thick-oxide drive) and a
# V_t-band part is always sellable. Same labels as the fast-logic market (so the price-curve keys match),
# different thresholds. FLAGGED.
LOW_POWER_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=2.70),               # the cleanest low-power parts
    SpeedBin("typical", lo_mA=2.40, hi_mA=2.70),
    SpeedBin("value", lo_mA=2.00, hi_mA=2.40),     # slow but sellable (down to the low-power I_Dsat floor)
))
LOW_POWER_PRICES: dict[str, float] = {              # FLAGGED house $ — only the ordering + bookkeeping matter
    "premium": 9.0,
    "typical": 6.0,
    "value": 3.0,
    "reject": 0.0,
}
LOW_POWER = DeviceTarget(
    name="low-power",
    specs=replace(
        DEFAULT_SPECS,
        v_t=SpecWindow("V_t (V)", lo=0.60, hi=0.85),        # crosses fast-logic's [0.45, 0.68]
        i_dsat_mA=SpecWindow("I_Dsat (mA)", lo=2.0, hi=4.2),  # lower FLOOR only (low drive is a feature)
        speed_bins=LOW_POWER_BINS,
    ),
    prices=LOW_POWER_PRICES,
    optimum_hint="thick gate oxide + deeper cut → high V_t, low leakage (the fast-logic reject corner)",
    substrate="low-res",     # same low-R logic substrate as fast-logic (dispositionable sibling)
)

# --------------------------------------------------------------------------- #
# The HV-I/O flavor (device-targets slice 2) — the junction-DEPTH axis, gated on avalanche breakdown.
# The third MOSFET flavor: an I/O-tolerant part that must survive a high reverse voltage on its drain–body
# junction, so it carries a **BV floor** (:func:`chip.breakdown.junction_breakdown`) the logic flavors do
# not. The slice-2 point (advisor): BV depends on the junction **depth** ``x_j`` (curvature crowding) — a
# *separate* axis from ``V_t`` (which reads N_A + t_ox, never x_j) — so two wafers with identical ``V_t``
# (same substrate + oxide) but different drive-in have different BV. That decoupling is why HV-I/O earns its
# own slice: the diffusion **drive-in** (deeper junction → higher BV), inert for the logic flavors, becomes
# the lever that makes a part HV-sellable. HV-I/O is the **highest-V_t** flavor (thickest I/O gate oxide),
# its V_t window crossing low-power's from *above* (un-nesting — advisor): a V_t over low-power's ceiling is
# HV-good / low-power-reject, a thinner-oxide low-power part is low-power-good / HV-reject (V_t too low),
# and — the new axis — a shallow-junction part is HV-reject on BV whatever its V_t. The BV floor (6 V) sits
# in the drive-in-reachable band at the nominal ~1e17 substrate (a shallow junction ≈ 5 V, a deep one ≈ 7 V);
# a genuine high-voltage part needs the lighter substrate of slice 3 (BV ∝ N_A^(−3/4)). All bands/prices
# FLAGGED — only the crossing + the BV-decoupling carry meaning.
# --------------------------------------------------------------------------- #
HV_IO_BV_FLOOR_V = 6.0              # FLAGGED house BV floor: above a shallow-junction part (~5 V at 1e17),
#                                    below a deep-junction one (~7 V) → a deliberate deep drive-in clears it
HV_IO_BINS = SpeedBins(bins=(       # HV runs at low drive (thick oxide); binned by I_Dsat like the others,
    SpeedBin("premium", lo_mA=2.35),                # positioned at the thick-oxide HV operating current
    SpeedBin("typical", lo_mA=2.10, hi_mA=2.35),
    SpeedBin("value", lo_mA=1.50, hi_mA=2.10),      # slow but sellable (down to the HV I_Dsat floor)
))
HV_IO_PRICES: dict[str, float] = {  # FLAGGED — STRICTLY ABOVE low-power at every bin: an I/O-tolerant part
    "premium": 14.0,                # commands a premium, so when a deep junction makes HV *available* it
    "typical": 10.0,               # out-revenues low-power on the SAME wafer → the gate-2 optimum flips to HV
    "value": 5.0,
    "reject": 0.0,
}
HV_IO = DeviceTarget(
    name="hv-io",
    specs=replace(
        DEFAULT_SPECS,
        v_t=SpecWindow("V_t (V)", lo=0.72, hi=1.10),         # highest-V_t flavor; crosses low-power [0.60,0.85]
        #                                                      from above (overlap [0.72,0.85]; disjoint from
        #                                                      fast-logic's [0.45,0.68])
        i_dsat_mA=SpecWindow("I_Dsat (mA)", lo=1.5, hi=4.2),  # low drive is fine (an I/O part, not a fast one)
        bv=SpecWindow("BV (V)", lo=HV_IO_BV_FLOOR_V, optional=True),  # THE new axis: the avalanche-breakdown
        #                                                              floor (optional → a die never scored
        #                                                              for BV is skipped, like leakage)
        speed_bins=HV_IO_BINS,
    ),
    prices=HV_IO_PRICES,
    optimum_hint="thick I/O gate oxide (high V_t) + DEEP S/D junction (long drive-in → high breakdown voltage)",
    substrate="low-res",     # still the low-R substrate: S2's BV comes from the DEEP junction, not the substrate
)

# The MOSFET family's dispositionable flavor set (fast-logic declared by default, the incumbent first). A
# lot may re-grade between these (same mask, same low-R substrate); it may NOT re-grade to a different
# *family* (a power rectifier) — that is a later slice's own declared run, never a harvest of a logic
# wafer — NOR across the substrate-resistivity class (the high-res native part below, slice 3, is grown
# on a different boule). All three share ``substrate="low-res"`` (the disposition substrate-class guard).
MOSFET_FLAVORS: tuple[DeviceTarget, ...] = (FAST_LOGIC, LOW_POWER, HV_IO)


# --------------------------------------------------------------------------- #
# The high-resistivity NATIVE part (device-targets slice 3) — the SUBSTRATE-resistivity axis.
# --------------------------------------------------------------------------- #
# Slice 3 turns ``BV``'s *other* knob — the body doping ``N_B`` itself (``BV ∝ N_B^(−3/4)``, the lighter
# substrate) — for a genuinely high-breakdown part, where slice 2 turned the junction **depth** ``x_j`` on
# the fixed ~1e17 substrate (a modest ~5–9 V). THE structural finding (advisor, verified on the line —
# mirrors slice 2's "x_j decouples BV from V_t"): in this single-doping compact model the substrate doping
# sets **both** ``BV`` *and* ``V_t``, and it moves them with **opposite signs, coupled** — lowering ``N_A``
# raises ``BV`` (good) and *craters* ``V_t`` together (1e17→1e16: BV ~5→12 V, V_t +0.55→+0.01 V; I_Dsat is
# ``N_A``-independent, so V_t and BV are the *only* axes that move). So a light enough substrate to give a
# real high ``BV`` puts ``V_t`` far below **every** logic-family window — substrate resistivity **cannot**
# give slice 2's high-``V_t`` hv-io its breakdown (that is exactly why x_j was slice 2's lever: it raises
# ``BV`` *without* touching ``V_t``).
#
# THE RESOLUTION (zero new physics — the coupling *is* the inversion): the high-``BV`` part does not have to
# be high-``V_t``. A high-resistivity substrate naturally runs a **native** device — the MOSFET *without* a
# threshold-adjust implant — at a low / near-zero ``V_t`` and a high junction breakdown (the real RF / analog
# / high-voltage-I/O use of high-res substrates). That native low-``V_t`` part is the *simpler, more
# physical* object, not a workaround: its low ``V_t`` (a logic **reject**) is the **feature**, and its high
# ``BV`` is unreachable on the logic substrate — a genuine "good is relative" crossing on **both** axes at
# once, with **no** physics added. (The ambitious alternative — a high-``V_t`` HV part on a light substrate
# via a channel/drift threshold-adjust implant, i.e. LDMOS — is a **named deferred edge**: in the as-built
# model an implant lifts ``V_t`` but never ``I_Dsat``, so high-res+implant would *strictly dominate* logic
# and the crossing would dissolve; rescuing it needs added mobility degradation = more physics, past this
# slice's size. Deferred like the 2-D / heat-mode edges — A2 Robin-G, E1 heat-mode, CG-3 transient.)
#
# THE SUBSTRATE COMMIT (advisor): resistivity is committed at **growth** (the boule), so this is **not** a
# same-wafer disposition sibling of the low-R flavors — it is its **own declared run** (you grow the light
# substrate up front), closer to slice 5's power rectifier than to slice 1/2's disposition menu. The physics
# enforces it: a low-R wafer re-graded to high-res yields ~0 % (V_t too high *and* BV unreachable) and a
# high-res wafer re-graded to logic yields ~0 % (V_t too low) — mutual rejection. The ``substrate`` tag +
# the :func:`disposition` substrate-class guard make that boundary explicit (you cannot mix substrate
# classes in one disposition menu).
#
# All bands/prices FLAGGED (ADR 0005 §5) — only the relationships carry meaning: the V_t windows are
# **disjoint** (logic [0.45,0.68] vs native [−0.15,0.35]) and the BV floor sits **above the low-R plane-
# parallel ceiling** (BV_pp(1e17) ≈ 9.3 V), so it is **physically unreachable** on the logic substrate by
# *any* drive-in and only the lighter boule (BV ≈ 12 V at 1e16) clears it.
HIGH_RES_BV_FLOOR_V = 10.0          # FLAGGED house BV floor: ABOVE the low-R ceiling BV_pp(1e17)≈9.3 V (so a
#                                     logic-substrate part can NEVER clear it) and below the high-res BV (≈12 V
#                                     at ~1e16) → the floor is a hard SUBSTRATE gate, not a tunable drive-in one
# The native part runs at the same thin gate oxide as logic, and ``I_Dsat`` is ``N_A``-independent (it reads
# C_ox·W/L·V_ov, never N_A), so its drive current is identical to fast-logic's — it bins on the *same*
# MARKET_BINS thresholds (the same drive-current grade), differing only in price (a specialty high-res part).
HIGH_RES_PRICES: dict[str, float] = {   # FLAGGED house $ — a specialty high-resistivity-substrate part
    "premium": 16.0,
    "typical": 11.0,
    "value": 6.0,
    "reject": 0.0,
}
HIGH_RES = DeviceTarget(
    name="high-res",
    specs=replace(
        DEFAULT_SPECS,
        v_t=SpecWindow("V_t (V)", lo=-0.15, hi=0.35),        # the NATIVE low-V_t band — DISJOINT from logic's
        #                                                      [0.45,0.68] (the low V_t is the feature, not a fail)
        i_dsat_mA=SpecWindow("I_Dsat (mA)", lo=2.0, hi=4.2),  # same thin-oxide drive as logic (N_A-independent)
        bv=SpecWindow("BV (V)", lo=HIGH_RES_BV_FLOOR_V, optional=False),  # the floor unreachable on the low-R
        #   substrate → only the light boule clears it. REQUIRED (not optional, unlike HV-I/O): breakdown is
        #   this SKU's *defining* property, and — unlike HV-I/O, whose high V_t window independently rejects a
        #   stray die — the native low-V_t window does NOT protect it, so a die with NO breakdown reading
        #   (bv_V=None, an unresolved junction) must FAIL high-res, not ship unrated (the advisor's S3 catch;
        #   the mirror of S2's nan-guard). Not reachable on the line today (the S/D always resolves), a guard.
        speed_bins=MARKET_BINS,                              # same drive-current grade as logic (see above)
    ),
    prices=HIGH_RES_PRICES,
    optimum_hint="grow a HIGH-resistivity (light) substrate → low native V_t (no threshold implant) + a high "
                 "junction breakdown — its own declared run, not a disposition of a low-R logic wafer",
    substrate="high-res",
)

# The high-resistivity substrate class — its own declared run (one native part), NOT a disposition sibling of
# the low-R MOSFET family. A menu of one (unlike MOSFET_FLAVORS) reinforces that high-res is *declared up
# front*, not harvested off a finished low-R lot. Re-grading across the two families is blocked by the
# :func:`disposition` substrate-class guard (and the physics already yields ~0 % across substrates).
HIGH_RES_FAMILY: tuple[DeviceTarget, ...] = (HIGH_RES,)


# --------------------------------------------------------------------------- #
# The power-rectifier family (device-targets slice 5) — the LIFETIME axis: short τ = fast switching.
# --------------------------------------------------------------------------- #
# The richest, last inversion. G4b's deep-level metals (Fe/Cu) destroy minority-carrier lifetime ``τ`` and,
# through it, the junction reverse **leakage** ``J_gen ∝ 1/τ`` — *the* device killer for a logic part. The
# power rectifier reads the **same ``τ`` in the opposite direction**: its reverse-recovery time ``t_rr ∝ τ``
# (:func:`chip.reverse_recovery.reverse_recovery_time`, the charge-control storage time), so a **short** ``τ``
# — a leaky, low-lifetime wafer that ruins logic — is exactly what makes a **fast** rectifier. The lifetime
# killer is the feature. (Real fast/soft-recovery rectifiers are made this way: gold/platinum doping or
# electron irradiation *deliberately* kills lifetime to speed switching — Sze, Baliga.)
#
# THE two-level declaration (the slice-5 backbone). The rectifier is a **different DEVICE FAMILY** — a
# vertical p-n diode, not a MOSFET — so it is committed up front at the mask and is **never** a disposition
# of a logic wafer (``docs/plans/device-targets.md`` §"the real-world line": reassigning a finished MOSFET
# wafer to a power rectifier is NOT real). It is its **own declared run** (like the high-res native part), and
# the new :attr:`DeviceTarget.structure` tag + the :func:`disposition` family guard enforce it: even though
# the rectifier *shares the light high-res substrate* with the native MOSFET (a power device needs the lighter
# boule for blocking voltage — its ``BV`` floor sits above the low-R ceiling, the same hard substrate gate
# slice 3 proved), the two are different families and cannot be re-graded across.
#
# THE inversion axis is LIFETIME, not the substrate (advisor discipline — keep slices' axes distinct). On the
# *same* high-res substrate the native MOSFET wants a **long** ``τ`` (clean feed, low leakage) and the
# rectifier a **short** ``τ`` (a metal-laden feed, fast ``t_rr``) — so a single feed-grade sweep flips the
# best SKU (gate 1, the τ cross), and declaring the rectifier moves the **purification** optimum dirty where
# the native part wants it clean (gate 2). The metals are Na-/dopant-clean, so they move ``τ`` (→ leakage,
# → ``t_rr``) **without** touching ``V_t``/``BV`` — a clean single-axis cross.
#
# THE leakage inversion (the lesson, made literal). The rectifier's leakage window is **OPEN**: the very
# reverse leakage that a short ``τ`` forces — and that *fails* a logic part — is **not an acceptance axis**
# for the rectifier. Its only parametric gates are ``t_rr`` (REQUIRED ceiling: fast enough) and ``BV``
# (REQUIRED floor: blocks enough); ``V_t``/``I_Dsat``/CD/NILS are open (a diode has no gate channel). The
# functional gates (resolve / void / bridge / defect / geometry) still apply — the wafer must physically fab.
# (A real rectifier still carries a finite, much-higher leakage rating, and a current/t_rr performance grade
# — both named scope edges; here the defining cross is ``t_rr``, so leakage is simply not its gate and the
# part takes a single ``"pass"`` bin.)
#
# All bands/prices FLAGGED (ADR 0005 §5) — only the relationships carry meaning: the τ windows cross (the
# rectifier's t_rr ceiling demands a τ a logic leakage spec forbids, and vice-versa) and the declaration
# moves the purification optimum.
POWER_T_RR_CEILING_NS = 500.0       # FLAGGED house t_rr ceiling: above a lifetime-killed (metal-feed) wafer
#                                     (~100 ns) and far below a clean float-zone diode (~7e5 ns at τ_bulk) →
#                                     only a short-τ (dirty / un-gettered) feed clears it — the τ gate
POWER_PRICES: dict[str, float] = {  # FLAGGED house $ — a specialty power-rectifier part (single "pass" bin)
    "pass": 12.0,
    "reject": 0.0,
}
POWER_RECTIFIER = DeviceTarget(
    name="power-rectifier",
    specs=SpecSet(
        # The MOSFET parametrics are OPEN — a diode has no gate channel (V_t/I_Dsat) and is not gated on the
        # gate-line printability margin (CD/NILS); the functional resolve gate still requires a printed wafer.
        cd_nm=SpecWindow("CD (nm)", optional=True),
        i_dsat_mA=SpecWindow("I_Dsat (mA)", optional=True),
        v_t=SpecWindow("V_t (V)", optional=True),
        nils=SpecWindow("NILS", optional=True),
        # The leakage INVERSION: open. The reverse leakage a short τ forces is tolerated, not a reject axis.
        leakage=SpecWindow("leakage (nA/cm²)", optional=True),
        # BV REQUIRED — the blocking-voltage floor (same light-substrate gate as the high-res native part:
        # above the low-R plane-parallel ceiling, so unreachable on a logic wafer → the rectifier needs the
        # light boule). REQUIRED, like the native part's BV: breakdown is a defining property of a power part.
        bv=SpecWindow("BV (V)", lo=HIGH_RES_BV_FLOOR_V, optional=False),
        # t_rr REQUIRED — the defining axis: fast enough reverse recovery (short τ). REQUIRED, so a die with
        # no t_rr reading (an unresolved junction → no τ) fails rather than ships unrated (the advisor's S3
        # pattern, the mirror of S2's nan-guard) — not reachable on the line today (the device always sets τ
        # when it resolves), a guard.
        t_rr_ns=SpecWindow("t_rr (ns)", hi=POWER_T_RR_CEILING_NS, optional=False),
        speed_bins=SpeedBins(),     # single open "pass" bin — no t_rr/current performance grade (a named edge)
    ),
    prices=POWER_PRICES,
    optimum_hint="grow a LIGHT (high-res) substrate for blocking voltage + run a lifetime-KILLED (metal-laden / "
                 "un-gettered) feed for a SHORT carrier lifetime → fast reverse recovery — its own declared "
                 "run, never a disposition of a logic wafer (the lifetime killer is the feature)",
    substrate="high-res",       # shares the light boule with the native MOSFET (for BV) — structure tells them apart
    structure="rectifier",      # the DIFFERENT device family — committed at the mask, never salvaged across
)

# The power-device family — its own declared run (one rectifier), a different FAMILY from every MOSFET. Like
# HIGH_RES_FAMILY it is a menu of one (declared up front, not harvested); re-grading to/from any MOSFET is
# blocked by the :func:`disposition` family guard (different :attr:`DeviceTarget.structure`), even though the
# rectifier shares the high-res *substrate* with the native MOSFET (the family guard, not the substrate one).
POWER_FAMILY: tuple[DeviceTarget, ...] = (POWER_RECTIFIER,)


# --------------------------------------------------------------------------- #
# Re-grading — score a FINISHED wafer against a different target (zero new physics)
# --------------------------------------------------------------------------- #
def _regrade_die(die: Die, target: DeviceTarget, geometry_reason: str | None) -> Die:
    """Re-grade one finished die against ``target`` — its physics is fixed; only the windows/bins change.

    Mirrors the pipeline's front-end verdict (:meth:`SpecSet.verdict`) **then** the back-end packaging
    (:func:`fab_game.steps.packaging_step`) — but reads the die's **already-computed** parameters
    (``V_t``/``I_Dsat``/CD/NILS/leakage) and its **irreversible** back-end state, never re-running a step:

    * A functional kill (particle / unresolved / void / bridge / geometry) and the parametric windows are
      re-evaluated by ``target.specs.verdict`` — so a die's *parametric* verdict is genuinely target-relative
      (the whole point), while a physical functional kill stays dead under every target (it short-circuits).
    * An **assembly scrap** (``assembled is False`` — a cracked/lifted-bond die) is irreversible: it stays
      dead under every target (re-grading cannot un-crack a die).
    * A die that the *declared* target front-end-failed (so it never reached assembly, ``assembled is None``)
      but **passes** this sibling's front end is treated as having **survived** assembly. This is **exact**
      at the default lossless back end (``assembly_yield = 1`` ⇒ every front-end-good die assembles); only a
      deliberately-lossy back end (the G6 demo corner) would have drawn it a survival it never made — a real
      but legitimately deferred edge (re-drawing here would add RNG, breaking "zero new physics").
    * A surviving part is re-binned by ``target.specs.speed_bins`` on its ``I_Dsat``; a part below the
      slowest sellable bin is a **bin-out** (a working but out-of-grade reject, ``verdict`` flips to fail).

    The append-only history gains one ``disposition`` record (the ``WaferState`` discipline). The new
    ``verdict``/``bin`` are what :func:`fab_game.scoring.score_wafer` reads to price the re-graded wafer.
    """
    knobs_in = {"target": target.name}
    verdict = target.specs.verdict(die, geometry_reason)
    if verdict.failed:                                       # front-end fail under this target — not shipped
        return die.record("disposition", knobs_in, {"target": target.name, "passed": False, "bin": None},
                          verdict=verdict, bin=None)
    if die.assembled is False:                              # irreversible assembly scrap — dead everywhere
        v = Verdict(False, ("assembly scrap — back-end functional kill (cracked die = scrap, irreversible)",))
        return die.record("disposition", knobs_in, {"target": target.name, "assembled": False},
                          verdict=v, bin=None)
    label = target.specs.speed_bins.assign(die.i_dsat_mA)   # re-bin the (would-)survived part
    if target.specs.speed_bins.is_reject(label):
        v = Verdict(False, (f"binned out — I_Dsat {die.i_dsat_mA:.2f} mA below {target.name}'s slowest "
                            f"sellable bin (a working but out-of-grade part)",))
        return die.record("disposition", knobs_in, {"target": target.name, "bin": label}, verdict=v, bin=label)
    return die.record("disposition", knobs_in, {"target": target.name, "passed": True, "bin": label},
                      verdict=verdict, bin=label)


def regrade(wafer: WaferState, target: DeviceTarget) -> WaferState:
    """Re-grade a **finished** wafer against ``target`` → a new :class:`WaferState` (zero new physics).

    The wafer is *physically fixed* — every die keeps its computed ``V_t``/``I_Dsat``/CD/leakage and its
    irreversible back-end state. Only the **grading** changes: each die is re-scored against ``target``'s
    windows + speed bins (:func:`_regrade_die`). This is the "same wafer, different spec" core of "good is
    relative" — the wafer is never re-fabricated (re-running the line would shift the assembly RNG order and
    change *physics-irrelevant* outcomes). Score the result with ``target.prices`` (see :func:`grade_for`).
    """
    geometry_reason = target.specs.geometry.check(wafer.geometry)
    dies = tuple(_regrade_die(d, target, geometry_reason) for d in wafer.dies)
    return replace(wafer, dies=dies)


def grade_for(wafer: WaferState, target: DeviceTarget, *, wafer_cost: float = WAFER_COST) -> ScoreCard:
    """Re-grade ``wafer`` against ``target`` and score it with ``target``'s price curve → a :class:`ScoreCard`.

    ``wafer_cost`` is the **already-sunk** fab cost (the same for every target — the wafer is built once), so
    across a disposition menu only the **revenue** differs; the cost is carried only so ``profit`` closes.
    """
    return score_wafer(regrade(wafer, target), prices=target.prices, wafer_cost=wafer_cost)


# --------------------------------------------------------------------------- #
# Disposition — the "which SKU?" readout over a finished, possibly off-target wafer
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TargetGrade:
    """How a finished wafer grades against one :class:`DeviceTarget` — the target + its :class:`ScoreCard`."""

    target: DeviceTarget
    scorecard: ScoreCard

    @property
    def revenue(self) -> float:
        return self.scorecard.revenue

    @property
    def yield_(self) -> float:
        return self.scorecard.yield_

    @property
    def line(self) -> str:
        """A one-line human readout — ``"<target>: <yield> yield, $<revenue> (<bin mix>)"``."""
        mix = ", ".join(f"{n}×{lbl}" for lbl, n in self.scorecard.bin_counts.items()) or "nothing sellable"
        return f"{self.target.name}: {self.yield_:.0%} yield, ${self.revenue:.0f} ({mix})"


def disposition(
    wafer: WaferState,
    targets: tuple[DeviceTarget, ...] = MOSFET_FLAVORS,
    *,
    wafer_cost: float = WAFER_COST,
) -> tuple[TargetGrade, ...]:
    """Grade a finished wafer against every flavor in the family, **best revenue first** — the SKU menu.

    The disposition readout: a lot that drifted off its declared target is re-scored against its sibling
    flavors (whole-wafer — the honest re-grade unit, not die-cherry-picking across products), and the player
    picks the SKU. Ranked by **revenue** (the fab cost is sunk and identical across targets, so revenue is
    the live lever); ties keep the input order (the declared flavor listed first, so an on-target lot reads
    naturally). Returns one :class:`TargetGrade` per target — ``result[0]`` is the best SKU for this wafer.

    **Family guard (slice 5) + substrate-class guard (slice 3).** Disposition is **within one device family
    *and* one substrate class** — the two up-front commitments the two-level declaration makes. The
    **family** (:attr:`DeviceTarget.structure`) is the mask/structure, committed at lithography: a MOSFET
    wafer is not a power rectifier, so they are never re-graded across (the rectifier is its own declared run,
    not a harvest). The **substrate** (:attr:`DeviceTarget.substrate`) is committed at growth: a low-R logic
    wafer is not a high-res part. A menu mixing either is a misconfiguration → raises (like the recipe's
    two-``G`` / over-and-under-etch guards). The family guard is the binding one for the high-res native
    MOSFET vs the power rectifier — they *share* the light substrate but are different families.
    """
    structures = {t.structure for t in targets}
    if len(structures) > 1:
        raise ValueError(
            "disposition is within ONE device family — the structure/mask is committed up front at "
            f"lithography, so a finished wafer cannot be re-graded across device families (got {sorted(structures)}). "
            "A power rectifier is its own declared run, not a disposition of a MOSFET wafer.")
    substrates = {t.substrate for t in targets}
    if len(substrates) > 1:
        raise ValueError(
            "disposition is within ONE substrate-resistivity class — the substrate is committed at growth "
            f"(the boule), so a finished wafer cannot be re-graded across substrates (got {sorted(substrates)}). "
            "A high-res native part is its own declared run, not a disposition of a low-R logic wafer.")
    grades = tuple(TargetGrade(t, grade_for(wafer, t, wafer_cost=wafer_cost)) for t in targets)
    return tuple(sorted(grades, key=lambda g: g.revenue, reverse=True))
