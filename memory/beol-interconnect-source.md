---
name: beol-interconnect-source
description: "F4 BEOL interconnect RC (source + build state — COMPLETE, all 4 slices): cited c_pul≈2 pF/cm AND its geometry-invariance (coax↔80nm line), Al/Cu/Ru ρ₀+λ, the ρ₀λ scaling FOM (Ru≈Cu, NOT better), the 2-3nm barrier floor, IBM 1997 dual-damascene, the mid-90s gate≈wire crossover; S2's exact damping law 1−wire_share + the re-binning trap; S3's node-unit rule (Cu bought 0.64 of a node), the challenger-first sign trap, the exhausted bulk-ρ axis; S4's TWO IMPOSSIBILITY RESULTS (size effect alone never flips the sign — asymptote 1.179>1; barrier alone flips only below 5.2nm, atop the 4.0nm no-conductor floor), the crossing as a BAND set by t_b, the FOM-ranks-but-doesn't-locate trap, and the live game-knob Ru gate"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f063ca99-8fcb-4960-8438-adf9d588be09
---

**Cited source for F4 BEOL interconnect / RC delay** (`chip/interconnect.py` — PLANNED, see
`docs/plans/beol-interconnect-f4.md`). Web-verified 2026-07-17. The load-bearing legs are the `c_pul`
invariance (tight) and the **`ρ₀λ` figure of merit** (which carries the Cu→Ru **sign trap**).

* **Wire capacitance per unit length `c_pul ≈ 2 pF/cm` (≡ 200 aF/µm) — CITED, and TIGHT because of its
  INVARIANCE, not its value.** "The capacitances per unit length of all electrical transmission or
  interconnect lines are very similar, **within factors of order unity**": a ~1 cm-diameter 50 Ω coax is
  **~1.5 pF/cm**; an on-chip line at **80 nm** center-to-center pitch is **~2 pF/cm**. **Seven orders of
  magnitude of geometry, the same `c_pul`.** Mechanism (why it is physics, not a lump): `C` per length
  depends on **ratios** of dimensions, not absolute size; on-chip, line-to-line **coupling** cap rises as
  area cap falls, holding the total. **Use TOTAL per-length C (area + fringing + coupling) — an area-only
  parallel-plate C omits coupling, understates C, and MISPLACES the crossover.**
  ⇒ **The crossover is driven by `R`, not `C`:** `R ∝ 1/(W·H)` rises as the cross-section shrinks while
  `C ∝ L` sits still.

* **The scaling scenario is load-bearing — CITED both ways.** *"If the interconnect length and
  interconnect pitch scale identically, the wire delay will remain constant with technology scaling."*
  So **local** wires (L scales with pitch) ⇒ `τ_wire` ≈ flat; **global** wires (L ~ chip-sized, fixed,
  cross-section shrinking) ⇒ `τ_wire` **explodes**. **The crossover is a global-wire statement** and the
  scenario must be stated on the figure or the crossover is an artifact. Interconnect delay ∝ 1/pitch².

* **Bulk resistivity `ρ₀` (µΩ·cm) + electron mean free path `λ` (nm) — CITED:** **Cu 1.68 / ~38.7–39** ·
  **Ru 7.1 / 10.8** (Ru's λ is ~**3.6×** shorter than Cu's — *not* ~6×). **Al ~2.65–2.7 / ~22 — FLAGGED**
  (Al ρ₀ is handbook, not pinned by the search; Al λ is single-source).

