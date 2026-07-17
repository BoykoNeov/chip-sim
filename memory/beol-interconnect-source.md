---
name: beol-interconnect-source
description: "F4 BEOL interconnect RC (source + build state, S1-S3 BUILT, S4 open): cited c_pul≈2 pF/cm AND its geometry-invariance (coax↔80nm line), Al/Cu/Ru ρ₀+λ, the ρ₀λ scaling FOM (Ru≈Cu, NOT better), the 2-3nm barrier floor, IBM 1997 dual-damascene, the mid-90s gate≈wire crossover; S2's exact damping law 1−wire_share + the re-binning trap; S3's node-unit rule (Cu bought 0.64 of a node), the challenger-first sign trap, and the exhausted bulk-ρ axis"
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
