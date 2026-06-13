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

from chip.wafer_prep import WaferGeometry

from .state import Die, Verdict


@dataclass(frozen=True)
class SpecWindow:
    """A one-sided or two-sided spec band on a named parameter. ``None`` bound = open on that side.

    ``optional`` windows skip a die that was not scored for this parameter (``value is None`` → no
    reason) instead of failing it "missing" — used for the **additive** G4b leakage output, which a
    die only carries once the device step has computed it (a bare/hand-built die is simply not binned
    on leakage). The core parametrics (``V_t``/CD/NILS) stay non-optional: in the real pipeline a
    resolved device always sets them, so a missing one there is a genuine fault.
    """

    name: str
    lo: float | None = None
    hi: float | None = None
    optional: bool = False

    def check(self, value: float | None) -> str | None:
        """Return a human reason if ``value`` is out of band (or missing), else ``None``."""
        if value is None:
            return None if self.optional else f"{self.name} missing"
        if self.lo is not None and value < self.lo:
            return f"{self.name} {value:.4g} < {self.lo:.4g} (low)"
        if self.hi is not None and value > self.hi:
            return f"{self.name} {value:.4g} > {self.hi:.4g} (high)"
        return None


@dataclass(frozen=True)
class GeometrySpec:
    """Wafer-level flatness windows — TTV/bow out of band scraps the **whole wafer** (G3, plan §5).

    Geometry is a *wafer* property (not per-die), so a violation is a functional reject of every die
    on the wafer (the front-of-line incoming-inspection gate). House numbers, flagged. ``check``
    returns the reason for the first window violated, else ``None`` (geometry in spec → no scrap).
    """

    ttv_um: SpecWindow = field(default_factory=lambda: SpecWindow("TTV (µm)", hi=1.0))
    bow_um: SpecWindow = field(default_factory=lambda: SpecWindow("bow (µm)", hi=40.0))

    def check(self, geometry: WaferGeometry | None) -> str | None:
        """The wafer's geometry scrap reason (``None`` if in spec, or if no geometry was produced)."""
        if geometry is None:
            return None
        return self.ttv_um.check(geometry.ttv_um) or self.bow_um.check(geometry.bow_um)


@dataclass(frozen=True)
class SpeedBin:
    """One performance (speed) bin: a label + a half-open I_Dsat band ``[lo, hi)`` in **mA** (G6).

    Parts are binned by drive current as a **speed proxy** (clock speed ∝ drive current → ∝ ``I_Dsat``):
    a faster die (higher ``I_Dsat``) sorts into a higher bin (premium). ``lo_mA``/``hi_mA`` are the
    inclusive-lower / exclusive-upper edges (``None`` = open on that side). House numbers, flagged.
    """

    label: str
    lo_mA: float | None = None
    hi_mA: float | None = None

    def contains(self, i_dsat_mA: float) -> bool:
        return ((self.lo_mA is None or i_dsat_mA >= self.lo_mA)
                and (self.hi_mA is None or i_dsat_mA < self.hi_mA))


@dataclass(frozen=True)
class SpeedBins:
    """The final-test **binning** policy — sort working parts into speed/value grades (G6, plan §5 step 9).

    Binning is a **grading policy, not physics** (ADR 0005 §1) — sorting parts that already passed the
    front-end spec into performance grades by **house** ``I_Dsat`` thresholds. It lives in the game
    layer; the only invariant asserted is the **partition** (every packaged part lands in exactly one
    bin, or the ``reject`` tail). A part below the slowest sellable bin is a **bin-out** — a working but
    out-of-grade reject (a functional part that does not ship), distinct from a front-end parametric
    fail.

    The default is a **single open bin** (``"pass"``) covering everything: every packaged-good die →
    ``"pass"``, never ``reject`` — so the seam *and* the G1–G5 banked demos are byte-for-byte unchanged
    (binning grades nothing by default). The G6 demo dials in real fast/typical/slow bins so the
    across-wafer ``I_Dsat`` spread sorts into value grades (a tight process → the premium bin dominates;
    a loose one → spread + a bin-out tail).
    """

    bins: tuple[SpeedBin, ...] = (SpeedBin("pass"),)
    reject_label: str = "reject"

    def assign(self, i_dsat_mA: float | None) -> str:
        """The bin label for a die's ``I_Dsat`` (mA) — the first containing bin, else ``reject_label``.

        ``None`` (a die with no device read) bins to ``reject_label`` (it cannot be graded). Bins are
        tried in order, so list them fastest→slowest (or non-overlapping) for a clean grade.
        """
        if i_dsat_mA is None:
            return self.reject_label
        for b in self.bins:
            if b.contains(i_dsat_mA):
                return b.label
        return self.reject_label

    def is_reject(self, label: str) -> bool:
        return label == self.reject_label

    @property
    def labels(self) -> tuple[str, ...]:
        """Every grade label plus the reject tail — the bin-histogram keys (a fixed, ordered set)."""
        return tuple(b.label for b in self.bins) + (self.reject_label,)