* **The `ρ₀λ` figure of merit — CITED, and it carries the sign trap.** Below `λ`, surface/grain-boundary
  scattering dominates: `ρ_eff ≈ ρ₀·(1 + C·λ/d)` → narrow limit `ρ_eff → C·ρ₀λ/d`, so the material enters
  **only** through `ρ₀λ` — "widely adopted to screen promising interconnect metals", "lower FOM = better
  upon scaling". **Values: Cu ≈ 65, Ru ≈ 77 µΩ·cm·nm ⇒ Ru is ~17% WORSE**, matching the literature's
  "Mo, Co and Ru **approximately match** the Cu resistivity" in the narrow-wire limit. (Al ≈ 58 — **do NOT
  headline**; rests on the two flagged Al numbers.)
  **THE TRAP:** Ru's bulk `ρ₀` is **~4× HIGHER** than Cu's. "Ru = lower resistivity" ships the sign
  backwards; so does "Ru wins because of its shorter mean free path" — the short λ only buys **parity**.
  Structurally the **F3 κ↔band-gap echo**: buying low `ρ₀` costs a long `λ`, so *the metric that ranks
  metals at 3 nm is not the metric that ranked them at 250 nm*.

* **The barrier — CITED, and it is the BEOL's interfacial layer (the F3-IL echo).** Cu needs a Ta/TaN
  diffusion barrier with a **~2–3 nm minimum thickness that does not scale**; at **sub-10 nm** trench
  widths barriers "consume a disproportionate fraction of the available conductor cross-section"; TaN is
  itself highly resistive. Ru needs **none** → **barrierless Ru line resistance is lowest at line CD
  <~20 nm**. So `W_eff = W − 2·t_barrier`: a **fixed** thickness eating a **shrinking** budget, with a hard
  geometric floor at `W = 2·t_barrier` (`W_eff → 0`, the wire is all barrier). **The win is GEOMETRIC, not
  a materials ride** ([[historical-modes-a4]]'s lesson). (Also cited, not modelled: RuCo liners cut barrier
  thickness ~33% → 20 Å, ~25% lower R.)

* **The honest Ru claim = TWO steps, both load-bearing:** `ρ₀λ` parity makes Ru **viable** (necessary, not
  sufficient); barrierless-ness **tips that already-near-parity metal over** below ~20 nm CD (sufficient
  *given* parity). Bulk ρ says "never", the size effect says "only a tie", and only the barrier geometry
  on top of the tie says "wins" — **neither currency alone gets the sign right** (exactly [[high-k-gate-f3]]'s
  IL: the better barrier that is still a pure loss).

* **Al→Cu, the 1997 era — CITED.** IBM announced manufacturable copper-CMOS **September 1997**; process
  **CMOS 7S**, **0.22 µm**, the industry's first **dual-damascene** flow; volume production 1998
  (Burlington VT, PowerPC). Reported: Cu conducts with **~40% less resistance** than Al → **~15%**
  microprocessor speed boost; PowerPC went **300 → 400 MHz** (~33%). **This half IS a genuine bulk-`ρ₀`
  win** (wires ≫ λ ⇒ `ρ_eff → ρ₀`) — unlike Cu→Ru.

