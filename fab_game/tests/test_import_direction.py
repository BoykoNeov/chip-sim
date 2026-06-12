"""The import-direction guard (ADR 0005 §2) — the dependency is one-way.

``fab_game → chip/engines``, **never** the reverse. The physics core must stay free of game/UI
dependencies so the existing validation gate keeps meaning exactly what it means today (and a
headless physics checkout stays light). This is enforced *mechanically*, not by convention: no
source file under ``chip/`` or ``engines/`` may import ``fab_game``.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PHYSICS_DIRS = ("chip", "engines")


def _imports_fab_game(source: str) -> bool:
    """True if the module's AST has any ``import fab_game`` / ``from fab_game[...] import ...``."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name == "fab_game" or a.name.startswith("fab_game.") for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "fab_game" or node.module.startswith("fab_game.")):
                return True
    return False


def test_physics_layer_never_imports_fab_game():
    """No file under chip/ or engines/ imports fab_game — the one-way boundary holds."""
    offenders = []
    for pkg in _PHYSICS_DIRS:
        for path in (_REPO_ROOT / pkg).rglob("*.py"):
            if _imports_fab_game(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, f"physics layer imports fab_game (forbidden, ADR 0005 §2): {offenders}"


def test_the_guard_can_detect_a_violation():
    """Sanity: the AST scanner actually fires on a planted import (so a green test means something)."""
    assert _imports_fab_game("import fab_game")
    assert _imports_fab_game("from fab_game.pipeline import run_line")
    assert _imports_fab_game("import chip\nimport fab_game.state as s")
    assert not _imports_fab_game("import chip\nfrom engines.diffusion import Diffusion1D")
    # A substring match must NOT false-positive on an unrelated name.
    assert not _imports_fab_game("import fab_games_unrelated")
