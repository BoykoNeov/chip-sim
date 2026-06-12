"""Spec windows → the per-die verdict (the plan §4).

Each critical device output has a spec ``[lo, hi]``. A die fails **parametrically** if a critical
parameter leaves its window, or **functionally** if the print never formed (the litho image did
not resolve / the device step refused). ``yield = good dies / total`` (computed in
:mod:`fab_game.pipeline`).

The windows are **house defaults, flagged** — illustrative pass/fail bands centred on the nominal
``demo_device`` device, *not* cited fab limits (ADR 0005 §5: ``fab_game`` is scored on mechanics,
not magnitudes). The defocus story rides the **CD** and **I_Dsat** windows (the channel-length
chain); the **V_t** window catches the ``t_ox`` / ``N_A`` channel (the device model's own
scope edge keeps ``V_t`` off the channel-length chain).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .state import Die, Verdict


@dataclass(frozen=True)
class SpecWindow:
    """A one-sided or two-sided spec band on a named parameter. ``None`` bound = open on that side."""

    name: str
    lo: float | None = None
    hi: float | None = None

    def check(self, value: float | None) -> str | None:
        """Return a human reason if ``value`` is out of band (or missing), else ``None``."""
        if value is None:
            return f"{self.name} missing"
        if self.lo is not None and value < self.lo:
            return f"{self.name} {value:.4g} < {self.lo:.4g} (low)"
        if self.hi is not None and value > self.hi:
            return f"{self.name} {value:.4g} > {self.hi:.4g} (high)"
        return None


@dataclass(frozen=True)
class SpecSet:
    """The full per-die acceptance test: a functional gate (resolved) + the parametric windows.

    The defocus chain rides **NILS** (the printability floor) and **CD/I_Dsat** (the channel-length
    chain); ``V_t`` rides the ``t_ox``/``N_A`` channel. The NILS floor is the *physically primary*
    defocus signature: a defocused image loses edge sharpness (NILS collapses) long before its CD
    midpoint shifts — so a too-defocused feature is unprintable even while its nominal CD looks
    fine, and only an *extreme* defocus finally collapses the CD (which then **raises** ``I_Dsat``
    via the shorter channel, hence an I_Dsat *ceiling*, not a floor, on the defocus side).
    """

    cd_nm: SpecWindow
    i_dsat_mA: SpecWindow
    v_t: SpecWindow
    nils: SpecWindow
    require_resolved: bool = True

    def verdict(self, die: Die) -> Verdict:
        """Score one die: functional gate first (short-circuits), then every parametric window.

        A functional fail (the litho image did not resolve at all) short-circuits — a print that
        never formed has no meaningful CD/V_t to bin. Otherwise every window (NILS printability, CD,
        I_Dsat, V_t) is checked and *all* failing reasons are collected (so the trail shows
        everything out of spec, not just the first).
        """
        if self.require_resolved and die.resolved is False:
            return Verdict(False, ("litho image not resolved (functional fail)",))
        reasons = [
            r for r in (
                self.nils.check(die.nils),
                self.cd_nm.check(die.cd_nm),
                self.i_dsat_mA.check(die.i_dsat_mA),
                self.v_t.check(die.V_t),
            ) if r is not None
        ]
        return Verdict(passed=not reasons, reasons=tuple(reasons))


# House-default windows (FLAGGED), centred on the nominal demo_device device
# (V_t ≈ 0.55 V, CD ≈ 167 nm, I_Dsat ≈ 3.3 mA, NILS ≈ 4.6). Set so the nominal recipe yields high
# and a defocused exposure drops it — the dramatic win. The NILS floor (~2.8) is anchored to the
# cited printability rule of thumb (NILS ≳ 2–3 to print reliably; [[litho-aerial-image-source]]);
# the CD/I_Dsat/V_t bands are house numbers. Tune in the demo, not the physics.
DEFAULT_SPECS = SpecSet(
    nils=SpecWindow("NILS", lo=2.8, hi=None),                # printability floor (the primary defocus catch)
    cd_nm=SpecWindow("CD (nm)", lo=150.0, hi=185.0),         # ±~11 % around 167 nm (extreme-defocus CD collapse)
    i_dsat_mA=SpecWindow("I_Dsat (mA)", lo=2.8, hi=4.2),     # floor < nominal 3.3; ceiling catches CD-collapse over-current
    v_t=SpecWindow("V_t (V)", lo=0.45, hi=0.68),             # the t_ox / N_A channel
)
