"""Headless renderers for a roguelike :class:`~fab_game.game.GameSession` — the strings the TUI v2 drives.

The text twin of :mod:`fab_game.dashboard` for the G7 **session** model (plan
``docs/plans/fab-game-tui.md`` §7; ADR 0002/0005). :mod:`fab_game.game` owns the entire roguelike
session headless and tested (the model: process / scrap a wafer down one boule, scored); this module
owns the **presentation** of that model — the header, the per-turn ledger, the end-of-run tally, and
the "inspect the next slice before deciding" affordance the player reads to choose. It computes no
new physics: every string is built from the already-played :class:`~fab_game.game.GameSession` /
:class:`~fab_game.game.RunRecord`, except :func:`projected_vt`, which calls the **validated**
:func:`fab_game.run_line` at a single nominal die (the cheap inspection the demo's scrap strategy
already uses).

**Why this is a separate, import-pure module — not a graft onto ``game.py`` or ``dashboard.py``.** The
repo keeps model and render apart (``state.py`` ↔ ``plots.py``; ``run_dashboard`` ↔
``dashboard_summary``), and a :class:`~fab_game.game.GameSession` is a different object than a
:class:`~fab_game.pipeline.LineResult`, so it earns its own peer renderer. And — the §9 / TUI-plan
discipline — the **load-bearing string-building lives outside the interactive surface**: a Textual App
(like ``ipywidgets.interact``) can swallow a callback exception and still look green, so the strings it
renders must be testable on their own. This module imports neither ``textual`` nor ``matplotlib``; it
is re-exported from :mod:`fab_game` and tested by ``tests/test_session_view.py``. :mod:`fab_game.tui`'s
``RoguelikeScreen`` is a thin driver that renders these verbatim.

The honest caveat on :func:`projected_vt` (the inspect affordance): it is a **single, nominal,
``NO_VARIATION`` die** — the centre ``V_t`` the player inspects to decide, **not** a guarantee every die
on the processed wafer passes (the real turn runs the stochastic spread over the whole grid). "Projected
``V_t`` … in spec" means the nominal die prints in spec, the right signal for the scrap/adapt call.
"""
from __future__ import annotations

from dataclasses import replace

from .game import GameSession, RunRecord
from .pipeline import run_line
from .recipe import DEFAULT_RECIPE, OxidationKnobs, Recipe
from .variation import NO_VARIATION


# --------------------------------------------------------------------------- #
# The recipe the next turn will run — the fidelity contract (preview == commit)
# --------------------------------------------------------------------------- #
def turn_recipe(session: GameSession, recipe: Recipe | None = None) -> Recipe:
    """The **exact** recipe :func:`~fab_game.game.process_wafer` will run for the next turn.

    Mirrors ``process_wafer`` (``game.py``): the player's ``recipe`` (default = ``config.base_recipe``)
    with its ``czochralski.slice_z`` overridden to :attr:`~fab_game.game.GameSession.next_slice_z` — the
    boule dictates *where* on it you are, the recipe is the *process*. THE fidelity contract: the inspect
    preview (:func:`projected_vt` / :func:`inspect_line`) and the committed turn must build from the
    **same** recipe-at-z, or the player inspects one wafer and processes another.
    """
    base = recipe if recipe is not None else session.config.base_recipe
    return replace(base, czochralski=replace(base.czochralski, slice_z=session.next_slice_z))


def oxide_recipe(minutes: float, *, base: Recipe = DEFAULT_RECIPE) -> Recipe:
    """The **adapt lever** as a recipe: ``base`` with the gate-oxide drive set to ``minutes``.

    Thinning the gate oxide lowers ``V_t`` (and lifts ``I_Dsat``) — the G7 lever that pulls the drifted
    boule tail back into spec. The single knob the roguelike screen exposes; every other knob stays at
    ``base`` (``DEFAULT_RECIPE`` unless the run overrides it). At the default 20 min this is ``base``
    by value (the seam).
    """
    return replace(base, oxidation=replace(base.oxidation, minutes=float(minutes)))


