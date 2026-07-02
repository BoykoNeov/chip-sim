# `fab_game` — the fab-line game (sand → a binned, packaged chip + a scored roguelike shell)

A gamified, full-production-line layer built **on top of** chip-sim: *recipe in → **yield** out, and
you can see **why** a die died.* Full plan: [`docs/plans/fab-game.md`](../docs/plans/fab-game.md);
the layering decision: [ADR 0005](../docs/decisions/0005-fab-game-layering.md).

> **Two layers, one repo, a one-way dependency.** The validated physics stays in `chip/` + `engines/`
> (cited triads); `fab_game/` owns only what *cannot* be physics-validated — the wafer state, the
> pipeline, spec windows, the stochastic spread + yield, and rework. The import direction is
> **`fab_game → chip/engines`, never the reverse**, enforced mechanically by
> `tests/test_import_direction.py`. New *process physics* always lands in the physics layer; this
> package holds balance, spec limits, and fun.

## G1 — the dramatic win (the harness + the vertical slice)

**All reuse, zero new physics.** G1 wires the *already-validated* diffusion → oxidation →
lithography → device back end through a state / variation / spec / yield / rework harness and banks
one artifact: **one bad knob → a dead die, with the failure trail.** The chain is

> defocus → the aerial image loses edge sharpness (**NILS** collapses) → the gate no longer prints
> reliably → those dies leave spec → the wafer **yield** drops, and the trail names *defocus*.

A center-to-edge focus bowl makes the failure **spatial** (the edge ring dies, the centre survives);
a litho **rework** (strip & re-expose at corrected focus) recovers it. The defocus chain rides
**CD → channel length → I_Dsat** and the **NILS** printability floor — **never `V_t`** (the device
model's own scope edge: `V_t` has no channel-length term; only `saturation_current` reads the CD).

## G2 — Czochralski + the Scheil axial-resistivity boule (the first new physics)

The first new, cited **front-of-line** physics ([`chip/czochralski.py`](../chip/czochralski.py),
triad-tested): a Czochralski boule grown from a boron melt has a **Scheil** axial dopant profile,
`C_s(z) = N_seed·(1−z)^(k−1)` (seed-end parameterized so the `z=0` slice is `1e17` *exactly* — the
seam survives). Because boron's segregation coefficient `k ≈ 0.8 < 1` (Trumbore 1960), the solid
that freezes later is *more* doped, so wafers sliced down the boule start at successively higher
substrate doping. That rising `N_A` **alone** walks the device `V_t` up across the spec window — so
the boule's **tail is scrapped**, purely from one crystal-growth knob:

> Scheil segregation → axial resistivity/`N_A` spread → device `V_t` spread → yield down the boule.

**Unit-of-run (the plan §10 question, resolved here):** a *run* is **one wafer at axial `slice_z`**
(`CzochralskiKnobs.slice_z`); the boule is shared context that sets the wafer's starting substrate
(`channel_N_A` is now a boule-slice **property**). `run_batch` is the sweep *down* the boule — an
analysis/demo view that surfaces where each slice sits on the Scheil curve, **not** the roguelike
loop. The axial boule story is per-wafer, so it composes orthogonally with the radial die map.

The Scheil maths are validated as cited physics in [`chip/tests/test_czochralski.py`](../chip/tests/test_czochralski.py)
(`k→1` uniform limit + exact seed; `∫₀¹ C_s = C_0` conservation; cited `k` + Masetti resistivity).
**Oxygen → thermal donors** (the planned G2 contamination demo) later landed as the **C1**
deepening (`czochralski.py §1e`; see *Scope-edge promotions* below) — because its `k` is contested and the
donor kinetics are calibrated, it runs on its own flagged magnitudes and never borrows Scheil's tight anchors.

## G3 — wafer prep + particles + the die map made physical

G2 gave each wafer a substrate; **G3 makes the across-wafer map physical.** New cited physics in
[`chip/wafer_prep.py`](../chip/wafer_prep.py) (triad-tested): the **defect-limited yield law** — a
die that catches a killer particle is dead *functionally*, with probability `Y = exp(−D₀·A)` of
zero defects (the **Murphy / Poisson** model; **Stapper**'s negative-binomial `(1+D₀A/α)^(−α)` for
clustered defects rides as the `α→∞` limit + named scope edge) — plus the exact **geometry**
bookkeeping (slice → lap/CMP sets thickness / TTV / bow).

> killer particles scattered at **locations** on the die map → dies they hit die *functionally* →
> yield; **and** a weak CMP leaves the **TTV** out of flatness spec → the wafer is **scrapped**,
> recoverable by a re-polish that **eats thickness**.

The placement (`fab_game/defects.py`) draws killer particles as a **per-die Poisson** process —
which, by the Poisson restriction/superposition property, *is* the global wafer scatter restricted
to each die's cell, against the **single** `state.die_area_cm2` that the closed form also uses. The
banked artifact ([`demo_wafer_prep.py`](demo_wafer_prep.py) → `docs/figures/fab-game-g3.png`) shows
the empirical defect yield **converging to the cited `exp(−D₀·A)` law** as the random placement is
swept over density — the game-layer wiring tied back to the validated physics. A killer defect is a
**functional** fail (the transistor exists but is dead — distinct from an unresolved litho image,
where the device *refuses*); geometry is a **wafer-level scrap** gate.

The yield *law* is validated as cited physics in [`chip/tests/test_wafer_prep.py`](../chip/tests/test_wafer_prep.py)
(`Y(0)=1` exact + `α→∞`→Poisson limit; area-additivity `Y(A₁+A₂)=Y(A₁)·Y(A₂)` conservation; cited
Murphy/Stapper forms + an illustrative `D₀` band). **Clustered placement** (a fitted `α`) and the
**TTV→focus-budget** propagation wire are named scope edges, deferred.

## G4 — silicon purification + the contamination consequence model

The front of the line: a feedstock **grade** is a starting **impurity vector**, and **purification is
segregation** — [`chip/purification.py`](../chip/purification.py) (triad-tested) is the **Pfann**
single-pass zone-refining closed form `C(u)/C₀ = 1 − (1−k)e^(−k·u)`, reusing Czochralski's one cited
Trumbore `k` table. The teachable result is straight off that table: a tiny-`k` metal (Fe `k≈8e-6`) is
scrubbed ~5 orders in one pass, while boron (`k≈0.8`) is barely touched — segregation cleans metals
superbly but cannot purify the dopants. Then each surviving impurity reaches a device number **only as
far as a receiving variable exists** (the crux — propagation is gated by the consequence model, not the
engine):

- **G4a — Na → oxide charge, residual B/P → net doping.** Mobile-ion **Na** incorporates into the gate
  oxide as charge `Q_ox`, lifting `chip.device`'s named `Q_ox=0` edge (`ΔV_FB = −Q_ox/C_ox`) → `V_t`
  **down**; residual **B/P** fold into the effective channel doping. A dirty **MGS** feed (one pass)
  walks `V_t` out the bottom → scrapped on `V_t`, the trail naming the Na.
- **G4b — deep-level metals → SRH lifetime → junction leakage** (the consequence net doping *cannot*
  carry). [`chip/lifetime.py`](../chip/lifetime.py) (triad-tested) is the **Shockley–Read–Hall**
  recombination centre: `1/τ = 1/τ_bulk + Σ σ_n·v_th·N_metal` (p-type low-injection → the **electron**
  cross-section governs) and the generation-limited reverse leakage `J_gen = q·n_i·W/(2τ) ∝ N_metal`.

> a **metal-laden but Na/dopant-clean** feed (the flagged `"metal"` grade) → `V_t` reads **fine**, yet
> the diode is **leaky** → the wafer is scrapped on **leakage**, the trail naming deep-level-metal SRH.
> *V_t is a bystander* — the device effect net doping can't see. Rework = more zone passes (tiny `k`
> scrubs by `k²`/pass → one extra pass recovers lifetime/leakage).

