"""The historical-modes B8 banked artifact: the high-κ gate dielectric — one thickness, two currencies (F3).

The period gate stack (thermal SiO₂, scaled thinner every node) run against the observable that ended it —
**direct gate tunnelling** — showing *why the SiO₂ roadmap hit a wall at ~1.5 nm, why HfO₂ cleared it
without moving the device at all, and why clearing it did not mean scaling forever*. One figure, three
panels:

  * **Left — the wall: the SiO₂ scaling ladder.** Walk the *electrical* gate (EOT) down the node ladder
    3.0 → 1.0 nm and read the gate leakage (:func:`chip.high_k.gate_leakage`). SiO₂'s physical thickness
    **is** its EOT (the κ=3.9 identity), so every ångström of electrical scaling is an ångström off the
    tunnel barrier: leakage climbs **~1 decade per ~1.8 Å**, monotonically, and crosses the ~1 A/cm²
    usability line at **EOT ≈ 1.5 nm** — with the ladder's last 2 nm costing **~11 decades**. HfO₂ walks
    the *same* electrical ladder ~5 decades below it; TiO₂ (κ=80, φ_B=**0**) is **dead flat** — 20× the
    physical thickness, no barrier, no benefit at any EOT. **The shape is the payload.** The HfO₂ a fab
    actually *builds* — with its interfacial layer — walks a few decades above the idealized one, and
    stops existing at all below EOT = t_IL (see the right panel).
  * **Middle — the discriminator: two currencies at one EOT (why no scalar can fake it).** At the 45 nm
    node's target **EOT = 1.0 nm**, build the same electrical gate in each material and read *both*
    currencies through the **real, untouched** :mod:`chip.device`: ``V_t`` and ``C_ox`` come out
    **byte-for-byte identical** for all three (the EOT identity — ``ε_SiO₂/EOT ≡ ε₀κ/t_phys``, so the
    capacitance path never learns which material it is), while ``t_phys`` moves 6.4× and ``j_gate``
    collapses. One input, two outputs, moving independently: a scalar "high-κ cuts leakage 1000×" cannot
    produce a **flat** V_t next to a collapsing leakage — it has nothing to be flat *about*.
  * **Right — the floor: the interfacial layer, and why the middle panel is a *ceiling*.** A real HfO₂
    gate grows ~0.5 nm of SiO₂ underneath it (unavoidable, and wanted — the interface quality of high-κ
    straight on Si is poor). Sweep that IL and the prefactor-free win falls **linearly**, ~0.56 decades
    per **ångström**, from the idealized ≳5.5 to ≳2.7 at a real 0.5 nm IL — and to **exactly zero** at
    ``t_IL = EOT``, where the high-κ has been squeezed out of its own budget and the "stack" is a plain
    SiO₂ gate again. That zero *is* the floor: **``EOT > t_IL`` for any κ, even κ=2000.** The IL is
    charged on **both** currencies at once, which is the point — it is the *better* barrier per nm
    (φ_B = 3.2 vs 1.4 eV) and **still** a pure loss, because per nm of *EOT spent* it returns 12.96
    where HfO₂ returns 25.78. A capacitance-only IL would have got that sign backwards.

Tight legs: the seams (SiO₂'s EOT **is** its physical thickness — :func:`chip.high_k.eot` is the identity
at κ=3.9; and ``t_IL = 0`` is the idealized stack byte-for-byte), the ``V_t``/``C_ox`` invariance at fixed
EOT (an identity, asserted here against the real ``device.py`` — and it holds across stack *structure*, not
just material), the **EOT floor** (geometric, prefactor-free), and the sign/monotonicity of the wall.
**Flagged — read the decades as "≳ N":** the prefactor is a house lump (it cancels in the ratios but sets
the absolute A/cm²), the tunnelling masses are fit-extracted with a wide spread (HfO₂ 0.08–0.2 m₀ bands the
win 3.9–9.5 decades at EOT = 1 nm). The reported literature spread for the matched-EOT win is **~2–6
decades** — *wider* than this model's idealized/as-built pair, so the IL is **one** real mechanism spreading
it, not the whole explanation. **The trap floor is not modelled** — real HfO₂ leakage is defect-limited well
before this model says so — and neither is how thin an IL can be made (~0.4–0.5 nm in practice, below which
it stops being a film and costs work-function control and reliability). The ladder is therefore **capped at
EOT = 1.0 nm**, inside the direct-tunnelling regime the model is honest in; the metal gate that rode in
*with* high-κ in 2007 is a named scope edge, not modelled here (a different discriminator — see
:mod:`chip.high_k`). Run headless:

    python -m chip.demo_highk_history
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import device as dev
from . import high_k as hk

# --- Recipe: one electrical gate, walked down the node ladder, built in three materials ----------- #
MATERIALS = ("SiO2", "HfO2", "TiO2")

# The EOT ladder — the *electrical* gate the roadmap scaled. Capped at 1.0 nm: below that this model
# leaves the regime it is honest in (direct tunnelling), and HfO₂'s real leakage is trap-limited long
# before the exponent says so. 3.0 nm ≈ the 0.25 µm-era gate; 1.0 nm ≈ the 45 nm node's target EOT.
EOT_LADDER_UM = np.linspace(3.0e-3, 1.0e-3, 200)     # µm — 3.0 → 1.0 nm
FEATURE_EOT_UM = 1.0e-3                              # µm — 1.0 nm: the node target the wall blocked
WALL_J_A_CM2 = 1.0                                   # A/cm² — the usability line (Robertson's scale)

# The interfacial layer — a real HfO₂ stack is NOT one layer. ~0.5 nm of SiO₂ sits under the high-κ: it
# grows during deposition/anneal whether or not you want it, and it is wanted (mobility, interface
# quality). It is the reason the idealized win is a *ceiling*: at this thickness the model's HfO₂ win
# halves, 5.6 → 2.8 decades. Ando puts the practical IL limit at ~0.4–0.5 nm — thinner stops being a film
# and costs work-function control and reliability, a scope edge this model does not carry (it prices any
# IL; a fab cannot build any IL).
FEATURE_T_IL_UM = 0.5e-3                             # µm — 0.5 nm: a representative 45 nm-era SiO₂ IL
IL_SWEEP_UM = np.linspace(0.0, FEATURE_EOT_UM * 0.98, 200)   # µm — 0 → (just short of) the EOT floor

# The device the gate stack sits on (a representative scaled n-MOSFET; the invariance below holds for
# ANY recipe — it is an identity, not a fit — so these numbers are illustrative, not load-bearing).
CHANNEL_N_A = 5.0e17           # cm⁻³ — p-type channel (a scaled-node channel doping)
CHANNEL_L_UM = 0.045           # µm — the 45 nm node's gate length (geometry only; V_t never reads it)
GATE = "n+poly"                # the metal gate that rode in with high-κ is a named scope edge, not this
DEVICE_WIDTH_UM = 1.0          # µm — device width W
# The V_t-adjust implant (§5) — not decoration: at a 1 nm gate the depletion term Q_dep/C_ox is tiny, so
# an unadjusted n-MOS sits at V_t ≈ 0.02 V (a device that never turns off). Every scaled node meters this
# acceptor sheet in; it lands V_t ≈ 0.35 V, an honest 45 nm-era threshold. It cannot disturb the
# invariance below — ΔV_t = q·dose/C_ox reads the *same* C_ox all three materials share.
VT_ADJUST_DOSE = 7.0e12        # cm⁻² — acceptor adjust dose (the dose-controlled source, cf. demo_implant)
VT_ADJUST_KIND = "p"           # acceptor ⇒ raises V_t (n-MOS)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-highk-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-highk-history.png"


@dataclass(frozen=True)
class HighKHistoryResult:
    """The B8 bundle the figure and summary consume."""

    materials: tuple[str, ...]
    # left — the ladder: the same electrical gate, each material's leakage as EOT scales down
    eot_um: np.ndarray
    j_gate: dict[str, np.ndarray]               # material → gate leakage along the ladder (A/cm²)
    j_gate_real: np.ndarray                     # HfO₂ *as built* — with the interfacial layer under it
    wall_eot_um: float                          # the EOT where SiO₂ crosses the usability line
    # middle — the discriminator at the feature EOT: two currencies, read through the real device.py
    stacks: dict[str, hk.GateStack]             # material → the matched-EOT stack (idealized, no IL)
    mos: dict[str, dev.MOSDevice]               # material → the device that stack makes (V_t, C_ox)
    real_stack: hk.GateStack                    # HfO₂ + the IL — the stack a fab actually builds
    # right — the IL: what it costs, and the floor it imposes (both prefactor-free)
    t_il_um: np.ndarray
    decades_saved_vs_t_il: np.ndarray           # the win, destroyed linearly by the IL → 0 at the floor


def _mos_at(eot_um: float) -> dev.MOSDevice:
    """The device an ``eot_um`` electrical gate makes — the **real** ``device.py``, fed EOT as ``t_ox_um``.

    This is the whole "``device.py`` untouched" claim in one line: EOT *is* the number
    :func:`chip.device.oxide_capacitance` wants (``ε_SiO₂/EOT ≡ ε₀κ/t_phys``), so the material never
    enters here — which is exactly why the right panel's V_t comes out flat.
    """
    return dev.threshold_voltage(
        CHANNEL_N_A, eot_um, gate=GATE, channel_length_um=CHANNEL_L_UM,
        implant_dose=VT_ADJUST_DOSE, implant_kind=VT_ADJUST_KIND,
    )


def floor_decades(decades: float) -> str:
    """Format a "≳ N decades" claim — **floored** to 1 dp, never rounded (the honesty rule).

    ``≳ N`` asserts the win is *at least* N, so the displayed N may only ever be **below** the computed
    value. Plain ``f"{x:.1f}"`` rounds to nearest and quietly breaks that: the featured HfO₂ win is
    5.565 decades, which ``.1f`` renders "5.6" — a number the model does not support. Flooring renders
    "5.5". The difference is cosmetically nil and exactly the kind of overstatement this module refuses
    everywhere else (see :func:`chip.high_k.leakage_decades_saved` on reading the result as "≳ N").
    """
    return f"{math.floor(decades * 10.0) / 10.0:.1f}"


def _wall_eot_um(j_sio2: np.ndarray, eot: np.ndarray) -> float:
    """The EOT where the SiO₂ ladder crosses :data:`WALL_J_A_CM2` — interpolated on log(J), monotone."""
    return float(np.interp(np.log10(WALL_J_A_CM2), np.log10(j_sio2), eot))


def compute() -> HighKHistoryResult:
    """Run the SiO₂ ladder → the wall → the matched-EOT escape → the IL's cost → the bundle."""
    # Left: each material walks the SAME electrical ladder; only t_phys (and so the tunnelling) differs.
    j_gate = {
        m: np.array([hk.gate_leakage(hk.DIELECTRICS[m].thickness_for_eot_um(e), m) for e in EOT_LADDER_UM])
        for m in MATERIALS
    }
    # …and the HfO₂ a fab actually builds carries the IL. It walks the same ladder a few decades higher,
    # and only exists above the floor the IL imposes (EOT > t_IL) — off which gate_stack refuses to speak.
    j_gate_real = np.array([
        hk.gate_stack(e, "HfO2", t_il_um=FEATURE_T_IL_UM).gate_leakage_A_cm2 if e > FEATURE_T_IL_UM
        else np.nan
        for e in EOT_LADDER_UM
    ])
    wall = _wall_eot_um(j_gate["SiO2"], EOT_LADDER_UM)

    # Middle: the same electrical gate at the feature EOT, built in each material — both currencies.
    stacks = {m: hk.gate_stack(FEATURE_EOT_UM, m) for m in MATERIALS}
    mos = {m: _mos_at(stacks[m].eot_um) for m in MATERIALS}
    real_stack = hk.gate_stack(FEATURE_EOT_UM, "HfO2", t_il_um=FEATURE_T_IL_UM)

    # Right: what the IL costs. Prefactor-free — this panel contains no flagged magnitude at all.
    decades_vs_il = np.array([
        hk.leakage_decades_saved(FEATURE_EOT_UM, "HfO2", t_il_um=t) for t in IL_SWEEP_UM
    ])

    return HighKHistoryResult(
        materials=MATERIALS, eot_um=EOT_LADDER_UM, j_gate=j_gate, j_gate_real=j_gate_real,
        wall_eot_um=wall, stacks=stacks, mos=mos, real_stack=real_stack,
        t_il_um=IL_SWEEP_UM, decades_saved_vs_t_il=decades_vs_il,
    )