def projected_vt(session: GameSession, recipe: Recipe | None = None) -> float:
    """The next slice's deterministic single-die ``V_t`` under ``recipe`` — the inspect-before-deciding affordance.

    A cheap ``NO_VARIATION``, ``grid_n=1`` run of the **same** recipe-at-z the turn will process
    (:func:`turn_recipe`), so the player previews the wafer the turn actually runs. This is a single,
    nominal die: the centre ``V_t``, **not** a guarantee every die passes (the real turn runs the
    stochastic spread over the whole grid). The same nominal inspection the demo's scrap strategy uses.
    """
    r = turn_recipe(session, recipe)
    return run_line(r, variation=NO_VARIATION, specs=session.config.specs, grid_n=1).dies[0].V_t


# --------------------------------------------------------------------------- #
# The rendered panels — built purely from the (already-played) session / records
# --------------------------------------------------------------------------- #
def session_header(session: GameSession) -> str:
    """The status line: mode · boule progress · budget · score · (run-over flag)."""
    cfg = session.config
    mode = "sandbox" if cfg.sandbox else "roguelike"
    head = (f"{mode}  ·  {session.wafer_index}/{cfg.n_wafers} wafers  ·  "
            f"budget ${session.budget:.2f}  ·  score ${session.score:+.2f}")
    if session.bankrupt:
        return head + "  ·  BANKRUPT — run over"
    if session.boule_exhausted:
        return head + "  ·  boule exhausted — run over"
    return head


def inspect_line(session: GameSession, recipe: Recipe | None = None) -> str:
    """Decision support: the next slice, its projected (nominal) ``V_t``, and whether it sits in spec.

    Reads :func:`projected_vt` (a single nominal die) against the ``V_t`` spec window. "in spec" means the
    nominal die prints in spec — the signal for the process/adapt/scrap call — **not** that every die on
    the stochastic wafer will pass. Returns a run-over note once the boule is exhausted / the run is
    bankrupt (there is no next slice to inspect).
    """
    if session.done:
        return "the run is over — no slice to inspect."
    cfg = session.config
    z = session.next_slice_z
    vt = projected_vt(session, recipe)
    win = cfg.specs.v_t
    in_spec = win.check(vt) is None
    flag = "in spec" if in_spec else "OUT of spec — the nominal die fails"
    return (f"next: turn {session.wafer_index + 1}/{cfg.n_wafers}  ·  slice z={z:.2f}  ·  "
            f"projected V_t {vt:.3f} V [{flag}]  (spec [{win.lo:.2f}, {win.hi:.2f}] V)")


def turn_line(record: RunRecord) -> str:
    """One ledger row: the turn, its slice, the action, the profit, and the outcome (bin mix / scrapped)."""
    sc = record.scorecard
    if record.scrapped:
        action, detail = "scrap  ", "scrapped unprocessed"
    else:
        bins = ", ".join(f"{n}×{b}" for b, n in sorted(sc.bin_counts.items())) or "no good dies"
        action, detail = "process", f"{sc.n_good}/{sc.n_total} good · {bins}"
    return f"T{record.wafer_index}  z{record.slice_z:04.2f}  {action}  profit ${sc.profit:+7.2f}  ({detail})"


def history_trail(session: GameSession) -> str:
    """The append-only ledger: one :func:`turn_line` per turn played (or a no-turns note)."""
    if not session.history:
        return "(no turns played yet — inspect the slice, then process or scrap)"
    return "\n".join(turn_line(r) for r in session.history)


def session_summary(session: GameSession) -> str:
    """The end-of-run tally: how the run ended, the final score, and the processed/scrapped/good split."""
    cfg = session.config
    n_proc = sum(not r.scrapped for r in session.history)
    n_scrap = sum(r.scrapped for r in session.history)
    n_good = sum(r.scorecard.n_good for r in session.history)
    ending = ("BANKRUPT" if session.bankrupt else
              "boule exhausted" if session.boule_exhausted else "in progress")
    return (f"run over ({ending}) — final budget ${session.budget:.2f}, score ${session.score:+.2f}\n"
            f"{len(session.history)} turns: {n_proc} processed, {n_scrap} scrapped, {n_good} good dies shipped")
