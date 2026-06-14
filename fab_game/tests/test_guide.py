"""Headless tests for the educational-mode prose (``fab_game.guide``) — the load-bearing leg.

The §9 / TUI-plan discipline (ADR 0005 §5): the strings the Textual *Educational* mode renders are
built and tested **here**, with no Textual at all, because the App (like ``ipywidgets.interact``) can
swallow a callback exception and still look green. These assert *mechanics*: the glossary is
**complete** (every selector the dashboard exposes + every concept the user asked to have explained
has an entry), each rendered guide actually **mentions** those concepts, and the strings are plain,
non-empty text — so the educational panel cannot silently ship empty or miss a term.
"""
from __future__ import annotations

import fab_game
from fab_game import guide


# The concepts the request named explicitly — the deliverable's checklist. Each must be explained
# (by name *and* with its own glossary entry), or educational mode has not done what was asked.
NAMED_CONCEPTS: dict[str, str] = {
    "defocus_nm": "Defocus",
    "slice_z": "Boule slice",
    "oxide_minutes": "Gate-oxide drive",
    "seed": "Seed",
    "v_t": "V_t",
    "i_dsat": "I_Dsat",
    "leakage": "Leakage",
    "nils": "NILS",
    "cd": "CD",
}


# --------------------------------------------------------------------------- #
# Completeness — the glossary covers every selector + every named concept
# --------------------------------------------------------------------------- #
def test_every_named_concept_has_a_glossary_entry():
    """Each concept the request named (defocus, boule slice z, gate-oxide drive, seed, V_t, I_Dsat,
    leakage, NILS, CD) has a :class:`~fab_game.guide.Term` — the proof the educational guide covers
    exactly what was asked, not just the knob keys."""
    for key in NAMED_CONCEPTS:
        assert key in guide.GLOSSARY_BY_KEY, f"no glossary entry for the requested concept {key!r}"
        term = guide.GLOSSARY_BY_KEY[key]
        assert term.name and term.summary and term.detail, f"{key!r} has an empty field"


def test_every_dashboard_selector_is_explained():
    """Every live dashboard knob key has a glossary entry (so the legend can never reference a missing
    term) and the knob set matches the dashboard's exposed selectors."""
    for key in guide.DASHBOARD_KNOBS:
        assert key in guide.GLOSSARY_BY_KEY
    # The guide's knob keys are exactly the dashboard's exposed knobs (the seam against run_dashboard).
    assert set(guide.DASHBOARD_KNOBS) == {"defocus_nm", "defect_density", "slice_z", "oxide_minutes", "seed"}


def test_glossary_keys_are_unique_and_all_legend_keys_resolve():
    """No duplicate term keys, and every key each screen's legend walks resolves to a real term."""
    keys = [t.key for t in guide.GLOSSARY]
    assert len(keys) == len(set(keys)), "duplicate glossary keys"
    for legend in (guide.DASHBOARD_KNOBS, guide.DASHBOARD_READOUTS, guide.ROGUELIKE_READOUTS):
        for key in legend:
            assert key in guide.GLOSSARY_BY_KEY


# --------------------------------------------------------------------------- #
# The rendered guides actually mention the concepts (and carry *what-to-do*)
# --------------------------------------------------------------------------- #
def test_dashboard_guide_mentions_every_dashboard_concept_and_what_to_try():
    """The dashboard guide names each selector + the printability/device readouts, and carries the
    exploratory *what to try* strategy (not just definitions)."""
    text = guide.dashboard_guide()
    assert text.strip()
    for label in ("Defocus", "Defect density", "Boule slice", "Gate-oxide drive", "Seed"):
        assert label in text, f"dashboard guide never explains {label!r}"
    for concept in ("NILS", "V_t", "I_Dsat", "CD"):
        assert concept in text
    assert "What to try" in text                       # the *what-to-do* block, distinct from the glossary
    assert "ring" in text.lower() and "scatter" in text.lower()   # the two map-texture stories


def test_roguelike_guide_carries_the_process_adapt_scrap_decision():
    """The roguelike guide frames the run (boule/Scheil drift) and states the actual decision —
    process / adapt (thin the oxide) / scrap — with the Goldilocks I_Dsat ceiling caveat."""
    text = guide.roguelike_guide()
    assert text.strip()
    assert "Scheil" in text and "V_t" in text          # the difficulty curve
    for action in ("Process", "Adapt", "Scrap"):
        assert action in text
    assert "I_Dsat" in text and "ceiling" in text       # the over-thinning brake (the honest caveat)
    assert "leak" in text.lower()                        # the readout V_t cannot see


def test_mode_intro_describes_both_modes():
    """The launch chooser prose names both modes and what distinguishes them (guided vs bare)."""
    assert "Educational" in guide.MODE_INTRO and "Hardcore" in guide.MODE_INTRO
    assert "explained" in guide.MODE_INTRO and "cockpit" in guide.MODE_INTRO


def test_glossary_text_is_one_block_per_term():
    """The full glossary renders one bullet per term — no term dropped, none duplicated."""
    text = guide.glossary_text()
    assert text.count("• ") == len(guide.GLOSSARY)


# --------------------------------------------------------------------------- #
# Import surface — re-exported and headless (no textual / matplotlib pulled in)
# --------------------------------------------------------------------------- #
def test_guide_is_reexported_from_the_package():
    """The package surfaces the guide helpers (so consumers — and the notebook later — need not reach
    into the submodule)."""
    for name in ("dashboard_guide", "roguelike_guide", "glossary_text", "MODE_INTRO", "GLOSSARY"):
        assert hasattr(fab_game, name)


def test_importing_guide_pulls_in_no_interactive_dependency():
    """``guide`` is import-pure: importing it (and the package) must not import textual/matplotlib, or
    the headless fast lane / ``import fab_game`` breaks (the same constraint session_view honours).

    Checked in a **fresh subprocess**, not this process's ``sys.modules`` — under ``-n auto`` a
    co-scheduled ``test_tui`` App pilot imports ``textual`` into the shared interpreter, so an in-process
    check would flake on test ordering. The subprocess isolates the import graph the assertion is about.
    """
    import subprocess
    import sys

    probe = (
        "import fab_game, fab_game.guide, sys; "
        "bad = [m for m in ('textual', 'matplotlib') if m in sys.modules]; "
        "assert not bad, bad"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert result.returncode == 0, f"importing fab_game.guide pulled in {result.stderr.strip()}"