def print_summary(r: HighKHistoryResult) -> None:
    """Print the B8 story — SiO₂ scales into a tunnelling wall; HfO₂ clears it without moving the device."""
    print("\nHistorical-modes B8: the high-κ gate dielectric (one thickness, two currencies)\n")
    sio2, hfo2 = r.j_gate["SiO2"], r.j_gate["HfO2"]
    top, bot = r.eot_um[0] * 1e3, r.eot_um[-1] * 1e3
    print(f"  The wall — the SiO₂ ladder ({top:.1f} → {bot:.1f} nm EOT, the electrical gate the roadmap scaled):")
    print(f"    physical thickness == EOT (the κ=3.9 identity) → every Å of scaling comes off the barrier")
    print(f"    leakage {sio2[0]:.1e} → {sio2[-1]:.1e} A/cm²  =  {np.log10(sio2[-1]/sio2[0]):.1f} decades"
          f"  (~1 decade per {hk.decade_thickness_um(hk.SIO2.barrier_eV, hk.SIO2.tunnel_mass_rel)*1e4:.2f} Å)")
    print(f"    → crosses the {WALL_J_A_CM2:.0f} A/cm² usability line at EOT ≈ {r.wall_eot_um*1e3:.2f} nm"
          f"  — the wall the SiO₂ roadmap stopped at\n")

    print(f"  The escape — the same electrical gate at EOT = {FEATURE_EOT_UM*1e3:.1f} nm, in three materials"
          f" + the stack a fab actually builds  (through the real, untouched device.py):\n")
    print(f"    {'material':<26} {'κ':>5} {'t_phys':>9} {'V_t':>8} {'C_ox':>11} {'j_gate':>11} {'vs SiO₂':>10}")
    # The as-built stack is a row here for the same reason it is a bar on the figure: without it the
    # table quotes the *idealized* win as the 45 nm number. Decades are FLOORED, not rounded — a "≳ N"
    # claim may only ever be understated, and plain `.1f` renders the 5.565 win as "5.6".
    for m in (*r.materials, "real"):
        s = r.real_stack if m == "real" else r.stacks[m]
        d = _mos_at(s.eot_um)
        # "≳" reads as a *win* claim, so only a positive gets it; a loss (TiO₂) is stated as a loss.
        # Flooring is the conservative direction either way — it can only ever understate the benefit.
        won = s.decades_saved_vs_sio2 > 0.0
        saved = ("—" if m == "SiO2" else
                 f"≳{floor_decades(s.decades_saved_vs_sio2)} dec" if won else
                 f"{floor_decades(s.decades_saved_vs_sio2)} dec")
        name = f"{s.material} + {s.t_il_um*1e3:.1f} nm IL" if s.has_interfacial_layer else s.material
        print(f"    {name:<26} {s.kappa:>5.1f} {s.t_phys_um*1e3:>7.2f} nm {d.V_t:>7.4f} V"
              f" {d.C_ox:>10.4e} {s.gate_leakage_A_cm2:>11.1e} {saved:>10}")

    # Counted over every row of the table above — the two-layer stack included, which is the stronger
    # claim: the invariance is over the stack's STRUCTURE, not just which material it is made of.
    rows = [*r.mos.values(), _mos_at(r.real_stack.eot_um)]
    vts = {d.V_t for d in rows}
    coxs = {d.C_ox for d in rows}
    hf = r.stacks["HfO2"]
    print(f"\n    → V_t and C_ox are BYTE-FOR-BYTE identical across all {len(rows)} ({len(vts)} distinct V_t,"
          f" {len(coxs)} distinct C_ox) — the two-layer stack included: only the")
    print(f"      TOTAL EOT ever reaches device.py, so it cannot tell these stacks apart at all."
          f" HfO₂ buys {hf.thickness_gain:.1f}× the physical thickness at the same")
    print(f"      electrical gate → ≳{floor_decades(hf.decades_saved_vs_sio2)} decades less leakage,")
    print(f"      for free device-side. TiO₂ (κ=80, φ_B=0) buys {r.stacks['TiO2'].thickness_gain:.0f}× the"
          f" thickness and leaks flat out at every EOT — 'more κ is better' is FALSE.")

    # The IL — the honest EOT floor, and why the row above is a CEILING rather than a prediction.
    real = r.real_stack
    print(f"\n  The floor — the interfacial layer (the bare HfO₂ row is IDEALIZED; no fab builds it):\n")
    print(f"    a real HfO₂ gate grows ~{real.t_il_um*1e3:.1f} nm of SiO₂ underneath it — unavoidable, and wanted")
    print(f"    (interface quality). It is charged on BOTH currencies at once:")
    print(f"      · capacitance — its EOT adds ({hk.K_SIO2} is SiO₂'s κ, so {real.t_il_um*1e3:.1f} nm of IL"
          f" costs {real.eot_floor_um*1e3:.1f} nm of EOT), leaving")
    print(f"        the high-κ only {(FEATURE_EOT_UM - real.eot_floor_um)*1e3:.1f} nm of budget →"
          f" t_phys {hf.t_phys_um*1e3:.2f} → {real.t_phys_um*1e3:.2f} nm")
    print(f"      · barrier — it adds its OWN α·t to the exponent. SiO₂ is the *better* barrier per nm"
          f" ({hk.SIO2.decay_per_um*1e-3:.1f} vs {hk.HFO2.decay_per_um*1e-3:.1f} /nm) …")
    print(f"        … and is STILL a pure loss, because per nm of EOT *spent* it returns only"
          f" {hk.SIO2.decay_per_eot_um*1e-3:.1f} where HfO₂ returns {hk.HFO2.decay_per_eot_um*1e-3:.1f}.")
    print(f"        (That ~{hk.HFO2.decay_per_eot_um/hk.SIO2.decay_per_eot_um:.1f}× IS the whole high-κ win,"
          f" handed back. A capacitance-only IL would have got this sign BACKWARDS.)")
    print(f"\n    → the win halves: ≳{floor_decades(hf.decades_saved_vs_sio2)} decades (idealized) →"
          f" ≳{floor_decades(real.decades_saved_vs_sio2)} decades (as built), and V_t does not move for"
          f" this either")
    print(f"      — only the stack's TOTAL EOT ever reaches device.py, so it cannot tell a two-layer"
          f" stack from a one-layer one.")
    print(f"    → and the hard part, which no κ fixes: EOT > {real.eot_floor_um*1e3:.1f} nm, FULL STOP."
          f" The IL's own EOT is a floor under the whole stack")
    print(f"      for ANY κ (even κ=2000) — geometric, no barrier physics, no calibrated constant. Every"
          f" Å of IL costs {(hf.decades_saved_vs_sio2 - hk.leakage_decades_saved(FEATURE_EOT_UM, 'HfO2', t_il_um=0.1e-3)):.2f} decades")
    print(f"      of the win, linearly, hitting exactly ZERO at t_IL = EOT — where the high-κ is squeezed"
          f" out and the 'stack' is a plain SiO₂ gate again.")
    print(f"\n    [read the decades as '≳ N' — exponent-dominated: the shared prefactor cancels in the ratio")
    print(f"     but m* is fit-extracted (HfO₂ 0.08–0.2 m₀ ⇒ a 3.9–9.5-decade band); the reported lit. spread")
    print(f"     for the matched-EOT win is ~2–6 decades, WIDER than the idealized/as-built pair above — the")
    print(f"     IL is one real mechanism spreading it, not the whole story. The trap floor is NOT modelled,")
    print(f"     nor is how thin an IL can be made (~0.4–0.5 nm in practice). Ladder capped at {bot:.1f} nm —")
    print(f"     the direct-tunnelling regime. Tight: the seams, the V_t/C_ox invariance (an identity), the")
    print(f"     EOT floor (geometric), and the wall's sign/monotonicity.]\n")