@dataclass(frozen=True)
class SpecSet:
    """The full per-die acceptance test: the functional gates + the parametric windows.

    Functional gates short-circuit before the parametrics, in order: (1) a **killer particle
    defect** caught at wafer prep — the transistor exists but is dead (distinct from an unresolved
    litho image, where the device never formed); (2) a litho image that **never resolved**; (3) a
    **deposition void / pinch-off** (G5 — a poor step coverage failed to fill the gate gap); (3b) an
    **under-etch residual bridge** (D1 — an incomplete clear left residual film shorting the gate lines,
    the mirror of the void's open). A
    wafer-level **geometry** scrap (TTV/bow out, passed in as ``geometry_reason``) is the outermost
    gate — it fails every die. Otherwise the parametric chain: the defocus chain rides **NILS** (the
    printability floor) and **CD/I_Dsat** (the channel-length chain); ``V_t`` rides the
    ``t_ox``/``N_A`` channel (the device's own scope edge keeps ``V_t`` off the channel-length chain);
    and (G4b) **leakage** rides the deep-level-metal channel — the junction reverse-leakage that a
    metal contaminant raises (the device output net doping cannot carry), an *optional* window so a
    die not scored for leakage is simply not binned on it.
    """

    cd_nm: SpecWindow
    i_dsat_mA: SpecWindow
    v_t: SpecWindow
    nils: SpecWindow
    leakage: SpecWindow = field(
        default_factory=lambda: SpecWindow("leakage (nA/cm²)", hi=10.0, optional=True))
    geometry: GeometrySpec = field(default_factory=GeometrySpec)
    speed_bins: SpeedBins = field(default_factory=SpeedBins)   # G6 final-test binning (default: one open bin)
    require_resolved: bool = True

    def verdict(self, die: Die, geometry_reason: str | None = None) -> Verdict:
        """Score one die: wafer-geometry scrap → defect/resolve functional gates → parametric windows.

        ``geometry_reason`` (computed once per wafer) scraps every die when set. A killer-defect or
        an unresolved image then short-circuits — neither has a meaningful parametric bin. Otherwise
        every window (NILS printability, CD, I_Dsat, V_t) is checked and *all* failing reasons are
        collected (so the trail shows everything out of spec, not just the first).
        """
        if geometry_reason is not None:
            return Verdict(False, (f"{geometry_reason} — wafer scrapped (functional fail)",))
        if die.killed_by_defect is True:
            n = len(die.defects)
            return Verdict(False, (f"killer particle defect ×{n} (functional fail)",))
        if self.require_resolved and die.resolved is False:
            return Verdict(False, ("litho image not resolved (functional fail)",))
        if die.voided is True:                                 # G5 — a deposition keyhole void / pinch-off
            return Verdict(False, ("deposition void / pinch-off (functional fail)",))
        if die.bridged is True:                                # D1 — an under-etch residual short
            return Verdict(False, ("under-etch residual bridge / short (functional fail)",))
        reasons = [
            r for r in (
                self.nils.check(die.nils),
                self.cd_nm.check(die.cd_nm),
                self.i_dsat_mA.check(die.i_dsat_mA),
                self.v_t.check(die.V_t),
                self.leakage.check(die.j_leak_nA_cm2),     # G4b — deep-level-metal junction leakage (optional)
            ) if r is not None
        ]
        return Verdict(passed=not reasons, reasons=tuple(reasons))


# House-default windows (FLAGGED), centred on the nominal demo_device device
# (V_t ≈ 0.55 V, CD ≈ 167 nm, I_Dsat ≈ 3.3 mA, NILS ≈ 4.6, leakage ≈ 0.01 nA/cm²). Set so the nominal
# recipe yields high and a defocused exposure drops it — the dramatic win. The NILS floor (~2.8) is
# anchored to the cited printability rule of thumb (NILS ≳ 2–3 to print reliably;
# [[litho-aerial-image-source]]); the CD/I_Dsat/V_t/leakage bands are house numbers. Tune in the demo,
# not the physics. The leakage ceiling (10 nA/cm²) sits well above the clean baseline AND above a
# solar-grade feed's once-refined residual metal (so an intermediate grade still passes), but below
# the metal-laden G4b demo scenario — the single binding calibration (the metals' device consequence).
DEFAULT_SPECS = SpecSet(
    nils=SpecWindow("NILS", lo=2.8, hi=None),                # printability floor (the primary defocus catch)
    cd_nm=SpecWindow("CD (nm)", lo=150.0, hi=185.0),         # ±~11 % around 167 nm (extreme-defocus CD collapse)
    i_dsat_mA=SpecWindow("I_Dsat (mA)", lo=2.8, hi=4.2),     # floor < nominal 3.3; ceiling catches CD-collapse over-current
    v_t=SpecWindow("V_t (V)", lo=0.45, hi=0.68),             # the t_ox / N_A channel
    leakage=SpecWindow("leakage (nA/cm²)", hi=10.0, optional=True),   # G4b deep-level-metal junction leakage
)