* **The crossover history — CITED (the era anchor S3's ladder must land on).** Gate delay dominated in the
  **mid-1980s**; gate and interconnect delay were **roughly equal by the mid-1990s**; Cu + low-κ were
  introduced at the **250 nm** node to blunt rising interconnect delay; **below 130 nm** interconnect delay
  worsens further despite low-κ. Interconnect delay relative to gate delay ≈ **doubles every generation**.

* **FLAGGED house lumps** (name them like B6's `SPIKE_CONCENTRATION`): wire length **`L`** (nothing in the
  sim carries one — checked: B6's `t_Al` is a contact-metallization *thickness*, not a line length), the
  Elmore **`0.38·RC`** distributed-line factor, the Fuchs–Sondheimer / Mayadas–Shatzkes coefficient `C`,
  `C_load`, `V_dd`, and the node→(W,H) ladder. Since `L` is a lump, **the headline must be prefactor-free:
  the `τ_wire/τ_gate` ratio and the crossover, never absolute picoseconds** (the [[high-k-gate-f3]]
  `decades_saved` discipline — a ratio cancels the house constant).

* **BOUND THE HEADLINE — the dropped driver↔wire cross terms (caught at S1 review).** Full single-stage
  Elmore = `R_d·(C_w+C_L) + R_w·(C_w/2+C_L)`. The module keeps `R_d·C_L` (=`τ_gate`, CV/I form) and
  `R_w·C_w` (=`τ_wire`) and **drops `R_driver·C_wire` and `R_wire·C_load`**. Since `R_d ~ V/I`,
  **`R_d·C_w` IS weakly `I_Dsat`-dependent** — the transistor *does* help charge the wire cap. ⇒ **The
  licensed claim is "the wire's INTRINSIC RC is a common-mode floor", NOT "the transistor can't touch the
  wire term".** The discriminator survives (the intrinsic `R_w·C_w` floor is real and `I_Dsat`-free), but
  **S2 must use the bounded phrasing.**

* **S4 IS NOT A Ru-ONLY SLICE — conclusion STANDS, but its S1 premise was WITHDRAWN at S2.** ~~The guard
  fires on copper's own crossover (~0.167 µm vs the ~0.19 µm the bulk model wants).~~ That number rested
  on a **test-local 23 fF load** (a *1 µm* channel), **not on anything the sim runs**. S2 wired the real
  chain — `C_load` = the fan-out-1 `C_ox·W·L` off the game's own device (`t_ox`≈14 nm, W=10 µm, L=the
  printed ~167 nm CD) = **4.1 fF** — and Cu's crossover moved to **~0.395 µm, comfortably INSIDE** the
  bulk regime. **Where the crossover lands is a statement about the LOAD, not a property of the slice**
  (`W_x ∝ 1/√C_load` — *that* direction is the invariant; both loads are now pinned in the S1 test).
  **S4 stays motivated for Cu** on the leg that never needed the operating point: the size-effect
  correction **grows as W scales below ~0.19 µm**, and the size effect became a *copper* problem at
  sub-200 nm (cited history). Only "this slice already sits outside its own model's competence" died —
  it does not; the Al→Cu era (250 nm) is **inside**. *Lesson: a claim about "the house operating point"
  computed from a test fixture is not about the house at all.*

* **The IBM ~40% check is a CONSISTENCY check, not a non-circular one** (corrected at S1 review). At fixed
  geometry `R_Al/R_Cu ≡ ρ_Al/ρ_Cu`, so it validates the *inputs*, not a structural form.
  [[high-k-gate-f3]]'s (φ_B,m*)→2 Å-slope check ran through the **exponential** (cited inputs predicting a
  *different functional form's* slope) and is genuinely stronger. **Do not quote this as F3-grade.**

* **NAMED, NOT MODELLED (honest ceilings).** **Repeater/buffer insertion** — real chips break long wires
  with repeaters, making delay ∝ `L` **not** `L²`; without naming it the model silently claims wire delay
  is unfixable and overstates the wall (the F3 trap-limited-floor analogue). **Low-κ ILD** — the C-side
  mirror of high-κ (cited: low-κ lowers `c_pul` hence delay; arrived *with* Cu at 250 nm). **Electro-
  migration** — Cu's *other* win over Al, a reliability mechanism, **wrong currency** for a delay
  observable. Crosstalk, inductance, multi-level RC stack, via resistance.

**S2 BUILT (2026-07-17) — the consumer, and the law it turned out to rest on.**
* **The damping law is the payload, and it is sharper than the crossover: `∂ln f/∂ln I_Dsat = 1 −
  wire_share`, EXACT at every `I_Dsat`** (from `f = I/(A+τ_wire·I)`), not a linearization. `τ_wire` is
  **common-mode** ⇒ it adds a *level* and **no spread**, so the across-wafer `I_Dsat` spread maps to a
  speed spread damped by exactly that factor **with the transistor histogram bit-for-bit unchanged**.
  → `Delay.drive_sensitivity`; the test checks it against a **numerical** log-derivative of the model's
  own `f`, so it is a check and not a restatement.
* **THE TRAP THAT LICENSES THE SLICE: re-binning on `τ_total` proves NOTHING by itself.** `τ_total` is
  strictly monotone in `I_Dsat`, so binning with edges mapped through *that same function* is a
  **byte-identical partition**. The edges must encode the **market's promise** ("a 2.6%-faster part"),
  anchored on the nominal part: **`τ_edge = τ_nom·(I_nom/I_edge)`** (`DelayBins.from_speed_bins`) — the
  *old premise's own arithmetic*. Adds **no new house number** (fractions = G6's existing bins) and
  **cancels the flagged `L`** (nominal ≡ typical under both policies ⇒ the level shift is gone, only the
  compression survives). Control: at `τ_wire = 0` the partition is **identical, grade for grade**.
