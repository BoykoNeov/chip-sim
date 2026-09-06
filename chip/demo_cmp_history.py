"""The historical-modes B11 banked artifact: CMP / planarity — the polish that defined the copper line (F8).

The period back end (aluminium wires, **subtractively etched** — every line on the wafer as thick as the
film that was deposited) run against the observable that copper brought with it: *the wire's thickness is
set by a polish, the polish must clear everywhere, and therefore it over-polishes somewhere — so for the
first time the wire has a spread of its own*. One figure, three panels:

  * **Left — the wall: the polish is forced into a window, and the window closes.** The clear-everywhere
    requirement (the source's own motivating paragraph) sets a floor on the mean removal: clearing the
    slowest site needs ``R̄ ≥ t_over/(1−s)``, i.e. the typical site is over-polished by **``s/(1−s)``**
    overburdens (:func:`chip.cmp.forced_overpolish_ratio`) — the module's headline, with no house constant
    in it, exactly zero at ``s = 0``. A resistance budget sets a ceiling (the fastest site must stay inside
    it), and the two bounds cross at **``s_crit = L/(2+L)``** (:func:`chip.cmp.critical_nonuniformity`):
    past it **no polish time exists** — clearing the slow centre necessarily over-thins the fast rim. Below
    the floor is residual copper (a short); above the ceiling is an over-thinned wire (a slow part). The
    ceiling's *placement* carries the flagged budget; the *closure* is structural.
  * **Middle — the payload: one transistor, many delays.** Hold the period transistor fixed (the real,
    untouched :mod:`chip.device`) and read the chip delay across the wafer radius. The aluminium line is
    **flat**: subtractive etch, the deposited thickness everywhere, ``τ_wire`` common-mode — F4/B9's
    premise, and its ``1 − wire_share`` law. A uniformly polished copper line (``s = 0``) is flat too, and
    lower by ``ρ_Cu/ρ_Al``. A *real* polish at the clear-everywhere time bends upward toward the rim — the
    fast edge clears first and keeps polishing — and the bend grows with ``s``. ``τ_gate`` is the same
    number at every radius on every curve: **the whole spread is the wire's**, and no per-die transistor
    quantity is upstream of it (``∂τ_wire/∂I_Dsat = 0``, enforced by construction in
    :func:`chip.interconnect.delay`). The panel also shows the other side of the window: a polish 10 %
    short of the clear time leaves a **centre disc** ``r < r*`` bridged with residual copper
    (:func:`chip.cmp.shorted_radius_frac`, a closed form) while the rim is *still* over-polished — polishing
    less does not reduce the non-uniformity, it only fails to clear.
  * **Right — the successor: where a fix can go, and where it cannot.** At the sim's pitch the copper loss
    is a **product of two levers and nothing else**: ``loss = η(pattern) · 2s/(1−s) · t_over/H₀`` at the
    rim. Sweep the pattern density at the house 0.5 µm pitch and the erosion efficiency
    ``η ∝ d/(1−d)`` diverges as the oxide that carries the pad load runs out — while dishing is **exactly
    zero** here (the cited trend crosses zero at ~1 µm pitch; dishing is a pad-and-power-rail problem, and
    the panel says what it *would* be at the source's 250 µm pitch). So the two things that cleared the
    wall are the two factors: **uniformity** (attack ``s`` — and it has to be through *pressure*: at
    matched speeds the pad–wafer speed is ``ω·d`` at every point on the wafer, derived, so Preston's ``V``
    is barred from carrying a radial signature and the zoned-pressure carrier head is where the work went)
    and **density control** (attack ``η`` — the design-rule density windows, slotting and dummy fill that
    hold the layout inside a band the polish can planarize over its 50–100 µm planarization length, cited).
    Polishing *less* is neither.

Why this is B11 and why it sits after B9 (the enabling claim, from the source's first paragraph)
-------------------------------------------------------------------------------------------------
*"Unlike Al, copper can not be easily plasma etched, and one must resort to a damascene process and use
CMP … to remove the excess copper and barrier materials, thereby accurately defining the copper lines in the
trenches."* B9's copper era **does not exist without this step**: the later slice is the earlier one's
precondition. The timeline puts it where the process puts it — after the metal is chosen, before the wire is
read.

The honesty ladder (the ``historical-modes.md`` triad)
--------------------------------------------------------
* **Tight — the seam.** ``s = 0`` ⇒ forced overpolish exactly zero ⇒ nominal thickness at every radius ⇒
  the copper curve is F4's number bit-for-bit at every point (asserted against the real
  :func:`chip.interconnect.delay` on the house :class:`chip.interconnect.WireGeometry`).
* **Tight — the transistor never moves.** ``τ_gate`` is one number across every curve; the wire term is the
  only thing on the middle panel that varies, and it varies with *radius*, not with any device quantity.
* **Tight — the two closed forms.** ``s/(1−s)`` and ``s_crit = L/(2+L)``, the floor and the closure. The
  floor contains no constant at all; the closure contains the budget and ``η``, both named.
* **Tight — the kinematic identity.** ``|v_rel| = ω·d`` everywhere at matched speeds (derived in
  :mod:`chip.cmp`, asserted exactly there) — which is what makes "uniformity is a pressure problem" a
  statement about the *product* and not a preference.
* **Cited, monotone only — the pattern legs.** Erosion ↑ with density (the source's Fig. 7, a shape fit to
  its stated mechanism, FLAGGED); dishing's log-linear trend crossing zero at ~1 µm pitch (Fig. 5); the
  50–100 µm copper planarization length (vs 3–5 mm for oxide CMP).
* **Flagged — every magnitude.** The radial amplitude ``s`` (the source averaged nine dies per wafer and
  supplies **no** radial profile; the sign of the edge effect is cited, its size is a house number), the
  overburden, the resistance budgets, ``η``'s prefactor, Preston's ``K`` (a rate, and only the *ratios*
  of removals appear here), and the absolute picoseconds (F4's ``L²`` lump). Every claim below is a shape,
  a ratio, or a closed form.

Named ceilings — the axes this figure does not carry
------------------------------------------------------
* **The sub-micron regime the source could not measure: NOT EXTRAPOLATED.** The 60–70 % dishing peak and
  the ~100 µm break point are three hundred times off this feature size and appear in no number here.
* **Slurry chemistry, pad conditioning, endpoint algorithms, multi-level stacking: NOT BUILT.** The panel
  names the zoned head and the density rules as *where the fix went*, not as models.
* **The cross terms (dishing↔density, erosion↔pitch): NAMED, NOT BUILT** — the source refutes the tidy
  split and this demo rides each mechanism on its primary axis only.
* **Copper-thickness feedback into ``C``: DELIBERATELY ABSENT.** F4's cited ``c_pul`` invariance says the
  capacitance per length does not read ``W``/``H``; dishing moves ``R`` only. Run headless:

    python -m chip.demo_cmp_history
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import cmp
from . import device as dev
from . import interconnect as ic

# --- Recipe: one period transistor, one house line, and the polish that defines it ---------------- #
# B9's own period transistor (chip.demo_beol_history — the same four numbers, so the two rungs read the
# same device through the REAL, untouched device.py). It is a BYSTANDER on this figure: nothing below moves
# it, which is the point — the wire gains a spread while the transistor under it never changes.
PERIOD_N_A = 2.0e17            # cm⁻³ — p-type channel doping (lands a period-plausible V_t)
PERIOD_T_OX_UM = 10.0e-3       # µm — 10 nm gate oxide: the 0.5 µm node's documented value
PERIOD_CHANNEL_L_UM = 0.5      # µm — the 0.5 µm node's gate length
PERIOD_WIDTH_UM = 10.0         # µm — device width W (sets I_Dsat and C_load together)

PERIOD_METAL = "Al"            # the subtractively etched period line — no polish defines it
MODERN_METAL = "Cu"            # the damascene line — chip.cmp.DAMASCENE_METALS' only member

# The house line and its layout: the trench depth IS the F4 wire's thickness (so "no loss" and "the F4
# wire" are one number), the line width IS the F4 wire's width, and the density is W/pitch — the source's
# own definition. One layout number (the pitch) is house, FLAGGED, and shared with the game knob.
HOUSE_GEOMETRY = ic.WireGeometry()
HOUSE_PITCH_UM = 0.5           # FLAGGED — the 250 nm line on a 0.5 µm pitch ⇒ density 0.5
OVERBURDEN_UM = 0.5            # FLAGGED — plated copper above the field oxide (the game knob's default)

# The two-sided window's currency: a budget on the wire's resistance rise. FLAGGED — a spec, not physics;
# the closure is structural for ANY budget, and both are drawn so the reader sees the budget move the
# crossing and not the shape.
R_BUDGET_TIGHT = 1.10          # the rim may carry ≤ +10 % wire resistance
R_BUDGET_LOOSE = 1.25          # …or ≤ +25 %

S_AXIS = np.linspace(0.0, 0.45, 361)            # across-wafer removal non-uniformity s
S_CURVES = (0.05, 0.10, 0.20)                   # the family drawn on the middle panel (0.10 = the house)
S_HOUSE = 0.10                                  # the game knob's default amplitude (FLAGGED)
SHORT_POLISH_FRACTION = 0.90                    # the "10 % short of the clear time" polish, middle panel
SPEED_MISMATCH = 0.02                           # a near-matched carrier/platen (real tools run within a few %)
R_AXIS = np.linspace(0.0, 1.0, 201)             # wafer radius, centre → edge-exclusion boundary
DENSITY_AXIS = np.linspace(0.05, 0.95, 181)     # pattern density at the house pitch, right panel

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-cmp-history.png"


@dataclass(frozen=True)
class CmpHistoryResult:
    """The B11 bundle the figure and summary consume."""

    # the period transistor — a bystander, through the real device.py
    mos: dev.MOSDevice
    i_dsat_A: float
    c_load_F: float
    tau_gate_s: float
    # the two flat lines — subtractive aluminium, and uniformly polished copper (the seam)
    tau_al_s: float
    tau_cu_uniform_s: float
    tau_wire_al_s: float
    tau_wire_cu_uniform_s: float
    # left — the window
    s_axis: np.ndarray
    floor_overburdens: np.ndarray               # 1/(1−s): clear the slowest site
    ceiling_tight: np.ndarray                   # the fastest site inside R_BUDGET_TIGHT (nan past s_crit)
    ceiling_loose: np.ndarray
    forced_overpolish: np.ndarray               # s/(1−s) — the floor minus 1, no constant
    s_crit_tight: float
    s_crit_loose: float
    loss_budget_tight: float
    loss_budget_loose: float
    # middle — the per-die wire
    r_axis: np.ndarray
    thickness_um: dict[float, np.ndarray]       # s → H(r) at the clear-everywhere time
    tau_total_s: dict[float, np.ndarray]        # s → τ_total(r); τ_gate identical everywhere
    rim_loss: dict[float, float]                # s → copper fraction lost at r = 1
    short_r_star: float                         # the shorted disc's edge for the 0.9·t_clear polish
    tau_total_short_s: np.ndarray               # τ_total(r) for that polish, nan inside r*
    # right — the two levers
    density_axis: np.ndarray
    rim_loss_vs_density: dict[float, np.ndarray]   # s → loss(d) at the rim (nan where polished out)
    house_density: float
    dishing_efficiency_house: float             # exactly 0.0 at the house pitch
    dishing_efficiency_source_pitch: float      # what it would be at the source's 250 µm pitch
    erosion_efficiency_house: float
    planarization_length_um: tuple[float, float]
    # the kinematic identity, as numbers for the summary
    v_matched_centre_m_s: float
    v_matched_edge_m_s: float
    v_offmatch_spread: float                    # (max − min)/mean over the wafer at a 10 % speed mismatch


def _period_device() -> tuple[dev.MOSDevice, float, float]:
    """The fixed period transistor → (device, ``I_Dsat``, ``C_load``), through the **real** ``device.py``."""
    mos = dev.threshold_voltage(PERIOD_N_A, PERIOD_T_OX_UM, channel_length_um=PERIOD_CHANNEL_L_UM)
    i_dsat = dev.saturation_current(mos, V_GS=ic.V_DD_HOUSE, width_um=PERIOD_WIDTH_UM)
    c_load = ic.gate_load_capacitance(
        dev.oxide_capacitance(PERIOD_T_OX_UM), PERIOD_WIDTH_UM, PERIOD_CHANNEL_L_UM,
    )
    return mos, i_dsat, c_load


def house_pattern(density: float | None = None) -> cmp.PatternGeometry:
    """The layout the polish sees at the house pitch — density ``W/pitch`` unless swept explicitly."""
    d = HOUSE_GEOMETRY.width_um / HOUSE_PITCH_UM if density is None else density
    return cmp.PatternGeometry(HOUSE_PITCH_UM, density=d)


def loss_budget(r_budget: float) -> float:
    """The copper fraction a wire may lose for its resistance to rise by at most ``r_budget``: ``1 − 1/R``."""
    if r_budget <= 1.0:
        raise ValueError(f"a resistance budget must exceed 1 (a rise), got {r_budget}")
    return 1.0 - 1.0 / r_budget


def polished_thickness_um(radius_frac: float, s: float, polish_fraction: float = 1.0) -> float | None:
    """``H(r)`` after a polish at ``polish_fraction`` × the clear-everywhere removal; ``None`` if shorted."""
    mean_removal = polish_fraction * OVERBURDEN_UM / (1.0 - s)
    p = cmp.polish(cmp.radial_removal_um(radius_frac, s, mean_removal), OVERBURDEN_UM,
                   HOUSE_GEOMETRY.thickness_um, house_pattern())
    return p.thickness_um if p.cleared else None


def _tau_total(thickness_um: float, i_dsat: float, c_load: float, metal: str) -> ic.Delay:
    geom = ic.WireGeometry(length_um=HOUSE_GEOMETRY.length_um, width_um=HOUSE_GEOMETRY.width_um,
                           thickness_um=thickness_um)
    return _delay(geom, i_dsat, c_load, metal)


def _delay(geometry: ic.WireGeometry, i_dsat: float, c_load: float, metal: str) -> ic.Delay:
    return ic.delay(geometry, i_dsat, c_load, metal=metal)


def compute() -> CmpHistoryResult:
    """Run the period device → the window → the per-die wire → the two levers."""
    mos, i_dsat, c_load = _period_device()
    H0, t_over = HOUSE_GEOMETRY.thickness_um, OVERBURDEN_UM
    pattern = house_pattern()

    # The two flat lines. Aluminium: subtractive, the deposited thickness everywhere, no polish — F4's
    # premise. Copper at s = 0: the forced overpolish is exactly zero, so this IS F4's copper number.
    al = _delay(HOUSE_GEOMETRY, i_dsat, c_load, PERIOD_METAL)
    cu = _delay(HOUSE_GEOMETRY, i_dsat, c_load, MODERN_METAL)
    tau_gate = cu.tau_gate_s
    assert al.tau_gate_s == tau_gate                             # the transistor is a bystander, bit-for-bit

    # Left: the window in overburdens. The floor is the clear-everywhere requirement; each ceiling is a
    # resistance budget; both from chip.cmp's closed forms rather than re-derived here.
    lb_t, lb_l = loss_budget(R_BUDGET_TIGHT), loss_budget(R_BUDGET_LOOSE)
    floor = np.array([1.0 / (1.0 - s) for s in S_AXIS])
    forced = np.array([cmp.forced_overpolish_ratio(float(s)) for s in S_AXIS])

    def ceiling(budget: float) -> np.ndarray:
        out = np.full_like(S_AXIS, np.nan)
        for i, s in enumerate(S_AXIS):
            w = cmp.polish_window_um(budget, H0, t_over, float(s), pattern)
            if w is not None:
                out[i] = w[1] / t_over
        return out

    s_crit_t = cmp.critical_nonuniformity(lb_t, H0, t_over, pattern)
    s_crit_l = cmp.critical_nonuniformity(lb_l, H0, t_over, pattern)

    # Middle: the wire across the wafer at the clear-everywhere time, for the s family. At the centre the
    # slowest site removes exactly the overburden — nominal thickness, F4's number — and the rim carries the
    # forced overpolish. τ_gate is the same float on every curve (delay() reads i_dsat only in the gate term).
    thickness, tau_total, rim_loss = {}, {}, {}
    for s in S_CURVES:
        H = np.array([polished_thickness_um(float(r), s) for r in R_AXIS], dtype=float)
        thickness[s] = H
        tau_total[s] = np.array([_tau_total(float(h), i_dsat, c_load, MODERN_METAL).tau_total_s for h in H])
        rim_loss[s] = 1.0 - float(H[-1]) / H0
    # …and the other side of the window: 10 % short of the clear time at the house s, a centre disc shorts.
    mean_short = SHORT_POLISH_FRACTION * t_over / (1.0 - S_HOUSE)
    r_star = cmp.shorted_radius_frac(S_HOUSE, mean_short, t_over)
    tau_short = np.full_like(R_AXIS, np.nan)
    for i, r in enumerate(R_AXIS):
        h = polished_thickness_um(float(r), S_HOUSE, SHORT_POLISH_FRACTION)
        if h is not None:
            tau_short[i] = _tau_total(h, i_dsat, c_load, MODERN_METAL).tau_total_s

    # Right: the loss at the rim as a product of the two levers, swept over density at the house pitch.
    # loss = η(d) · overpolish_rim / H₀ with overpolish_rim = t_over·((1+s)/(1−s) − 1) = t_over·2s/(1−s);
    # nan where the trench would be polished out (loss ≥ 1 — polish() refuses there, and so does this).
    loss_vs_d = {}
    for s in S_CURVES:
        over_rim = t_over * 2.0 * s / (1.0 - s)
        vals = np.array([cmp.loss_efficiency(house_pattern(float(d))) * over_rim / H0 for d in DENSITY_AXIS])
        vals[vals >= 1.0] = np.nan
        loss_vs_d[s] = vals

    # The kinematic identity, as numbers: at matched speeds |v_rel| is ω·d at the centre AND the edge; a
    # near-matched tool (SPEED_MISMATCH off) spreads it by only ~mismatch·(r_wafer/d) over radius and angle.
    omega, d_off, r_wafer = 2.0 * math.pi, 0.2, 0.1
    v_c = cmp.relative_speed_m_s(omega, omega, d_off, 0.0)
    v_e = cmp.relative_speed_m_s(omega, omega, d_off, r_wafer, angle_rad=1.0)
    off = [cmp.relative_speed_m_s((1.0 + SPEED_MISMATCH) * omega, omega, d_off, r, angle_rad=a)
           for r in np.linspace(0.0, r_wafer, 11) for a in np.linspace(0.0, 2.0 * math.pi, 13)]
    v_spread = (max(off) - min(off)) / float(np.mean(off))

    return CmpHistoryResult(
        mos=mos, i_dsat_A=i_dsat, c_load_F=c_load, tau_gate_s=tau_gate,
        tau_al_s=al.tau_total_s, tau_cu_uniform_s=cu.tau_total_s,
        tau_wire_al_s=al.tau_wire_s, tau_wire_cu_uniform_s=cu.tau_wire_s,
        s_axis=S_AXIS, floor_overburdens=floor, ceiling_tight=ceiling(lb_t), ceiling_loose=ceiling(lb_l),
        forced_overpolish=forced, s_crit_tight=s_crit_t, s_crit_loose=s_crit_l,
        loss_budget_tight=lb_t, loss_budget_loose=lb_l,
        r_axis=R_AXIS, thickness_um=thickness, tau_total_s=tau_total, rim_loss=rim_loss,
        short_r_star=r_star, tau_total_short_s=tau_short,
        density_axis=DENSITY_AXIS, rim_loss_vs_density=loss_vs_d, house_density=pattern.density,
        dishing_efficiency_house=cmp.dishing_efficiency(pattern),
        dishing_efficiency_source_pitch=cmp.dishing_efficiency(
            cmp.PatternGeometry(cmp.CITED.density_mask_pitch_um, density=pattern.density)),
        erosion_efficiency_house=cmp.erosion_efficiency(pattern),
        planarization_length_um=cmp.CITED.planarization_length_um,
        v_matched_centre_m_s=v_c, v_matched_edge_m_s=v_e, v_offmatch_spread=v_spread,
    )


def print_summary(r: CmpHistoryResult) -> None:
    """Print the B11 story — the wire gets a spread, the window closes, and where the fix had to go."""
    print("\nHistorical-modes B11: CMP / planarity (the polish that defined the copper line)\n")
    print(f"  The period transistor — FIXED, a bystander, through the real, untouched device.py:")
    print(f"    B9's own: a {PERIOD_CHANNEL_L_UM} µm-era n-MOS, {PERIOD_T_OX_UM*1e3:.0f} nm gate oxide,"
          f" W = {PERIOD_WIDTH_UM:.0f} µm, at V_dd = {ic.V_DD_HOUSE} V")
    print(f"    → V_t = {r.mos.V_t:.3f} V, I_Dsat = {r.i_dsat_A*1e3:.2f} mA, τ_gate = {r.tau_gate_s*1e12:.2f} ps"
          f" — the SAME float on every curve below\n")

    H0 = HOUSE_GEOMETRY.thickness_um
    print(f"  The period line — {PERIOD_METAL}, SUBTRACTIVELY etched: the deposited {H0*1e3:.0f} nm everywhere,"
          f" no polish defines it")
    print(f"    → τ_wire = {r.tau_wire_al_s*1e12:.2f} ps at every die (common-mode: B9's premise, and its"
          f" 1 − wire_share law)")
    print(f"  The modern line — {MODERN_METAL}, DAMASCENE: copper cannot be plasma-etched, so the trench is cut,")
    print(f"    flooded, and the excess is polished off — the polish IS what sets the wire's thickness")
    print(f"    → uniformly polished (s = 0): τ_wire = {r.tau_wire_cu_uniform_s*1e12:.2f} ps"
          f" (ρ_Cu/ρ_Al = {r.tau_wire_cu_uniform_s/r.tau_wire_al_s:.3f}, F4's number bit-for-bit — the seam)\n")

    print(f"  The wall — clearing EVERYWHERE forces over-polishing SOMEWHERE (mean removal in overburdens):")
    print(f"    floor  = 1/(1−s): clear the slowest site  ⇒  the typical site is over-polished by s/(1−s)")
    print(f"    ceiling: the fastest site inside a resistance budget  ⇒  the window closes at s_crit = L/(2+L)")
    print(f"      {'s':>6} {'floor':>7} {'forced':>8} {'ceiling +10%':>13} {'ceiling +25%':>13}")
    for s in (0.0, 0.05, 0.10, 0.20, 0.30):
        i = int(np.argmin(np.abs(r.s_axis - s)))
        ct, cl = r.ceiling_tight[i], r.ceiling_loose[i]
        print(f"      {s:>6.2f} {r.floor_overburdens[i]:>7.3f} {r.forced_overpolish[i]:>8.3f} "
              f"{('CLOSED' if np.isnan(ct) else f'{ct:.3f}'):>13} {('CLOSED' if np.isnan(cl) else f'{cl:.3f}'):>13}")
    print(f"    → s_crit = {r.s_crit_tight:.3f} at a +{(R_BUDGET_TIGHT-1)*100:.0f}% budget, "
          f"{r.s_crit_loose:.3f} at +{(R_BUDGET_LOOSE-1)*100:.0f}%: the BUDGET moves the crossing;"
          f" the closure is structural.")
    print(f"      The floor contains no constant at all. Polishing LESS lowers nothing here — it only")
    print(f"      drops below the floor, where the slow centre keeps residual copper (a short).\n")

    print(f"  The payload — one transistor, many delays (polished at the clear-everywhere time):")
    print(f"      {'s':>6} {'H(centre)':>10} {'H(rim)':>8} {'rim loss':>9} {'τ(centre)':>10} {'τ(rim)':>8} {'spread':>7}")
    for s in S_CURVES:
        H, t = r.thickness_um[s], r.tau_total_s[s]
        print(f"      {s:>6.2f} {H[0]*1e3:>9.1f}nm {H[-1]*1e3:>7.1f}nm {r.rim_loss[s]:>8.1%} "
              f"{t[0]*1e12:>9.2f}ps {t[-1]*1e12:>7.2f}ps {t[-1]/t[0]-1:>+6.1%}")
    print(f"    → the centre is F4's number (the slowest site removes exactly the overburden); the rim")
    print(f"      carries the forced overpolish. τ_gate did not move: the spread is the WIRE's, and no")
    print(f"      per-die transistor quantity is upstream of it (∂τ_wire/∂I_Dsat = 0 by construction).")
    print(f"    → and the other side: a polish {1-SHORT_POLISH_FRACTION:.0%} short of the clear time at s = {S_HOUSE}"
          f" shorts every die inside r* = {r.short_r_star:.2f}")
    print(f"      (residual copper bridging the trenches — {r.short_r_star**2:.0%} of the wafer's area) while the"
          f" rim is STILL over-polished.\n")

    print(f"  The successor — at this pitch the loss is a PRODUCT of two levers: loss = η(density) · 2s/(1−s) · t_over/H₀")
    print(f"    dishing efficiency at the house {HOUSE_PITCH_UM} µm pitch: {r.dishing_efficiency_house:.3f} — EXACTLY zero"
          f" (the cited trend crosses zero at ~{cmp.DISH_ZERO_PITCH_UM:.0f} µm;")
    print(f"      at the source's {cmp.CITED.density_mask_pitch_um:.0f} µm pitch it would be "
          f"{r.dishing_efficiency_source_pitch:.2f} — dishing is a pad-and-rail problem, not a signal-line one)")
    print(f"    erosion efficiency at the house density {r.house_density:.2f}: {r.erosion_efficiency_house:.3f},"
          f" and ∝ d/(1−d): it DIVERGES as the oxide that carries the pad load runs out")
    print(f"      {'density':>8} " + " ".join(f"{'rim loss s=' + f'{s:.2f}':>16}" for s in S_CURVES))
    for d in (0.2, 0.5, 0.7, 0.9):
        i = int(np.argmin(np.abs(r.density_axis - d)))
        cells = " ".join(f"{('polished OUT' if np.isnan(r.rim_loss_vs_density[s][i]) else f'{r.rim_loss_vs_density[s][i]:.1%}'):>16}"
                         for s in S_CURVES)
        print(f"      {d:>8.2f} {cells}")
    print(f"    → lever 1, UNIFORMITY (attack s) — and it has to be PRESSURE: at matched speeds the pad–wafer")
    print(f"      speed is ω·d at every point (centre {r.v_matched_centre_m_s:.3f} m/s, edge {r.v_matched_edge_m_s:.3f} m/s"
          f" — identical, derived);")
    print(f"      a {SPEED_MISMATCH:.0%} speed mismatch spreads it by only {r.v_offmatch_spread:.1%} over the wafer. Preston's V cannot")
    print(f"      carry the radius, so the zoned-pressure carrier head and endpoint detection are where the work went.")
    print(f"    → lever 2, DENSITY (attack η) — design-rule density windows, slotting and dummy fill hold the layout")
    print(f"      inside a band the polish planarizes over its {r.planarization_length_um[0]:.0f}–"
          f"{r.planarization_length_um[1]:.0f} µm planarization length (cited; 3–5 mm for oxide CMP).")
    print(f"    → polishing LESS attacks neither factor.\n")
    print(f"  [FLAGGED: s, the overburden, the budgets, η's prefactor and the absolute ps are house numbers;")
    print(f"   the two closed forms, the seam, the monotone shapes and the identity are the claims.]")


def save_figure(r: CmpHistoryResult) -> Path:
    """Render and save the B11 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    AL_COLOR = "tab:gray"
    CU_COLOR = "tab:orange"
    SHORT_COLOR = "tab:red"
    WINDOW_COLOR = "tab:green"
    S_COLORS = {0.05: "#f4c17a", 0.10: "tab:orange", 0.20: "#a34a00"}

    fig, axes = plt.subplots(1, 3, figsize=(17.6, 6.4))
    H0 = HOUSE_GEOMETRY.thickness_um

    # --- Left: the window — the floor nobody can lower, the ceiling a budget sets, and the closure ------- #
    ax = axes[0]
    s = r.s_axis
    ok = ~np.isnan(r.ceiling_tight)
    ax.fill_between(s[ok], r.floor_overburdens[ok], r.ceiling_tight[ok], color=WINDOW_COLOR, alpha=0.18,
                    label=f"the window: clears everywhere AND the rim\nstays inside +{(R_BUDGET_TIGHT-1)*100:.0f}% wire R")
    ax.fill_between(s, 0.0, r.floor_overburdens, color=SHORT_COLOR, alpha=0.10)
    ax.plot(s, r.floor_overburdens, "-", color=SHORT_COLOR, lw=2.4,
            label="FLOOR 1/(1−s): clear the slowest site\n— below it, residual copper SHORTS the centre")
    ax.plot(s[ok], r.ceiling_tight[ok], "-", color=CU_COLOR, lw=2.2,
            label=f"CEILING: the fastest site inside +{(R_BUDGET_TIGHT-1)*100:.0f}% R\n— above it, the rim is over-thinned (SLOW)")
    okl = ~np.isnan(r.ceiling_loose)
    ax.plot(s[okl], r.ceiling_loose[okl], "--", color=CU_COLOR, lw=1.4, alpha=0.8,
            label=f"…the same ceiling at a +{(R_BUDGET_LOOSE-1)*100:.0f}% budget\n(the BUDGET moves the crossing, not the shape)")
    ax.axhline(1.0, color="k", lw=0.9, ls=":")
    ax.axvline(r.s_crit_tight, color=WINDOW_COLOR, lw=1.2, ls="--")
    ax.annotate(f"s_crit = {r.s_crit_tight:.3f} = L/(2+L)\npast it NO polish time exists:\n"
                f"clearing the slow centre necessarily\nover-thins the fast rim",
                xy=(r.s_crit_tight, 1.0 / (1.0 - r.s_crit_tight)), xytext=(0.975, 0.30),
                textcoords="axes fraction", fontsize=7.0, ha="right", va="top", color="darkgreen",
                arrowprops=dict(arrowstyle="->", color="darkgreen", lw=1.0),
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="lightgray", alpha=0.92))
    i_h = int(np.argmin(np.abs(s - S_HOUSE)))
    ax.annotate("", xy=(S_HOUSE, r.floor_overburdens[i_h]), xytext=(S_HOUSE, 1.0),
                arrowprops=dict(arrowstyle="<->", color=SHORT_COLOR, lw=1.4))
    ax.annotate(f"the floor sits s/(1−s) = {r.forced_overpolish[i_h]:.3f} overburdens above\n"
                f"'just cleared' at s = {S_HOUSE}: the over-polish you are FORCED\ninto, with no house constant "
                f"in it — exactly 0 at s = 0.\nEvery nanometre of dishing is bought by non-uniformity.",
                xy=(S_HOUSE, 0.5 * (1.0 + r.floor_overburdens[i_h])), xytext=(0.03, 0.965),
                textcoords="axes fraction", fontsize=7.0, ha="left", va="top", color=SHORT_COLOR,
                arrowprops=dict(arrowstyle="->", color=SHORT_COLOR, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="lightgray", alpha=0.92))
    ax.plot([0.0], [1.0], "o", color="k", ms=8, zorder=6)
    ax.annotate("the seam: s = 0, removal = 1 overburden,\nnothing dished, F4's wire on every die",
                xy=(0.0, 1.0), xytext=(8, -14), textcoords="offset points", fontsize=6.9, ha="left", va="top")
    ax.set_xlim(0.0, float(s[-1]))
    ax.set_ylim(0.6, 2.6)
    ax.set_xlabel("across-wafer removal non-uniformity  s   [FLAGGED amplitude; the SHAPE is the claim]")
    ax.set_ylabel("mean removal  R̄ / t_over   (overburdens)")
    ax.set_title("The wall: clearing EVERYWHERE forces over-polishing SOMEWHERE —\n"
                 "the window is s/(1−s) above 'just cleared', and it closes at s_crit", fontsize=9.5)
    ax.legend(fontsize=6.6, loc="upper left", bbox_to_anchor=(0.0, 0.72), framealpha=0.94)
    ax.grid(True, alpha=0.15)

    # --- Middle: one transistor, many delays -------------------------------------------------------------- #
    ax = axes[1]
    rr = r.r_axis
    ref = r.tau_cu_uniform_s
    Y_TOP = 1.075
    al_ratio = r.tau_al_s / ref
    ax.axhline(al_ratio, color=AL_COLOR, lw=2.6,
               label=f"period: {PERIOD_METAL}, subtractively etched — the deposited\n{H0*1e3:.0f} nm on every die; "
                     f"τ_wire common-mode (B9's premise)\n— FLAT at {al_ratio:.2f}×, off this scale ↑")
    ax.annotate(f"↑ {PERIOD_METAL}: {al_ratio:.2f}× — flat at every radius (off-scale)",
                xy=(0.985, Y_TOP - 0.003), fontsize=7.0, ha="right", va="top",
                color=AL_COLOR, fontweight="bold")
    ax.axhline(1.0, color=CU_COLOR, lw=2.0, ls=":",
               label=f"{MODERN_METAL} polished UNIFORMLY (s = 0): F4's number, bit-for-bit,\nat every radius — the seam")
    for s_val in S_CURVES:
        ax.plot(rr, r.tau_total_s[s_val] / ref, "-", color=S_COLORS[s_val], lw=2.2,
                label=f"{MODERN_METAL} polished at the clear-everywhere time, s = {s_val:.2f}:\n"
                      f"rim copper −{r.rim_loss[s_val]:.1%} → delay {r.tau_total_s[s_val][-1]/ref-1:+.1%}")
    # the other side of the window: the shorted centre disc of a too-short polish
    ax.axvspan(0.0, r.short_r_star, color=SHORT_COLOR, alpha=0.10, hatch="//", lw=0)
    okk = ~np.isnan(r.tau_total_short_s)
    ax.plot(rr[okk], r.tau_total_short_s[okk] / ref, "--", color=SHORT_COLOR, lw=1.8,
            label=f"…polished {1-SHORT_POLISH_FRACTION:.0%} SHORT of that time (s = {S_HOUSE}):\n"
                  f"every die inside r* = {r.short_r_star:.2f} SHORTS; the rim is still over-polished")
    ax.annotate(f"residual copper bridges the trenches\nfor r < r* = {r.short_r_star:.2f} — a functional short\n"
                f"on {r.short_r_star**2:.0%} of the wafer's area, graded\nby radius (never the whole wafer)",
                xy=(0.5 * r.short_r_star, 1.0 + 0.36 * (Y_TOP - 1.0)), fontsize=6.9, ha="center",
                va="center", color=SHORT_COLOR,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=SHORT_COLOR, alpha=0.92))
    ax.annotate(f"τ_gate = {r.tau_gate_s*1e12:.2f} ps — the SAME float on every curve.\n"
                f"The transistor did not move; the whole spread is the\nwire's, and it comes from where the die "
                f"sat on the polisher.\n(the delay histogram's first non-transistor component)",
                xy=(0.975, 0.03), xycoords="axes fraction", fontsize=7.0, ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=CU_COLOR, alpha=0.92))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.99, Y_TOP)
    ax.set_xlabel("wafer radius  r   (0 = centre, 1 = edge-exclusion boundary)")
    ax.set_ylabel(f"chip delay  τ_total / τ_total({MODERN_METAL}, uniform)   [prefactor-free]")
    ax.set_title("The payload: one transistor, many delays — a polish at the\n"
                 "clear-everywhere time gives the wire a spread of its own", fontsize=9.5)
    ax.legend(fontsize=6.6, loc="upper left", bbox_to_anchor=(0.0, 0.965))
    ax.grid(True, alpha=0.15)

    # --- Right: the two levers, and the one that is not a lever ------------------------------------------ #
    ax = axes[2]
    d = r.density_axis
    for s_val in S_CURVES:
        ax.plot(d, r.rim_loss_vs_density[s_val] * 100.0, "-", color=S_COLORS[s_val], lw=2.2,
                label=f"rim copper loss at the clear time, s = {s_val:.2f}")
    ax.axvline(r.house_density, color="k", lw=1.0, ls=":")
    ax.annotate(f"the house line: density {r.house_density:.2f}\n({HOUSE_GEOMETRY.width_um*1e3:.0f} nm on a "
                f"{HOUSE_PITCH_UM} µm pitch)",
                xy=(r.house_density, 0.0), xytext=(0, 6), textcoords="offset points", fontsize=6.9,
                ha="center", va="bottom")
    ax.annotate(f"loss = η(density) · 2s/(1−s) · t_over/H₀  — a PRODUCT of two levers\n\n"
                f"η here is ALL erosion: dishing at a {HOUSE_PITCH_UM} µm pitch is EXACTLY 0\n"
                f"(the cited trend crosses zero at ~{cmp.DISH_ZERO_PITCH_UM:.0f} µm; at the source's "
                f"{cmp.CITED.density_mask_pitch_um:.0f} µm\npitch it would be {r.dishing_efficiency_source_pitch:.1f} — "
                f"dishing is a pad-and-rail problem).\nErosion ∝ d/(1−d) diverges as the oxide that carries the pad "
                f"load runs out.\n\n"
                f"LEVER 1 — uniformity (s): and it must be PRESSURE. At matched speeds the\n"
                f"pad–wafer speed is ω·d at EVERY point (derived: {r.v_matched_centre_m_s:.3f} = "
                f"{r.v_matched_edge_m_s:.3f} m/s);\nPreston's V cannot carry a radius, so the fix went into the "
                f"zoned-pressure head.\n"
                f"LEVER 2 — density (η): design-rule density windows, slotting, dummy fill —\n"
                f"hold the layout inside a band the polish planarizes over its "
                f"{r.planarization_length_um[0]:.0f}–{r.planarization_length_um[1]:.0f} µm\nplanarization length (cited).\n"
                f"NOT A LEVER — polishing less: it lowers neither factor, it only fails to clear.",
                xy=(0.03, 0.975), xycoords="axes fraction", fontsize=6.9, ha="left", va="top",
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="lightgray", alpha=0.94))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 60.0)
    ax.set_xlabel("pattern density  d = line width / pitch   (at the house pitch)")
    ax.set_ylabel("trench copper lost at the rim  (%)   [η FLAGGED: a shape fit]")
    ax.set_title("The successor: the loss is a product of two levers — polish\n"
                 "UNIFORMITY (through pressure) and pattern DENSITY; 'polish less' is neither", fontsize=9.5)
    ax.legend(fontsize=6.8, loc="center left", bbox_to_anchor=(0.02, 0.42))
    ax.grid(True, alpha=0.15)

    fig.suptitle("Historical-modes B11 — CMP / planarity: COPPER CANNOT BE PLASMA-ETCHED, so the line is cut, flooded and polished back — "
                 "the polish defines the wire, and F4's copper era does not exist without it\n"
                 "clearing everywhere forces over-polishing somewhere (s/(1−s), no constant; 0 at s = 0)   ·   so the wire gains a spread "
                 "the transistor cannot explain   ·   and the window closes at s_crit = L/(2+L)\n"
                 "— THE RADIAL AMPLITUDE s IS A HOUSE NUMBER (the source averaged nine dies per wafer); the two closed forms, "
                 "the seam, the monotone shapes and the V ≡ ω·d identity are the claims",
                 fontsize=10.0)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.905))
    DOCS_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS_FIGURE, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µm, τ, ω, →, ∂ on legacy codepages

    r = compute()
    print_summary(r)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
