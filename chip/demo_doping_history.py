"""The historical-modes A1 banked artifact: the dose-control wall pre-implant doping hit.

The honest accounting of the cheat :mod:`chip.demo_implant` makes to "match" a light V_t-adjust dose by
predep — it tunes the surface concentration ``N_s`` *below* the solid-solubility limit, which is not a
free knob. This demo shows, on one figure, why the light-dose regime belonged to **ion implantation**:

  * **Left — the period sources are all surface-flooded.** The classic predep sources
    (:data:`chip.doping_history.SOURCES`) as-deposited: the *constant* sources (POCl₃, BBr₃) pin the
    surface at the **solid-solubility limit** (an ``erfc``); the *limited* source (spin-on-glass) meters a
    finite dose to a surface *below* solubility — the one real physics axis (constant vs limited).
  * **Right — the dose-control wall.** A constant source's **controllable-dose floor**
    (:func:`chip.doping_history.predep_dose_floor`) sits *above* the ~5e11 V_t-adjust dose across the
    stated ``(T_predep, t_min)`` box — predep cannot reproducibly meter it. Spin-on-glass reaches lower
    (the pre-implant workaround) but **imprecisely, with no independent depth control**. Ion implant
    meters any dose electrically (beam charge), depth set *independently* by energy — the decoupling that
    modernised the ~1968 predep planar line.

The wall is a **FLAGGED controllability proxy**, sign-robust only across the box printed on the figure;
the tight legs are the predep dose identity and the constant-source-at-solubility **seam** (see
:mod:`chip.doping_history`). Run headless (saves the figure, prints the flow):

    python -m chip.demo_doping_history
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import diffusion_dopant as dd
from . import doping_history as dh

# --- The recipe: as-deposited period profiles + the dose-control wall box -------------------- #
LENGTH_UM = 1.2                 # substrate depth domain (µm) for the as-deposited profiles
N_CELLS = 800
PREDEP_T = 900.0               # °C — the predep temperature for the as-deposited constant-source erfcs
PREDEP_MIN = 20.0              # min — a visible erfc predep for the left panel
SOG_DOSE = 5.0e12             # cm⁻² — the finite dose the spin-on-glass (limited source) meters

# The FLAGGED (T_predep, t_min) controllability box the wall's sign is asserted across (module honesty
# label). t_min is the smallest reproducible predep time on the steep √t curve — a house input.
BOX_T_CELSIUS = (800.0, 900.0)     # °C — the predep-temperature corners
BOX_T_MIN_S = (0.1, 1.0)           # s  — the minimum-controllable-predep-time corners

# The reachable-dose bands for the right panel (cm⁻²). The constant floor is COMPUTED (predep_dose_floor);
# the others are FLAGGED house edges: spin-on-glass reaches lower than a constant source but imprecisely;
# implant is beam-current-limited (~1e10) and precise. The V_t-adjust target is chosen with margin below
# the constant floor.
VT_DOSE = dh.VT_ADJUST_DOSE        # 5e11 cm⁻²
SOG_PRACTICAL_FLOOR = 2.0e11       # cm⁻² — finite source reaches lower, but imprecise (FLAGGED)
IMPLANT_FLOOR = 1.0e10             # cm⁻² — implant meters precisely down to ~beam-current limits (FLAGGED)
DOSE_CEILING = 1.0e15              # cm⁻² — top of the reachable bars (all methods reach high)
IMPLANT_ENERGY_KEV = 15.0          # keV — the shallow V_t-adjust energy (depth set INDEPENDENTLY of dose)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-doping-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-doping-history.png"


@dataclass(frozen=True)
class DopingHistoryResult:
    """The A1 dose-control-wall bundle the figure and summary consume."""

    x_um: np.ndarray
    profiles: tuple[dh.SourceProfile, ...]     # the as-deposited period-source profiles (left panel)
    # the dose-control wall (right panel), all cm⁻²:
    floor_min: float                            # min constant-predep floor across the box (the wall edge)
    floor_max: float                            # max constant-predep floor across the box
    floors_by_source: dict[str, dict[str, float]]  # per constant source: min/max floor across the box
    vt_dose: float
    sog_floor: float
    implant_floor: float
    implant_R_p_um: float                       # the implant's depth at IMPLANT_ENERGY_KEV (independent knob)


def compute() -> DopingHistoryResult:
    """Run the as-deposited period profiles + the dose-control-wall box → :class:`DopingHistoryResult`."""
    grid = dd.uniform_grid(LENGTH_UM * dd.CM_PER_UM, N_CELLS)

    # Left panel: each period source as-deposited (constant → erfc at solubility; limited → finite-dose Gaussian).
    profiles = (
        dh.run_source(grid, dh.SOURCES["BBr3"], T_predep_celsius=PREDEP_T, t_predep_s=PREDEP_MIN * 60.0),
        dh.run_source(grid, dh.SOURCES["POCl3"], T_predep_celsius=PREDEP_T, t_predep_s=PREDEP_MIN * 60.0),
        dh.run_source(grid, dh.SOURCES["SOG"], T_predep_celsius=PREDEP_T, t_predep_s=PREDEP_MIN * 60.0,
                      dose=SOG_DOSE),
    )

    # Right panel: the constant-source dose floor across the (T_predep, t_min) box — the wall.
    floors_by_source: dict[str, dict[str, float]] = {}
    all_floors: list[float] = []
    for key in ("BBr3", "POCl3"):
        src = dh.SOURCES[key]
        vals = [
            dh.predep_dose_floor(src, T_predep_celsius=T, t_min_s=t)
            for T in BOX_T_CELSIUS for t in BOX_T_MIN_S
        ]
        floors_by_source[key] = {"min": min(vals), "max": max(vals)}
        all_floors.extend(vals)

    # The implant's depth at the V_t-adjust energy — the knob it moves INDEPENDENTLY of dose.
    R_p, _ = dd.range_statistics("B", IMPLANT_ENERGY_KEV)

    return DopingHistoryResult(
        x_um=grid.centers / dd.CM_PER_UM,
        profiles=profiles,
        floor_min=min(all_floors), floor_max=max(all_floors),
        floors_by_source=floors_by_source,
        vt_dose=VT_DOSE, sog_floor=SOG_PRACTICAL_FLOOR, implant_floor=IMPLANT_FLOOR,
        implant_R_p_um=R_p / dd.CM_PER_UM,
    )


def print_summary(r: DopingHistoryResult) -> None:
    """Print the dose-control-wall story — the light dose predep cannot reproducibly meter."""
    print("\nHistorical-modes A1: the dose-control wall pre-implant doping hit "
          "(why the light V_t-adjust dose belonged to implant)\n")
    print("  the period sources, as-deposited (all surface-peaked):")
    for p in r.profiles:
        kind = "constant (erfc at solubility)" if p.source.source_type == "constant" else \
               "limited (finite dose → surface below solubility)"
        print(f"    {p.source.name:<38} {kind:<44} surface N = {p.surface_conc:.2e} cm⁻³")
    print()
    print(f"  the dose-control wall (FLAGGED, across the box T_predep ∈ {BOX_T_CELSIUS} °C, "
          f"t_min ∈ {BOX_T_MIN_S} s):")
    for key, band in r.floors_by_source.items():
        src = dh.SOURCES[key]
        print(f"    {src.name:<38} controllable-dose floor Q_min = "
              f"{band['min']:.2e} … {band['max']:.2e} cm⁻²")
    print(f"    → the V_t-adjust dose {r.vt_dose:.1e} cm⁻² sits BELOW every constant floor "
          f"(min {r.floor_min:.2e}) — predep cannot reproducibly meter it.")
    print(f"    → spin-on-glass (limited) reaches ~{r.sog_floor:.1e} cm⁻² (lower — the pre-implant "
          f"workaround) but imprecise, with NO independent depth control.")
    print(f"    → ion implant meters ~{r.implant_floor:.1e} cm⁻² precisely, depth set INDEPENDENTLY by "
          f"energy (R_p = {r.implant_R_p_um:.3f} µm at {IMPLANT_ENERGY_KEV:.0f} keV).")
    print(f"  → the WALL is a flagged controllability proxy (sign holds across the stated box, margin "
          f"{r.floor_min / r.vt_dose:.1f}×); the tight legs are the predep dose identity + the seam.\n")


def save_figure(r: DopingHistoryResult) -> Path:
    """Render and save the A1 dose-control-wall artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    # --- Left: the period sources, all surface-flooded (constant at solubility; limited below) ---
    ax = axes[0]
    colors = {"BBr3": "tab:orange", "POCl3": "tab:green", "SOG": "tab:blue"}
    for p in r.profiles:
        key = next(k for k, s in dh.SOURCES.items() if s is p.source)
        style = "-" if p.source.source_type == "constant" else "--"
        ax.semilogy(r.x_um, np.maximum(p.N, 1e12), style, color=colors[key], lw=2, label=p.source.name)
    for key in ("B", "P"):
        ax.axhline(dd.DOPANTS[key].N_solid_solubility, color="0.6", ls=":", lw=1)
    ax.text(0.98, 0.97, "constant sources pinned\nat solid solubility (dotted)",
            transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color="0.35")
    ax.set_xlabel("depth  x  (µm)")
    ax.set_ylabel("concentration  N(x)  (cm⁻³)")
    ax.set_xlim(0.0, 0.12)
    ax.set_ylim(1e16, 5e21)
    ax.set_title("The period sources: all surface-peaked, constant ones flooded at solubility", fontsize=9.5)
    ax.legend(fontsize=8, loc="lower left")

    # --- Right: the dose-control wall — reachable dose per method (log x), the V_t target below the floor ---
    ax = axes[1]
    rows = [
        ("constant predep\n(POCl₃ / BBr₃)", r.floor_min, DOSE_CEILING, "tab:orange", None,
         "wall: can't meter below floor"),
        ("limited source\n(spin-on-glass)", r.sog_floor, DOSE_CEILING, "tab:blue", "///",
         "reaches lower, but imprecise / no depth control"),
        ("ion implant\n(beam charge)", r.implant_floor, DOSE_CEILING, "tab:green", None,
         "precise; depth = energy (independent)"),
    ]
    for i, (label, lo, hi, color, hatch, note) in enumerate(rows):
        ax.barh(i, width=np.log10(hi) - np.log10(lo), left=np.log10(lo), height=0.55,
                color=color, alpha=0.35 if hatch else 0.6, hatch=hatch, edgecolor=color)
        ax.text(np.log10(lo), i + 0.34, f"  {note}", fontsize=7.3, color="0.3", va="bottom")
    ax.axvline(np.log10(r.vt_dose), color="tab:red", ls="--", lw=1.8)
    ax.text(np.log10(r.vt_dose) - 0.08, -0.5, f"V_t-adjust target {r.vt_dose:.0e}", color="tab:red",
            fontsize=8, ha="right", va="center")
    ax.axvspan(np.log10(1e9), np.log10(r.floor_min), color="tab:red", alpha=0.05)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([row[0] for row in rows], fontsize=8.5)
    ax.set_ylim(-0.6, 3.4)
    xticks = [10, 11, 12, 13, 14, 15]
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"$10^{{{t}}}$" for t in xticks])
    ax.set_xlim(9.7, 15.2)
    ax.set_xlabel("reproducibly reachable dose  Q  (cm⁻²)")
    ax.set_title(f"The dose-control wall: predep floor > V_t target (box {BOX_T_CELSIUS} °C, "
                 f"{BOX_T_MIN_S} s)", fontsize=9.5)
    ax.text(0.98, 0.04, "floor FLAGGED (controllability proxy);\nsign holds across the box",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.3, color="0.35")

    fig.suptitle("Historical-modes A1 — the dose-control wall: light doses belonged to ion implantation",
                 fontsize=12)
    fig.tight_layout()
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ⁻³, → on legacy codepages

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
