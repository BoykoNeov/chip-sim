"""The historical-modes B9 banked artifact: the BEOL interconnect — the delay the transistor doesn't set (F4).

The period back end (aluminium wires, scaled with the node) run against the observable that ended it — the
**wire/gate crossover** — showing *why chip speed stopped being a transistor property in the mid-1990s, what
copper actually bought, and why there was no third metal after it*. One figure, three panels:

  * **Left — the wall: the node-scaling ladder.** Walk a **global** line's cross-section down the real node
    ladder (1.0 → 0.25 µm, ``W`` = the node, ``H`` = 2``W``) holding the transistor fixed, and read the two
    terms. ``τ_gate`` is a **flat line** — nothing on this ladder touches it. ``τ_wire`` climbs as
    **1/W²** (``R ∝ 1/(W·H)`` rises; ``C`` does not move — the cited ``c_pul`` invariance), crosses
    ``τ_gate`` at ``W_x`` and keeps going. **The shape is the payload**: a crossing exists, it is
    monotone, and it happens with **no help from the transistor at all**. Copper's curve is the same
    curve, ``ρ_Cu/ρ_Al`` lower — *parallel*, not shallower.
  * **Middle — the payload: what a better transistor is still worth.** At the featured node, sweep
    ``I_Dsat`` and read the (normalised) clock rate. The **premise the sim still encodes** —
    :class:`fab_game.spec.SpeedBin`'s "clock speed ∝ drive current" — is the straight diagonal: 3% more
    drive, 3% faster part. Reality bends away from it, with slope **exactly** ``1 − wire_share``
    (:attr:`chip.interconnect.Delay.drive_sensitivity`), because ``τ_wire`` is a **common-mode** floor that
    adds a level and no spread. At the featured node an aluminium line leaves a 3%-better transistor worth
    **0.7%**. That is the pre-1997 assumption dying, in one panel.
  * **Right — the escape, and why there was no third metal.** ``W_x ∝ √ρ₀`` — **prefactor-free**. So
    Al→Cu's 1.58× in resistivity moves the crossover by ``√1.58`` = 0.80×, which is **0.64 of a 0.7× node
    step**: the celebrated 1997 escape bought about *two-thirds of one node*. And the √ is brutal in the
    other direction — buying the **next** node needs ``ρ ≤ 0.82 µΩ·cm``, while **silver, the best
    elemental conductor that exists, is 1.59** and buys 3%. **On the bulk-resistivity axis the ladder is
    out of metals.** That is not "no metal ever beats copper" — it is the *axis* being exhausted, which is
    exactly why the next move (slice 4) changes the axis: at narrow ``W`` the material enters only through
    ``ρ₀λ``, and the metal that **loses** on bulk ρ wins on geometry.

**The inversion that is the deep point of the arc (prefactor-free, and it cuts the other way):**
``W_x ∝ √I_Dsat`` exactly as ``W_x ∝ √ρ₀``. So a **2× better transistor pulls the crossover out to a 1.41×
wider wire — an *earlier* node — by the very same √2 that a 2× better metal pushes it in.** The transistor's
own progress is what creates the wire wall. The two improvements this whole sim can make trade against each
other one-for-one, and only one of them is on the wire's side.

The honesty ladder (the ``historical-modes.md`` triad; the F3 slice-3 lessons applied)
--------------------------------------------------------------------------------------
* **Tight — the shape, and it is the whole claim.** ``τ_gate`` is flat along a wire ladder
  (``∂τ_wire/∂I_Dsat = 0`` is structural in :mod:`chip.interconnect` — ``I_Dsat`` does not appear in the
  wire term), ``τ_wire ∝ 1/W²`` is monotone, so a crossing **exists** and the wire share rises to 1. No
  house constant can remove it.
* **Tight — the prefactor-free ratios.** ``W_x(Al)/W_x(Cu) = √(ρ_Al/ρ_Cu)`` = 1.26 and
  ``τ_wire(Al)/τ_wire(Cu) = ρ_Al/ρ_Cu`` = 1.58 contain **no** house constant: ``L``, ``c_pul``, ``V_dd``,
  ``C_load``, the aspect ratio and the Elmore factor cancel exactly. The right panel is built entirely out
  of these, and it is where the era claim lives (the F3 ``leakage_decades_saved`` discipline).
* **Tight — the damping law.** ``∂ln f/∂ln I_Dsat = 1 − wire_share``, **exact at every ``I_Dsat``** rather
  than a linearisation. Every house constant enters only through ``wire_share``, which is a *readout*.
* **A CONSISTENCY check, not a prediction — where the crossover lands.** ``W_x ∝ L``, and ``L`` is the
  module's dominant house lump (:data:`chip.interconnect.GLOBAL_WIRE_LENGTH_UM`, 1 mm — nothing in the sim
  carries a wire length). The **period device recipe below is a second lump-carrier**: across a plausible
  channel-doping range the landing moves by ~¾ of a node. So the fact that an *untuned* 1 mm line and a
  period-plausible transistor put ``W_x(Al)`` at **~0.45 µm** — the mid-1990s, where the cited history says
  gate and interconnect delay became roughly equal — is a **consistency check on the constants**, exactly
  the status of :mod:`chip.interconnect`'s IBM ~40% check. **It is not a prediction, and the figure says
  so.** Lead with the shape and the 1.26 shift.
* **Flagged — the magnitudes.** ``L``, the Elmore factor, ``V_dd`` and Al's ``ρ₀`` (all
  :mod:`chip.interconnect`'s, and all cancelling in the ratios); the node→(``W``, ``H``) mapping (``W`` =
  the node number, ``H`` = 2``W``) — historically the node name *was* roughly the metal half-pitch, but the
  aspect ratio is a house choice; and **silver's ``ρ₀`` = 1.59 µΩ·cm, handbook** (the same status as Al's).
  **Absolute picoseconds are not a claim this demo makes** — which is why the middle panel's axes are
  *normalised* rather than a fabricated GHz.

Where this demo stops, and what it hands to slice 4
---------------------------------------------------
The ladder is **capped at W = 0.20 µm** — not for tidiness, but because that is where this model stops
being honest. :mod:`chip.interconnect` is **bulk-ρ only** (``ρ_eff = ρ₀``), valid for ``W ≫ λ``; copper's
:meth:`chip.interconnect.Metal.bulk_regime_ok` refuses below ``5λ`` ≈ **0.194 µm**. The next rung of the
real node ladder is **0.18 µm — and the model may not speak there.** That cap is not a coincidence and it
is the cleanest possible hand-off: the cited history says the size effect became a **copper** problem at
sub-200 nm, and that below 130 nm interconnect delay worsens further despite low-κ. **Slice 4 promotes λ
from a guard to a term** (the ``ρ₀λ`` figure of merit + the un-scalable barrier), which is the only way the
Cu→Ru sign comes out right. Walking this ladder past its cap would fabricate exactly the number slice 4
exists to compute — the F3 magnitude trap.

Named ceilings — the axes this model does not carry (without these it overstates the wall)
------------------------------------------------------------------------------------------
* **Repeater / buffer insertion — the big one, and it softens everything above.** Real chips break long
  wires into segments with repeaters, which makes delay ∝ ``L`` and **not** ``L²``. The ladder here is the
  **un-repeated** global wire. Un-named, this figure silently claims wire delay is unfixable and
  **overstates the wall** — the F3 trap-limited-floor analogue: the mechanism that stops the extrapolation
  being real.
* **Low-κ ILD — the C-side mirror of high-κ (B8's own subject, inverted).** F3 bought physical thickness by
  *raising* κ; low-κ buys ``C_wire`` by *lowering* ε. Cited as real, and it arrived **with** copper at the
  250 nm node — so the historical escape was *two* moves and this figure draws one. Not modelled.
* **Electromigration** — copper's *other* win over aluminium, and a real reason Al died. A **reliability**
  mechanism: the wrong currency for a delay observable.
* **The driver↔wire cross terms.** ``R_driver·C_wire`` is dropped and *is* weakly ``I_Dsat``-dependent, so
  the licensed claim is "the wire's **intrinsic** RC is a common-mode floor", never "the transistor cannot
  touch the wire". See :mod:`chip.interconnect`.
* No crosstalk, no inductance, no multi-level RC stack, no via resistance. Run headless:

    python -m chip.demo_beol_history
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import device as dev
from . import interconnect as ic

# --- Recipe: one fixed transistor, one global wire, walked down the node ladder -------------------- #
METALS = ("Al", "Cu")

# The real historical node ladder — 0.7× per generation, and these are the actual node names (1.0 → 0.25
# µm spans ~1990 → ~1997). W = the node number: historically the node name *was* roughly the metal
# half-pitch, which is what makes this a node ladder rather than an invented geometry table. The aspect
# ratio H/W = 2 is a house choice (FLAGGED) — it cancels in every ratio this demo headlines.
NODE_LADDER_UM = (1.0, 0.7, 0.5, 0.35, 0.25)
NODE_SHRINK = 0.7                      # the linear shrink per generation — what "one node" means below
NEXT_NODE_UM = 0.18                    # the rung after 0.25 — and the one the bulk model REFUSES (below)
ASPECT_RATIO = 2.0                     # FLAGGED — house line aspect ratio H/W

# The ladder is capped at 0.20 µm because that is where this model stops being honest, not for tidiness:
# chip.interconnect is bulk-ρ only, and Cu's bulk_regime_ok refuses below 5λ ≈ 0.194 µm. The next real
# node (0.18) is already off-limits — which is precisely slice 4's territory (the size effect became a
# *copper* problem at sub-200 nm, cited). Walking past this would fabricate slice 4's number.
LADDER_FLOOR_UM = 0.20
W_LADDER_UM = np.linspace(NODE_LADDER_UM[0], LADDER_FLOOR_UM, 240)   # µm — 1.0 → 0.20

# The featured node — 250 nm, and it is the right rung for two independent reasons: it is the node at
# which copper and low-κ were introduced (cited), and its geometry (W = 0.25, H = 0.5) is *exactly*
# chip.interconnect.WireGeometry's default — the same line the game's F4 knob (slice 2) runs, so this
# panel and the game's binning inversion are talking about one wire. (The wire_share still differs from
# slice 2's ≈0.71: same wire, a *different transistor* — this demo's period 0.5 µm-era device vs the
# game's. That is the point rather than a discrepancy — wire_share is a readout of the pair, and τ_wire
# is the half that does not move.)
FEATURE_W_UM = 0.25

# The period transistor — FIXED while the wire scales, and read through the REAL, untouched device.py.
# A mid-1990s 0.5 µm-era n-MOS: ~10 nm gate oxide (the documented period value at that node) at the 3.3 V
# supply chip.interconnect already carries as period-appropriate. N_A is chosen to land V_t ≈ 0.58 V — a
# period-plausible threshold at 3.3 V — NOT to place the crossover. It is a lump-carrier all the same:
# see the module docstring's consistency-check note. Freezing the transistor is what isolates the claim —
# the crossover happens with no help from the gate — and the middle panel prices the freeze rather than
# hiding it (W_x ∝ √I_Dsat).
PERIOD_N_A = 2.0e17                    # cm⁻³ — p-type channel doping (lands a period-plausible V_t)
PERIOD_T_OX_UM = 10.0e-3               # µm — 10 nm gate oxide: the 0.5 µm node's documented value
PERIOD_CHANNEL_L_UM = 0.5              # µm — the 0.5 µm node's gate length
PERIOD_WIDTH_UM = 10.0                 # µm — device width W (sets I_Dsat and C_load together)

# The drive sweep for the middle panel — the transistor improving, at a fixed node. Normalised on both
# axes: absolute picoseconds (and so a "GHz" clock rate) are NOT a claim this module makes, since τ_wire
# carries the flagged L. The premise's diagonal and reality's bend are both prefactor-free shapes.
DRIVE_SWEEP = np.linspace(0.5, 4.0, 200)          # I_Dsat / I_Dsat(period), dimensionless
FEATURE_DRIVE_GAIN = 1.03                         # the "3% faster transistor" the premise prices at 3%

# Silver — the BOUND on the bulk-resistivity axis, deliberately NOT added to chip.interconnect.METALS:
# it was never an interconnect metal (electromigration, corrosion, and it does not damascene), so it is
# not a candidate — it is the answer to "is there a better conductor?". ρ₀ = 1.59 µΩ·cm is FLAGGED
# (handbook, the same status as Al's). λ = 53 nm is handbook too and is UNUSED by this demo's bulk axis —
# it is carried only for the flagged aside in the summary (Ag's ρ₀λ ≈ 84 is *worse* than Cu's 65 and even
# Ru's 77: the best bulk conductor is the worst scaling metal, which is slice 4's subject, not this one).
SILVER = ic.Metal("silver (the bound — never an interconnect metal)", rho0_uohm_cm=1.59, mfp_nm=53.0)
RHO_SWEEP_UOHM_CM = np.linspace(0.5, 3.0, 200)    # the "is there a better metal?" axis

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-beol-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-beol-history.png"


@dataclass(frozen=True)
class BeolHistoryResult:
    """The B9 bundle the figure and summary consume."""

    metals: tuple[str, ...]
    # the fixed period transistor — the flat term, read through the real device.py
    mos: dev.MOSDevice
    i_dsat_A: float
    c_load_F: float
    tau_gate_s: float                           # flat along the whole ladder: nothing here touches it
    # left — the ladder: the wire term climbing 1/W² past the transistor's flat line
    w_um: np.ndarray
    tau_wire_s: dict[str, np.ndarray]           # metal → τ_wire along the ladder
    wire_share: dict[str, np.ndarray]           # metal → the graded readout of who sets the speed
    crossover_um: dict[str, float]              # metal → W_x (carries L — a consistency check, not a claim)
    # middle — the payload: the premise's diagonal vs the damped reality, at the featured node
    feature: dict[str, ic.Delay]                # metal → the featured node's decomposed delay
    drive_ratio: np.ndarray                     # I_Dsat / I_Dsat(period)
    f_ratio: dict[str, np.ndarray]              # metal → f/f(period); "premise" → the ∝ I_Dsat diagonal
    # right — the escape and its ceiling: W_x/W_x(Cu) = √(ρ/ρ_Cu), prefactor-free
    rho_uohm_cm: np.ndarray
    wx_ratio_vs_cu: np.ndarray                  # √(ρ/ρ_Cu) — contains no house constant at all
    rho_for_next_node: float                    # the ρ the NEXT node would need — and nothing has it


def _period_device() -> tuple[dev.MOSDevice, float, float]:
    """The fixed period transistor → (device, ``I_Dsat``, ``C_load``), through the **real** ``device.py``.

    This is the "``device.py`` untouched" claim in one function: the chain runs exactly as it does
    everywhere else in the sim (the F2/F3 loose-coupling discipline — plain scalars across the boundary),
    and :mod:`chip.interconnect` never learns anything about it beyond two floats.
    """
    mos = dev.threshold_voltage(PERIOD_N_A, PERIOD_T_OX_UM, channel_length_um=PERIOD_CHANNEL_L_UM)
    i_dsat = dev.saturation_current(mos, V_GS=ic.V_DD_HOUSE, width_um=PERIOD_WIDTH_UM)
    c_load = ic.gate_load_capacitance(
        dev.oxide_capacitance(PERIOD_T_OX_UM), PERIOD_WIDTH_UM, PERIOD_CHANNEL_L_UM,
    )
    return mos, i_dsat, c_load


def _geometry(width_um: float) -> ic.WireGeometry:
    """The ladder's line at linewidth ``width_um`` — the house global length, ``H`` = ``AR``·``W``."""
    return ic.WireGeometry(width_um=width_um, thickness_um=ASPECT_RATIO * width_um)


