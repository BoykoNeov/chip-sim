"""The fab-line game — G1: the harness + the vertical slice (the dramatic win).

A gamified, full-production-line layer built **on top of** chip-sim (ADR 0005,
``docs/plans/fab-game.md``). This package owns everything the validated physics layer must
not — the wafer state, the pipeline driver, spec windows, the stochastic spread + yield, and
the rework mechanic — and consumes the *already-validated* ``chip/`` + ``engines/`` physics in
**one direction only** (``fab_game → chip/engines``, never the reverse; an import-direction
guard enforces it).

G1 is **all reuse, zero new physics.** It wires the existing diffusion → oxidation →
lithography → device back end through a state/variation/spec/yield/rework harness and banks
the artifact: *one bad knob → a dead die, with the failure trail.* The chain the demo drives
is **defocus → printed CD → channel length → I_Dsat** (never ``V_t`` — the device model's own
scope edge: ``V_t`` carries no channel-length term, only ``saturation_current`` reads the CD).

Build order (slice-first *within* G1): the deterministic single-die path is pinned
**bit-for-bit** against :func:`chip.demo_device.compute` (the seam test) before a die map,
the stochastic layer, yield, or rework exists — so "the harness does not change the physics"
is proven first.
"""
from __future__ import annotations

from .state import (
    DefectEvent,
    Die,
    DieStepRecord,
    StepRecord,
    Verdict,
    WaferState,
    build_die_map,
    die_area_cm2,
)
from .recipe import (
    DEFAULT_RECIPE,
    CzochralskiKnobs,
    DeviceKnobs,
    DiffusionKnobs,
    EtchDepositionKnobs,
    LithoKnobs,
    OxidationKnobs,
    PackagingKnobs,
    PurificationKnobs,
    Recipe,
    WaferPrepKnobs,
)
from .variation import NO_VARIATION, DiePerturbation, Variation
from .spec import DEFAULT_SPECS, GeometrySpec, SpecSet, SpecWindow, SpeedBin, SpeedBins
from .defects import scatter_defects
from .pipeline import (
    BatchResult,
    LineResult,
    ReworkRecord,
    diagnose,
    initial_wafer,
    rework_deposition,
    rework_litho,
    rework_polish,
    run_batch,
    run_line,
    wafer_yield,
)
from .scoring import BIN_PRICES, REWORK_COSTS, SCRAP_COST, WAFER_COST, ScoreCard, score_wafer
from .game import (
    MARKET_BINS,
    GameConfig,
    GameSession,
    ReworkSpec,
    RunRecord,
    new_session,
    play,
    process_wafer,
    scrap_wafer,
)

__all__ = [
    # state
    "Die", "DieStepRecord", "StepRecord", "Verdict", "WaferState", "build_die_map",
    "DefectEvent", "die_area_cm2",
    # recipe
    "Recipe", "PurificationKnobs", "CzochralskiKnobs", "WaferPrepKnobs", "DiffusionKnobs",
    "OxidationKnobs", "LithoKnobs", "EtchDepositionKnobs", "DeviceKnobs", "PackagingKnobs",
    "DEFAULT_RECIPE",
    # variation
    "Variation", "DiePerturbation", "NO_VARIATION",
    # spec
    "SpecSet", "SpecWindow", "GeometrySpec", "SpeedBin", "SpeedBins", "DEFAULT_SPECS",
    # defects
    "scatter_defects",
    # pipeline
    "run_line", "run_batch", "initial_wafer", "wafer_yield", "diagnose", "rework_litho",
    "rework_polish", "rework_deposition", "LineResult", "BatchResult", "ReworkRecord",
    # scoring (G7)
    "score_wafer", "ScoreCard", "BIN_PRICES", "WAFER_COST", "SCRAP_COST", "REWORK_COSTS",
    # game / roguelike session (G7)
    "GameConfig", "GameSession", "RunRecord", "ReworkSpec", "MARKET_BINS",
    "new_session", "process_wafer", "scrap_wafer", "play",
]
