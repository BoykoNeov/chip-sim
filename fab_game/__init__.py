"""The fab-line game — a gamified full-production-line layer built **on top of** chip-sim.

Layered per ADR 0005 (``docs/plans/fab-game.md``). This package owns everything the validated
physics layer must not — the wafer state, the pipeline driver, spec windows, the stochastic
spread + yield, and the rework mechanic — and consumes the *already-validated* ``chip/`` +
``engines/`` physics in **one direction only** (``fab_game → chip/engines``, never the reverse;
an import-direction guard enforces it). New *process physics* always lands in the physics layer;
this package holds balance, spec limits, and fun.

What it now spans (see ``fab_game/README.md`` for the full milestone log):

* **The line** — sand → a binned, packaged chip: Czochralski boule, wafer prep, purification,
  the validated diffusion/oxidation/litho/device back end, etch & deposition, packaging (G1–G7),
  plus the crystal-growth deepenings (CG-1/2/3) and the scope-edge promotions (C1/D1/A2/A1/E1/S4).
* **The play modes** — the G7 roguelike session (:mod:`~fab_game.game`), the guided 4-knob
  dashboard (:mod:`~fab_game.dashboard`), the staged sand→chip **journey**
  (:mod:`~fab_game.journey`), and the Textual TUI (:mod:`~fab_game.tui`, the ``[tui]`` extra,
  the *only* ``textual`` importer and not re-exported here so the fast lane stays headless).
* **Device targets** (:mod:`~fab_game.targets`) — "good is application-relative": re-score the
  *same* wafer against partially-inverted specs (fast-logic / low-power / HV-I/O / high-res /
  power-rectifier), reading the cited device outputs :mod:`chip.breakdown` (avalanche ``BV``) and
  :mod:`chip.reverse_recovery` (``t_rr ∝ τ``).

The load-bearing discipline (ADR 0005 §5): the deterministic single-die path is pinned
**bit-for-bit** against :func:`chip.demo_device.compute` (the seam test), and the game layer is
tested for *mechanics invariants*, not cited magnitudes.
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
from .targets import (
    FAST_LOGIC,
    LOW_POWER,
    MARKET_BINS,
    MOSFET_FLAVORS,
    DeviceTarget,
    TargetGrade,
    disposition,
    grade_for,
    regrade,
)
from .dashboard import (
    dashboard_recipe,
    dashboard_summary,
    knob_errors,
    oxide_minutes_error,
    run_dashboard,
)
from .game import (
    GameConfig,
    GameSession,
    ReworkSpec,
    RunRecord,
    new_session,
    play,
    process_wafer,
    scrap_wafer,
)
from .session_view import (
    history_trail,
    inspect_line,
    oxide_recipe,
    projected_vt,
    session_header,
    session_summary,
    turn_line,
    turn_recipe,
)
from .guide import (
    GLOSSARY,
    GLOSSARY_BY_KEY,
    MODE_INTRO,
    Term,
    dashboard_guide,
    glossary_text,
    roguelike_guide,
    term_block,
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
    # targets ("good is relative" — multi-target specs + disposition, device-targets slice 1)
    "DeviceTarget", "FAST_LOGIC", "LOW_POWER", "MOSFET_FLAVORS", "MARKET_BINS",
    "TargetGrade", "regrade", "grade_for", "disposition",
    # dashboard (the guided slider-driven slice — §9 UX)
    "dashboard_recipe", "run_dashboard", "dashboard_summary", "knob_errors", "oxide_minutes_error",
    # game / roguelike session (G7)  — MARKET_BINS moved to targets.py; exported in the targets group above
    "GameConfig", "GameSession", "RunRecord", "ReworkSpec",
    "new_session", "process_wafer", "scrap_wafer", "play",
    # session_view (the headless renderers the TUI v2 roguelike screen drives)
    "turn_recipe", "oxide_recipe", "projected_vt", "inspect_line", "session_header",
    "turn_line", "history_trail", "session_summary",
    # guide (the educational-mode prose the TUI renders verbatim)
    "Term", "GLOSSARY", "GLOSSARY_BY_KEY", "MODE_INTRO", "term_block", "dashboard_guide",
    "roguelike_guide", "glossary_text",
]
