"""Packaging & test: the back-end (assembly) yield funnel — a chain of independent step yields.

The last operation of the fab line proper (plan §5 step 9, §6 G6; ADR 0005), and the physics the
fab-line game's **G6** consumes: *after wafer sort decides which dies work, the good dies are diced,
attached, wire-bonded, and encapsulated — each a back-end operation that can lose a part — then final-
tested and **binned** by performance.* This module owns the **one citable piece** of that story — the
**cumulative (multiplicative) yield funnel** — as a closed form with a real validation triad. The
*binning* (sorting working parts into speed grades by house thresholds) is **not** citable physics — it
is a grading policy — so it lives in the game layer (:mod:`fab_game`), exactly as ADR 0005 §1 dictates.

The yield funnel — the cited model
-----------------------------------
A part must survive **every** back-end operation to ship. With independent per-step survival
probabilities (yields) ``y₁, y₂, …, y_n`` — dicing, die-attach, wire-bond, encapsulation — the
**assembly yield** is their product::

    Y_assembly = Π yᵢ                                              (cumulative / funnel yield)

and the **overall** yield is the same product extended through the front end::

    Y_overall = Y_wafer-sort · Y_assembly · Y_final-test

This multiplicativity is *the* property of independent stages — a part that survives stage A *and*
stage B survives with probability ``y_A·y_B`` — and it is the cited **yield-funnel** decomposition
(Sze, *VLSI Technology* 2nd ed., yield chapter — the same text the wafer-prep defect law cites; May &
Spanos, *Fundamentals of Semiconductor Manufacturing and Process Control*, Wiley 2006, Ch. 5, the
cumulative-yield model; Tummala, *Fundamentals of Microsystems Packaging*, the assembly-step
decomposition). The **per-step magnitudes** are **flagged house numbers** (:data:`ASSEMBLY_STEPS`) —
only the *funnel composition* and the limits are asserted; the numbers are the game's back-end knob.

Validation triad (plan §7) — what is tight vs loose
---------------------------------------------------
* **Analytical limit / seam (the bit-exact anchor).** ``assembly_yield()`` over all-perfect steps
  (every ``yᵢ = 1``) is **exactly 1.0** (a perfect back end loses nothing — the identity the G6 game
  wiring rides), and a single step returns *itself* bit-for-bit. This is the structural seam, like
  Czochralski's ``k → 1``, wafer-prep's ``Y(0) = 1``, and the SRH ``N_metal = 0`` limit.
* **Conservation / identity (multiplicativity — a genuine identity).** ``Y(A ∪ B) = Y(A)·Y(B)``: the
  yield of a combined set of steps is the product of the sub-products (regrouping / associativity is
  exactly the **independence** of the stages), and ``n`` identical steps of yield ``y`` give ``yⁿ`` —
  the same status as wafer-prep's area-additivity ``Y(A₁+A₂) = Y(A₁)·Y(A₂)``. *Honest caveat (the §7
  discipline):* the multiplicative **algebra** is structural — its real weight is that ``Π yᵢ`` is the
  **only** composition law under independence, and *that* is validated by the **realization**, not the
  arithmetic: the game layer's per-die **Bernoulli survival → empirical packaged yield → ``Π yᵢ``** (a
  law-of-large-numbers convergence, the non-circular leg, exactly as wafer-prep's stochastic placement
  converges to ``exp(−D₀A)``). The expected packaged count out of ``n`` good dies is ``n·Y`` — the rate
  that realization must hit.
* **Benchmark (loose) — the cited funnel + flagged step bands.** The funnel decomposition is the
  textbook one (Sze; May & Spanos; Tummala). The :data:`ASSEMBLY_STEPS` per-operation yields are
  **flagged illustrative** levels (a mature back end loses very little; a marginal one loses more);
  only the *ordering* (more steps / a worse step → strictly lower yield) and the limits are asserted,
  never the numbers (ADR 0005 §5: the game is scored on mechanics, not magnitudes).

Named scope edge (the honest ceiling)
-------------------------------------
* **Independent, scalar step yields.** Each operation is a single survival probability; real back
  ends have *correlated* / batch failures (a bad bond-wire lot, a mold-compound excursion) that the
  independent product underestimates the spread of — a named calibrated edge, not modelled.
* **No mechanical / thermal package model.** Wire-bond pull strength, die-attach voiding, mold-cap
  stress, package-induced parametric drift (stress → ``V_t`` shift) are all out: the *mechanism* (each
  operation can kill a part) is the cited physics, the *magnitudes* are house, and the package does not
  shift the device parameters here.
* **Binning is a grading policy, not physics** — sorting working parts into speed bins by house
  thresholds lives in the game layer (:mod:`fab_game`), with the partition bookkeeping (every packaged
  part → exactly one bin-or-reject) as its mechanics invariant. No parametric-distribution / ``Cpk``
  model is asserted here (the realized parameter spread is the nonlinear image of the process variation,
  not a clean Gaussian — so a CDF-based bin-fraction would be a *loose overlay*, never a tight leg).

Units
-----
All yields are dimensionless probabilities ∈ ``[0, 1]``; the product is dimensionless ∈ ``[0, 1]``.

Validation boundary
-------------------
No shared engine — the funnel is a closed form (like Deal–Grove / Scheil / the defect law), so this
module's tests carry the whole triad: the all-perfect / single-step seam (analytic), multiplicativity
+ the ``yⁿ`` identity (conservation), and the cited funnel + flagged step bands (benchmark). The
**stochastic** per-die assembly realization and its convergence to ``Π yᵢ``, and the binning partition,
live in the game layer (:mod:`fab_game`, mechanics invariants), where the randomness and the grading
policy belong.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Flagged back-end step yields — illustrative house levels, NOT cited fab numbers.
# A part must survive every operation to ship; the per-step survival probabilities multiply (the
# funnel). Only the *composition* (the product) and the limits (yᵢ=1 ⇒ no loss) are asserted; the
# magnitudes are house (the game's back-end quality knob), exactly as wafer_prep's DEFECT_DENSITY_BANDS,
# purification's FEEDSTOCK_GRADES, and etch_deposition's STEP_COVERAGE.
# --------------------------------------------------------------------------- #
ASSEMBLY_STEPS: dict[str, float] = {
    "dice": 0.995,        # wafer dicing/singulation — a saw chip/crack scraps the die (irreversible)
    "attach": 0.997,      # die-attach to the leadframe/substrate — a void/tilt loses the part
    "bond": 0.994,        # wire-bond — a lifted/non-stick bond (the back end's busiest, lossiest step)
    "encapsulate": 0.998, # mold / encapsulation — a void or incomplete fill
}


# --------------------------------------------------------------------------- #
# The yield funnel — the multiplicative (cumulative) yield of independent steps
# --------------------------------------------------------------------------- #
def assembly_yield(*step_yields: float) -> float:
    """Cumulative back-end yield ``Y = Π yᵢ`` — the product of independent per-step survival yields.

    Each ``yᵢ`` ∈ ``[0, 1]`` is the fraction of parts that survive one back-end operation; a part must
    survive **all** of them, so the yields multiply (the cited funnel). **No arguments → 1.0** (an
    empty funnel loses nothing) and a **single** yield returns *itself* bit-for-bit (the analytic
    seam); all-``1.0`` → ``1.0`` exactly (a perfect back end). Decreases monotonically as steps are
    added or a step worsens, and is multiplicative over any partition of the steps
    (:func:`assembly_yield` ``(a, b) == assembly_yield(a) * assembly_yield(b)`` — the independence
    identity). Raises on a non-probability yield.
    """
    product = 1.0
    for y in step_yields:
        if not 0.0 <= y <= 1.0:
            raise ValueError(f"each step yield must be a probability in [0, 1], got {y}")
        product *= y
    return product


def expected_packaged(n_good: int, *step_yields: float) -> float:
    """Expected number of shipped parts ``n_good · Π yᵢ`` out of ``n_good`` front-end-good dies.

    The mean of the per-die Bernoulli back-end survival summed over the good dies — the rate the
    game layer's stochastic assembly realization (:mod:`fab_game`) must converge to (the non-circular
    leg, the packaging analogue of wafer-prep's ``λ = D₀·A``). The overall funnel is the same product
    one level up: ``Y_overall = Y_front · assembly_yield(*steps)``. Pure bookkeeping: ``n_good ≥ 0``.
    """
    if n_good < 0:
        raise ValueError(f"n_good must be ≥ 0, got {n_good}")
    return n_good * assembly_yield(*step_yields)