def save_figure(r: HighKHistoryResult) -> Path:
    """Render and save the B8 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    colors = {"SiO2": "tab:red", "HfO2": "tab:green", "TiO2": "tab:purple"}
    labels = {"SiO2": "thermal SiO₂ (period, κ=3.9)",
              "HfO2": "HfO₂, idealized — no interfacial layer (κ=25)",
              "TiO2": "TiO₂ (κ=80, φ_B=0 — the counterexample)"}
    IL_COLOR = "tab:olive"

    fig, axes = plt.subplots(1, 3, figsize=(18.5, 4.9))

    # --- Left: the wall — the scaling ladder in the electrical gate ---------------------------------- #
    ax = axes[0]
    eot_nm = r.eot_um * 1e3
    for m in r.materials:
        ax.semilogy(eot_nm, r.j_gate[m], "-", color=colors[m], lw=2.2, label=labels[m])
    # The HfO₂ a fab actually builds — the idealized curve above it is the ceiling, not the product.
    ax.semilogy(eot_nm, r.j_gate_real, "-", color=IL_COLOR, lw=2.2,
                label=f"HfO₂ + {r.real_stack.t_il_um*1e3:.1f} nm SiO₂ interfacial layer (as built)")
    ax.axhline(WALL_J_A_CM2, color="k", ls="--", lw=1.2)
    ax.annotate(f"~{WALL_J_A_CM2:.0f} A/cm² — the usability line", xy=(eot_nm[0], WALL_J_A_CM2 * 3),
                fontsize=7.4, ha="left", va="bottom")
    ax.axvline(r.wall_eot_um * 1e3, color="tab:red", ls=":", lw=1.3)
    ax.annotate(f"SiO₂'s wall\nEOT ≈ {r.wall_eot_um*1e3:.2f} nm", xy=(r.wall_eot_um * 1e3, 0.80),
                xycoords=("data", "axes fraction"), fontsize=7.4, color="tab:red", ha="center", va="bottom")
    ax.axvline(FEATURE_EOT_UM * 1e3, color="tab:blue", ls=":", lw=1.3)
    ax.annotate("the 45 nm\nnode's target", xy=(FEATURE_EOT_UM * 1e3, 0.80),
                xycoords=("data", "axes fraction"), fontsize=7.4, color="tab:blue", ha="right", va="bottom")

    # The display floor is an HONESTY device, not a cosmetic one. The exponent keeps falling off the thick
    # end of the ladder (HfO₂ at EOT=3 nm is 19 nm of physical oxide → ~1e-22 A/cm²), but that number is
    # meaningless: a real stack is trap-limited *long* before it, and this model does not carry that floor
    # (a named scope edge in chip.high_k). Letting curves EXIT the axis says "off scale, don't read a number
    # here"; plotting them would put a fabricated 1e-22 in front of a student — and would squash SiO₂'s
    # wall, the actual payload, into a third of the panel.
    ax.set_ylim(1.0e-12, 1.0e10)
    ax.annotate("↓ off scale — real stacks hit a trap-limited\nfloor this model does not carry",
                xy=(0.98, 0.04), xycoords="axes fraction", fontsize=6.8, color="dimgray",
                ha="right", va="bottom", style="italic")
    ax.invert_xaxis()                                # the ladder is walked *down* — scaling reads left→right
    ax.set_xlabel("equivalent oxide thickness  EOT  (nm)   [the electrical gate — scaling →]")
    ax.set_ylabel("gate leakage  J_g  (A/cm²)   [flagged scale]")
    ax.set_title("The wall: SiO₂'s physical thickness IS its EOT, so scaling\n"
                 f"the gate thins the tunnel barrier (~1 decade / "
                 f"{hk.decade_thickness_um(hk.SIO2.barrier_eV, hk.SIO2.tunnel_mass_rel)*1e4:.1f} Å)", fontsize=9.5)
    ax.legend(fontsize=7.4, loc="lower left")
    ax.grid(True, which="both", alpha=0.15)

    # --- Middle: the discriminator — two currencies at one EOT (through the real device.py) ---------- #
    # The as-built HfO₂ stack sits in this panel too, and not for completeness: without it the "2007,
    # 45 nm" label would sit on the *idealized* bar, i.e. this figure would present the no-IL number as
    # the shipped product. It also widens the invariance claim from material to stack STRUCTURE — the
    # two-layer stack reaches device.py as one EOT, so its V_t is on the same flat line.
    ax = axes[1]
    bars = (*r.materials, "real")
    stacks = {**r.stacks, "real": r.real_stack}
    bar_colors = {**colors, "real": IL_COLOR}
    x = np.arange(len(bars))
    j = [stacks[m].gate_leakage_A_cm2 for m in bars]
    ax.bar(x, j, width=0.55, color=[bar_colors[m] for m in bars], alpha=0.85)
    ax.set_yscale("log")
    ax.set_ylabel("gate leakage  J_g  (A/cm²)   [log — collapses]", color="tab:gray")
    ax.set_ylim(min(j) * 1e-3, max(j) * 1e4)
    for i, m in enumerate(bars):
        s = stacks[m]
        label = (f"t_phys\n{s.t_phys_um*1e3:.1f} nm" if not s.has_interfacial_layer else
                 f"{s.t_phys_um*1e3:.1f} nm HfO₂\n+ {s.t_il_um*1e3:.1f} nm IL")
        ax.text(i, s.gate_leakage_A_cm2 * 3.0, label,
                ha="center", va="bottom", fontsize=7.6, color=bar_colors[m], fontweight="bold")

    ax2 = ax.twinx()                                 # the other currency — dead flat
    vt = [_mos_at(stacks[m].eot_um).V_t for m in bars]
    ax2.plot(x, vt, "o--", color="tab:blue", lw=2.0, ms=9)
    ax2.set_ylabel("threshold voltage  V_t  (V)   [identical — the EOT identity]", color="tab:blue")
    # Seat the (flat) V_t line above every bar: the bars span decades, so any lower placement runs the
    # line *inside* a bar and hides the panel's whole point — that it does not move.
    ax2.set_ylim(vt[0] - 0.9, vt[0] + 0.1)
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax2.annotate(f"V_t = {vt[0]:.4f} V — byte-for-byte identical for all four, the two-layer\n"
                 f"stack included (C_ox too: only the TOTAL EOT ever reaches device.py)",
                 xy=(1.0, vt[0]), xycoords="data", xytext=(0.5, 0.58), textcoords="axes fraction",
                 fontsize=7.6, color="tab:blue", ha="center", va="bottom",
                 arrowprops=dict(arrowstyle="->", color="tab:blue", lw=1.0))

    ax.set_xticks(x)
    ax.set_xticklabels(["SiO₂\n(period)", "HfO₂\n(idealized:\nno IL)", "TiO₂\n(κ=80,\nno barrier)",
                        "HfO₂ + IL\n(2007, 45 nm:\nas built)"], fontsize=8.0)
    ax.set_title(f"The discriminator at EOT = {FEATURE_EOT_UM*1e3:.1f} nm: one input, two currencies\n"
                 f"(HfO₂: {r.stacks['HfO2'].thickness_gain:.1f}× the thickness, same device,"
                 f" ≳{floor_decades(r.stacks['HfO2'].decades_saved_vs_sio2)} decades less leakage"
                 f" — ≳{floor_decades(r.real_stack.decades_saved_vs_sio2)} as built)", fontsize=9.5)

    # --- Right: the interfacial layer — the honest floor, and why the middle panel is a ceiling ------ #
    # This panel is PREFACTOR-FREE: decades_saved is a ratio, so the house J₀ cancels exactly and nothing
    # flagged is plotted here. It is the module's tightest claim rendered — the cost is a straight line
    # and the floor is where that line hits zero.
    ax = axes[2]
    t_il_nm = r.t_il_um * 1e3
    ax.plot(t_il_nm, r.decades_saved_vs_t_il, "-", color=IL_COLOR, lw=2.4)
    ax.axhline(0.0, color="k", lw=1.0)
    floor_nm = FEATURE_EOT_UM * 1e3
    ax.axvspan(floor_nm, floor_nm * 1.06, color="tab:red", alpha=0.18)
    ax.annotate("EOT floor:\nt_IL = EOT.\nNo κ — not even\nκ=2000 — gets\nbelow this.",
                xy=(floor_nm, 0.52), xycoords=("data", "axes fraction"), fontsize=7.2, color="tab:red",
                ha="right", va="center", fontweight="bold")

    # the two ends of the line, and the stack a fab actually ships in between
    ax.plot([0.0], [r.stacks["HfO2"].decades_saved_vs_sio2], "o", color=colors["HfO2"], ms=9, zorder=5)
    ax.annotate(f"idealized: no IL\n≳{floor_decades(r.stacks['HfO2'].decades_saved_vs_sio2)} decades"
                f"  ← the ceiling,\nnot a product",
                xy=(0.0, r.stacks["HfO2"].decades_saved_vs_sio2), xytext=(0.13, 0.86),
                textcoords="axes fraction", fontsize=7.4, color=colors["HfO2"], va="top",
                arrowprops=dict(arrowstyle="->", color=colors["HfO2"], lw=1.0))
    ax.plot([r.real_stack.t_il_um * 1e3], [r.real_stack.decades_saved_vs_sio2], "o",
            color=IL_COLOR, ms=9, zorder=5)
    ax.annotate(f"as built (~{r.real_stack.t_il_um*1e3:.1f} nm IL)\n"
                f"≳{floor_decades(r.real_stack.decades_saved_vs_sio2)} decades — about HALF",
                xy=(r.real_stack.t_il_um * 1e3, r.real_stack.decades_saved_vs_sio2), xytext=(0.40, 0.60),
                textcoords="axes fraction", fontsize=7.4, color=IL_COLOR, va="top",
                arrowprops=dict(arrowstyle="->", color=IL_COLOR, lw=1.0))
    ax.annotate("← the high-κ is squeezed out:\nthe 'stack' is a plain SiO₂ gate,\nso it saves nothing",
                xy=(floor_nm * 0.985, 0.0), xytext=(0.52, 0.14), textcoords="axes fraction",
                fontsize=7.2, color="dimgray", va="top",
                arrowprops=dict(arrowstyle="->", color="dimgray", lw=1.0))

    per_A = (r.stacks["HfO2"].decades_saved_vs_sio2
             - hk.leakage_decades_saved(FEATURE_EOT_UM, "HfO2", t_il_um=0.1e-3))
    ax.set_xlabel(f"interfacial-layer thickness  t_IL  (nm)   [SiO₂, under the HfO₂]")
    ax.set_ylabel("gate-leakage decades saved vs SiO₂\n[prefactor-free — cited constants only]")
    ax.set_title(f"The floor: the IL is charged on BOTH currencies at once —\n"
                 f"it is the *better* barrier and still a pure loss ({per_A:.2f} dec/Å)", fontsize=9.5)
    ax.set_xlim(-0.03, floor_nm * 1.06)
    ax.grid(True, alpha=0.15)

    fig.suptitle("Historical-modes B8 — the high-κ gate dielectric: the SAME electrical gate (V_t, C_ox "
                 "untouched) with a 6.4× thicker tunnel barrier — the wall SiO₂ could not scale past, "
                 "and the interfacial layer that floors the escape",
                 fontsize=11)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ₂, →, κ on legacy codepages

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
