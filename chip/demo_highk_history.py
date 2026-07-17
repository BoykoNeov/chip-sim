"""The historical-modes B8 banked artifact: the high-κ gate dielectric — one thickness, two currencies (F3).

The period gate stack (thermal SiO₂, scaled thinner every node) run against the observable that ended it —
**direct gate tunnelling** — showing *why the SiO₂ roadmap hit a wall at ~1.5 nm, and why HfO₂ cleared it
without moving the device at all*. One figure, two panels:

  * **Left — the wall: the SiO₂ scaling ladder.** Walk the *electrical* gate (EOT) down the node ladder
    3.0 → 1.0 nm and read the gate leakage (:func:`chip.high_k.gate_leakage`). SiO₂'s physical thickness
    **is** its EOT (the κ=3.9 identity), so every ångström of electrical scaling is an ångström off the
    tunnel barrier: leakage climbs **~1 decade per ~1.8 Å**, monotonically, and crosses the ~1 A/cm²
    usability line at **EOT ≈ 1.5 nm** — with the ladder's last 2 nm costing **~11 decades**. HfO₂ walks
    the *same* electrical ladder ~5 decades below it; TiO₂ (κ=80, φ_B=**0**) is **dead flat** — 20× the
    physical thickness, no barrier, no benefit at any EOT. **The shape is the payload.**
  * **Right — the discriminator: two currencies at one EOT (why no scalar can fake it).** At the 45 nm
    node's target **EOT = 1.0 nm**, build the same electrical gate in each material and read *both*
    currencies through the **real, untouched** :mod:`chip.device`: ``V_t`` and ``C_ox`` come out
    **byte-for-byte identical** for all three (the EOT identity — ``ε_SiO₂/EOT ≡ ε₀κ/t_phys``, so the
    capacitance path never learns which material it is), while ``t_phys`` moves 6.4× and ``j_gate``
    collapses. One input, two outputs, moving independently: a scalar "high-κ cuts leakage 1000×" cannot
    produce a **flat** V_t next to a collapsing leakage — it has nothing to be flat *about*.

Tight legs: the seam (SiO₂'s EOT **is** its physical thickness — :func:`chip.high_k.eot` is the identity at
κ=3.9), the ``V_t``/``C_ox`` invariance at fixed EOT (an identity, asserted here against the real
``device.py``), and the sign/monotonicity of the wall. **Flagged — read the decades as "≳ N":** the
prefactor is a house lump (it cancels in the ratios but sets the absolute A/cm²), the tunnelling masses are
fit-extracted with a wide spread (HfO₂ 0.08–0.2 m₀ bands the win 3.9–9.5 decades at EOT = 1 nm; lit. ~3–5),
and **the trap floor is not modelled** — real HfO₂ leakage is defect-limited well before this model says so.
The ladder is therefore **capped at EOT = 1.0 nm**, inside the direct-tunnelling regime the model is
honest in; the metal gate that rode in *with* high-κ in 2007 is a named scope edge, not modelled here (a
different discriminator — see :mod:`chip.high_k`). Run headless:

    python -m chip.demo_highk_history
"""
from __future__ import annotations

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
    wall_eot_um: float                          # the EOT where SiO₂ crosses the usability line
    # right — the discriminator at the feature EOT: two currencies, read through the real device.py
    stacks: dict[str, hk.GateStack]             # material → the matched-EOT stack
    mos: dict[str, dev.MOSDevice]               # material → the device that stack makes (V_t, C_ox)


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


def _wall_eot_um(j_sio2: np.ndarray, eot: np.ndarray) -> float:
    """The EOT where the SiO₂ ladder crosses :data:`WALL_J_A_CM2` — interpolated on log(J), monotone."""
    return float(np.interp(np.log10(WALL_J_A_CM2), np.log10(j_sio2), eot))


def compute() -> HighKHistoryResult:
    """Run the SiO₂ ladder → the wall → the matched-EOT escape → :class:`HighKHistoryResult`."""
    # Left: each material walks the SAME electrical ladder; only t_phys (and so the tunnelling) differs.
    j_gate = {
        m: np.array([hk.gate_leakage(hk.DIELECTRICS[m].thickness_for_eot_um(e), m) for e in EOT_LADDER_UM])
        for m in MATERIALS
    }
    wall = _wall_eot_um(j_gate["SiO2"], EOT_LADDER_UM)

    # Right: the same electrical gate at the feature EOT, built in each material — both currencies.
    stacks = {m: hk.gate_stack(FEATURE_EOT_UM, m) for m in MATERIALS}
    mos = {m: _mos_at(stacks[m].eot_um) for m in MATERIALS}

    return HighKHistoryResult(
        materials=MATERIALS, eot_um=EOT_LADDER_UM, j_gate=j_gate, wall_eot_um=wall,
        stacks=stacks, mos=mos,
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
          f"  (through the real, untouched device.py):\n")
    print(f"    {'material':<26} {'κ':>5} {'t_phys':>9} {'V_t':>8} {'C_ox':>11} {'j_gate':>11} {'vs SiO₂':>10}")
    for m in r.materials:
        s, d = r.stacks[m], r.mos[m]
        saved = "—" if m == "SiO2" else f"{s.decades_saved_vs_sio2:+.1f} dec"
        print(f"    {s.material:<26} {s.kappa:>5.1f} {s.t_phys_um*1e3:>7.2f} nm {d.V_t:>7.4f} V"
              f" {d.C_ox:>10.4e} {s.gate_leakage_A_cm2:>11.1e} {saved:>10}")

    vts = {d.V_t for d in r.mos.values()}
    coxs = {d.C_ox for d in r.mos.values()}
    hf = r.stacks["HfO2"]
    print(f"\n    → V_t and C_ox are BYTE-FOR-BYTE identical across all three ({len(vts)} distinct V_t,"
          f" {len(coxs)} distinct C_ox): the EOT identity means the capacitance path never")
    print(f"      learns which material it is. HfO₂ buys {hf.thickness_gain:.1f}× the physical thickness at"
          f" the same electrical gate → ≳{hf.decades_saved_vs_sio2:.1f} decades less leakage,")
    print(f"      for free device-side. TiO₂ (κ=80, φ_B=0) buys {r.stacks['TiO2'].thickness_gain:.0f}× the"
          f" thickness and leaks flat out at every EOT — 'more κ is better' is FALSE.")
    print(f"\n    [read the decades as '≳ N' — exponent-dominated: the shared prefactor cancels in the ratio")
    print(f"     but m* is fit-extracted (HfO₂ 0.08–0.2 m₀ ⇒ a 3.9–9.5-decade band; lit. ~3–5), and the trap")
    print(f"     floor is NOT modelled. The ladder is capped at {bot:.1f} nm — the direct-tunnelling regime.")
    print(f"     Tight: the seam, the V_t/C_ox invariance (an identity), and the wall's sign/monotonicity.]\n")