def nodes_bought(width_ratio: float) -> float:
    """How many **0.7× node steps** a crossover shift of ``width_ratio`` is worth — the honest unit.

    A metal that moves ``W_x`` by 0.80× has *not* bought "a node": a node step is 0.70×, so it bought
    ``ln(0.80)/ln(0.70)`` = **0.64** of one. Stating a 0.80× shift as "roughly one node" rounds a win
    **up**, which is the one direction this repo never rounds (B8's ``floor_decades`` rule, in the
    crossover's currency). Al→Cu is the live instance: 1.58× in ρ is 0.64 of a node, not one.
    """
    if width_ratio <= 0.0:
        raise ValueError(f"width_ratio must be > 0, got {width_ratio}")
    return math.log(width_ratio) / math.log(NODE_SHRINK)


def compute() -> BeolHistoryResult:
    """Run the period device → the node ladder → the crossover → the damping law → the metal ceiling."""
    mos, i_dsat, c_load = _period_device()
    tau_gate = ic.gate_delay(c_load, i_dsat)

    # Left: the same fixed transistor, a scaling wire. τ_gate never moves; τ_wire climbs as 1/W².
    delays = {
        m: [ic.delay(_geometry(w), i_dsat, c_load, metal=m) for w in W_LADDER_UM] for m in METALS
    }
    tau_wire = {m: np.array([d.tau_wire_s for d in delays[m]]) for m in METALS}
    share = {m: np.array([d.wire_share for d in delays[m]]) for m in METALS}
    crossover = {
        m: ic.crossover_width_um(i_dsat, c_load, metal=m, aspect_ratio=ASPECT_RATIO) for m in METALS
    }

    # Middle: at the featured node, the transistor improves and the part does not follow. Normalised —
    # the premise (SpeedBin's "speed ∝ I_Dsat") is the diagonal; each metal bends away from it.
    feature = {m: ic.delay(_geometry(FEATURE_W_UM), i_dsat, c_load, metal=m) for m in METALS}
    f_ratio: dict[str, np.ndarray] = {"premise": DRIVE_SWEEP.copy()}     # f ∝ I_Dsat, exactly
    for m in METALS:
        tau = np.array([
            ic.delay(_geometry(FEATURE_W_UM), i_dsat * g, c_load, metal=m).tau_total_s
            for g in DRIVE_SWEEP
        ])
        f_ratio[m] = feature[m].tau_total_s / tau                        # (1/τ)/(1/τ_nom)

    # Right: W_x/W_x(Cu) = √(ρ/ρ_Cu) — prefactor-free, and the reason there was no third metal.
    wx_ratio = np.sqrt(RHO_SWEEP_UOHM_CM / ic.METALS["Cu"].rho0_uohm_cm)
    rho_next = ic.METALS["Cu"].rho0_uohm_cm * NODE_SHRINK**2             # ρ for one MORE node of W_x

    return BeolHistoryResult(
        metals=METALS, mos=mos, i_dsat_A=i_dsat, c_load_F=c_load, tau_gate_s=tau_gate,
        w_um=W_LADDER_UM, tau_wire_s=tau_wire, wire_share=share, crossover_um=crossover,
        feature=feature, drive_ratio=DRIVE_SWEEP, f_ratio=f_ratio,
        rho_uohm_cm=RHO_SWEEP_UOHM_CM, wx_ratio_vs_cu=wx_ratio, rho_for_next_node=rho_next,
    )


