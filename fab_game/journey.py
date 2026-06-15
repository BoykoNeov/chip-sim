"""The staged sand→chip journey — decide at each fab stage, watch the consequence propagate (phases 1–3).

The player-facing framing the roguelike (:mod:`fab_game.game`) and the dashboard
(:mod:`fab_game.dashboard`) never gave. Instead of one wafer down a boule (game) or four live sliders
(dashboard), a *journey* builds **one wafer's recipe stage by stage** — pick the feedstock and purify it,
grow the boule, slice a wafer, then (later phases) polish, diffuse, oxidize, pattern, etch, package — a
real decision at each stage, watched as it lands downstream: from no-effect, through a graded yield ring,
to an outright scrap.

**Phases 1–4 build four stages — purification, crystal growth, the slice/cut, and the S/D diffusion.**
Every later stage runs at its recipe default (the journey just carries them). The slice stage is the first
that **reads a prior committed decision**: a faster phase-2 pull flattens the boule's axial Scheil drift
(CG-1), so you can cut a wafer *deeper* down the boule and still land in the ``V_t`` window — the journey's
"watch it propagate" payoff. The scaffold is deliberately thin — an accumulating
:class:`~fab_game.recipe.Recipe` plus the in-progress decision (a few idempotent overlay fields), **not** a
nine-stage state machine — per the repo's anti-over-build rule: a stage gets built when it has a consumer.

**Honesty note (phase 4):** phases 1–3 add *zero new physics* — they re-sequence propagation chains the
line already had (Na→Q_ox→V_t, Voronkov→yield, Scheil→V_t). Phase 4 is the exception: the diffusion
outputs ``x_j``/``R_s`` fed **nothing scored** (the device reads ``N_A``/``t_ox``/CD, never ``R_s``), so
the dose was inert. To make the dose a real decision phase 4 adds a genuine device term — an additive S/D
**series resistance** on :func:`chip.device.saturation_current` (source degeneration, default-0 seam) —
wiring ``R_s`` → ``I_Dsat``. So the journey's "adds no physics" claim is *formally false at phase 4*; the
term is justified because phase 4 is its consumer, and it lands on the **existing** I_Dsat spec (no new
window). See :func:`JourneyState.diffuse` / :data:`DIFFUSION_SD_CONTACT_SQUARES`.

The purification stage is the showcase for the **gradual-failure policy** (the edge-loaded Na ring,
:meth:`fab_game.variation.Variation.na_factor`). You start with a dirty feedstock and **refine it step by
step** — each zone-refining increment scrubs the impurity vector (Na/Fe/Cu fall by ``k^n``, boron barely
moves), and a :func:`forecast` runs the line at the recipe-so-far to show the consequence **band**
(``clean`` → ``ring`` → ``dead``, the ok→rework→fail spectrum) **and the channel it fails on**
(mobile-ion Na → a ``V_t`` ring, or deep-level metal → junction leakage — so a dirty feed that *looks*
fine on threshold can still die on leakage). The continuous refining effort is the lever
(``front_purity``'s ``k^n`` is smooth in ``n``), so you can place the residual in the marginal band where
the graded ring lives — then :meth:`~JourneyState.commit` (fold the decision into the recipe) and
:func:`finish` (run the whole line and score the wafer, reusing the :mod:`fab_game.game` economics).

Discipline (matching :class:`fab_game.game.GameSession`): the state is an **immutable** frozen dataclass
(each action returns a new state), the log is **append-only**, and ``(seed, grade, actions)`` is
**deterministic**. Zero new physics — it composes :func:`run_line` + :func:`score_wafer` (ADR 0005). The
**live UI** (a notebook ``interact`` / a Textual journey screen) is the deferred next increment; this
module is headless and tested, and :mod:`fab_game.demo_journey` is a *watch-a-playthrough* artifact over it.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from chip.purification import Contamination, FEEDSTOCK_GRADES, zone_refine

from .game import GameConfig
from .pipeline import LineResult, run_line
from .recipe import DEFAULT_RECIPE, Recipe
from .scoring import ScoreCard, score_wafer
from .spec import DEFAULT_SPECS
from .variation import NO_VARIATION, Variation

DEFAULT_GRADE = "solar"          # start with an intermediate (dirty) feed — the refining IS the gameplay
DEFAULT_STEP = 0.25              # one refine() increment, in zone-passes (≈ half a decade of Na per step)
DEFAULT_GRID_N = 11              # forecast map resolution — fine enough to resolve the OSF core/ring/rim
#                                  (at 11 the radial growth optimum reads a clean ~96 %; coarser dicing
#                                  over-weights the core/rim and the optimum never clears "clean")

# Crystal growth (phase 2) — the pull-rate decision rides a fixed RADIAL hot zone so BOTH grown-in
# consequences are graded (the gradual-failure policy): a vacancy void CORE (pull too fast) + an
# interstitial dislocation/leakage RIM (pull too slow) + a clean OSF ring between, with pull rate moving
# the ring. The centre gradient + boost are FLAGGED house knobs (chosen so the two-sided window has an
# interior optimum ~V*); ξ_t + the Voronkov criterion are the cited tight legs. (Uniform G would make the
# slow side an all-or-nothing leakage CLIFF — the radial profile is what grades it; A2's wired knob.)
GROWTH_G_CENTER_K_PER_MM = 4.0   # the centre interface gradient G_center (radial: G(r)=G_center·(1+boost·r²))
GROWTH_RADIAL_BOOST = 4.0        # the radial steepness — sets the void-core/leak-rim spread (the OSF ring)
DEFAULT_PULL_MM_MIN = 2.0        # the two-sided optimum at this hot zone (~93 %: minimal core + cleared rim)

# Slice/cut (phase 3) — the wafer-prep decision is **where down the boule to cut** (the axial fraction
# solidified, ``czochralski.slice_z`` ∈ [0, 1)). It reads the boule's axial Scheil drift (G2): boron's
# k<1 walks the substrate doping — so ``V_t`` — UP toward the tail, so a wafer cut too deep lands above
# the ``V_t`` window. The consequence is graded (not a cliff): the radial t_ox non-uniformity already in
# the line spreads ``V_t`` across the die map — so the **centre** dies (nominal, highest ``V_t``) cross the
# high ceiling first while the **rim** (thinner gate oxide → lower ``V_t``) survives longest → a **centre
# core** of ``V_t`` kills before the whole wafer goes out. This is the *inverse* radial signature of stage-1's
# Na **edge** ring (Na is edge-loaded and pushes ``V_t`` DOWN into the *low* bound, so the rim fails first;
# here the high bound is hit centre-first) — the gradual-failure policy, no new physics. Honestly
# **one-sided absent economics** — cutting at the seed (slice_z 0) is always safest; the value of cutting
# deeper (more wafers per boule = throughput) is the same deferred cost side as purification's refining
# effort. What makes the cut a real decision *today* is the phase-2 coupling: a faster pull flattens the
# drift, so a flat boule can be cut deep while a slow-pulled one is already lost to its leakage rim.
DEFAULT_SLICE_Z = 0.5            # a representative mid-boule cut (clean on a flat/optimum-pulled boule)

# Diffusion (phase 4) — the S/D junction decision is the **predep dose** (how much dopant you lay down
# before the drive-in redistributes it). It sets the diffused-layer **sheet resistance** ``R_s``; the
# drive-in is deliberately NOT the lever (it conserves dose — sealed Neumann both ends — so it trades
# junction depth for ``R_s`` weighting but barely moves ``R_s``, the same trap a slow pull was for the
# Scheil drift). The consequence is a NEW device consumer (phase 4 is honestly NOT "zero new physics"
# like phases 1–3): the diffusion outputs ``x_j``/``R_s`` fed nothing scored before — the device reads
# ``N_A``/``t_ox``/CD, never ``R_s`` — so the dose was inert. Phase 4 wires ``R_s`` → a parasitic S/D
# **series resistance** ``R_series = R_s·n_□`` → **source degeneration** (``chip.device`` v-add,
# default-0 seam) that **starves** ``I_Dsat`` (lands on the EXISTING I_Dsat floor — no new spec). An
# under-diffused (cool/short) predep → high ``R_s`` → low drive current → the wafer fails I_Dsat. ONE-SIDED
# (like purification/slice): more dose only lowers ``R_s`` — over-diffusion's harm is the short-channel
# tar pit the device model omits, so we do NOT fake a high-dose failure (the gradual-failure "inflate an
# unrelated variable" fudge). Graded by the existing radial t_ox non-uniformity (edge oxide thinner →
# higher C_ox → higher I_Dsat → survives; the thicker-oxide CENTRE crosses the floor first → an I_Dsat
# **centre core**, same radial sense as the slice V_t core but a different channel).
DIFFUSION_SD_CONTACT_SQUARES = 0.15   # the flagged house n_□ = R_series/R_s (a wide W=10µm device:
#                                       L_access/W ≈ 1.5µm/10µm); nominal R_series ≈ 12 Ω sits comfortably
#                                       inside the I_Dsat window, an under-diffused predep walks it out
DEFAULT_PREDEP_C = 950.0          # °C — the nominal (clean) predep temperature = the recipe default
DEFAULT_PREDEP_MIN = 10.0         # min — the nominal predep time = the recipe default

# Oxidation (phase 5) — the gate-oxide-growth decision is the **oxide time** (how long to grow the thin
# dry-O₂ gate oxide; the recipe holds the ambient/T/orientation). The grown ``t_ox`` is the one quantity
# the device reads **two ways at once**: ``V_t = V_FB + 2φ_F + Q_dep/C_ox`` (thicker oxide → larger ``V_t``)
# AND ``I_Dsat ∝ C_ox·(V_GS−V_t)²`` (thicker oxide → lower ``C_ox`` → lower ``I_Dsat``). So oxidation is the
# first genuinely **TWO-SIDED** stage that needs **no economics** (like crystal growth, not the one-sided
# purify/slice/diffuse): too **thin** → ``V_t`` under the floor + ``I_Dsat`` over the ceiling (a low
# threshold / over-current), too **thick** → ``V_t`` over the ceiling + ``I_Dsat`` under the floor (a high
# threshold / starved drive), with a clean window between. It adds **ZERO new physics** — the t_ox→V_t/I_Dsat
# chain is the device's *core* read — so phase 5 RESTORES the "zero new physics" framing phase 4 broke (no
# new device term at all). The grading is the oxidation step's **own** radial ``t_ox`` non-uniformity (edge
# ~2.5 % thinner, :attr:`fab_game.variation.Variation.t_ox_edge_frac`) — the spread phases 3–4 *borrowed*,
# finally grading its **home** stage; and the two sides fail at **opposite radii** (the only stage that does):
# under-oxidized → the thinnest **rim** crosses the thin-side bounds first → an EDGE RING (echoing stage-1's
# Na ring); over-oxidized → the thickest **centre** crosses the thick-side bounds first → a CENTRE CORE
# (echoing the slice/diffusion cores). The lever is **time**, not (T, minutes): in the thin reaction-limited
# regime ``t_ox ≈ (B/A)·t`` is monotone, and temperature moves both Deal–Grove constants and risks the
# Massoud thin-dry band — a second knob the window doesn't need.
DEFAULT_OXIDE_MIN = 20.0          # the recipe-nominal gate-oxide time (≈14 nm dry/1000 °C) = the seam. NOTE:
#                                   oxide_min=None ⇒ the recipe NOMINAL, not "stage disengaged" — you cannot
#                                   make a MOSFET with no gate oxide, so the seam is the lever AT NOMINAL
#                                   (bit-identical to the pre-phase-5 journey), not an off switch like the
#                                   diffusion consumer's default-0.
OXIDE_OFF_NOMINAL_FRAC = 0.06     # the |t_ox − nominal|/nominal band that flags an oxidation root in the
#                                   channel trail. The nominal recipe's radial+jitter t_ox spread is ~3 %
#                                   and the pass band ~±9 %, so 6 % cleanly separates "the oxide IS the
#                                   cause" from a nominal-oxide V_t/I_Dsat death that is really Na/Scheil/
#                                   series-R (so the phase 1–4 channel tests, all at nominal oxide, are
#                                   untouched — their worst die never trips this band). FLAGGED house number.

# Consequence bands (the ok → rework → fail spectrum) — yield thresholds with margin so a boundary
# forecast doesn't flicker (ADR 0005 §5: coarse player guidance, not a magnitude claim). The CLEAN floor
# is 0.90, not 1.0: the radial growth optimum caps ~93 % (the OSF core/rim always cost a few dies — perfect
# silicon is hard), so "clean" must mean "as clean as this stage gets", not "flawless".
CLEAN_BAND = 0.90                # ≥ this yield: clean — the decision didn't (meaningfully) bite
DEAD_BAND = 0.05                 # ≤ this yield: dead — scrap (essentially every die out)


def consequence_band(yield_: float) -> str:
    """Map a forecast yield to the ok→rework→fail band: ``"clean"`` / ``"ring"`` / ``"dead"``."""
    if yield_ >= CLEAN_BAND:
        return "clean"
    if yield_ <= DEAD_BAND:
        return "dead"
    return "ring"


# --------------------------------------------------------------------------- #
# The consequence forecast — run the recipe-so-far, band it, name the channel
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StageForecast:
    """The downstream consequence of the recipe-so-far — the line run at it, banded and channel-named.

    ``band`` the ok→rework→fail spectrum (:func:`consequence_band`); ``channel`` the dominant failure
    mechanism the trail names (``V_t`` mobile-ion / leakage metal / drive current), or ``None`` when clean;
    ``yield_``/``mean_vt`` the readout; ``result`` the wafer (for the map/trail); ``contamination`` the
    current impurity vector (cm⁻³); ``headline`` the one-line human summary.
    """

    band: str
    channel: str | None
    yield_: float
    mean_vt: float | None
    contamination: dict
    result: LineResult
    headline: str


def _mean_vt(result: LineResult) -> float | None:
    vts = [d.V_t for d in result.wafer.dies if d.V_t is not None]
    return sum(vts) / len(vts) if vts else None


def _nominal_oxide_nm(ox_knobs) -> float:
    """The known-good gate-oxide thickness (nm) — the reference an oxidation root is measured against.

    Grown for the **nominal** :data:`DEFAULT_OXIDE_MIN` at the recipe's own ambient/T/orientation (so it
    stays coherent if those move), NOT a hardcoded ~14 nm. The phase-5 channel discriminator flags a die
    whose *inherited* ``t_ox`` is off this by more than :data:`OXIDE_OFF_NOMINAL_FRAC`."""
    from chip.oxidation import grow_oxide
    return grow_oxide(ox_knobs.ambient, ox_knobs.T_celsius, DEFAULT_OXIDE_MIN,
                      orientation=ox_knobs.orientation).t_ox_nm


def _oxidation_root(worst, ox_knobs, reasons: str) -> str | None:
    """Name a gate-oxide-thickness root for a ``V_t``/``I_Dsat`` death, or ``None`` (oxide is in band).

    Phase 5 collides with every other parametric root — over-oxidation's ``V_t``-high looks like the Scheil
    cut, under-oxidation's ``V_t``-low like the mobile-ion Na, its ``I_Dsat``-low like the S/D series
    resistance. The V_t/I_Dsat **sign pattern is not unique** (a deep Scheil cut raises ``N_A`` → raises
    ``V_t`` → lowers the overdrive → *also* drags ``I_Dsat`` down — the same signs as over-oxidation), so we
    key on the **unambiguous** fingerprint: the die's *inherited* ``t_ox`` itself, off the known-good
    thickness (advisor). Only fires for a ``V_t``/``I_Dsat`` *parametric* reason (not a functional particle/
    void/bridge kill) and only when the oxide is genuinely off nominal — the nominal recipe's ~3 % radial+
    jitter spread never trips the 6 % band, so the seam and the phase 1–4 channel tests are untouched."""
    if worst.t_ox_um is None:
        return None
    if not ("v_t" in reasons or "i_dsat" in reasons or "i_d" in reasons):
        return None                                       # a functional kill — oxide thickness is not the root
    t_ox_nm = worst.t_ox_um * 1.0e3
    nominal_nm = _nominal_oxide_nm(ox_knobs)
    if t_ox_nm > nominal_nm * (1.0 + OXIDE_OFF_NOMINAL_FRAC):
        return (f"gate oxide too thick — over-oxidized (V_t high + I_Dsat starved; "
                f"{t_ox_nm:.1f} nm vs ~{nominal_nm:.1f} nm nominal — grow less oxide)")
    if t_ox_nm < nominal_nm * (1.0 - OXIDE_OFF_NOMINAL_FRAC):
        return (f"gate oxide too thin — under-oxidized (V_t low + I_Dsat over the ceiling; "
                f"{t_ox_nm:.1f} nm vs ~{nominal_nm:.1f} nm nominal — grow more oxide)")
    return None


def _dominant_channel(result: LineResult, recipe: Recipe) -> str | None:
    """Name the channel the dead dies fail on (the consequence the player watches propagate), or ``None``.

    Reads the worst (outer-most) dead die's verdict reasons. The same verdict word can have **different
    roots** in different stages, so it reads the crystal-growth regime to disambiguate: with the Voronkov
    hot zone engaged (``thermal_gradient`` set), a *killer particle* is a **grown-in void/COP** (pull too
    fast) and *leakage* is from **grown-in dislocations** (pull too slow) — otherwise leakage is a
    deep-level **metal** (the purification story) and a particle is a fab-floor defect. The **gate-oxide**
    root (phase 5) is checked **first** for a ``V_t``/``I_Dsat`` death — it collides with the Na/Scheil/
    series-R roots on the V_t/I_Dsat *sign*, so it is discriminated on the inherited ``t_ox`` (see
    :func:`_oxidation_root`)."""
    dead = result.dead_dies
    if not dead:
        return None
    worst = max(dead, key=lambda d: d.radius_frac)
    reasons = " ".join(worst.verdict.reasons).lower()
    grown_in = recipe.czochralski.thermal_gradient_K_per_mm is not None   # Voronkov hot zone engaged
    oxide_root = _oxidation_root(worst, recipe.oxidation, reasons)         # phase 5: t_ox off nominal → the gate oxide
    if oxide_root is not None:
        return oxide_root
    if "v_t" in reasons:
        # Disambiguate the two V_t roots by *direction* (the spec reason says "(high)"/"(low)"): the
        # purification story drives V_t **down** (mobile-ion Na → Q_ox → V_FB down), the slice/cut story
        # drives it **up** (cutting deep down the boule → Scheil-walked high substrate N_A). Only name the
        # cut when a slice was actually taken (advisor: key the high branch on direction AND the stage
        # being engaged) — so a high-V_t from some other root isn't auto-blamed on the cut.
        sliced_deep = recipe.czochralski.slice_z > 0.0
        if "(high)" in reasons and sliced_deep:
            return "V_t — Scheil axial drift (cut too far down the boule → high substrate doping)"
        return "V_t — mobile-ion Na → gate-oxide charge"
    if "leak" in reasons:
        if grown_in:
            return "junction leakage — grown-in dislocations (crystal pulled too slow)"
        return "junction leakage — deep-level metal (Fe/Cu)"
    if "particle" in reasons or "defect" in reasons:
        if grown_in:
            return "grown-in voids/COPs (crystal pulled too fast)"
        return "killer particle (fab-floor defect)"
    if "i_dsat" in reasons or "i_d" in reasons:
        # Discriminate the diffusion series-R root by DIRECTION (like the V_t high/low split): a parasitic
        # S/D series resistance only ever STARVES the drive (I_Dsat *low*), and only when the diffusion
        # consumer is engaged — so a defocus/over-etch CD-collapse over-current (I_Dsat *high*) stays the
        # generic branch.
        if recipe.diffusion.sd_contact_squares > 0.0 and "(low)" in reasons:
            return "I_Dsat — S/D series resistance (junction under-diffused → high R_s starves the drive)"
        return "drive current (I_Dsat)"
    return worst.verdict.reasons[0] if worst.verdict.reasons else "unknown"


def forecast(state: "JourneyState") -> StageForecast:
    """Run the line at the current recipe (variation **on**, so the ring shows) → the consequence band.

    Reuses :func:`run_line` — zero new physics. Single seed (the journey's), like the dashboard; the bands
    carry a margin so a boundary forecast does not flicker. ``clean`` ⇒ the recipe-so-far didn't bite;
    ``ring`` ⇒ a marginal recipe kills **part** of the wafer (spatially an edge ring or a centre core,
    depending on the stage — rework territory); ``dead`` ⇒ scrapped."""
    recipe = state.current_recipe
    # NOTE (device-targets slice 1): the forecast bands against DEFAULT_SPECS — the **fast-logic** baseline
    # — deliberately, not the declared target. The band is a coarse "did the recipe bite?" yield guide, not
    # a SKU verdict; a target-aware forecast (and the disposition readout that re-scores the *finished* wafer
    # against the sibling flavors, :func:`fab_game.targets.disposition`) is wired at the UI slice. ``finish``
    # already scores the real wafer against the declared target's windows/prices (its ``config``).
    wafer = run_line(recipe, seed=state.seed, variation=Variation(), specs=DEFAULT_SPECS, grid_n=state.grid_n)
    result = LineResult.of(state.label, wafer)
    y = result.yield_
    band = consequence_band(y)
    channel = _dominant_channel(result, recipe) if band != "clean" else None
    if band == "clean":
        headline = f"clean — {y:.0%} yield, no meaningful consequence"
    elif band == "dead":
        headline = f"DEAD — {y:.0%} yield, scrapped on {channel}"
    else:
        headline = f"ring — {y:.0%} yield, part of the wafer fails on {channel}"
    return StageForecast(band=band, channel=channel, yield_=y, mean_vt=_mean_vt(result),
                         contamination=state.contamination.as_dict(), result=result, headline=headline)


def refining_trajectory(grade: str, *, max_effort: float = 2.0, step: float = DEFAULT_STEP):
    """The impurity vector at each refining effort ``0..max_effort`` — the multi-step 'watch it develop'.

    Na/Fe/Cu fall by ``k^n`` (the tiny-``k`` metals fastest), boron barely moves (``k ≈ 0.8``) — the
    teachable segregation contrast, straight from the cited ``k`` table. Returns a tuple of
    ``(effort, Contamination)``."""
    if grade not in FEEDSTOCK_GRADES:
        raise ValueError(f"unknown feedstock grade {grade!r} (have {sorted(FEEDSTOCK_GRADES)})")
    feed = FEEDSTOCK_GRADES[grade]
    n = int(round(max_effort / step))
    return tuple((round(i * step, 6), zone_refine(feed, i * step)) for i in range(n + 1))


def boule_profile(state: "JourneyState", *, n_slices: int = 7, z_max: float = 0.9):
    """The axial V_t profile down the boule (seed → tail) at the current pull — the 'watch it develop' view.

    Runs the line (``NO_VARIATION`` → the clean Scheil signal, one die) at ``n_slices`` axial positions and
    returns ``(slice_z, mean_V_t)`` pairs. Scheil segregation walks the substrate doping (so ``V_t``) up the
    boule; a **faster pull flattens** that drift (CG-1's ``k_eff → 1``). This is the boule developing as it
    is pulled — the profile the cut stage (phase 3) will read to choose where to slice."""
    out = []
    for i in range(n_slices):
        z = i * z_max / (n_slices - 1) if n_slices > 1 else 0.0
        rec = replace(state.current_recipe,
                      czochralski=replace(state.current_recipe.czochralski, slice_z=z))
        wafer = run_line(rec, seed=state.seed, variation=NO_VARIATION, specs=DEFAULT_SPECS, grid_n=1)
        vt = wafer.dies[0].V_t
        out.append((round(z, 4), float(vt) if vt is not None else float("nan")))
    return tuple(out)


DEMO_PREDEP_C = 900.0            # the representative predep temperature the demo sweeps the TIME (dose) at
#                                  (a wide graded I_Dsat band lives in the predep-time lever here; cf. the
#                                  T lever, whose graded edge at a full 10-min predep is narrower)


def oxidation_trajectory(state: "JourneyState", *,
                         minutes_sweep: tuple[float, ...] = (14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0)):
    """The gate device down a gate-oxide-**time** sweep — the phase-5 'watch the oxide set the device' view.

    For each oxidation time, runs the line (``NO_VARIATION`` → the clean signal, one die) with the oxidation
    stage engaged and returns ``(minutes, t_ox_nm, V_t, i_dsat_mA)``. A longer oxidation grows a thicker
    gate oxide → ``V_t`` rises (``Q_dep/C_ox``) **and** ``I_Dsat`` falls (``C_ox`` down): the two-sided
    consequence the player reads. The clean one-die device walks from the thin-side (``V_t`` low / ``I_Dsat``
    over the ceiling) up through the window to the thick-side (``V_t`` high / ``I_Dsat`` starved); under
    variation the radial ``t_ox`` spread grades each crossing into an edge ring (thin) or a centre core
    (thick)."""
    out = []
    for m in minutes_sweep:
        eng = state.oxidize(m)
        wafer = run_line(eng.current_recipe, seed=state.seed, variation=NO_VARIATION,
                         specs=DEFAULT_SPECS, grid_n=1)
        die = wafer.dies[0]
        out.append((float(m), float(die.t_ox_um) * 1.0e3 if die.t_ox_um is not None else float("nan"),
                    float(die.V_t) if die.V_t is not None else float("nan"),
                    float(die.i_dsat_mA) if die.i_dsat_mA is not None else float("nan")))
    return tuple(out)


def diffusion_trajectory(state: "JourneyState", *, predep_C: float = DEMO_PREDEP_C,
                         predep_sweep_min: tuple[float, ...] = (6.0, 5.0, 4.0, 3.0, 2.5, 2.0)):
    """The S/D junction down a **predep-dose** sweep (predep *time*) — the phase-4 'watch the dose set the
    junction' view.

    For each predep time (at a fixed representative ``predep_C``), runs the line (``NO_VARIATION`` → the
    clean signal, one die) with the diffusion stage engaged and returns
    ``(predep_min, R_s_ohm_sq, x_j_um, i_dsat_mA)``. A shorter predep lays down **less dose** → a higher
    sheet resistance ``R_s`` → (through the series-R consumer) a lower ``I_Dsat`` — the dose decision the
    cut stage's :func:`boule_profile` is to the cut. The clean one-die ``I_Dsat`` walks toward the spec
    floor as the dose drops; under variation the radial t_ox spread grades the crossing into a centre
    core."""
    out = []
    for t in predep_sweep_min:
        eng = state.diffuse(predep_C=predep_C, predep_min=t)
        wafer = run_line(eng.current_recipe, seed=state.seed, variation=NO_VARIATION,
                         specs=DEFAULT_SPECS, grid_n=1)
        die = wafer.dies[0]
        out.append((float(t), float(die.R_s) if die.R_s is not None else float("nan"),
                    float(die.x_j_um) if die.x_j_um is not None else float("nan"),
                    float(die.i_dsat_mA) if die.i_dsat_mA is not None else float("nan")))
    return tuple(out)


# --------------------------------------------------------------------------- #
# The journey state — an immutable, accumulating recipe + the purification decision
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class JourneyState:
    """An immutable staged build of one wafer's recipe — a decision per fab stage (purify → grow → cut → diffuse).

    ``recipe`` the accumulator (committed stages); the *in-progress* decision is whichever stage's lever is
    set — ``grade``/``effort`` (purify), ``pull_rate`` (grow), ``slice_z`` (cut), ``predep_C``/``predep_min``
    (diffuse), ``oxide_min`` (oxidize) — each folded into :attr:`current_recipe` until :meth:`commit`.
    ``seed``/``grid_n`` the forecast determinism + resolution, ``log`` the append-only trail. Each action
    returns a **new** state (the ``WaferState``/``GameSession`` discipline)."""

    recipe: Recipe = DEFAULT_RECIPE
    grade: str = DEFAULT_GRADE
    effort: float = 0.0
    pull_rate: float | None = None   # crystal-growth lever (mm/min); None = growth not engaged (the seam)
    slice_z: float | None = None     # slice/cut lever — axial fraction [0,1); None = cut not engaged (the seam)
    predep_C: float | None = None    # diffusion lever — predep temperature (°C); None = diffusion not engaged (seam)
    predep_min: float = DEFAULT_PREDEP_MIN  # predep time (min) — only meaningful once predep_C is set
    oxide_min: float | None = None   # oxidation lever — gate-oxide time (min); None = recipe NOMINAL (the seam,
    #                                  i.e. the lever at nominal — not an off switch; a MOSFET always has a gate oxide)
    seed: int = 0
    grid_n: int = DEFAULT_GRID_N
    log: tuple[str, ...] = ()

    @property
    def current_recipe(self) -> Recipe:
        """The accumulator with the in-progress decisions folded in: the purification grade + effort, the
        crystal-growth pull (at the fixed radial hot zone) when set, and the slice/cut axial position when set.

        Each lever overlays a single recipe slice (purification, or the shared Czochralski knobs — pull +
        slice compose on it), and is **idempotent** for an already-committed decision (re-applying the value
        it baked). So a single :meth:`commit` can fold whichever stage is in progress, and a lever left
        ``None`` is a true seam — the overlay is the identity, so a journey that never grows/cuts is
        byte-identical to the recipe default (``slice_z`` 0)."""
        recipe = replace(self.recipe, purification=replace(self.recipe.purification,
                                                           grade=self.grade, zone_passes=self.effort))
        cz = recipe.czochralski
        if self.pull_rate is not None:
            cz = replace(cz, pull_rate_mm_min=self.pull_rate,
                         thermal_gradient_K_per_mm=GROWTH_G_CENTER_K_PER_MM,
                         radial_gradient_boost=GROWTH_RADIAL_BOOST)
        if self.slice_z is not None:
            cz = replace(cz, slice_z=self.slice_z)
        if cz is not recipe.czochralski:                      # only touch the recipe when a lever is engaged
            recipe = replace(recipe, czochralski=cz)
        if self.predep_C is not None:                         # diffusion stage engaged → overlay the predep
            recipe = replace(recipe, diffusion=replace(           # dose + turn on the series-R consumer (n_□)
                recipe.diffusion, T_predep_C=self.predep_C, t_predep_min=self.predep_min,
                sd_contact_squares=DIFFUSION_SD_CONTACT_SQUARES))
        if self.oxide_min is not None:                        # oxidation stage engaged → overlay the oxide time
            recipe = replace(recipe, oxidation=replace(recipe.oxidation, minutes=self.oxide_min))
        return recipe

    @property
    def label(self) -> str:
        """A short human label for the recipe-so-far (grade · refine, the pull rate if grown, the cut if sliced)."""
        s = f"{self.grade}·refine×{self.effort:g}"
        if self.pull_rate is not None:
            s += f" · pull {self.pull_rate:g} mm/min"
        if self.slice_z is not None:
            s += f" · cut z={self.slice_z:g}"
        if self.predep_C is not None:
            s += f" · predep {self.predep_C:g}°C/{self.predep_min:g}min"
        if self.oxide_min is not None:
            s += f" · oxide {self.oxide_min:g}min"
        return s

    @property
    def contamination(self) -> Contamination:
        """The purified impurity vector at the current grade + effort (the seam currency)."""
        return self.current_recipe.contamination

    def choose_grade(self, grade: str) -> "JourneyState":
        """Pick a raw feedstock — resets the refining effort to 0 (a fresh, unrefined charge)."""
        if grade not in FEEDSTOCK_GRADES:
            raise ValueError(f"unknown feedstock grade {grade!r} (have {sorted(FEEDSTOCK_GRADES)})")
        return replace(self, grade=grade, effort=0.0,
                       log=self.log + (f"feedstock: {grade} (raw, unrefined)",))

    def refine(self, step: float = DEFAULT_STEP) -> "JourneyState":
        """Advance the zone-refining by one increment of effort — the multi-step 'watch it develop'."""
        if step <= 0:
            raise ValueError(f"refine step must be > 0, got {step}")
        nxt = replace(self, effort=self.effort + step)
        c = nxt.contamination
        return replace(nxt, log=self.log + (f"refine +{step:g} → effort {nxt.effort:g}: "
                                            f"Na {c.Na:.2e} cm⁻³",))

    def grow(self, pull_rate: float = DEFAULT_PULL_MM_MIN) -> "JourneyState":
        """Set (or recalibrate) the boule pull rate — the crystal-growth lever (mm/min).

        The pull rate rides the fixed radial hot zone (:data:`GROWTH_G_CENTER_K_PER_MM` /
        :data:`GROWTH_RADIAL_BOOST`): too fast → a vacancy void **core**, too slow → an interstitial
        dislocation/leakage **rim**, the clean OSF ring between — pull rate moves the ring. Call again to
        recalibrate (re-decide + re-observe — the Level-1 multi-step; a true variable mid-pull *schedule*
        is the named deferred Level-2)."""
        if pull_rate <= 0:
            raise ValueError(f"pull rate must be > 0 mm/min, got {pull_rate}")
        return replace(self, pull_rate=pull_rate,
                       log=self.log + (f"grow: pull {pull_rate:g} mm/min "
                                       f"(ξ_centre = {pull_rate / GROWTH_G_CENTER_K_PER_MM:.3f})",))

    def cut(self, slice_z: float = DEFAULT_SLICE_Z) -> "JourneyState":
        """Slice a wafer from the boule at axial fraction ``slice_z`` ∈ [0, 1) — the phase-3 wafer-prep lever.

        Reads the boule's axial Scheil drift (use :func:`boule_profile` to *watch it develop* first — the
        seed→tail ``V_t`` walk this cut samples): boron's k<1 raises the substrate doping (so ``V_t``)
        toward the tail, so a wafer cut **too deep** lands above the ``V_t`` window — failing the **centre**
        dies first (a graded ``V_t`` **core**: the radial t_ox non-uniformity grades the cliff — the rim's
        thinner oxide gives it a lower ``V_t``, so it survives the high ceiling longest), then the whole
        wafer. Cutting at the **seed** (``slice_z`` 0) is always safest; how deep you can cut and stay
        in spec is set by the **phase-2 pull** (a faster pull flattened the drift — :func:`boule_profile`).
        Call again to re-cut (re-decide; the boule is unchanged, only where you take the wafer)."""
        if not 0.0 <= slice_z < 1.0:
            raise ValueError(f"slice_z must be in [0, 1), got {slice_z}")
        return replace(self, slice_z=slice_z,
                       log=self.log + (f"cut: slice z={slice_z:g} (axial fraction down the boule)",))

    def diffuse(self, predep_C: float = DEFAULT_PREDEP_C,
                predep_min: float = DEFAULT_PREDEP_MIN) -> "JourneyState":
        """Set the S/D **predep dose** — the phase-4 diffusion lever (predep temperature °C + time min).

        The decision is *how much dopant to lay down* before the drive-in redistributes it: the predep
        (a constant-source ``erfc`` at the solubility limit, :func:`chip.diffusion_dopant.two_step`) sets
        the diffused-layer **sheet resistance** ``R_s``. Engaging the stage also turns on the series-R
        consumer (``sd_contact_squares`` = the house :data:`DIFFUSION_SD_CONTACT_SQUARES`), which wires
        ``R_s`` → a parasitic **source** series resistance ``R_series = R_s·n_□`` → **source degeneration**
        starving ``I_Dsat`` (:func:`chip.device.saturation_current`). So an **under-diffused** (cool/short)
        predep → high ``R_s`` → low drive current → the wafer fails the I_Dsat floor (a graded,
        **centre-weighted ``I_Dsat`` core**: the edge's thinner gate oxide gives more drive, so the
        thicker-oxide centre crosses first — centre-weighted, blurred by CD scatter, not a clean monotone
        like the slice V_t core). Use :func:`diffusion_trajectory` to *watch the dose set the junction*
        first. The
        **drive-in is deliberately not the lever** — it conserves dose, so it swings ``x_j`` but barely
        moves ``R_s``. ONE-SIDED (like purify/slice): a hotter/longer predep only lowers ``R_s`` (the
        over-diffusion harm — short-channel rolloff — is the device model's omitted scope edge, not faked
        here). Call again to re-decide."""
        if predep_C <= 0.0:
            raise ValueError(f"predep temperature must be > 0 °C, got {predep_C}")
        if predep_min <= 0.0:
            raise ValueError(f"predep time must be > 0 min, got {predep_min}")
        nxt = replace(self, predep_C=predep_C, predep_min=predep_min)
        rs = nxt.current_recipe.diffusion
        from chip.diffusion_dopant import two_step
        from chip.junction import analyze_junction
        _, drivein = two_step(rs.dopant, T_predep=rs.T_predep_C, t_predep_min=rs.t_predep_min,
                              T_drivein=rs.T_drivein_C, t_drivein_min=rs.t_drivein_min, length_um=rs.length_um)
        junc = analyze_junction(drivein, rs.dopant, nxt.current_recipe.effective_channel_N_A)
        return replace(nxt, log=self.log + (f"diffuse: predep {predep_C:g}°C/{predep_min:g}min → "
                                            f"R_s {junc.R_s:.0f} Ω/sq, x_j {junc.x_j_um:.3f} µm",))

    def oxidize(self, minutes: float = DEFAULT_OXIDE_MIN) -> "JourneyState":
        """Set the gate-oxide growth **time** — the phase-5 oxidation lever (min, dry O₂ at the recipe T).

        The decision is *how much gate oxide to grow*: the thin dry-O₂ oxide thickness ``t_ox``
        (:func:`chip.oxidation.grow_oxide`) the device reads **two ways at once** — ``V_t = V_FB + 2φ_F +
        Q_dep/C_ox`` (thicker → higher ``V_t``) and ``I_Dsat ∝ C_ox·(V_GS−V_t)²`` (thicker → lower
        ``I_Dsat``). So this is the first genuinely **two-sided** stage with **no economics** (like crystal
        growth): grow **too little** → ``V_t`` under the floor + ``I_Dsat`` over the ceiling (a low
        threshold / over-current); grow **too much** → ``V_t`` over the ceiling + ``I_Dsat`` under the floor
        (a high threshold / starved drive); a clean window between. **Zero new physics** — the t_ox→V_t/I_Dsat
        chain is the device's core read (phase 5 RESTORES the framing phase 4 broke). The consequence is
        **graded** by the oxidation step's own radial ``t_ox`` non-uniformity (edge ~2.5 % thinner), and the
        two sides fail at **opposite radii**: under-oxidized → the thinnest **rim** crosses first → an **edge
        ring** (cf. stage-1's Na ring); over-oxidized → the thickest **centre** crosses first → a **centre
        core** (cf. the slice/diffusion cores). How much oxide you can grow before the ``V_t`` ceiling bites
        is **set by the phase-3 cut** (a deeper cut → higher ``N_A`` → higher baseline ``V_t`` → less
        headroom): the V_t budget is shared, the same propagation payoff as the cut↔pull coupling. The lever
        is **time**, not temperature (a single monotone knob; ``T``/ambient/orientation stay at the recipe
        default). Use :func:`oxidation_trajectory` to *watch the oxide set the device* first. Call again to
        re-decide."""
        if minutes <= 0.0:
            raise ValueError(f"oxidation time must be > 0 min, got {minutes}")
        from chip.oxidation import grow_oxide
        nxt = replace(self, oxide_min=minutes)
        ox = nxt.current_recipe.oxidation
        g = grow_oxide(ox.ambient, ox.T_celsius, ox.minutes, orientation=ox.orientation)
        return replace(nxt, log=self.log + (f"oxidize: {minutes:g} min → gate oxide "
                                            f"{g.t_ox_nm:.1f} nm ({g.regime})",))

    def commit(self) -> "JourneyState":
        """Fold the in-progress decision(s) into the accumulating recipe — the next stage builds on it.

        One ``commit`` folds whichever stage is in progress: each lever (purify / grow / cut / diffuse /
        oxidize) overlays a recipe slice **idempotently** (re-applying the value it baked), so re-committing
        is a no-op and the order doesn't matter — this thin scaffold suffices for all of them. The clean refactor
        ("actions modify the recipe directly; commit is just a log boundary") only earns its keep once a
        stage needs **order-dependent or non-idempotent** folding — a knob whose committed value can't be
        re-derived from the state (e.g. an accumulating thermal budget). None of purify/grow/cut is — so
        not yet."""
        return replace(self, recipe=self.current_recipe, log=self.log + (f"committed: {self.label}",))


def new_journey(grade: str = DEFAULT_GRADE, *, seed: int = 0, grid_n: int = DEFAULT_GRID_N,
                recipe: Recipe = DEFAULT_RECIPE) -> JourneyState:
    """A fresh journey at a raw feedstock grade, unrefined (effort 0)."""
    if grade not in FEEDSTOCK_GRADES:
        raise ValueError(f"unknown feedstock grade {grade!r} (have {sorted(FEEDSTOCK_GRADES)})")
    return JourneyState(recipe=recipe, grade=grade, effort=0.0, seed=seed, grid_n=grid_n,
                        log=(f"feedstock: {grade} (raw, unrefined)",))


def finish(state: JourneyState, *, config: GameConfig | None = None) -> tuple[LineResult, ScoreCard]:
    """Run the full accumulated recipe end-to-end and score the wafer — reusing the :mod:`fab_game.game`
    economics (market bins, prices, wafer cost) rather than forking a parallel scoring path.

    Returns the scored :class:`~fab_game.pipeline.LineResult` and its :class:`~fab_game.scoring.ScoreCard`.
    Even with only purification interactive (every later stage at its default), the journey is playable
    start-to-finish: raw feed → committed recipe → binned, packaged, scored wafer."""
    cfg = config if config is not None else GameConfig()
    recipe = state.current_recipe
    wafer = run_line(recipe, seed=state.seed, variation=cfg.variation, specs=cfg.specs, grid_n=state.grid_n)
    result = LineResult.of(f"journey finish: {state.grade} × {state.effort:g}", wafer)
    sc = score_wafer(wafer, prices=cfg.prices, wafer_cost=cfg.wafer_cost, rework_cost=0.0)
    return result, sc
