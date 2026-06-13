"""Integration test for the G5 etch/deposition demo (the demo IS the integration check).

The etch demo wires the new etch-bias + step-coverage physics (:mod:`chip.etch_deposition`) through the
harness into the mid-line artifact. Its ``compute`` is the end-to-end check that the over-etch → CD →
I_Dsat chain and the conformality → void → functional-kill chain hold together — asserted on the robust
thesis (the seam is flat, a real etch walks the CD out of window, PVD voids where CVD fills, rework
recovers the void but not the etch), not brittle exact numbers (the physics is pinned in
``chip/tests/test_etch_deposition.py``, the wiring in ``test_etch.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game.demo_etch import compute


def test_demo_overetch_walks_cd_out_of_window():
    """The seam (A=1) is flat at the printed CD; a real etch (A<1) walks the CD monotonically down,
    and the good RIE crosses the CD floor over the over-etch sweep."""
    r = compute()
    ideal = r.cd_by_aniso[r.etch_curves[0]]                    # A = 1.0
    assert ideal[0] == ideal[-1]                              # perfectly anisotropic → flat (the seam)
    rie = r.cd_by_aniso[r.etch_curves[1]]                     # A = 0.95
    assert all(b <= a for a, b in zip(rie, rie[1:]))          # monotonically shrinking with over-etch
    assert rie[0] >= r.cd_lo > rie[-1]                        # in spec at endpoint, out the bottom by max over-etch
    # I_Dsat rises as the CD shrinks (shorter channel → more drive current).
    idsat = r.idsat_by_aniso[r.etch_curves[1]]
    assert idsat[-1] > idsat[0]


def test_demo_pvd_voids_where_cvd_fills():
    """The poor PVD voids the gate gap the conformal CVD fills → the PVD wafer is scrapped functionally."""
    r = compute()
    assert r.pvd_voids is True and r.cvd_voids is False
    assert r.gate_gap_ar > 0.0
    assert r.void_yield_before == 0.0                         # all dies voided (functional kill)
    # The void trail names the non-conformal-fill cause (not defocus, not a particle).
    assert "VOID" in r.void_trail and "aspect ratio" in r.void_trail


def test_demo_rework_recovers_the_void_not_the_overetch():
    """Reworkable vs irreversible: re-depositing recovers the PVD void but cannot undo an over-etched CD."""
    r = compute()
    assert r.void_yield_before == 0.0 and r.void_yield_after == 1.0          # void: stripped & recovered
    assert r.overetch_yield_before == 0.0 and r.overetch_yield_after == 0.0  # etch: irreversible
    # The over-etch trail names the etch bias as the root cause (a parametric CD/I_Dsat fail).
    assert "etch bias" in r.overetch_trail
    assert any(tag in r.overetch_trail for tag in ("CD", "I_Dsat"))


def test_etch_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import etch_figure

    r = compute()
    fig = etch_figure(r)
    assert len(fig.axes) >= 3                                 # etch-bias / void / rework panels
    plt.pyplot.close(fig)