def print_summary(r: BeolHistoryResult) -> None:
    """Print the B9 story — the wire catches the transistor, copper buys 2/3 of a node, then nothing."""
    print("\nHistorical-modes B9: the BEOL interconnect (the delay the transistor doesn't set)\n")
    print(f"  The period transistor — FIXED while the wire scales, through the real, untouched device.py:")
    print(f"    a {PERIOD_CHANNEL_L_UM} µm-era n-MOS, {PERIOD_T_OX_UM*1e3:.0f} nm gate oxide,"
          f" W = {PERIOD_WIDTH_UM:.0f} µm, at V_dd = {ic.V_DD_HOUSE} V")
    print(f"    → V_t = {r.mos.V_t:.3f} V, I_Dsat = {r.i_dsat_A*1e3:.2f} mA, C_load ="
          f" {r.c_load_F*1e15:.1f} fF  ⇒  τ_gate = {r.tau_gate_s*1e12:.2f} ps, and NOTHING below moves it\n")

    top, bot = r.w_um[0], r.w_um[-1]
    print(f"  The wall — the node ladder ({top:.2f} → {bot:.2f} µm, a global line's cross-section scaling):")
    print(f"    τ_gate is FLAT (∂τ_wire/∂I_Dsat = 0 both ways: the two terms share no variable), while")
    print(f"    τ_wire ∝ 1/W² climbs — R ∝ 1/(W·H) rises, C ∝ L does not move (the cited c_pul invariance)")
    for m in r.metals:
        print(f"      {m}: τ_wire {r.tau_wire_s[m][0]*1e12:5.2f} → {r.tau_wire_s[m][-1]*1e12:5.1f} ps"
              f"   wire share {r.wire_share[m][0]*100:4.1f}% → {r.wire_share[m][-1]*100:4.1f}%"
              f"   crosses τ_gate at W_x ≈ {r.crossover_um[m]:.3f} µm")
    print(f"    → the crossing EXISTS and is monotone with no help from the transistor at all — the wire")
    print(f"      caught the gate because R rose, not because anything improved.")
    print(f"    [W_x ∝ L (a 1 mm house line) and moves ~a node across a plausible device recipe: that the")
    print(f"     untuned pair lands W_x(Al) ≈ {r.crossover_um['Al']:.2f} µm — the mid-1990s, where the cited")
    print(f"     history puts gate ≈ interconnect — is a CONSISTENCY check on the constants, NOT a prediction.]\n")

    al, cu = r.feature["Al"], r.feature["Cu"]
    gain = FEATURE_DRIVE_GAIN - 1.0
    print(f"  The payload — at the featured {FEATURE_W_UM*1e3:.0f} nm node, what a better transistor is worth:")
    print(f"    the premise the sim still encodes (fab_game.spec.SpeedBin: 'clock speed ∝ drive current')")
    print(f"    prices a {gain*100:.0f}% better transistor at {gain*100:.0f}% — ∂ln f/∂ln I_Dsat = 1. Reality:\n")
    print(f"      {'metal':<10} {'τ_gate':>9} {'τ_wire':>9} {'wire share':>11} {'∂ln f/∂ln I':>12} {'a +3% transistor buys':>22}")
    for m in r.metals:
        d = r.feature[m]
        print(f"      {m:<10} {d.tau_gate_s*1e12:>7.2f} ps {d.tau_wire_s*1e12:>7.2f} ps"
              f" {d.wire_share*100:>10.1f}% {d.drive_sensitivity:>12.3f} {gain*d.drive_sensitivity*100:>21.2f}%")
    print(f"\n    → exact at every I_Dsat (∂ln f/∂ln I = 1 − wire_share, from f = I/(A + τ_wire·I)) — not a")
    print(f"      linearisation. τ_wire is COMMON-MODE: it adds a level and no spread, so the across-wafer")
    print(f"      I_Dsat spread maps to a speed spread damped by exactly this factor with the transistor")
    print(f"      histogram bit-for-bit unchanged. The damping is SYMMETRIC — it pulls the slow tail up as")
    print(f"      it pulls the fast tail down: it costs the premium GRADE, never the die count.")
    print(f"    → and it cuts the other way too, prefactor-free: W_x ∝ √I_Dsat exactly as W_x ∝ √ρ₀, so a")
    print(f"      2× better transistor pulls the crossover out to a {math.sqrt(2.0):.2f}× WIDER wire — an"
          f" *earlier* node —")
    print(f"      by the same √2 a 2× better metal pushes it in. The transistor's own progress is what")
    print(f"      creates the wire wall.\n")

    # Both read the same way — "the challenger's W_x, relative to the incumbent's" — so neither is
    # inverted. crossover_width_ratio(a, b) is W_x(a)/W_x(b) = √(ρ_a/ρ_b), so the challenger goes FIRST
    # and a value < 1 is a win. Writing either as 1/ratio(incumbent, challenger) is the same number for
    # Al→Cu and the *reciprocal* for Cu→Ag, which is how the sign got away the first time this ran.
    shift = ic.crossover_width_ratio("Cu", "Al")          # W_x(Cu)/W_x(Al) = 0.796 — what 1997 bought
    ag_shift = ic.crossover_width_ratio(SILVER, "Cu")     # W_x(Ag)/W_x(Cu) = 0.973 — what is left to buy
    print(f"  The escape, and why there was no third metal (this block is PREFACTOR-FREE — pure ρ ratios):")
    print(f"    Al→Cu: ρ {ic.METALS['Al'].rho0_uohm_cm} → {ic.METALS['Cu'].rho0_uohm_cm} µΩ·cm"
          f" = {ic.wire_delay_ratio('Al','Cu'):.2f}× less wire delay ({(1-1/ic.wire_delay_ratio('Al','Cu'))*100:.0f}% —"
          f" IBM reported ~40%)")
    print(f"    but W_x ∝ √ρ₀, so the crossover moves only {shift:.3f}× = {nodes_bought(shift):.2f} OF A NODE."
          f"  The 1997 escape bought")
    print(f"    about two-thirds of one generation — it did not change the slope, it shifted the line.\n")
    print(f"    The next node needs W_x × {NODE_SHRINK} ⇒ ρ ≤ {r.rho_for_next_node:.2f} µΩ·cm."
          f"  Silver — the best elemental")
    print(f"    conductor there is — is {SILVER.rho0_uohm_cm} µΩ·cm: it buys {ag_shift:.3f}× ="
          f" {nodes_bought(ag_shift):+.2f} of a node. NOTHING is at {r.rho_for_next_node:.2f}.")
    print(f"    → ON THE BULK-RESISTIVITY AXIS, THE LADDER IS OUT OF METALS. Note what that is and is not:")
    print(f"      not 'no metal beats Cu' — the AXIS is exhausted, so the axis has to change. Below ~5λ the")
    print(f"      material enters only through ρ₀λ, where the ordering is NOT the bulk ordering (Ag's"
          f" ρ₀λ ≈ {SILVER.rho0_lambda:.0f}")
    print(f"      is worse than Cu's {ic.METALS['Cu'].rho0_lambda:.0f} — the best bulk conductor is the worst"
          f" scaling metal) [λ handbook, FLAGGED].")
    print(f"      That is slice 4: the ρ₀λ figure of merit and the barrier that does not scale.\n")

    print(f"  Where this demo stops — and it is the hand-off, not tidiness:")
    print(f"    the ladder is capped at W = {LADDER_FLOOR_UM:.2f} µm because chip.interconnect is BULK-ρ only")
    print(f"    (ρ_eff = ρ₀, valid for W ≫ λ) and Cu's bulk_regime_ok refuses below 5λ ≈"
          f" {5*ic.METALS['Cu'].mfp_nm/1e3:.3f} µm.")
    print(f"    The next real node — {NEXT_NODE_UM} µm — is already off-limits to this model. Cited history"
          f" agrees:")
    print(f"    the size effect became a COPPER problem at sub-200 nm, long before Ru was on a roadmap.\n")

    print(f"    [named ceilings, without which this figure overstates the wall: REPEATERS — real chips break")
    print(f"     long wires into segments, making delay ∝ L and NOT L²; this ladder is the un-repeated global")
    print(f"     wire. LOW-κ ILD — the C-side mirror of B8's high-κ, and it arrived WITH copper at 250 nm, so")
    print(f"     the historical escape was two moves and this draws one. Electromigration (Cu's other win) is")
    print(f"     a reliability currency, not a delay one. The driver↔wire Elmore cross terms are dropped, one")
    print(f"     of which IS weakly I_Dsat-dependent ⇒ the claim is 'the wire's INTRINSIC RC is a common-mode")
    print(f"     floor', never 'the transistor can't touch the wire'. Tight: the shape, the ratios, the law.]\n")


