"""Diode reverse recovery: minority-carrier lifetime → switching speed (device-targets slice 5).

The **new device output** the power-rectifier target needs (``docs/plans/device-targets.md`` slice 5).
G4b's :mod:`chip.lifetime` already turned the deep-level metals (Fe/Cu) into a minority-carrier lifetime
``τ`` and, through it, the junction reverse **leakage** ``J_gen ∝ 1/τ`` — *the* device-killer for a logic
part. This module is the consumer that reads the **same ``τ`` in the opposite direction**: a p-n rectifier
switched from forward conduction to reverse blocking cannot turn off until its **stored minority charge**
recombines, so its **reverse-recovery time** ``t_rr ∝ τ``. A *short* lifetime — a leaky, low-lifetime
diode that net doping cannot save and that ruins a logic wafer — is exactly what makes a **fast** rectifier.
That sign flip on one physical quantity is the slice-5 inversion (the richest of the device-targets table):
the lifetime killer is the feature.

Why this is the lifetime axis (the structural point — the device-targets inversion table)
-----------------------------------------------------------------------------------------
``τ`` feeds **two** scored device outputs that pull in **opposite** directions:

* the junction reverse **leakage** ``J_gen = q·n_i·W/(2·τ)`` (:mod:`chip.lifetime`) — a logic part wants it
  **small**, i.e. a **long** ``τ`` (a clean feed); and
* the reverse-recovery time ``t_rr ∝ τ`` (here) — a power rectifier wants it **small**, i.e. a **short**
  ``τ`` (a lifetime-killed feed).

So the *same* wafer that is logic-good (clean, low-leakage, but a slow rectifier) is rectifier-reject, and a
lifetime-killed wafer that is logic-reject (leaky) is rectifier-good (fast) — a genuine "good is relative"
crossing on the **lifetime** axis, with **no new lifetime physics**: ``τ`` is the G4b reading, and this
module only adds the one cited *consequence* a rectifier reads off it.

The model — the storage time *derived* from the charge-control equation (no remembered fit)
-------------------------------------------------------------------------------------------
The classic charge-control description of a p-n diode (Sze, *Physics of Semiconductor Devices* §2.5;
Baliga, *Fundamentals of Power Semiconductor Devices*): the stored minority charge ``Q`` in the quasi-
neutral region obeys::

    dQ/dt = −Q/τ + i(t)

In steady forward conduction ``i = I_F`` so ``Q_F = I_F·τ`` (the stored charge). At ``t = 0`` the diode is
switched and the external circuit forces a **constant reverse current** ``−I_R``; while charge remains the
junction stays forward-biased, so ``i = −I_R`` and::

    dQ/dt = −Q/τ − I_R   ⇒   Q(t) = (I_F·τ + I_R·τ)·e^(−t/τ) − I_R·τ

The **storage phase** ends when the stored charge at the junction edge reaches zero, ``Q(t_s) = 0``::

    t_s = τ·ln(1 + I_F/I_R)

— so ``t_s`` is **linear in ``τ``** with a slope set only by the operating-point ratio ``I_F/I_R``. The
total reverse-recovery time ``t_rr = t_s + t_f`` adds a depletion-capacitance/transit-limited **fall time**
``t_f`` that does **not** scale with ``τ``; for a lifetime-controlled rectifier ``t_s`` dominates, so the
device output here is the storage-dominated ``t_rr ≈ t_s ∝ τ`` (``t_f`` is the named scope edge). Like
:mod:`chip.breakdown` deriving ``BV`` from the ionization integral rather than reading an empirical curve,
``t_s`` here is **solved from the charge-control ODE**, not a remembered ``t_rr``-vs-``τ`` fit — only the
cited model form and the flagged operating-point ratio go in.

Validation triad (ADR 0005 §5 — cite the form, flag the magnitude)
------------------------------------------------------------------
* **Analytical limit (tight).** ``t_s = τ·ln(1 + I_F/I_R)`` is the *exact* solution of the charge-control
  ODE with ``Q(0) = I_F·τ``: integrating ``dQ/dt = −Q/τ − I_R`` forward, the stored charge crosses zero at
  precisely the closed-form ``t_s`` (the criterion closes, the analogue of breakdown's ``∫α dx = 1`` on the
  triangular field). The proportionality ``t_rr ∝ τ`` (``t_rr/τ`` independent of ``τ``) is exact by
  construction, as are the limits ``I_R → ∞ ⇒ t_rr → 0`` (a large reverse current sweeps the charge out
  instantly) and ``I_F/I_R → 0 ⇒ t_rr → 0`` (no stored charge to remove).
* **Monotonicity (by construction).** ``t_rr`` rises with ``τ`` — the cited lifetime-killing direction
  (shorter lifetime → faster recovery, *why* gold/platinum or irradiation lifetime control speeds power
  rectifiers) — and with the operating-point ratio ``I_F/I_R``.
* **Benchmark (loose).** The operating-point factor ``ln(1 + I_F/I_R)`` is an **O(1)** number for a typical
  switching test (``I_F ≈ I_R`` → ``ln 2 ≈ 0.69``); the absolute ``t_rr`` then tracks ``τ`` to that factor.
  ``I_F/I_R`` is a **flagged** house operating point (ADR 0005 §5) — only the cited *form* (``t_rr ∝ τ``,
  charge-control) and the lifetime-killing *direction* are asserted, never the magnitude.

Named scope edge (the honest ceiling)
-------------------------------------
* **Storage-time-dominated.** ``t_rr ≈ t_s ∝ τ``; the depletion-capacitance/transit-limited **fall time**
  ``t_f`` (which does *not* scale with ``τ``) is named, not modelled — the model is the lifetime-controlled
  regime where ``t_s`` dominates (the regime the slice-5 inversion lives in).
* **Constant-reverse-current switching.** ``I_R`` is taken constant during storage (the textbook
  charge-control idealization); a real ``di/dt``-limited circuit shapes the waveform, folded into the
  flagged operating point.
* **One effective lifetime.** ``t_rr`` reads the single low-injection minority-carrier ``τ`` of
  :mod:`chip.lifetime` (the same ``τ`` the leakage reads); high-level-injection and ambipolar effects in a
  conductivity-modulated power diode are out (the lifetime module's own named ceiling).

Units — semiconductor-conventional CGS (as :mod:`chip.lifetime` / :mod:`chip.breakdown`)
---------------------------------------------------------------------------------------
Lifetime ``τ`` in **s**; the operating-point ratio ``I_F/I_R`` is dimensionless; ``t_rr`` in **s**
(reported **ns**, the rectifier-relevant scale). No new constants beyond the flagged operating point — the
lifetime itself comes from :mod:`chip.lifetime`.

Validation boundary
-------------------
No shared engine — ``t_rr`` is the closed-form solution of the charge-control ODE (like the compact ``V_t``
/ the SRH lifetime / Deal–Grove / the breakdown root-find), so this module's tests carry the whole triad:
the ODE solution closes on the charge-zero crossing (analytic limit), ``t_rr`` is monotone in ``τ`` and
``I_F/I_R`` (by construction), and the operating-point factor is the cited ``O(1)`` value (benchmark). The
model form is pinned to the cited charge-control description; the operating point is a flagged house value.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# The flagged operating point — the only house number the recovery time rides.
# --------------------------------------------------------------------------- #
# I_F/I_R: the forward-to-reverse current ratio of the switching test. A typical reverse-recovery
# measurement drives comparable forward and reverse currents (I_F ≈ I_R → ln 2 ≈ 0.69), so this is an
# O(1) number. FLAGGED (ADR 0005 §5): it sets the t_rr/τ slope but only the cited proportionality
# t_rr ∝ τ and the lifetime-killing direction are asserted, never this magnitude.
IF_OVER_IR_DEFAULT: float = 1.0


def storage_factor(if_over_ir: float = IF_OVER_IR_DEFAULT) -> float:
    """The operating-point factor ``K = ln(1 + I_F/I_R)`` in ``t_s = K·τ`` (dimensionless) — derived.

    Falls out of the charge-control storage-phase solution ``Q(t_s) = 0`` (see the module docstring), not a
    remembered fit. ``K → 0`` as ``I_F/I_R → 0`` (no stored charge) and grows only logarithmically with the
    forward/reverse current ratio (``ln 2 ≈ 0.69`` at the typical ``I_F = I_R``).
    """
    if if_over_ir < 0.0:
        raise ValueError(f"I_F/I_R must be ≥ 0, got {if_over_ir}")
    return math.log1p(if_over_ir)


def reverse_recovery_time(tau: float, if_over_ir: float = IF_OVER_IR_DEFAULT) -> float:
    """Reverse-recovery (storage) time ``t_rr ≈ t_s = τ·ln(1 + I_F/I_R)`` (s) — the rectifier's switching speed.

    The storage-dominated reverse recovery of a p-n rectifier, **linear in the minority-carrier lifetime**
    ``τ`` (:func:`chip.lifetime.srh_lifetime` — the *same* ``τ`` the junction leakage reads, in the opposite
    direction): a **short** ``τ`` (a lifetime-killed / metal-laden feed — a logic leakage reject) gives a
    **fast** rectifier, a **long** ``τ`` (a clean feed — logic-good) a **slow** one. ``if_over_ir`` is the
    flagged switching operating point (:data:`IF_OVER_IR_DEFAULT`). The depletion/transit fall time ``t_f``
    (not ``τ``-scaling) is the named scope edge — this is the lifetime-controlled storage term that carries
    the slice-5 inversion.
    """
    if tau < 0.0:
        raise ValueError(f"lifetime τ must be ≥ 0, got {tau}")
    return tau * storage_factor(if_over_ir)


# --------------------------------------------------------------------------- #
# The bundled recovery reading (the loose-coupling currency the device step lifts onto the die)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DiodeRecovery:
    """A rectifier's switching reading: the reverse-recovery time, its lifetime, and the operating point.

    ``t_rr`` (s) the storage-dominated reverse-recovery time, ``tau`` (s) the minority-carrier lifetime it
    reads (the G4b SRH lifetime), ``if_over_ir`` the flagged switching operating point. Plain scalars — the
    loose-coupling currency the fab-line game's device step lifts onto the die (a new field), the analogue of
    :class:`chip.breakdown.JunctionBreakdown` / :class:`chip.lifetime.DiodeLeakage`.
    """

    t_rr: float
    tau: float
    if_over_ir: float

    @property
    def t_rr_ns(self) -> float:
        """Reverse-recovery time in nanoseconds (the rectifier-scale spec-window / readout unit)."""
        return self.t_rr * 1.0e9


def diode_recovery(tau: float, if_over_ir: float = IF_OVER_IR_DEFAULT) -> DiodeRecovery:
    """Read a diode's reverse recovery off its minority-carrier lifetime ``τ`` (s) — the device-step wiring.

    Convenience bundle of :func:`reverse_recovery_time` for the device step: a **short**-``τ`` (lifetime-
    killed) wafer in, a **fast** rectifier out — the device consequence net doping cannot carry, and the
    sign-inverted twin of the junction leakage the same ``τ`` produces.
    """
    return DiodeRecovery(t_rr=reverse_recovery_time(tau, if_over_ir), tau=tau, if_over_ir=if_over_ir)
