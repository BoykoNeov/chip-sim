"""The stochastic spread — process variation as a seeded, reproducible layer (the plan §4).

The deterministic physics core computes the *nominal* output from the knobs; this layer spreads
it across the die map so yield is honest. Two channels, per the advisor's split:

* **Systematic knob** (center-to-edge trend) is routed *through the physics* — the per-die
  effective focus is ``defocus + focus_tilt·radius_frac``, so the Bossung CD response is the real
  optics, not a hand-applied CD shift. This is the channel the "propagation actually wired"
  invariant constrains.
* **Die-to-die scatter** is applied at the **output** (a small CD / t_ox jitter), the cheap,
  honest model of within-wafer non-uniformity — it never needs a second physics solve.

**Determinism contract.** Every random number is drawn from one seeded
``numpy.random.default_rng`` threaded through the pipeline, consumed in **fixed die order** — so a
(seed, recipe) pair reproduces the wafer exactly (a roguelike "seed"). When ``enabled`` is False
*both* channels vanish (trend **and** scatter), so a zero-variation run collapses to one physics
call per step == :mod:`chip.demo_device` (the seam — trend-off ⇔ variation-off).

The magnitudes here are **house defaults, flagged** — illustrative within-wafer non-uniformity,
not cited fab numbers (ADR 0005 §5: ``fab_game`` is mechanics, not magnitudes).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .state import Die


@dataclass(frozen=True)
class DiePerturbation:
    """One die's drawn perturbation: a focus-knob delta (through physics) + output jitters.

    ``defocus_nm_delta`` is *added to the litho defocus knob* (systematic tilt + scatter, both
    genuine focus error → the Bossung optics map it to CD); ``t_ox_factor`` multiplies the grown
    oxide thickness and ``cd_nm_delta`` is added to the printed CD (output-level non-uniformity);
    ``etch_factor`` (G5) multiplies the etch undercut (etch-rate non-uniformity → an etch-bias jitter
    routed *through* :func:`chip.etch_deposition.etch_feature`'s ``bias_factor`` hook — so it only
    moves the CD where the etch is non-ideal, ``anisotropy < 1``). The **identity**
    ``DiePerturbation(0.0, 1.0, 0.0, 1.0)`` is the no-variation element (the seam).
    """

    defocus_nm_delta: float = 0.0
    t_ox_factor: float = 1.0
    cd_nm_delta: float = 0.0
    etch_factor: float = 1.0


@dataclass(frozen=True)
class Variation:
    """House-default within-wafer process variation (FLAGGED — illustrative, not cited magnitudes).

    Systematic center-to-edge trends (added at ``radius_frac = 1``, linear in radius) plus
    die-to-die Gaussian scatter. ``enabled=False`` turns **both** off → the seam.
    """

    enabled: bool = True
    # Systematic center-to-edge trends (full value at the wafer edge, linear in radius_frac):
    focus_tilt_nm: float = 55.0        # edge dies sit this many nm out of focus (focus bowl)
    t_ox_edge_frac: float = -0.025     # edge gate oxide ~2.5 % thinner (furnace non-uniformity)
    na_edge_boost: float = 2.5         # mobile-ion Na edge-loading: edge dies see (1+boost)× the wafer Na
    #                                    (handling/edge-bead/furnace radial gradients concentrate Na at the
    #                                    rim) → an edge-RING of V_t kills at a marginal feed, not an all-or-
    #                                    nothing flip (the gradual-failure policy: the honest slope under the
    #                                    Na→Q_ox→V_t cliff). FLAGGED house number — the mechanism/direction is
    #                                    real, the steepness illustrative (ADR 0005 §5); ~3.5× rim/centre is
    #                                    well inside the real handling regime. Parabolic r² (a thin rim), not
    #                                    the bowl's linear r. 0 ⇒ uniform Na (the pre-ring behaviour).
    # Die-to-die random scatter (Gaussian σ):
    focus_sigma_nm: float = 20.0       # focus jitter
    cd_sigma_nm: float = 1.5           # line-width roughness on the printed CD
    t_ox_sigma_frac: float = 0.008     # oxide-thickness jitter
    etch_bias_sigma_frac: float = 0.0  # etch-rate non-uniformity (G5; 0 ⇒ no draw — keeps banked demos byte-identical)

    def _trends(self, die: Die) -> tuple[float, float]:
        """The deterministic center-to-edge trends at this die: (defocus tilt nm, t_ox frac shift)."""
        r = die.radius_frac
        return self.focus_tilt_nm * r, self.t_ox_edge_frac * r

    def na_factor(self, radius_frac: float) -> float:
        """Edge-loaded mobile-ion Na multiplier at this die (``1 + na_edge_boost·r²``; ``1.0`` when off).

        The honest *slope* under the Na→Q_ox→V_t **cliff** (the gradual-failure policy). Mobile-ion
        sodium is edge-loaded in reality — edge handling/bead, furnace-tube radial gradients — so the
        rim dies see more Na, their ``V_t`` is driven furthest down, and a marginal feed kills an
        **edge ring** (some dies fail, not all): the canonical contamination wafer-map signature, the
        graded ok→rework→fail band a uniform shift can't produce. Deterministic (no ``rng`` draw — a
        center-to-edge trend like the focus bowl, so it never perturbs the random stream).

        Seam-exact: ``1.0`` when ``enabled`` is False (uniform Na ⇒ ``demo_device``) and irrelevant to a
        clean ``Na = 0`` feed (``0·factor = 0``). Composes with — does **not** double-count — the focus
        bowl: the bowl kills the rim through CD→NILS, this through Q_ox→V_t (different spec channels, so
        a marginal feed at a defocus offset stacks two real edge effects rather than one counted twice).
        **Both** the parabolic ``r²`` *profile* and the ``na_edge_boost`` *steepness* are FLAGGED house
        numbers (ADR 0005 §5 — cite the channel, flag the shape **and** the magnitude): real edge-loading
        could be a sharper rim, so ``r²`` is illustrative, not derived (it matches the OSF-ring shape only
        by convention, not by a shared cause).
        """
        if not self.enabled:
            return 1.0
        return 1.0 + self.na_edge_boost * radius_frac * radius_frac

    def perturbation(self, die: Die, rng: np.random.Generator) -> DiePerturbation:
        """Draw this die's full perturbation from ``rng`` — systematic trend **+** scatter.

        Consumes 3 normals in a fixed order (focus, t_ox, CD), then a **4th only when**
        ``etch_bias_sigma_frac > 0`` (the etch non-uniformity, drawn *last* so an enabled run with the
        default ``etch_bias_sigma_frac = 0`` draws byte-identically to before G5 — the G1–G4 banked
        demos are unchanged). With ``enabled=False`` returns the identity perturbation **without
        touching ``rng``** — so the seam is exact *and* a disabled-variation run does not perturb the
        random stream.
        """
        if not self.enabled:
            return DiePerturbation()
        focus_tilt, t_ox_trend = self._trends(die)
        # The three existing draws, in their fixed order (focus, t_ox, CD)…
        defocus_nm_delta = focus_tilt + float(rng.normal(0.0, self.focus_sigma_nm))
        t_ox_factor = 1.0 + t_ox_trend + float(rng.normal(0.0, self.t_ox_sigma_frac))
        cd_nm_delta = float(rng.normal(0.0, self.cd_sigma_nm))
        # …then a 4th, conditional draw LAST: only consume the RNG for the etch jitter when it is
        # switched on, so an enabled run with the default etch σ = 0 draws byte-identically to before
        # G5 (the G1–G4 banked demos are unchanged).
        etch_factor = 1.0
        if self.etch_bias_sigma_frac > 0.0:
            etch_factor = 1.0 + float(rng.normal(0.0, self.etch_bias_sigma_frac))
        return DiePerturbation(
            defocus_nm_delta=defocus_nm_delta,
            t_ox_factor=t_ox_factor,
            cd_nm_delta=cd_nm_delta,
            etch_factor=etch_factor,
        )

    def systematic_perturbation(self, die: Die) -> DiePerturbation:
        """The **trend-only** perturbation — the center-to-edge focus bowl, no random scatter.

        Used by litho **rework**: a re-exposure happens in the same scanner, so the focus bowl (the
        systematic tilt) *persists* — only the player's global focus offset is corrected. Dropping
        the random scatter models a fresh, well-controlled re-exposure. Deterministic (no ``rng``),
        identity when disabled. (So re-exposing at the *same* recipe does **not** rescue an
        edge-tilt failure — only correcting the focus does — which is what makes rework honest.)
        """
        if not self.enabled:
            return DiePerturbation()
        focus_tilt, t_ox_trend = self._trends(die)
        return DiePerturbation(defocus_nm_delta=focus_tilt, t_ox_factor=1.0 + t_ox_trend)


# The seam element: variation off → both channels vanish → demo_device bit-for-bit.
NO_VARIATION = Variation(enabled=False)