def save_figure(r: BeolHistoryResult) -> Path:
    """Render and save the B9 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    colors = {"Al": "tab:red", "Cu": "tab:orange"}
    labels = {"Al": "aluminium (period, ρ₀ = 2.65 µΩ·cm)", "Cu": "copper (1997, ρ₀ = 1.68 µΩ·cm)"}
    GATE_COLOR = "tab:blue"
    PREMISE_COLOR = "tab:gray"

    fig, axes = plt.subplots(1, 3, figsize=(19.5, 5.4))

    # --- Left: the wall — the wire term climbing past the transistor's flat line ---------------------- #
    ax = axes[0]
    for m in r.metals:
        ax.loglog(r.w_um, r.tau_wire_s[m] * 1e12, "-", color=colors[m], lw=2.2, label=labels[m])
    ax.axhline(r.tau_gate_s * 1e12, color=GATE_COLOR, ls="-", lw=2.2,
               label=f"τ_gate — the transistor, held FIXED ({r.tau_gate_s*1e12:.1f} ps)")
    ax.set_xlim(1.06, 0.163)                         # inverted: the ladder is walked *down* (scaling →)
    ax.set_ylim(0.45, 45.0)

    for m in r.metals:
        ax.plot([r.crossover_um[m]], [r.tau_gate_s * 1e12], "o", color=colors[m], ms=9, zorder=5)
    # sits directly above its own line, in the wedge the rising curves have not reached yet
    ax.annotate("τ_gate is FLAT — nothing on this ladder\ntouches the transistor",
                xy=(0.045, 0.565), xycoords="axes fraction", fontsize=7.2, color=GATE_COLOR,
                ha="left", va="bottom")
    ax.annotate(f"the crossover — W_x ≈ {r.crossover_um['Al']:.2f} / {r.crossover_um['Cu']:.2f} µm (Al / Cu).\n"
                f"Placement carries the house L: a\nCONSISTENCY check, not a prediction.",
                xy=(r.crossover_um["Al"], r.tau_gate_s * 1e12), xytext=(0.045, 0.175),
                textcoords="axes fraction", fontsize=7.0, color="k", va="center",
                arrowprops=dict(arrowstyle="->", color="k", lw=1.0))

    # the real node rungs, and the featured one
    for n in NODE_LADDER_UM:
        ax.axvline(n, color="k", ls=":", lw=0.6, alpha=0.35)
    ax.axvline(FEATURE_W_UM, color="k", ls="--", lw=1.1)
    ax.annotate("250 nm — Cu arrives\n(the middle panel)", xy=(FEATURE_W_UM * 1.03, 0.035),
                xycoords=("data", "axes fraction"), fontsize=7.0, ha="right", va="bottom")

    # The cap is an HONESTY device (B8's display-floor move, in this module's currency): the bulk model
    # simply may not speak below 5λ_Cu — and the next REAL node sits inside that refusal, which is the
    # cleanest way to draw the hand-off. Letting the ladder run on would fabricate slice 4's number.
    guard_um = 5.0 * ic.METALS["Cu"].mfp_nm / 1e3
    ax.axvspan(guard_um, 0.163, color="tab:purple", alpha=0.13)
    ax.axvline(NEXT_NODE_UM, color="tab:purple", ls="-.", lw=1.1)
    ax.annotate(f"the bulk ρ model refuses\nbelow 5λ_Cu ≈ {guard_um:.2f} µm — and\n"
                f"the next real node ({NEXT_NODE_UM} µm)\nis already in here → slice 4",
                xy=(0.988, 0.44), xycoords="axes fraction", fontsize=6.8, color="tab:purple",
                ha="right", va="top", style="italic", fontweight="bold")

    ax.set_xlabel("linewidth  W  (µm)   [= the node; a global line, H = 2W — scaling →]")
    ax.set_ylabel("delay  (ps)   [flagged scale — τ_wire ∝ L², L is a house lump]")
    ax.set_title("The wall: τ_wire ∝ 1/W² climbs (R rises, C does not)\n"
                 "past a transistor that never moved — a better metal\nshifts the line, it does not bend it",
                 fontsize=9.5)
    ax.legend(fontsize=6.9, loc="upper left")
    ax.grid(True, which="both", alpha=0.15)

    # --- Middle: the payload — the premise's diagonal vs the damped reality --------------------------- #
    ax = axes[1]
    ax.plot(r.drive_ratio, r.f_ratio["premise"], "--", color=PREMISE_COLOR, lw=2.2,
            label="the premise still in the tree: f ∝ I_Dsat\n(fab_game.spec.SpeedBin — slope 1)")
    for m in r.metals:
        d = r.feature[m]
        ax.plot(r.drive_ratio, r.f_ratio[m], "-", color=colors[m], lw=2.4,
                label=f"{m} at {FEATURE_W_UM*1e3:.0f} nm — slope = 1 − wire_share = {d.drive_sensitivity:.2f}")
    ax.plot([1.0], [1.0], "o", color="k", ms=7, zorder=5)
    ax.annotate("the period part", xy=(1.0, 1.0), xytext=(0.14, 0.62), textcoords="axes fraction",
                fontsize=7.2, arrowprops=dict(arrowstyle="->", color="k", lw=1.0))

    al = r.feature["Al"]
    gain = FEATURE_DRIVE_GAIN - 1.0
    ax.annotate(f"a +{gain*100:.0f}% transistor is worth\n+{gain*al.drive_sensitivity*100:.1f}% of a part on"
                f" an Al line\n(the premise says +{gain*100:.0f}%)\n\nτ_wire is COMMON-MODE: a level,\n"
                f"no spread ⇒ the wafer's I_Dsat\nspread stops making a speed\nspread. Tightening CD control\n"
                f"stops buying speed grades.",
                xy=(0.955, 0.045), xycoords="axes fraction", fontsize=7.2, color="k",
                ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="lightgray", alpha=0.9))
    ax.set_xlabel("drive current  I_Dsat / I_Dsat(period)   [the transistor improving →]")
    ax.set_ylabel("clock rate  f / f(period)   [normalised: absolute GHz is NOT a claim]")
    ax.set_title(f"The payload at {FEATURE_W_UM*1e3:.0f} nm: ∂ln f/∂ln I_Dsat = 1 − wire_share,\n"
                 f"EXACT at every I_Dsat — the pre-1997 premise dying", fontsize=9.5)
    ax.legend(fontsize=7.0, loc="upper left")
    ax.grid(True, alpha=0.15)

    # --- Right: the escape and its ceiling — W_x/W_x(Cu) = √(ρ/ρ_Cu), prefactor-free ------------------ #
    # This panel contains NO house constant at all: L, c_pul, V_dd, C_load, AR and the Elmore factor all
    # cancel in the ratio. It is the module's tightest claim rendered — and the setup for slice 4.
    ax = axes[2]
    ax.plot(r.rho_uohm_cm, r.wx_ratio_vs_cu, "-", color="k", lw=2.2)
    ax.set_xlim(3.05, 0.45)                          # inverted: better conductor to the right
    ax.set_ylim(0.50, 1.46)

    # Nothing exists past silver — the ceiling, and it is a fact about the periodic table rather than
    # about this model. The "one more node" target line lands INSIDE this band: that is the whole panel.
    ax.axvspan(SILVER.rho0_uohm_cm, 0.45, color="tab:red", alpha=0.10)
    ax.annotate("no elemental conductor exists\nin here — silver is the floor\nof the periodic table",
                xy=(0.585, 0.955), xycoords="axes fraction", fontsize=7.2, color="tab:red",
                ha="left", va="top", fontweight="bold")

    for m in r.metals:
        rho = ic.METALS[m].rho0_uohm_cm
        y = math.sqrt(rho / ic.METALS["Cu"].rho0_uohm_cm)
        ax.plot([rho], [y], "o", color=colors[m], ms=10, zorder=5)
        ax.annotate(f"{m}  {rho}", xy=(rho, y), xytext=(-8, 9), textcoords="offset points",
                    fontsize=7.6, color=colors[m], fontweight="bold", ha="center")
    ag_y = math.sqrt(SILVER.rho0_uohm_cm / ic.METALS["Cu"].rho0_uohm_cm)
    ax.plot([SILVER.rho0_uohm_cm], [ag_y], "o", color="dimgray", ms=10, zorder=5)
    ax.annotate(f"Ag {SILVER.rho0_uohm_cm} [handbook] — the best\nthere is: buys"
                f" {nodes_bought(ic.crossover_width_ratio(SILVER, 'Cu')):+.2f} of a node",
                xy=(SILVER.rho0_uohm_cm, ag_y), xytext=(0.36, 0.40), textcoords="axes fraction",
                fontsize=7.2, color="dimgray", ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color="dimgray", lw=1.0))

    # what Al→Cu actually bought, in node units — and what one MORE node would cost
    shift = ic.crossover_width_ratio("Cu", "Al")     # challenger first — see print_summary on the sign
    ax.annotate("", xy=(ic.METALS["Cu"].rho0_uohm_cm, 1.0), xytext=(ic.METALS["Al"].rho0_uohm_cm,
                math.sqrt(ic.METALS["Al"].rho0_uohm_cm / ic.METALS["Cu"].rho0_uohm_cm)),
                arrowprops=dict(arrowstyle="->", color="tab:green", lw=2.0))
    ax.annotate(f"1997: ρ ×{1/ic.wire_delay_ratio('Al','Cu'):.2f} …\nbut W_x only ×{shift:.2f}\n"
                f"= {nodes_bought(shift):.2f} of a 0.7× node",
                xy=(0.055, 0.615), xycoords="axes fraction", fontsize=7.4, color="tab:green",
                fontweight="bold", ha="left", va="top")

    ax.axhline(NODE_SHRINK, color="tab:purple", ls="--", lw=1.4)
    ax.axvline(r.rho_for_next_node, color="tab:purple", ls=":", lw=1.2)
    ax.annotate(f"one MORE node needs W_x ×{NODE_SHRINK}\n⇒ ρ ≤ {r.rho_for_next_node:.2f} µΩ·cm — and"
                f" nothing is there",
                xy=(r.rho_for_next_node, NODE_SHRINK), xytext=(0.30, 0.10), textcoords="axes fraction",
                fontsize=7.2, color="tab:purple", fontweight="bold", va="center",
                arrowprops=dict(arrowstyle="->", color="tab:purple", lw=1.0))
    ax.annotate("…but the AXIS is exhausted, not the search:\n"
                "below ~5λ the material enters only through ρ₀λ,\n"
                "where the ordering is NOT the bulk ordering —\n"
                "that is slice 4, and it is how a metal with 4×\n"
                "copper's bulk ρ still wins.",
                xy=(0.585, 0.775), xycoords="axes fraction", fontsize=6.8, color="dimgray",
                ha="left", va="top", style="italic")

    ax.set_xlabel("bulk resistivity  ρ₀  (µΩ·cm)   [better conductor →]")
    ax.set_ylabel("crossover width  W_x / W_x(Cu)   [= √(ρ/ρ_Cu) — prefactor-free]")
    ax.set_title("The escape and its ceiling: W_x ∝ √ρ₀, so copper bought\n"
                 "0.64 of a node — and on the bulk-ρ axis there is no third metal", fontsize=9.5)
    ax.grid(True, alpha=0.15)

    fig.suptitle("Historical-modes B9 — the BEOL interconnect: the wire caught the transistor with no help from it "
                 "(τ_wire ∝ 1/W², τ_gate flat), copper bought two-thirds\nof a node, and the bulk-resistivity axis "
                 "ran out of metals   ·   an UN-REPEATED global wire: real chips insert repeaters, which make "
                 "delay ∝ L and not L²", fontsize=10.0)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ₂, →, ρ, λ on legacy codepages

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