* **THE COMPRESSION IS SYMMETRIC (advisor caught the framing).** The wire pulls the slow tail **up** as
  it pulls the fast tail down: premium collapses **and the bin-out tail shrinks** (loose: reject 2→0;
  tight: premium 23→**0**). ⇒ licensed claim = **"sorting by drive current stops producing a speed
  spread; the premium GRADE collapses"**, *never* "wires cost yield". **A grading loss, not a yield
  loss** — the die count is untouched. (`from_speed_bins` preserves labels ⇒ the existing price curve
  scores it unchanged.)
* **Shape:** `DeviceKnobs.interconnect` (`"Al"`|`"Cu"`, None=seam) → `Die.delay`/`delay_ps` (**not**
  `tau_ps` — `Die.tau` is already the **lifetime**) → `spec.DelayBins`/`DelayBin`, a **sibling** of
  `SpeedBins` (not a mode flag, not a pseudo-`I_Dsat` — that would overload a documented field, F3's
  rejected move). Keeping `SpeedBin`'s mA bands leaves the false premise **legible in the tree** as the
  era artifact it is. Lives in `device_step` (where `I_Dsat`+`C_ox` are; no BEOL step exists).
  **Metal-only knob** — geometry stays the module default (anti-front-load; S3 sweeps the module).
* **The bound SWAP is the real ordering trap:** `lo_mA` (the *fast* edge) → **`hi_ps`**. `DelayBin` is
  `(lo, hi]` — the deliberate mirror of `SpeedBin`'s `[lo, hi)`. But **honest scope: the inclusive/
  exclusive convention is NOT empirically distinguishable** — an exact-edge part resolves arbitrarily
  because the mapped edge and the part's own delay are ~1 ulp apart in float. Kept as the principled
  reading only; the *swap* is what a test can (and does) catch.
* **Three-rung seam:** knob off (nothing emitted) → knob on + `delay_bins=None` (**delay emitted, read by
  no one** — still byte-for-byte; the `bv_V`/`t_rr`/`j_gate` additive discipline) → knob on + delay
  binning (the inversion). **It is the PAIR that overturns the premise, never the knob alone.**

**S3 BUILT (2026-07-17) — the B9 demo (`demo_beol_history.py`, the 9th rung). Two claims it CORRECTED:**
* **Cu bought 0.64 of a node, NOT "roughly one"** — `W_x ∝ √ρ₀` ⇒ 1.58× in ρ = 0.796× in W_x, and a node
  step is **0.70×** ⇒ `ln(0.796)/ln(0.7)` = 0.64. `crossover_width_ratio`'s docstring said "roughly one
  node" (~50% overstatement); **fixed + pinned**. B8's `floor_decades` rule in the crossover's currency.
  New helper `nodes_bought()` makes the node the unit.