The SRH law's **tight legs are the machinery, not the magnitudes** (plan §7 loose tier): the analytic
leg is the low-injection reduction of the full `U(n,p)` statistics (`σ_p`, `E_t` drop out → `σ_n`); the
conservation leg is **detailed balance** `U=0` at `p·n=n_i²` (exact for any parameters). The capture
cross-sections (Sze; Graff) + the clean-FZ `τ~ms` / `[Fe]~1e12→µs` order are **flagged loose**
([`chip/tests/test_lifetime.py`](../chip/tests/test_lifetime.py)). The leakage is computed *inside* the
device step (a new die field + an *optional* leakage spec window), so the provenance/bookkeeping is
unchanged and the metals never touch `V_t`/`I_Dsat`. **Gettering / precipitation / oxide breakdown**
stay named **Tier-3** edges.

## G5 — etch & deposition (the mid-line, between litho and the device)

The missing mid-line operations, the plan's **flagged-phenomenology** tier (§7) —
[`chip/etch_deposition.py`](../chip/etch_deposition.py) (triad-tested), two sections wired into the
pipeline **after litho, before the device** as one `etch_deposition_step`:

- **Etch — anisotropy → etch bias → the gate CD (the parametric failure).** A real etch is directional
  but not perfectly so: with anisotropy `A < 1` it undercuts the mask, and the **over-etch** needed to
  clear residue deepens the etch → widens the undercut → the transferred gate CD shrinks below the
  printed CD (`bias = 2·(1−A)·h·(1+OE)`). The etched CD **overwrites `cd_nm`**, so the device reads the
  *gate* CD — a shorter channel → `I_Dsat ∝ W/L` over its ceiling, CD out the bottom of its window. A
  perfectly anisotropic etch (`A = 1`) is the seam (zero bias). (The mirror failure — too *little* etch,
  a residual that bridges the gate lines into a short — landed as the **D1** under-etch promotion below,
  completing the plan's over/under-etch pair.)
- **Deposition — step coverage → a keyhole void (the functional failure).** The gap between gate lines
  (`pitch − CD`, aspect ratio `gate-height / gap`, *derived from the inherited gate geometry*) must be
  filled; a poor line-of-sight **PVD** (`SC ≈ 0.3`) pinches off a void where a conformal **CVD**
  (`≈ 0.9`) fills (`void ⇔ AR > SC/(1−SC)`) — a **functional** kill (the die's `V_t`/`I_Dsat` read fine),
  parallel to a killer particle. `SC = 1` (conformal) never voids — the seam.

> a poor **PVD** coverage voids the same gate gap a conformal **CVD** fills → scrapped on the **void**,
> the trail naming the non-conformal fill. **Rework is the reworkable/irreversible contrast** (the plan's
> "depo strippable; over-etch irreversible"): `rework_deposition` re-deposits a void conformally → it
> recovers, but a die whose CD was collapsed by over-etch stays dead (you cannot un-etch the gate).

The one genuinely **tight** leg is the bit-for-bit **seam** (`A=1` ⇒ bias 0 for any film/over-etch;
`SC=1` ⇒ never voids); the bias / underlayer / aspect-ratio algebra is **machinery (regression guards),
not a conservation anchor** (no only-possible-law content here, unlike wafer-prep area-additivity);
the magnitudes (anisotropy, step coverage, the pinch-off AR) are **flagged house numbers** — only the
cited *forms* (Wolf & Tauber; Plummer–Deal–Griffin; Campbell) and band orderings are asserted
([`chip/tests/test_etch_deposition.py`](../chip/tests/test_etch_deposition.py)). The optional etch-rate
non-uniformity is a **conditional 4th RNG draw** (fires only when its σ>0 → the G1–G4 demos are
byte-identical). **CMP planarization is named and deferred** (no device consumer in the compact model —
its real consumers, dishing→opens and planarity→focus budget, are unwired; TTV→focus is already a
`wafer_prep` edge).

## G6 — packaging & final-test binning (the back end; the line now runs sand → a binned chip)

The back end closes the line ([`chip/packaging.py`](../chip/packaging.py), triad-tested): a part must survive
every assembly op (dice → attach → wire-bond → encapsulate), so the **cumulative (multiplicative)
assembly-yield funnel** is `Y_assembly = Π yᵢ` (`assembly_yield(*ys)`; `expected_packaged(n, *ys) = n·Y`). The
one genuinely tight leg is the bit-exact seam (`yᵢ = 1 ⇒ Y = 1`); multiplicativity `Y(A∪B) = Y(A)·Y(B)` is the
identity, but the **load-bearing non-circular leg is the game-side per-die Bernoulli converging to `Πyᵢ`** (LLN —
exactly G3's placement → `exp(−D₀·A)`), not the arithmetic. The per-step numbers are flagged house values.

> **Binning is NOT physics — it is a grading policy** (the one trap here): `SpeedBins` / `SpeedBin` live in
> `spec.py` as a deterministic partition of survivors by `I_Dsat` (the speed proxy), default a **single open
> `"pass"` bin** = the seam. (A Gaussian "bin-convergence" leg would be near-tautological *and* the realized
> `I_Dsat` is non-Gaussian, so it would not converge — the convergence story belongs to assembly only.)

The G6 win: binning turns **process spread → a value distribution** — a tight process fills the premium bin, a
loose one (poor line-width control) spreads the grades and **bins a tail OUT**, and the headline "**works but
never shipped**": a back-end assembly scrap with a *perfect front end*. The assembly kill is a per-die
**Bernoulli drawn LAST**, gated on `assembly_yield < 1 ∧ variation.enabled` (the G5 conditional-draw-last
discipline → default knobs / `NO_VARIATION` ⇒ **G1–G5 byte-for-byte**). The four-way partition {front-end fail /
assembly scrap / bin-out / binned-good} tiles the map (good + bad = total). **Both rework loops now skip dies
that reached the back end** (`assembled is not None`) — a cracked die stays scrapped, never resurrected by a
re-exposure (a latent-bug fix from the done-check). **Rebond is named and deferred** (cracked die = scrap is the
honest default). Banked [`demo_packaging.py`](demo_packaging.py) → `fab-game-g6.png`.

## G7 — the roguelike game shell (scoring + the session; purely additive game policy)

The game shell over the now-complete line — **no physics / `run_line` / `WaferState` touched**, so it *executes*
ADR 0005 rather than deciding anew (the prior demos stay green trivially). Two game-layer modules:

- **`scoring.py` — the economics.** `BIN_PRICES` (premium/typical/value/reject → \$, flagged house) + wafer /
  scrap / rework costs; `score_wafer(wafer) → ScoreCard` (`revenue = Σ price·count` over shipped = `verdict.passed`
  dies, `profit = revenue − cost`). Mechanics-tested for bookkeeping + **monotonicity** (a better bin mix never
  earns less — the economic image of "propagation wired").
- **`game.py` — the session.** Immutable `GameSession` / `GameConfig`, `MARKET_BINS` (a *real* multi-grade
  `SpeedBins`, not the G6 seam), `process_wafer` / `scrap_wafer` / `play`, an append-only `RunRecord` history, and
  `ReworkSpec` (folds the tested rework paths into a turn).

The framing is **physics-grounded, not invented: one boule = one run, each wafer a turn, and the G2 Scheil `V_t`
drift IS the difficulty curve** — boron segregates down the boule (`V_t` walks 0.55 → 0.75, out the ceiling by
z ≈ 0.8), so early slices are easy and the **tail forces a decision**. The player's lever is to **thin the gate
oxide** (lower `t_ox` → lower `V_t` *and* higher `I_Dsat`), pulling the tail back into spec and the premium bin.

> **The honest framing (twice-corrected during build — keep it intact): of "adapt"'s +\$366 edge over naive,
> ~90 % (+\$336) is a premium WINDFALL** — thinning upgrades healthy, never-in-danger wafers to premium (the
> scaling lever) — and only **~10 % (+\$30) is the actual doomed-tail rescue.** The clean, cost-independent lesson
> is **scrap-vs-naive** (cut the loss on the tail). Adapt is **double-braked**: the `I_Dsat` ceiling brakes it
> *in-model* (over-thinning the extreme tail tips it over → a real Goldilocks fumble on the last wafer), and
> gate-oxide reliability brakes it *unmodeled* (the windfall is "free" only because that cost is off-book). It is
> **not** "adapt rescues the tail." Banked [`demo_game.py`](demo_game.py) → `fab-game-g7.png` (naive < scrap-the-tail < adapt).

### Playing it — the front-ends (thin drivers over the headless session)

Everything above is headless and tested; the UIs are thin skins (the discipline: the swallow-prone UI surface
renders pre-tested strings/figures verbatim, so the *renderers* carry the tests, not the UI run):

- **The §9 guided dashboard** — `dashboard.py` (`run_dashboard` / `dashboard_summary`) + `plots.dashboard_figure`,
  surfaced in the `fab_game.ipynb` "command the whole line" section: `run_line` behind 4 dramatic, legible knobs
  (defocus → edge ring · `D₀` → scattered kills · `slice_z` → Scheil drift · `t_ox` → the G7 rescue lever).
  Variation is **ON** (else the map is a binary all-pass/all-fail flip, not a story). The safety net is
  `tests/test_dashboard.py`, *not* the notebook run (`interact` swallows callback exceptions).
- **The Textual TUI** — `tui.py`, the **only** `textual` importer and **not** re-exported from `__init__` (so
  `import fab_game` and the fast lane stay headless; `[tui]` extra). `FabLineApp` drives the dashboard core + the
  headless `plots.wafer_map_text` ASCII die map; `RoguelikeScreen` drives a `GameSession` down one boule (one
  oxide-minutes Input = the adapt lever + Process / Scrap / New-run Buttons, disabled once `session.done`). The
  load-bearing string renderers live in **`session_view.py`** (import-pure, tested *without* textual). The pilot's
  load-bearing leg is **fidelity, not movement**: a driven Process/adapt/Scrap sequence == headless `play(...)`.
  - **Launch-time mode — Educational vs Hardcore.** `python -m fab_game.tui` opens a `ModeSelectScreen`:
    **Hardcore** is the bare cockpit (today's TUI, unchanged); **Educational** layers on a verbatim **guide
    panel** that explains every selector + readout (defocus · boule slice z · gate-oxide drive · seed · V_t ·
    I_Dsat · NILS · CD · leakage · Scheil drift …) and *what to do* — exploratory strategy on the dashboard, the
    process/adapt/scrap decision on the roguelike screen. The prose is **presentation only** (no knob/recipe/
    physics touched → the seam is byte-identical, the guide is `display:none` in hardcore) and lives in the
    new import-pure **`guide.py`** (`dashboard_guide` / `roguelike_guide` / `glossary_text` / `MODE_INTRO`),
    tested headless in `tests/test_guide.py` — the TUI renders it verbatim.

**The tycoon mode is the one remaining front-end** (same harness, different objective) — deferred.

## Crystal-growth deepenings (CG-1/2/3) — follow-ons to G2's boule, not new line stages

Three additive, opt-in, seam-safe sections in [`chip/czochralski.py`](../chip/czochralski.py) (every knob defaults
off ⇒ G1–G7 byte-for-byte). Each sits in the **flagged-phenomenology tier** — a cited *form* + a tight limit, no
conservation law:

- **CG-1 — Burton–Prim–Slichter `k_eff(pull rate)`** (§1b): a freezing-interface boundary layer lifts the
  *effective* segregation toward 1 with pull rate, so *pulling faster flattens the Scheil drift.* **Honest finding:
  boron barely moves** — `k₀ = 0.80` already sits near 1, so at realistic Si pull `k_eff ≈ 0.81–0.84` (modest; a
  flat boron boule would need ~10–20 mm/min, beyond realistic Si). One-sided in-model (no brake) → the demo shows
  the physics consequence only, not a score-war. ([`demo_crystal_growth.py`](demo_crystal_growth.py) → `fab-game-cg1.png`.)
- **CG-2 — Voronkov `V/G` grown-in defect criterion** (§1c): `ξ = V/G > ξ_t` ⇒ vacancy-rich (voids / COPs →
  gate-oxide killers), feeding the **same cited G3 Poisson map** — the in-model brake CG-1 lacked. **The finding:
  CG-1 and CG-2 do NOT trade off** — CG-1's parametric benefit is flat across the decision region, so **CG-2's
  criterion alone sets the pull** (the plateau location is the cited `ξ_t`; the only edge past it is throughput,
  unmodeled). ([`demo_voronkov.py`](demo_voronkov.py) → `fab-game-cg2.png`.)
- **CG-3 — Stefan interface heat balance** (§1d): supplies CG-2's gradient `G` from a quasi-steady front
  (`G_s = (L·ρ·V + k_l·G_l)/k_s`). **The finding: `ξ = V/G_s` SATURATES at `ξ_max = k_s/(L·ρ) ≈ 0.32`** as
  `V → ∞` — latent heat steepens `G_s` in lockstep, so fast pull's in-model cost is **bounded, not a cliff**
  (correcting CG-2's unbounded fixed-`G`). Closed-form, no engine amendment (the only consumer needs the algebraic
  balance, not the transient front `X(t)`). ([`demo_stefan.py`](demo_stefan.py) → `fab-game-cg3.png`.)

## Scope-edge promotions (C1/D1/A2/A1/E1) — named edges that earned a consumer

[`docs/plans/scope-edge-backlog.md`](../docs/plans/scope-edge-backlog.md) triaged the bag of named-but-unbuilt
edges *by consumer*; these five had one and were built (additive, opt-in, seam-safe). **The backlog is now
exhausted — every remaining edge lacks a consumer.**

- **C1 — crucible oxygen → thermal donors** (`czochralski.py §1e`): the cited **Kaiser–Frisch–Reiss fourth-power**
  initial rate `∝ [O_i]⁴`; the donors compensate the p-substrate (`N_A − N_TD`, exact) → `V_t` **down** via the
  G4a net-doping chain. Seam by **both** paths (no oxygen *or* no anneal); type inversion is guarded. (This is the
  G2-deferred oxygen demo, finally landed.) ([`demo_thermal_donors.py`](demo_thermal_donors.py) → `fab-game-c1.png`.)
- **D1 — under-etch** (`etch_deposition.py §3`): the mirror of G5's over-etch — an incomplete clear leaves
  `residual = UE·film` that **bridges** adjacent gate lines into a functional **SHORT** (the dual of the deposition
  void's OPEN). `cd_nm` is untouched (a purely functional kill); mutually exclusive with over-etch (a `__post_init__`
  guard). The demo is the **etch process window** — a Goldilocks band bracketed by a short (under) and a CD-collapse
  open (over). ([`demo_under_etch.py`](demo_under_etch.py) → `fab-game-d1.png`.)
- **A2 — OSF ring = CG-2 made radial** (`czochralski.py §1f`): a radial `G(r) = G_center·(1 + boost·r²)` makes
  `ξ(r)` fall outward, crossing `ξ_t` at `osf_ring_radius`. **The finding: vacancy density is monotone in ξ, so the
  kills PEAK at the centre and are ZERO at the ring — a COP-degraded vacancy CORE + a clean rim, NOT a ring of dead
  dies** (the ring is where kills *stop*; core mortality is modest, not a wipeout). Tight = the ring *location*
  (coefficient-robust) + the topology signs; the `G(r)` profile and the ring's on-wafer existence are flagged.
  `boost = None` ⇒ CG-2 byte-for-byte. ([`demo_osf_ring.py`](demo_osf_ring.py) → `fab-game-a2.png`.)
- **A1 — the interstitial side of Voronkov** (`czochralski.py §1g` + [`chip/lifetime.py`](../chip/lifetime.py)):
  `ξ < ξ_t` (slow pull) ⇒ grown-in dislocations (the void-density mirror across `ξ_t`) ⇒ a recombination channel
  (`1/τ += K·ρ_disl`) ⇒ junction **LEAKAGE** (the G4b channel), *not* yield. This closes a **two-sided window**
  (fast → yield loss, slow → leakage, the optimum AT `ξ_t`) and is also A2's deferred leaky-rim consumer → the
  **OSF ring is the one annulus clean of both**. **Honest finding: realistic CZ is vacancy-side, so A1 is a
  CORNER** — its value is the criterion's *symmetry* (slow pull is no longer free) + A2's rim, not a main-line
  trade. `V_t` / `I_Dsat` never move (the bystander). ([`demo_dislocation.py`](demo_dislocation.py) → `fab-game-a1.png`.)
- **E1 — spike/RTA thermal budget** (`chip/diffusion_dopant.py §4`): a piecewise-linear `T(t)` drives `D(T(t))`
  through the engine's callable-`D` path — `ThermalProgram` / `thermal_budget = ∫D dt` / `equivalent_isothermal_time`
  / `drive_in_program`. **The finding: the Arrhenius budget collapses near the peak** (a 19 s spike deposits ~2.5 s
  of peak-equivalent budget; the top 50 °C carries ~84 %) → a faster ramp → smaller `∫D dt` → shallower `x_j` (why
  RTA is shallow). **The verify-at-build verdict: the emergent-`T` "heat-mode" engine is FALSIFIED** —
  `√(D_dopant/α_thermal) ≈ 1.2e-6`, so `T` is flat over a junction; `D(T(t))` *is* the engine's shipped `D(t)` (the
  OED `effective_Dt` twin), not a new engine. No chip-side heat-mode consumer exists. ([`demo_thermal_budget.py`](demo_thermal_budget.py) → `fab-game-e1.png`.)
- **S4 — crucible oxygen's DUAL-USE** (`czochralski.py §1h` `internal_gettering_efficiency` + [`chip/purification.py`](../chip/purification.py)
  `getter_metals`): the asset face of C1's oxygen. Bulk oxygen **precipitates** trap the deep-level metals (Fe/Cu)
  out of the device region — **internal gettering** (Tan–Gardner–Tice, *Phys. Rev. Lett. 64, 196, 1990*) — so the
  *same* `[O_i]` that costs `V_t` (donors, C1) **buys back** junction leakage. A *process-trade-off within one
  device* (distinct from the S1–S3 market segmentation — no second SKU): too little oxygen leaks (un-gettered
  metals), too much craters `V_t` (donors at the non-skippable forming-gas sinter), a **Goldilocks** in between.
  Cited = the precipitation threshold (~12 ppma ≈ 6e17 cm⁻³); flagged = the efficiency magnitude. Gettering touches
  **Fe/Cu only** (never the Na→`Q_ox`→`V_t` chain) → the two oxygen channels stay orthogonal. Off by default (no
  `[O_i]` ⇒ the seam). ([`demo_internal_gettering.py`](demo_internal_gettering.py) → `fab-game-s4.png`.)

## The staged sand→chip journey (a third play mode)

Where the roguelike (`game.py`) runs one wafer down a boule and the dashboard (`dashboard.py`) exposes
four live sliders, the **journey** ([`journey.py`](journey.py)) builds **one wafer's recipe stage by
stage** — a real decision at each fab stage, watched as it propagates downstream: from no-effect,
through a graded yield ring, to an outright scrap. Each stage runs a **four-beat loop — decide →
observe → forecast → commit**: `forecast(state)` runs the line at the recipe-so-far and returns the
consequence **band** (`clean → ring → dead`, the ok→rework→fail spectrum) *and the channel it fails on*,
then `commit()` folds the decision into the accumulating `Recipe`. The scaffold is deliberately thin (an
immutable frozen `JourneyState` + a few idempotent overlay fields, **not** a nine-stage state machine —
per the repo's anti-over-build rule: a stage is built when it has a consumer).

Six stages are built (`refine` → `grow` → `cut` → `diffuse` → `oxidize`, then a cost-scored `finish`):

- **Purify (`refine`)** — the showcase for the **gradual-failure policy**: you start with a dirty
  feedstock and refine it step by step (`k^n` zone-refining, smooth in the continuous effort lever), and
  the forecast shows the marginal band where the edge-loaded **Na ring** lives (a `V_t` ring from
  mobile-ion Na, or junction leakage from deep-level metal — a feed that *looks* fine on threshold can
  still die on leakage).
- **Grow (`grow`)** — the pull-rate decision rides a fixed **radial** hot zone so both grown-in
  consequences are graded: a vacancy void **core** (pull too fast) + an interstitial dislocation/leakage
  **rim** (pull too slow) + a clean OSF ring between, with pull rate moving the ring.
- **Cut (`cut`)** — the first stage that **reads a prior committed decision**: a faster phase-2 pull
  flattens the boule's axial Scheil drift (CG-1), so you can slice *deeper* down the boule and still land
  in the `V_t` window — the "watch it propagate" payoff.
- **Diffuse (`diffuse`)** — the **honesty exception**: phases 1–3 add *zero new physics* (they
  re-sequence propagation chains the line already had), but the diffusion `x_j`/`R_s` fed nothing scored,
  so this stage adds one genuine device term — an additive S/D **series resistance** on
  `chip.device.saturation_current` (source degeneration, default-0 seam) wiring `R_s → I_Dsat`. The
  "adds no physics" claim is formally false here; the term is justified because this stage is its consumer,
  and it lands on the *existing* `I_Dsat` spec (no new window).
- **Oxidize (`oxidize`)** — the gate-oxide time; on its own a one-sided lever (thinner is always better),
  turned **two-sided** only by the cost side below.
- **`finish`** — runs the whole line and scores the wafer, reusing the `game.py` economics **plus** the
  process-cost side ([`scoring.py`](scoring.py) `process_cost` / `score_wafer(process_cost=…)`): refining
  is priced ∝ passes and S/D predep ∝ the real `∫D dt`, so net profit has an **interior** maximum
  (`under < opt < over`) — the one-sided stages become a **Goldilocks**. (The 950 °C predep default is
  revealed to be ~9× over-dosed; cut throughput cost is deferred — a multi-wafer / roguelike concern.)

Everything is headless and tested (deterministic in `(seed, grade, actions)`, immutable state,
append-only log); the live UI (a notebook `interact` / a Textual journey screen) is the deferred next
increment. [`demo_journey.py`](demo_journey.py) is a *watch-a-playthrough* artifact over it.

## Device targets — "good is application-relative"

The DTCO lesson ([`targets.py`](targets.py), [`docs/plans/device-targets.md`](../docs/plans/device-targets.md)):
the *same* physical property that ruins a part for one product is a *feature* for another, so a finished
wafer is **re-scored against multiple specs** — `regrade` / `disposition` grade the already-computed dies
against a different `DeviceTarget`'s windows + bins, **never re-fabricating**. Two guards come first: the
target windows genuinely **cross**, and a declaration **moves** the recipe optimum. Five slices are built:

- **S1 — the zero-new-physics spine** (`FAST_LOGIC` ↔ `LOW_POWER`): pure grading on the `V_t` axis — a
  high `V_t` is slow logic (reject) but a low-leakage low-power part (premium).
- **S2 — `HV_IO` + avalanche `BV`** (`chip.breakdown`, [[avalanche-breakdown-source]]): the one cited new
  device output, scored by an optional `bv` window; `x_j` **decouples** `BV` from `V_t` (the junction-depth
  axis), so HV-I/O is a genuinely orthogonal acceptance axis, not a relabel of thick-oxide low-power.
- **S3 — the high-resistivity `HIGH_RES` native part** (the substrate axis, again zero new physics): turns
  `BV`'s *other* knob, the substrate doping (`BV ∝ N_B^(−3/4)`, set at growth). Because `N_A` moves `BV`↑
  and `V_t`↓ coupled, the high-`BV` part is the **native** low-`V_t` device (no threshold implant); the
  substrate is committed at growth, so it is its own declared run, not a same-wafer disposition sibling.
- **S5 — the `POWER_RECTIFIER` family on the lifetime axis** (`chip.reverse_recovery`,
  [[reverse-recovery-source]]): cited `t_rr ∝ τ` — a short `τ` is a leaky logic **reject** but a **fast**
  rectifier (the killer *is* the feature). It introduces a new `structure` device-family field + a family
  guard: the rectifier **shares** the S3 high-res substrate, so the *family* guard (not the substrate one)
  is what keeps them apart — a mask/structure is committed up front and never salvaged across families.

(**S4** — crucible oxygen's dual-use internal gettering — is a *process trade-off within one device*, not
a market-segmentation slice, so it lives in the scope-edge promotions above, not here.)

## Module map

- **`state.py`** — the immutable `WaferState` / `Die` die-map + append-only `DieStepRecord`
  provenance (the "why did this die?" trail). G2 added the substrate fields `slice_z` /
  `resistivity_ohm_cm`; G3 added per-die **`defects`** / `killed_by_defect` / `radius_frac`, the
  wafer-level **`geometry`**, the `DefectEvent` type, and the **single** `die_area_cm2` /
  cell-geometry helpers; G4 added the wafer-level **`contamination`** vector and the per-die
  **`tau`** / **`j_leak`** (G4b); G5 added per-die **`gate_height_nm`** + **`voided`**; D1 added
  **`bridged`** (the under-etch short); G6 added **`assembled`** + **`bin`** (the back-end scrap flag
  + the speed grade).
- **`recipe.py`** — the per-step knob dataclasses; `DEFAULT_RECIPE` **is** `chip.demo_device`'s
  coherent n-MOSFET recipe (the seam anchor). G2 added **`CzochralskiKnobs`**; G3 added
  **`WaferPrepKnobs`**; G4 added **`PurificationKnobs`** + the derived `contamination` /
  `effective_channel_N_A` properties; G5 added **`EtchDepositionKnobs`** (defaulting to perfectly
  anisotropic + conformal = the seam); G6 added **`PackagingKnobs`** (4 per-step yields, default
  1.0 = seam). The crystal-growth deepenings and promotions all hang off `CzochralskiKnobs` as
  opt-in, default-`None` knobs/properties (CG-1 `pull_rate_mm_min` → `k_eff`; CG-2
  `thermal_gradient_K_per_mm` → `voronkov_ratio` / `grown_in_defect_density`; CG-3
  `melt_gradient_K_per_mm` → `interface_gradient_K_per_mm`; A2 `radial_gradient_boost` →
  `osf_ring_radius`; A1 `interstitial_dislocation_density`; C1 `oxygen_conc_cm3` /
  `thermal_donor_anneal_min` → `thermal_donor_density`), plus D1's `EtchDepositionKnobs.under_etch_frac`
  (a `__post_init__` guards the two-`G` and over-vs-under conflicts) and E1's
  `DiffusionKnobs.drivein_program`.
- **`variation.py`** — the seeded stochastic spread: a center-to-edge trend routed *through the
  physics* + die-to-die output scatter. `NO_VARIATION` collapses to one physics call (the seam).
  Magnitudes are **flagged house defaults**, not cited. G5 added the **conditional** etch-rate channel
  (default 0 → no 4th draw → the banked demos stay byte-identical).
- **`defects.py`** (G3) — the seeded **per-die Poisson** killer-particle placement (off without
  touching the RNG when the stochastic layer is disabled or the line is clean — the seam); A2 added
  the optional **`density_fn`** hook (a per-die radial density; `None` keeps the byte-identical
  uniform path).
- **`spec.py`** — spec windows → the per-die verdict (NILS / CD / I_Dsat / V_t); G3 added the
  killer-defect **functional** gate and the wafer-level **`GeometrySpec`** (TTV/bow) scrap gate; G4b
  added the *optional* **leakage** window; G5 added the **deposition-void** functional gate; D1 added
  the **bridge** (under-etch short) gate; G6 added **`SpeedBins`** / **`SpeedBin`** — the deterministic
  final-test binning partition (a grading policy, *not* physics; default one open `"pass"` bin = the seam).
- **`steps.py`** — the deterministic step wrappers; G3 added `wafer_prep_step`; G4 wired the **device
  step's contamination reads** (Na→`Q_ox`→`V_t`; G4b Fe/Cu→`chip.lifetime`→the leakage field), all
  *inside* `device_step`; G5 added **`etch_deposition_step`** (etch overwrites `cd_nm`, depo sets
  `voided`, D1 sets `bridged`); C1/A1 thread the thermal-donor / dislocation reads into `device_step`
  (both call sites); G6 added **`packaging_step`** (after the front-end `test` step).
- **`pipeline.py`** — `run_line` (the driver, one seeded RNG in fixed die order; purification +
  wafer-prep run first, the etch/depo step between litho and the device, **packaging last**),
  `wafer_yield`, `diagnose` (the failure trail — killer-defect / `Q_ox` / metal-SRH-leakage /
  dislocation-leakage / etch-bias / void / under-etch-bridge / assembly-scrap / bin-out branches),
  `rework_litho`, `rework_polish`, `rework_deposition` (**both rework loops now skip dies that reached
  the back end** — a cracked die stays dead), the A2 radial `density_fn` wiring, `_package_wafer`, and
  `run_batch`.
- **`scoring.py`** (G7) — the economics: `BIN_PRICES` + wafer / scrap / rework costs, `score_wafer →
  ScoreCard` (revenue over shipped dies, profit). The journey's cost side added `process_cost(recipe) →
  ProcessCost` + the `score_wafer(process_cost=…)` add-on (a byte-identical roguelike seam).
- **`game.py`** (G7) — the roguelike session: immutable `GameSession` / `GameConfig`,
  `new_session` / `process_wafer` / `scrap_wafer` / `play`, the append-only `RunRecord`, and
  `ReworkSpec`. One boule = one run, each wafer a turn.
- **`targets.py`** — device targets ("good is application-relative"): the `DeviceTarget` spec/bin
  bundles (`FAST_LOGIC` / `LOW_POWER` / `HV_IO` / `HIGH_RES` / `POWER_RECTIFIER`), `MOSFET_FLAVORS` /
  `POWER_FAMILY`, and `regrade` / `grade_for` / `disposition` (re-score a finished wafer, never re-fab;
  a `structure` family guard + a substrate-class guard). **`MARKET_BINS` lives here** (moved out of
  `game.py` so a `DeviceTarget` can own its bins without a `game ↔ targets` import cycle).
- **`journey.py`** — the staged sand→chip journey (the third play mode): the immutable `JourneyState`
  with the `refine` / `grow` / `cut` / `diffuse` / `oxidize` / `commit` stage methods, `forecast` (the
  consequence band), and `finish` (run + cost-scored). Headless and deterministic; composes `run_line`
  + `score_wafer`, zero new physics except the phase-4 S/D `R_series` device term.
- **`dashboard.py`** + **`session_view.py`** — the headless UI cores: `run_dashboard` /
  `dashboard_summary` (the §9 guided 4-knob slice over `run_line`) and the `GameSession` string
  renderers (`turn_recipe` / `projected_vt` / `inspect_line` / `session_header` / `turn_line` /
  `history_trail` / `session_summary`). Import-pure and tested directly — the swallow-prone UIs render
  them verbatim.
- **`guide.py`** — the educational-mode prose (import-pure, re-exported, tested without textual): the
  `Term`/`GLOSSARY` glossary of every selector + readout and the `dashboard_guide` / `roguelike_guide` /
  `glossary_text` / `MODE_INTRO` renderers the TUI shows verbatim in Educational mode (presentation only).
- **`tui.py`** — the Textual front-end (`ModeSelectScreen` + `FabLineApp` + `RoguelikeScreen`), the
  **only** `textual` importer and **not** re-exported from `__init__` (the fast lane stays headless;
  `[tui]` extra). A thin driver of the cores above; `python -m fab_game.tui` prompts Educational vs
  Hardcore at launch.
- **`plots.py`** — the figure builders (not in the correctness path), incl. `dashboard_figure` (§9)
  and the headless `wafer_map_text` ASCII die map (the TUI's map).
- **`gallery.py`** — the game-layer gallery (`docs/fab-game.html` + `fab-game.local.html`), surfacing
  the `fab-game-*.png` artifacts; reuses chip's gallery primitives, lives in `fab_game/` for the ADR
  0005 boundary.
- **the `demo_*.py` modules** — one banked artifact per milestone: `demo_fab_game` (g1) ·
  `demo_boule` (g2) · `demo_wafer_prep` (g3) · `demo_purification` (g4) · `demo_lifetime` (g4b) ·
  `demo_etch` (g5) · `demo_packaging` (g6) · `demo_game` (g7) · `demo_crystal_growth` (cg1) ·
  `demo_voronkov` (cg2) · `demo_stefan` (cg3) · `demo_thermal_donors` (c1) · `demo_under_etch` (d1) ·
  `demo_osf_ring` (a2) · `demo_dislocation` (a1) · `demo_thermal_budget` (e1) ·
  `demo_internal_gettering` (s4) · `demo_reverse_recovery` (device-targets s5) · `demo_journey` (the
  staged-journey playthrough).
- **`fab_game.ipynb`** — the thin notebook skin (the §9 dashboard section + the interactive skin; not
  in the correctness path).

## Test discipline (ADR 0005 §5) — mechanics invariants, not cited magnitudes

- **`test_seam.py`** — the load-bearing one: nominal + zero variation reproduces
  `chip.demo_device` **bit-for-bit** (the harness does not change the physics).
- **`test_determinism.py`** — same (seed, recipe) → identical wafer; a different seed moves it.
- **`test_propagation.py`** — the device genuinely *reads* the inherited `t_ox`/`CD` (monotone,
  physics-guaranteed), and refuses on an upstream functional fail.
- **`test_bookkeeping.py`** — good + bad = total; provenance append-only; rework accounting closes.
- **`test_import_direction.py`** — the one-way boundary holds.
- **`test_demo_fab_game.py`** — the banked artifact's thesis (the dramatic win + rework recovery).
- **`test_boule.py`** (G2) — the boule wired: seed-slice seam exact, the Scheil `N_A`→`V_t`
  propagation, determinism / no new RNG (Scheil is a closed form), and batch bookkeeping.
- **`test_demo_boule.py`** (G2) — the boule artifact's thesis (the V_t walk scraps the tail).
- **`test_defects.py`** (G3) — placement determinism + the load-bearing **convergence** leg (the
  empirical kill rate → the cited `exp(−D₀·A)`, against the single die area), and the
  killer-defect → functional-fail wiring.
- **`test_geometry.py`** (G3) — the TTV/bow **scrap** gate and the `rework_polish` accounting
  (recovers a TTV scrap, eats thickness; cannot fix bow or remove a killer particle).
- **`test_contamination.py`** (G4a) — purification scrubs the wafer; a dirty feed's Na walks `V_t`
  out of spec (named), more passes recover, a clean grade is the seam.
- **`test_leakage.py`** (G4b) — the metals → SRH lifetime → junction-leakage wiring: a metal feed is
  scrapped on **leakage** (not `V_t`) and named; more passes recover; clean is the baseline seam.
- **`test_demo_purification.py`** / **`test_demo_lifetime.py`** (G4a/G4b) — the banked artifacts'
  theses (the Na→`V_t` kill + rework; the isolated metal → leaky-diode kill + rework).
- **`test_etch.py`** (G5) — the etch/depo wiring: the etched CD overwrites the device's currency
  (over-etch → CD ↓ → `I_Dsat` ↑), a poor coverage voids functionally, the unresolved/runaway cases
  degrade gracefully, and the etch-rate channel is deterministic *and* draws no RNG when off.
- **`test_demo_etch.py`** (G5) — the banked artifact's thesis (the over-etch CD walk out of window, the
  PVD-voids/CVD-fills contrast, the reworkable-void / irreversible-etch rework).
- **`test_packaging.py`** / **`test_demo_packaging.py`** (G6) — the assembly funnel + the Bernoulli →
  `Πyᵢ` convergence, the binning partition, and the **rework-guard** (a back-end scrap is never
  resurrected by a re-exposure).
- **`test_scoring.py`** / **`test_game.py`** / **`test_demo_game.py`** (G7) — the economics (bookkeeping +
  monotonicity) and the session (determinism, the budget closes, sandbox-vs-roguelike, the drift arc;
  the demo's naive < scrap < adapt thesis).
- **`test_crystal_growth.py`** / **`test_voronkov.py`** / **`test_stefan.py`** (+ their `test_demo_*`,
  CG-1/2/3) — each deepening wired through the boule + each default-off seam byte-for-byte.
- **`test_thermal_donors.py`** (C1) · `test_etch.py` (D1's wiring) · **`test_osf_ring.py`** (A2) ·
  **`test_dislocation.py`** (A1) (+ their `test_demo_*`, incl. `test_demo_under_etch.py` /
  `test_demo_thermal_budget.py`) — the scope-edge promotions: each consequence wired, each seam
  reproduces the prior demos byte-for-byte.
- **`test_targets.py`** / **`test_targets_hv.py`** / **`test_targets_highres.py`** /
  **`test_targets_power.py`** (device targets S1/S2/S3/S5) — the grading mechanics, not magnitudes: the
  windows genuinely **cross**, a declaration **moves** the recipe optimum, `regrade` never re-fabs, and the
  `structure` family guard + substrate-class guard hold (the power rectifier shares the high-res substrate
  but stays a different family).
- **`test_journey.py`** — the staged journey: immutable state + append-only log, `(seed, grade, actions)`
  determinism, the `cut`-reads-`grow` propagation, the phase-4 `R_series` device term, and the cost-scored
  `finish` interior optimum (`under < opt < over`).
- **`test_dashboard.py`** / **`test_session_view.py`** / **`test_tui.py`** — the headless UI cores (the
  real safety net) + the `importorskip` Textual pilots (**fidelity, not movement**: a driven session ==
  headless `play(...)`; no notebook-style xdist flake).
- **`test_gallery.py`** — the gallery manifest is complete (every `fab-game-*.png` is surfaced) + the
  golden HTML.

## Run it

```sh
python -m fab_game.demo_fab_game          # G1 defocus → dead-edge ring, banks docs/figures/fab-game-g1.png
python -m fab_game.demo_boule             # G2 boule → V_t spread, banks fab-game-g2.png
python -m fab_game.demo_wafer_prep        # G3 particle map + yield law + TTV scrap, banks fab-game-g3.png
python -m fab_game.demo_purification      # G4a Na → V_t scrap + rework, banks fab-game-g4.png
python -m fab_game.demo_lifetime          # G4b metals → leaky diode + rework, banks fab-game-g4b.png
python -m fab_game.demo_etch              # G5 over-etch CD walk + void map + rework, banks fab-game-g5.png
python -m fab_game.demo_packaging         # G6 assembly funnel + bin histogram + outcome map, banks fab-game-g6.png
python -m fab_game.demo_game              # G7 three strategies down one boule, banks fab-game-g7.png
python -m fab_game.demo_crystal_growth    # CG-1 BPS k_eff flattens the drift, banks fab-game-cg1.png
python -m fab_game.demo_voronkov          # CG-2 V/G COP brake, banks fab-game-cg2.png
python -m fab_game.demo_stefan            # CG-3 ξ saturation, banks fab-game-cg3.png
python -m fab_game.demo_thermal_donors    # C1 oxygen → donors → V_t down, banks fab-game-c1.png
python -m fab_game.demo_under_etch        # D1 under-etch short + the etch process window, banks fab-game-d1.png
python -m fab_game.demo_osf_ring          # A2 OSF ring: vacancy core + clean rim, banks fab-game-a2.png
python -m fab_game.demo_dislocation       # A1 two-sided window: slow pull → leakage, banks fab-game-a1.png
python -m fab_game.demo_thermal_budget    # E1 spike/RTA budget collapse → shallow x_j, banks fab-game-e1.png
python -m fab_game.demo_internal_gettering # S4 oxygen dual-use: Goldilocks [O_i], banks fab-game-s4.png
python -m fab_game.demo_reverse_recovery  # device-targets S5 t_rr ∝ τ (lifetime killer is the feature), banks fab-game-s5.png
python -m fab_game.demo_journey           # the staged sand→chip journey playthrough (decide → observe → commit), banks fab-game-journey.png

python -m fab_game.tui                    # the Textual TUI (dashboard + roguelike screen; needs the [tui] extra)
python -m fab_game.gallery                # regenerate docs/fab-game.html (+ fab-game.local.html)
pytest fab_game/ -q                       # the mechanics suite (rides the fast lane)
jupyter lab fab_game/fab_game.ipynb       # the interactive skin + the §9 dashboard (needs the [viz,notebook] extras)
```