def save_figure(r: HighKHistoryResult) -> Path:
    """Render and save the B8 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    colors = {"SiO2": "tab:red", "HfO2": "tab:green", "TiO2": "tab:purple"}
    labels = {"SiO2": "thermal SiO₂ (period, κ=3.9)",
              "HfO2": "HfO₂ (modern, κ=25)",
              "TiO2": "TiO₂ (κ=80, φ_B=0 — the counterexample)"}

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: the wall — the scaling ladder in the electrical gate ---------------------------------- #
    ax = axes[0]
    eot_nm = r.eot_um * 1e3
    for m in r.materials:
        ax.semilogy(eot_nm, r.j_gate[m], "-", color=colors[m], lw=2.2, label=labels[m])
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
    ax.annotate("↓ the exponent keeps falling, but real stacks hit a\n"
                "trap-limited floor this model does not carry (off scale)",
                xy=(0.97, 0.03), xycoords="axes fraction", fontsize=6.8, color="dimgray",
                ha="right", va="bottom", style="italic")
    ax.invert_xaxis()                                # the ladder is walked *down* — scaling reads left→right
    ax.set_xlabel("equivalent oxide thickness  EOT  (nm)   [the electrical gate — scaling →]")
    ax.set_ylabel("gate leakage  J_g  (A/cm²)   [flagged scale]")
    ax.set_title("The wall: SiO₂'s physical thickness IS its EOT, so scaling\n"
                 f"the gate thins the tunnel barrier (~1 decade / "
                 f"{hk.decade_thickness_um(hk.SIO2.barrier_eV, hk.SIO2.tunnel_mass_rel)*1e4:.1f} Å)", fontsize=9.5)
    ax.legend(fontsize=7.4, loc="lower left")
    ax.grid(True, which="both", alpha=0.15)

    # --- Right: the discriminator — two currencies at one EOT (through the real device.py) ----------- #
    ax = axes[1]
    x = np.arange(len(r.materials))
    j = [r.stacks[m].gate_leakage_A_cm2 for m in r.materials]
    ax.bar(x, j, width=0.55, color=[colors[m] for m in r.materials], alpha=0.85)
    ax.set_yscale("log")
    ax.set_ylabel("gate leakage  J_g  (A/cm²)   [log — collapses]", color="tab:gray")
    ax.set_ylim(min(j) * 1e-3, max(j) * 1e4)
    for i, m in enumerate(r.materials):
        s = r.stacks[m]
        ax.text(i, s.gate_leakage_A_cm2 * 3.0, f"t_phys\n{s.t_phys_um*1e3:.1f} nm",
                ha="center", va="bottom", fontsize=7.6, color=colors[m], fontweight="bold")

    ax2 = ax.twinx()                                 # the other currency — dead flat
    vt = [r.mos[m].V_t for m in r.materials]
    ax2.plot(x, vt, "o--", color="tab:blue", lw=2.0, ms=9)
    ax2.set_ylabel("threshold voltage  V_t  (V)   [identical — the EOT identity]", color="tab:blue")
    # Seat the (flat) V_t line above every bar: the bars span decades, so any lower placement runs the
    # line *inside* a bar and hides the panel's whole point — that it does not move.
    ax2.set_ylim(vt[0] - 0.9, vt[0] + 0.1)
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax2.annotate(f"V_t = {vt[0]:.4f} V — byte-for-byte identical for all three\n"
                 f"(C_ox too: the capacitance path never learns the material)",
                 xy=(1.0, vt[0]), xycoords="data", xytext=(0.5, 0.58), textcoords="axes fraction",
                 fontsize=7.6, color="tab:blue", ha="center", va="bottom",
                 arrowprops=dict(arrowstyle="->", color="tab:blue", lw=1.0))

    ax.set_xticks(x)
    ax.set_xticklabels(["SiO₂\n(period)", "HfO₂\n(2007, 45 nm)", "TiO₂\n(κ=80, no barrier)"], fontsize=8.5)
    ax.set_title(f"The discriminator at EOT = {FEATURE_EOT_UM*1e3:.1f} nm: one input, two currencies\n"
                 f"(HfO₂: {r.stacks['HfO2'].thickness_gain:.1f}× the thickness, same device,"
                 f" ≳{r.stacks['HfO2'].decades_saved_vs_sio2:.1f} decades less leakage)", fontsize=9.5)

    fig.suptitle("Historical-modes B8 — the high-κ gate dielectric: the SAME electrical gate (V_t, C_ox "
                 "untouched) with a 6.4× thicker tunnel barrier — the wall SiO₂ could not scale past",
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