* **`crossover_width_ratio` argument order is a LIVE sign trap (the S2 bound-swap's cousin): CHALLENGER
  FIRST.** The first run shipped **Ag as −0.08 of a node** (worse than Cu — false) from an
  incumbent-first call + reciprocal. For Al→Cu the reciprocal is the *same* number; for Cu→Ag it is *its
  reciprocal* ⇒ renders as a plausible figure, **only the sign gives it away**. Pinned by a test.
* **New headline, prefactor-free, and it earns S4 structurally: ON THE BULK-ρ AXIS THE LADDER IS OUT OF
  METALS.** One more node needs `ρ ≤ 0.82`; **Ag (the best elemental conductor) is 1.59** → +0.08 of a
  node. **SCOPE IT TO THE AXIS** (advisor): "no metal beats Cu" is *false* — S4 has Ru winning with 4×
  Cu's bulk ρ. The **axis** is exhausted ⇒ the axis must change. On the scaling axis **Ag's ρ₀λ ≈ 84 is
  worse than Cu's 65 AND Ru's 77** — the best bulk conductor is the worst scaling metal. [Ag ρ₀/λ =
  handbook, FLAGGED.]
* **The arc's deep point (replaced a fragile framing the advisor killed): `W_x ∝ √I_Dsat` EXACTLY as
  `W_x ∝ √ρ₀`** ⇒ a 2× better transistor pulls the wall in to a 1.41× *wider* wire (an **earlier** node)
  by the same √2 a 2× better metal pushes it out. **The transistor's own progress creates the wire wall.**
  (The killed gloss: "freezing the gate is conservative" — the bias rides on *which* τ_gate you freeze at;
  ≈neutral at the crossover node, and it **flips to overstating** if you freeze newer.)
* **Shape:** wire-ONLY ladder (open Q4 decided), transistor frozen as a **real `device.py`** read (0.5 µm
  era, 10 nm oxide, `N_A` → `V_t`=0.58 V — chosen on device grounds, NOT to place the crossover). No
  `beol_history.py` wrapper (Al+Cu already in `METALS`; the ladder is a recipe, not physics — B7/B8).
  Rungs = the **real** node ladder (node name ≈ metal half-pitch pre-2000). Featured 250 nm rung **is
  `WireGeometry()`'s default byte-for-byte** = the line S2's knob runs (share differs: same wire,
  different transistor).
* **The cap is BINDING, not cosmetic:** ladder floor 0.20 µm because Cu's `bulk_regime_ok` refuses below
  `5λ` ≈ **0.194 µm** — and **the next real node (0.18) is already inside the refusal**, drawn as a shaded
  zone with the rung in it. Cleanest hand-off to S4; matches cited history (size effect = a *copper*
  problem at sub-200 nm).
* **The landing is a CONSISTENCY check, never a prediction** — `W_x ∝ L` **and the device recipe is a
  2nd lump-carrier** (`W_x(Al)` moved 0.49→0.38 µm across a plausible `N_A` range ≈ ¾ of a node). An
  untuned 1 mm line + a period device landing `W_x(Al)` ≈ 0.45 µm (the mid-90s, where cited history puts
  gate ≈ wire) has exactly the **IBM ~40%** status. Lead with the shape + the 1.26 shift.

**S4 BUILT (2026-08-10) — the narrow-wire era. F4 is COMPLETE (4 slices); the card GRADUATED.**
* **The plan's "two steps, both load-bearing" became TWO IMPOSSIBILITY RESULTS, cited constants only**
  (advisor — much stronger than the ladder it replaces as the headline).
  **(a) The size effect ALONE can never flip Cu→Ru at ANY width.** The no-barrier ratio falls
  *monotonically* from `ρ₀(Ru)/ρ₀(Cu)` = **4.23** to the asymptote `ρ₀λ(Ru)/ρ₀λ(Cu)` = **1.179**, and
  1.179 > 1. So "Ru wins because its λ is short" is false **in the limit**, not approximately. `C` cancels
  in the asymptote ⇒ no flagged input.
  **(b) The barrier ALONE on bulk ρ can't either**, except at `W < 2t_b/(1 − ρ₀Cu/ρ₀Ru)` = **5.24 nm** —
  a **1.2 nm** window sitting on top of the **4.0 nm** conductor floor. No fab has been there.
* **The geometric floor `W = 2·t_b` is HEADLINE** (4–6 nm over the cited range): a Cu line narrower than
  its two liners is **all barrier, no conductor**, for any ρ/L/C/AR. F3's "`EOT > t_IL` for ANY κ" in the
  wire's currency, and *inside* the roadmap. `conductor_width_um` raises rather than extrapolating.
* **The three-rung ladder is now the illustration, not the claim** (at 12 nm, C=1, t_b=2):
  **4.23 → 1.90 → 0.92**, with **barrier-only = 2.82** as the control that kills the one-mechanism version.
* **The crossing is a BAND and the band IS the finding: 12.9 → 17.1 nm over the CITED t_b = 2–3 nm** (≈ a
  node); ~9.7–21.1 nm over flagged `C` ∈ [0.375, 2]. ⇒ *where* Ru wins is set by the thickness of the layer
  that stopped scaling. Lit. <~20 nm; the band sits a node INSIDE it and both conservative simplifications
  push that way. **Status = the IBM ~40% consistency check's, NOT a prediction.**
* **THE FOM RANKS METALS BUT DOES NOT LOCATE THE CROSSING.** The deep-limit closed form (`R ∝ ρ₀λ/W_eff²`
  for both) gives **50.5 nm** vs the full form's **12.9** — **4× wrong**, because at the crossing Ru is
  *not in its own deep limit* (`Cλ/W` ≈ 0.84, not ≫1): the short λ that makes Ru viable is what keeps it
  near-bulk. Pinned by a test so a later slice can't "simplify" to it.
* **THE LIVE BUG THE ADVISOR CAUGHT (blocking): adding Ru to `METALS` reached the GAME KNOB.**
  `fab_game/steps.py` resolved `knobs.interconnect` straight out of `METALS`. What Ru would have returned
  is **not even wrong** — at 250 nm Ru really *is* ~4× worse — so a **true** number reads as a **false
  verdict on the metal**. Fix: `BULK_ERA_METALS = ("Al","Cu")`, refused by name *with the reason*. The S4
  gate **MIGRATED** (from "not in the registry" to "not offered where it would be misread"), never lifted.
* **Al is REFUSED on the narrow axis, and the refusal is LOAD-BEARING.** Al's `ρ₀λ` ≈ 58 screens *better*
  than Cu's 65 — unsupportable here, since Al's real disqualifier (**electromigration**) is a reliability
  currency F4 doesn't carry. `barrier_nm=None` ⇒ narrow reads raise. **Advisor: do NOT re-source Al** — it
  buys a citation fight, not a claim. S3's "the cap is binding, not cosmetic", applied to a *metal*.
* **FOUR simplifications, each with its DIRECTION named** (the conclusion is a sign): `C` = 1.0 round and
  **unfitted** ⇒ **errs AGAINST Ru** (Cu at 6.3 µΩ·cm in an 18 nm line vs a **measured ~9** — web-verified:
  an 18 nm line ≈ 9 µΩ·cm, an 80 nm line ≈ near-bulk); width-only `W_eff` ⇒ **also against Ru**; the
  **scattering dimension `d` = the conductor WIDTH, not a cross-section** ⇒ **also against Ru**; barrier as
  perfectly dead area ⇒ **for Ru**. A single `C` can't span both ends — the grain-boundary term is NAMED,
  not built (advisor: splitting `C` = a second lump, no new claim).
* **THE SCATTERING-DIMENSION CATCH, and the one place the advisor was WRONG on a direction.** Post-build
  the advisor flagged the missing 4th simplification (right — scattering sees both surface pairs, not just
  `W`) but argued it with **`d = 2WH/(W+H)`**, which flips the 12 nm rung to **1.12 (Ru LOSING)**. Measured
  out, the opposite holds: the additive-rate derivation gives **`1/d = 1/W_eff + 1/H`** (the standard
  rectangular form), **half** the advisor's `d` ⇒ rung **0.917 → 0.889 (Ru wins by MORE)**, crossing
  12.9 → 13.4 nm. **The tiebreak is EVIDENCE, not taste:** at 18 nm the conventions give Cu ρ_eff = 6.3
  (ours) / **8.1** (standard) / 4.9 (advisor's) vs a **measured ~9** — the advisor's is furthest off.
  **Kept width-only anyway, for a reason that is not preference:** bringing `H` in would put the **flagged
  AR into the headline ratio**, and `resistance_ratio` is prefactor-free *because* `H`/`AR` cancel.
  **Rule: a prefactor-free claim that errs against its own conclusion beats a better-calibrated one that
  doesn't.** Pinned by a test that hand-rolls the standard form. *Lesson: when a reviewer's counter-example
  would cost a headline, re-derive the convention AND check it against a measured datum before conceding.*
* **The guard was NOT retired.** S1 and S3 both wrote "slice 4 removes the need for `bulk_regime_ok`" —
  **wrong**: `delay`/`crossover_width_um` are still bulk-only. S4 added a **second path beside** the first.
  Corrected in both places + pinned.
* **The node convention EXPIRED.** S3's "W = the node number" is a *pre-2000* fact; a modern "3 nm node"
  has no 3 nm linewidth, so panel 4's axis is a **drawn linewidth, never a node**. Pinned by a **source-text**
  test — the one thing golden-HTML currency tests structurally cannot catch.
* **Shape:** `interconnect.py` §6 (`effective_resistivity`, `conductor_width_um`/`conductor_floor_width_um`,
  `narrow_line_resistance`, `resistance_ratio` **challenger-first** with `size_effect`/`barrier` switches,
  `size_effect_ratio_limit`, `barrier_only_flip_width_um`, `equal_resistance_width_um`/`_nm`).
  **Naming:** `crossover_*` = gate↔wire; **`equal_resistance_*` = metal↔metal** — a deliberate split
  (advisor), the `Die.tau` collision class. `NARROW_WIRE_METALS` is **derived** from `METALS`. A **4th demo
  panel on its OWN sub-60 nm axis** — *not* a continuation of the 0.20 µm ladder, so the era seam stays
  visible. **No new game knob** (the demo is the consumer — F3's slice-4 shape).
* **F4's build RELEASED F8's gate** — CMP's "nothing reads a layer thickness" (backlog D2) fired: `R ∝
  1/(W·H)` is now electrical. F8 moved `hold` → `ok` on the roadmap page. Remaining gate is a *shape*
  problem: F4's geometry is one house line, so per-die dishing needs a per-die cross-section.

**Seam:** the game's `SpeedBins.assign(i_dsat_mA)` (`fab_game/spec.py`) **already** bins on `I_Dsat` as a
speed proxy — its docstring says "clock speed ∝ drive current" — which is the *era-appropriate and false*
pre-1997 premise F4 overturns by re-binning on `τ_total = τ_gate(I_Dsat) + τ_wire`, where
**`∂τ_wire/∂I_Dsat = 0`**. Knob off ⇒ binning reads `i_dsat_mA` byte-for-byte as today (the default
`SpeedBins` is already a single open `"pass"` bin). `τ_wire` is a **common-mode floor** on every die, so
past the crossover the across-wafer `I_Dsat` spread stops mapping to a speed spread — **tightening CD
control stops buying speed grades** (re-scores G6's tight/loose histograms; never re-fabs, the
[[device-targets-plan]] discipline). Cross-refs: [[high-k-gate-f3]] (the IL echo + the ratio discipline),
[[silicide-contact-source]] (F2 — the other two-term R model; `CONTACT_LENGTH_UM` is `L`'s precedent),
[[historical-modes-b6]] (the Al metallization sibling), [[fab-game-g6]] (the binning consumer),
[[gradual-failure-preferred]], [[roadmap-page]] (F4's card comes off when it ships).
