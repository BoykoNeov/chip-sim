"""Silicon purification: zone-refining segregation + the contamination consequence vector (front-of-line).

The first step of the fab line proper (plan §5 step 1, §5a, §7; ADR 0005) and the physics the
fab-line game's **G4** consumes to make "badly purified feedstock" a *device* consequence. Two parts,
laddered honestly per the plan's fidelity ladder — the segregation math is the **tight, verifiable**
leg; the metal/ion device-degradation magnitudes are **calibrated/loose**, flagged:

1. **Zone-refining purification — the Pfann single-pass closed form (the cited triad core).** A molten
   *zone* of length ``L`` swept once along a solid ingot purifies by the same ``k < 1`` segregation
   that drives Czochralski (:mod:`chip.czochralski`): the freezing interface rejects solute back into
   the zone, so the solid left behind near the **start** of the sweep is depleted. With ``u = x/L`` the
   position in **zone-lengths** from the start and a uniform initial concentration ``C_0`` (Pfann)::

       C(u) = C_0·[1 − (1 − k)·e^(−k·u)]                              (cm⁻³)

   At the start ``C(0) = k·C_0`` (the **scrubbing identity** — the leading solid gets only fraction
   ``k`` of the charge); the zone then enriches as it sweeps, ``C(u) → C_0`` as ``u → ∞`` (steady
   state: solid frozen at ``C_0`` == liquid drawn in). The contrast that makes refining *work* is read
   straight off the cited ``k`` table: a **tiny-k metal** (Fe ``k ≈ 8e-6``) is scrubbed ~5 orders at
   the leading end in one pass, while **boron** (``k ≈ 0.8``) is barely touched — so segregation
   refining cleans metals superbly but cannot purify the dopants. The usable (purified) ingot length
   scales as ``~L/k``, so the smaller ``k``, the longer the clean region.

2. **The contamination consequence vector (Tier 1, the wiring — flagged where calibrated).** A
   feedstock grade (MGS / solar / EGS, :data:`FEEDSTOCK_GRADES`) is a starting **impurity vector**
   (:class:`Contamination`, species → cm⁻³); zone refining scrubs each species by *its* ``k``. Only
   the impurities whose **device receiving variable already exists** propagate to a number today
   (plan §5a "the crux — propagation is gated by the receiving variable, not the engine"):

   * **mobile-ion sodium** ``Na`` → **gate-oxide charge** ``Q_ox`` → a flat-band/``V_t`` shift
     (:func:`sodium_oxide_charge`; lifts :mod:`chip.device`'s named ``Q_ox = 0`` edge);
   * **residual shallow dopant** ``B`` / ``P`` → **net channel doping** (:attr:`Contamination.net_doping_shift`,
     free — same units as ``N_A``).

   **Deep-level metals** (``Fe`` / ``Cu``) ride along in the vector and are *scrubbed* by refining, but
   their device consequence — an **SRH recombination centre** (minority-carrier lifetime, junction
   leakage) — needs a device output net doping cannot carry: the **named G4b gap** (a future
   ``lifetime.py``, plan §5a Tier 2). They are tracked now so the state does not guess that API later.

The Siemens chlorosilane distillation route is a different domain (separations, weak device coupling) —
modelled as a **grade knob**, not a column sim (plan §5a). Gettering / precipitation / oxide breakdown
stay named **Tier-3** edges.

Validation triad (plan §7) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight) — the ``k→1`` no-purification limit + the exact scrubbing identity.** At
  ``k = 1`` the profile collapses to the constant ``C(u) ≡ C_0`` (no segregation) **bit-for-bit**
  (``(1 − k) = 0`` exactly); and ``C(0) = k·C_0`` (the leading-solid scrubbing fraction) + the
  steady-state ``C(u) → C_0`` are asserted. The ``k→1`` bit-exactness mirrors Czochralski's seed seam.
* **Conservation (tight, *reframed*) — the swept-out solute, NOT a recovered dose.** Unlike Scheil
  (``∫₀¹ C_s = C_0`` recovers the whole charge), the single-pass Pfann formula describes **only the
  swept region** — the solute depleted from the leading end is carried in the zone and piled into the
  **final zone-length** (a normal-freeze pile-up this closed form does *not* model). So ``∫ C du``
  over the swept ingot falls **short** of ``C_0·u`` by exactly the closed-form deficit
  ``∫₀^u (C_0 − C) du' = (C_0/k)·(1 − k)·(1 − e^(−k·u))`` (:func:`pfann_swept_solute`) — the solute the
  zone has carried toward the tail. That closed form vs direct quadrature is the conservation
  (machinery) check; "mass recovers ``C_0``" is **not** claimed (the end-zone pile-up is the named edge).
* **Benchmark (loose) — the cited Trumbore ``k`` + the feedstock-grade contrast.** The segregation
  coefficients are the canonical **Trumbore (1960, BSTJ 39:205)** values **reused** from
  :mod:`chip.czochralski` (:data:`~chip.czochralski.SEGREGATION_K` — same equilibrium melt↔crystal
  data, *not* duplicated; ``Na`` added there as another illustrative strong segregator). The
  feedstock-grade impurity vectors (:data:`FEEDSTOCK_GRADES`) and the ``Na → Q_ox`` incorporation
  length are **flagged illustrative house numbers** (ADR 0005 §5: the game is scored on mechanics, not
  magnitudes); the tight leg is the segregation math, not a contamination magnitude.

Named scope edge (the honest ceiling)
-------------------------------------
* **Single-pass front model.** The cited closed form is the *single* sweep. Multi-pass refining
  (:func:`zone_refine` with ``n_passes > 1``) is modelled as the **leading-end front tracking**
  ``C_front/C_0 = k^n`` — *exact at ``n = 1``* (``= k·C_0``), a **flagged approximation** for ``n > 1``
  (the rigorous multi-pass *ultimate distribution*, Lord/Reiss, is not built). The end-zone pile-up
  and the ``k_eff(v)`` growth-rate/stirring dependence (Burton–Prim–Slichter) are the same named edges
  as Czochralski's.
* **Calibrated consequence magnitudes.** ``Na → Q_ox`` rides a **flagged** bulk→areal incorporation
  length (:data:`NA_OXIDE_INCORPORATION_CM`); the deep-level-metal consequence (SRH lifetime / leakage)
  is **not** modelled at all (the G4b gap) — metals are scrubbed and carried, not yet consequential.
  Oxygen → thermal donors stays the separate, contested-``k`` deferral (Czochralski's scope edge).
* **Full activation / uniform contamination.** The impurity vector is a wafer-level scalar per species
  (uniform across the die map — it composes orthogonally with the boule axial story, like
  Czochralski's ``slice_z``); within-wafer contamination non-uniformity is out.

Units — semiconductor-conventional CGS (as :mod:`chip.czochralski` / :mod:`chip.device`)
---------------------------------------------------------------------------------------
Position ``u = x/L`` dimensionless (zone-lengths); concentration in **cm⁻³**; the swept-solute integral
in **cm⁻³·(zone-length)** (``L = 1`` units); oxide charge ``Q_ox`` in **C/cm²** (the unit
:mod:`chip.device`'s flat-band term reads); the incorporation length in **cm**.

Validation boundary
-------------------
No shared engine — the Pfann profile is a closed form (like Deal–Grove / Scheil / the compact ``V_t``),
so this module's tests carry the whole triad: the ``k→1`` + scrubbing-identity + steady-state limits
(analytic), the swept-solute closed-form vs quadrature (conservation), and the cited Trumbore ``k`` +
the flagged grade contrast (benchmark). The ``k`` values are reused from the cited
:mod:`chip.czochralski` table, **not** re-pinned here.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np

from .czochralski import SEGREGATION_K, segregation_coefficient
from .junction import Q_ELEMENTARY

# --------------------------------------------------------------------------- #
# 1. The Pfann single-pass zone-refining profile + its swept-solute integral
# --------------------------------------------------------------------------- #
def pfann_profile(zones, C0: float, k: float):
    """Pfann single-pass profile ``C(u) = C_0·[1 − (1−k)·e^(−k·u)]`` (cm⁻³), ``u = x/L`` zone-lengths.

    ``zones`` (``u = x/L ≥ 0``, the distance swept in zone-lengths) scalar or array; ``C_0`` the
    uniform initial concentration (cm⁻³); ``k`` the segregation coefficient. Returns the **leading-end**
    scrubbing value ``k·C_0`` at ``u = 0``, rises monotonically toward ``C_0`` for ``k < 1``
    (steady state as ``u → ∞``), and is the constant ``C_0`` **bit-for-bit** for ``k = 1`` (no
    purification — ``(1−k) = 0`` exactly). The deficit from ``C_0`` is the solute the zone sweeps
    toward the tail (:func:`pfann_swept_solute`).
    """
    zones = np.asarray(zones, dtype=float)
    if np.any(zones < 0.0):
        raise ValueError("zones (x/L, zone-lengths swept) must be ≥ 0")
    out = C0 * (1.0 - (1.0 - k) * np.exp(-k * zones))
    return float(out) if out.ndim == 0 else out


def pfann_swept_solute(zones, C0: float, k: float):
    """Cumulative swept-out solute ``∫₀^u (C_0 − C) du' = (C_0/k)·(1−k)·(1 − e^(−k·u))`` (cm⁻³·L units).

    The closed-form antiderivative of ``C_0 − C(u)`` and the **conservation (machinery) leg**: it is the
    solute the molten zone has carried toward the tail by position ``u`` (the depletion of the leading,
    purified region). Checked against direct quadrature of ``C_0 − C`` (:func:`pfann_profile`). Note this
    is **not** a recovered-dose identity (the single-pass formula omits the final-zone pile-up — the
    named scope edge): ``∫ C du`` over the swept ingot is short of ``C_0·u`` by exactly this deficit.
    As ``u → ∞`` it → ``(C_0/k)·(1−k)`` (all the swept region's removable solute, now in the end zone).
    """
    zones = np.asarray(zones, dtype=float)
    out = (C0 / k) * (1.0 - k) * (1.0 - np.exp(-k * zones))
    return float(out) if out.ndim == 0 else out


def front_purity(k: float, n_passes: int = 1) -> float:
    """Leading-end purity fraction ``C_front/C_0`` after ``n_passes`` zone passes — ``k`` for one pass.

    The single-pass leading-solid value is ``C(0)/C_0 = k`` (exact, from :func:`pfann_profile`). Multiple
    passes are modelled as the **front-tracking** approximation ``k^n`` (each pass re-scrubs the already-
    graded leading end by ``k``): *exact at* ``n = 1``, **flagged** for ``n > 1`` (the rigorous
    multi-pass ultimate distribution is the named scope edge). ``n_passes = 0`` → ``1.0`` (no refining).
    """
    if n_passes < 0:
        raise ValueError(f"n_passes must be ≥ 0, got {n_passes}")
    return float(k ** n_passes)


# --------------------------------------------------------------------------- #
# 2. The contamination vector — a feedstock/wafer impurity vector (the seam currency)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Contamination:
    """A feedstock/wafer impurity vector (bulk **cm⁻³**), species → concentration — the §3 contamination field.

    Carries the **full** impurity set so the wafer state need not guess the API as consequences land
    (the state.py "arrive with their named consumers" pattern). G4a wires only the consequences whose
    device receiving variable already exists:

    * ``Na`` (mobile ion) → gate-oxide charge ``Q_ox`` (:func:`sodium_oxide_charge`) — the headline,
      lifting :mod:`chip.device`'s ``Q_ox = 0`` named edge;
    * ``B`` / ``P`` (residual shallow dopant) → **net doping** (:attr:`net_doping_shift`, free).

    ``Fe`` / ``Cu`` (deep-level metals) ride along — *scrubbed* by refining but with **no device
    consequence yet**: their SRH lifetime / leakage effect is the named **G4b** gap (plan §5a Tier 2).
    All fields default to ``0.0`` → :attr:`is_clean` (the pristine baseline, the seam).
    """

    Na: float = 0.0      # mobile ion → gate-oxide charge Q_ox (Tier 1, headline)
    B: float = 0.0       # residual acceptor → net p-doping (Tier 1)
    P: float = 0.0       # residual donor → net n-doping (Tier 1)
    Fe: float = 0.0      # deep-level metal → SRH lifetime/leakage (G4b — rides along, no consequence yet)
    Cu: float = 0.0      # deep-level metal → SRH (G4b)

    def as_dict(self) -> dict[str, float]:
        """The impurity vector as ``{species: cm⁻³}`` (fixed field order)."""
        return {f.name: float(getattr(self, f.name)) for f in fields(self)}

    @property
    def is_clean(self) -> bool:
        """True if every species is zero — the pristine baseline (the seam: clean ⇒ no consequence)."""
        return all(v == 0.0 for v in self.as_dict().values())

    @property
    def net_doping_shift(self) -> float:
        """Net acceptor shift ``B − P`` (cm⁻³) the residual shallow dopant adds to the channel doping.

        Residual acceptor (``B``) raises the p-type channel doping (and ``V_t``); residual donor (``P``)
        lowers it. Added to ``N_A`` by the device consumer — free, since it is the same unit.
        """
        return self.B - self.P


def zone_refine(feed: Contamination, n_passes: int = 1) -> Contamination:
    """Zone-refine a feedstock impurity vector → the purified :class:`Contamination` at the leading end.

    Each species is scrubbed by **its own** cited segregation coefficient
    (:data:`~chip.czochralski.SEGREGATION_K`, reused — not duplicated): ``C_out = C_in·k^(n_passes)``
    (:func:`front_purity` — exact single-pass ``k·C_0`` at ``n_passes = 1``, the flagged front-tracking
    approximation beyond). The tiny-``k`` metals are scrubbed orders of magnitude while ``B`` (``k ≈ 0.8``)
    is barely touched — the segregation-purification contrast, straight from the ``k`` table. A clean
    feed (``0``) stays clean for any ``k``/``n`` (``0·k^n = 0`` — the seam). ``n_passes = 0`` is a no-op.
    """
    if n_passes < 0:
        raise ValueError(f"n_passes must be ≥ 0, got {n_passes}")
    return Contamination(**{
        species: conc * front_purity(segregation_coefficient(species), n_passes)
        for species, conc in feed.as_dict().items()
    })


# Feedstock grades → starting impurity vectors (cm⁻³) — FLAGGED illustrative house numbers, NOT cited
# fab data (ADR 0005 §5). The contrast is the teachable bit: a metallurgical-grade (MGS) feed is orders
# dirtier than electronic-grade (EGS); zone refining then scrubs the tiny-k metals superbly but leaves
# the dopants (and the device-poisoning Na) needing *enough* passes. "clean" is the idealized pristine
# baseline (all zero) — the seam default (a clean feed adds no contamination, so demo_device is exact).
# Residual shallow dopant (B/P) is kept small vs an intentional ~1e17 substrate (a real flow refines
# before growth) so the **mobile-ion Na → Q_ox → V_t** consequence is the dominant, edge-lifting story
# (the advisor's headline) rather than being masked by a net-doping shift; the metals are high so the
# scrubbing contrast (Fe scrubbed ~5 orders vs B barely) is stark.
FEEDSTOCK_GRADES: dict[str, Contamination] = {
    "clean": Contamination(),                                              # idealized — the seam baseline
    "EGS":   Contamination(Na=1.0e13, B=1.0e13, P=1.0e13, Fe=1.0e12, Cu=1.0e12),   # electronic-grade (clean)
    "solar": Contamination(Na=5.0e16, B=1.0e15, P=1.0e15, Fe=5.0e15, Cu=5.0e15),   # solar-grade (intermediate)
    "MGS":   Contamination(Na=1.0e18, B=1.0e16, P=5.0e15, Fe=1.0e18, Cu=5.0e17),   # metallurgical-grade (dirty)
}


# --------------------------------------------------------------------------- #
# 3. The contamination consequences (Tier 1) — the device receiving variables
# --------------------------------------------------------------------------- #
# Bulk Na (cm⁻³) → areal mobile-ion density in the gate oxide (cm⁻²): a FLAGGED house incorporation
# length (the fraction of bulk Na that reaches the oxide as mobile charge is a calibrated/loose
# consequence magnitude — plan §5a; the tight leg is the segregation scrubbing, not this number).
# ~0.3 µm so a ~1e16 cm⁻³ residual Na gives ~3e11 cm⁻² → a ~0.15 V flat-band shift at a thin gate oxide
# (the classic mobile-ion-contamination regime — enough to walk V_t out the bottom of its window).
NA_OXIDE_INCORPORATION_CM: float = 3.0e-5      # cm — FLAGGED house bulk→areal Na incorporation length


def sodium_oxide_charge(N_Na: float, incorporation_cm: float = NA_OXIDE_INCORPORATION_CM) -> float:
    """Gate-oxide mobile-ion charge ``Q_ox = q·(N_Na·d_incorp)`` (C/cm²) from bulk sodium ``N_Na`` (cm⁻³).

    Mobile Na⁺ that reaches the gate oxide is **positive** fixed/mobile charge, so ``Q_ox > 0`` →
    a **negative** flat-band shift ``ΔV_FB = −Q_ox/C_ox`` (:mod:`chip.device`) → ``V_t`` driven **down**.
    The bulk→areal bridge (``N_areal = N_Na·d_incorp``) is the **flagged, calibrated** consequence
    magnitude (``incorporation_cm`` a house length); a clean wafer (``N_Na = 0``) gives ``Q_ox = 0``
    exactly (the seam). The segregation that *sets* ``N_Na`` (:func:`zone_refine`) is the tight leg.
    """
    return Q_ELEMENTARY * N_Na * incorporation_cm
