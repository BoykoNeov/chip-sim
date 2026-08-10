# Plan — F4 BEOL interconnect (the delay the transistor doesn't set)

> **STATUS: COMPLETE — ALL FOUR SLICES BUILT (S1–S3 2026-07-17, S4 2026-08-10).** `chip/interconnect.py`
> + `chip/tests/test_interconnect.py` (40 tests); S2 wired the game consumer: `DeviceKnobs.interconnect`,
> `Die.delay`, `spec.DelayBins`, `fab_game/tests/test_interconnect_binning.py` (14 tests); S3 =
> `chip/demo_beol_history.py` + tests, the 9th timeline rung (B9); **S4 = the narrow-wire era —
> `interconnect.py` §6, Ru in the registry, a 4th demo panel, 15 demo tests.**
> `device.py` untouched throughout. Cited constants → `memory/beol-interconnect-source.md`.
> **The roadmap card graduated 2026-08-10** (the second to do so, on F3's reading of "shipped" = the
> *last* slice), and **F4's build RELEASED F8's gate** — CMP now has the layer-thickness reader it was
> fenced behind, so its card moved from `hold` to `ok` on the same page.
>
> **S4's findings — what the plan asserted, and what the build turned into closed form:**
> 1. **The plan's "two steps, both load-bearing" became two IMPOSSIBILITY RESULTS, on cited constants
>    only** (advisor). *(a)* The size effect alone **can never** flip Cu→Ru at any width: the no-barrier
>    ratio falls monotonically from `ρ₀(Ru)/ρ₀(Cu)` = 4.23 to the asymptote `ρ₀λ(Ru)/ρ₀λ(Cu)` = **1.179**,
>    and 1.179 > 1. *(b)* The barrier alone on bulk ρ flips it only below `2t_b/(1 − ρ₀Cu/ρ₀Ru)` = **5.2 nm**
>    — a **1.2 nm** window sitting on top of the **4.0 nm** width where copper has no conductor at all.
>    Both are stronger than the "still losing at 12 nm" the ladder shows, and neither needs `C` or a
>    geometry. The ladder (**4.23 → 1.90 → 0.92**, barrier-only control **2.82**) is now the *illustration*;
>    these are the claim.
> 2. **The geometric floor `W = 2·t_b` is headline, not footnote** — 4–6 nm over the cited barrier range,
>    for any ρ, L, C or aspect ratio. F3's "`EOT > t_IL` for ANY κ" in the wire's currency, and it sits
>    *inside* the published roadmap. `conductor_width_um` raises below it rather than extrapolating.
> 3. **The crossing is a BAND, and the band is the finding.** 12.9 → 17.1 nm over the *cited* `t_b` = 2–3 nm
>    (≈ a node), ~9.7–21.1 nm over the flagged `C` ∈ [0.375, 2]. ⇒ **where ruthenium wins is set by the
>    thickness of the layer that stopped scaling.** Literature says <~20 nm; the band sits a node inside it
>    and **both** Ru-conservative simplifications push that way — so the direction is understood, not tuned.
>    Status: the IBM ~40% consistency check's.
> 4. **The `ρ₀λ` FOM ranks metals but does NOT locate the crossing.** The tempting deep-limit closed form
>    (`R ∝ ρ₀λ/W_eff²` for both) says **50.5 nm** against the full form's **12.9** — wrong by 4×, because at
>    the crossing Ru is *not in its own deep limit* (`Cλ/W` ≈ 0.84). The short mean free path that makes Ru
>    viable is exactly what keeps it near-bulk. Pinned by a test so a later slice cannot "simplify" to it.
> 5. **The S4 gate MIGRATED rather than lifting — and it was a live bug.** `fab_game/steps.py` resolved
>    the knob straight out of `METALS`, so adding Ru silently made it a game option. What it would return
>    is not even wrong: at 250 nm Ru really *is* ~4× worse, so the player reads a **true** number as a
>    false verdict on the metal. New `BULK_ERA_METALS = ("Al","Cu")`, refused by name with the reason.
> 6. **Aluminium is REFUSED on the narrow axis, and the refusal is load-bearing.** Al's `ρ₀λ` ≈ 58 screens
>    *better* than copper's 65 — and F4 cannot support that comparison, because Al's real disqualifier is
>    electromigration, a reliability currency the module does not carry. `barrier_nm=None` ⇒ the narrow
>    reads raise. (Advisor: do **not** re-source Al — it buys a citation fight, not a claim.) S3's "the cap
>    is binding, not cosmetic", applied to a metal instead of a width.
> 7. **FOUR simplifications, each with its DIRECTION named**, because the slice's conclusion is a sign:
>    `C` = 1.0 is round and unfitted and **errs against Ru** (it puts Cu at 6.3 µΩ·cm in an 18 nm line where
>    the measurement is ~9); width-only `W_eff` also **errs against Ru**; **the scattering dimension `d` =
>    the conductor width, not a cross-section** — also **against Ru**; the barrier as perfectly dead area
>    **errs for Ru**. A single `C` cannot span both ends of the measured range — the grain-boundary term is
>    named, not built (advisor: splitting `C` adds a lump and no claim).
> 10. **The fourth simplification was a post-build advisor catch, and its DIRECTION had to be checked
>     rather than accepted.** The advisor flagged that `effective_resistivity` takes `d` = the conductor
>     width while real scattering sees both surface pairs — correct, and it was missing from the ladder —
>     but argued the direction with `d = 2WH/(W+H)`, which flips the 12 nm rung to 1.12 (Ru losing) and
>     would have cost the panel its punchline. **Measured out, the opposite is true.** The additive-rate
>     derivation gives `1/d = 1/W_eff + 1/H` (the standard rectangular form), *half* the advisor's `d`:
>     under it the rung goes 0.917 → **0.889** (Ru wins by MORE) and the crossing 12.9 → 13.4 nm. The tie
>     is broken on evidence, not taste — at an 18 nm line the three conventions give Cu ρ_eff = 6.3 (ours)
>     / **8.1** (standard) / 4.9 (the advisor's) against a **measured ~9**, so the advisor's form is the
>     furthest from the data. Kept width-only for a second reason that is not a preference: bringing `H`
>     into the scattering would put the **flagged aspect ratio into the headline ratio**, and
>     `resistance_ratio` is prefactor-free precisely because `H` and `AR` cancel. **A prefactor-free claim
>     that errs against its own conclusion beats a better-calibrated one that does not.** Pinned by a test
>     that computes the standard form by hand, so a future convention change confronts the direction.
> 8. **The guard was NOT retired.** S1 and S3 both wrote "slice 4 removes the need for `bulk_regime_ok`".
>    Wrong: `delay`/`crossover_width_um` are still bulk-only, so their bound is unchanged. S4 added a
>    *second path beside* the first. Corrected in both places and pinned by a test.
> 9. **The node convention EXPIRED, and the 4th panel may not reuse it.** S3's left panel is licensed to
>    write "W = the node number" because pre-2000 the node name really was ~the metal half-pitch. A modern
>    "3 nm node" has no 3 nm linewidth, so panel 4's axis is labelled a **drawn linewidth** and never a node.
>    A source-text test pins both labels — the one thing the golden-HTML currency tests structurally cannot
>    catch (F3's follow-up commit: they confirm the prose did not *change*, never that it is still *true*).
>
> **S3's findings — two of them corrected claims this plan/module were already making:**
> 1. **Copper bought 0.64 of a node, not "roughly one".** `W_x ∝ √ρ₀`, so Al→Cu's 1.58× in ρ moves the
>    crossover 0.796× — and a node step is **0.70×**, so that is `ln(0.796)/ln(0.7)` = **0.64 of a node**.
>    `crossover_width_ratio`'s docstring claimed "roughly one node" (a ~50% overstatement of the 1997
>    escape); **fixed at S3**, and pinned by `test_copper_bought_two_thirds_of_a_node_and_is_never_rounded_up_to_one`.
>    This is B8's `floor_decades` rule in the crossover's currency: never round a win up. New helper
>    `demo_beol_history.nodes_bought()` makes the node the unit.
> 2. **`crossover_width_ratio` argument order is a live sign trap — the S2 bound-swap's cousin.** The
>    demo's first run shipped **silver as buying −0.08 of a node** (i.e. as *worse* than copper, which is
>    false) because the call was made incumbent-first and reciprocated. For Al→Cu that reciprocal is the
>    same number; for Cu→Ag it is *its reciprocal*, so the error renders as a perfectly plausible figure
>    and only the **sign** gives it away. **The challenger goes first**; docstring fixed, direction pinned
>    by a test.
> 3. **The new headline (prefactor-free, and it earns S4 structurally): on the bulk-ρ axis the ladder is
>    out of metals.** `W_x ∝ √ρ₀` ⇒ one more node needs `ρ ≤ 0.82 µΩ·cm`; **silver — the best elemental
>    conductor there is — is 1.59** and buys +0.08 of a node. **Scoped deliberately to the axis** (advisor):
>    "no metal beats Cu" would be *false*, since S4 has Ru winning with 4× copper's bulk ρ. The **axis** is
>    exhausted, which is exactly *why* the axis must change — and on the scaling axis Ag's `ρ₀λ` ≈ 84 is
>    worse than Cu's 65 (and Ru's 77): the best bulk conductor is the worst scaling metal. [Ag ρ₀/λ
>    handbook — FLAGGED, the same status as Al's.]
> 4. **The deep point of the arc, and it replaced a fragile framing.** `W_x ∝ √I_Dsat` **exactly as**
>    `W_x ∝ √ρ₀`: a 2× better transistor pulls the crossover out to a 1.41× *wider* wire — an **earlier**
>    node — by the very same √2 a 2× better metal pushes it in. **The transistor's own progress is what
>    creates the wire wall.** (This replaced a "freezing the gate is conservative" gloss the advisor
>    killed: the bias direction rides on *which* τ_gate you freeze at — conservative only if you freeze at
>    the ladder's oldest device, ≈neutral at the crossover node, and it **flips to overstating** if you
>    freeze newer. The √ inversion is rigorous and says more.)
>
> **S2's finding — the damping law, sharper than the crossover:** `∂ln f/∂ln I_Dsat = 1 − wire_share`,
> **exact at every `I_Dsat`** (from `f = I/(A + τ_wire·I)`), not a linearization. It is the payload in one
> line: `τ_wire` is **common-mode**, so it adds a *level* and **no spread** — the across-wafer `I_Dsat`
> spread maps to a speed spread damped by exactly that factor while the transistor histogram is
> bit-for-bit unchanged. As `wire_share → 1` a better transistor buys **nothing**. Measured end-to-end
> (house geometry, `wire_share ≈ 0.71`): a tight process's **23 premium parts → 0**.
>
> **S2's framing correction (advisor — it inverts the obvious reading): the compression is SYMMETRIC.**
> The wire pulls the slow tail **up** exactly as it pulls the fast tail down — the bin-out tail *shrinks*
> (loose process: reject 2 → 0). ⇒ the licensed claim is **"sorting by drive current stops producing a
> speed spread; the premium *grade* collapses"**, never "wires cost yield". A **grading loss, not a yield
> loss** — the die count is untouched.
>
> **S2's trap, and what licenses the slice:** `τ_total` is strictly monotone in `I_Dsat`, so re-binning
> with edges mapped through *that same function* is a **byte-identical partition** — re-binning alone
> proves nothing. The edges must encode the **market's promise** ("a 2.6%-faster part"), anchored on the
> nominal part: `τ_edge = τ_nom·(I_nom/I_edge)` (`DelayBins.from_speed_bins`). Adds **no new house number**
> and **cancels the flagged `L`** (nominal ≡ typical under both policies), so only the compression
> survives. Control: at `τ_wire = 0` the partition is identical, grade for grade.
>
> **Corrections the S1 review forced — S3/S4 inherit them:**
> 1. **The headline is bounded.** The module drops the driver↔wire Elmore cross terms, one of which
>    (`R_driver·C_wire`) **is** weakly `I_Dsat`-dependent. ⇒ the licensed claim is **"the wire's
>    *intrinsic* RC is a common-mode floor"**, *not* "the transistor can't touch the wire term". The
>    discriminator survives; the stronger phrasing was unearned. **S2 uses the bounded form throughout.**
> 2. ~~**S4 is not a Ru-only slice** — the guard fires on copper's own crossover (~0.167 µm).~~
>    **PREMISE WITHDRAWN at S2; the conclusion stands on other legs.** That ~0.167 µm rested on a
>    **test-local 23 fF load** (a *1 µm* channel), not on anything the sim runs. Wiring the **real** chain
>    (S2's `C_load` = the fan-out-1 `C_ox·W·L` off the game's own device ⇒ **4.1 fF**) puts Cu's crossover
>    at **~0.395 µm** — **comfortably inside** the bulk regime (Cu wants W > ~0.19 µm). *Where the
>    crossover lands is a statement about the **load**, not a property of the slice.* **S4 is still
>    motivated for copper** — because the size-effect correction **grows as W scales below ~0.19 µm**, and
>    the size effect became a *copper* problem at sub-200 nm (cited history, which never needed the
>    operating-point claim). What died is only "this slice already sits outside its own model's
>    competence": it does not. Fixed in the S1 docstring + test; **both** loads now pinned, with the
>    direction (`W_x ∝ 1/√C_load`) as the invariant rather than either number.
> 3. **The IBM ~40% check is a *consistency* check, not a non-circular one** — at fixed geometry
>    `R_Al/R_Cu ≡ ρ_Al/ρ_Cu`, so it validates the inputs, not a structural form. Weaker than F3's. (The S1
>    *test file's* header still billed it "non-circular" while the module said otherwise — fixed at S2.)
>
> Predecessor F3 (high-κ) shipped 2026-07-17 and its card graduated. **F4's roadmap card stays up until
> S4** — the graduation rule fires when the slice *plan* completes, as F3's did.

**The discriminating observable, stated first (the build's licence):** chip delay is **two terms with no
shared variable**, and no single scalar can move both:

- **Gate delay** `τ_gate = C_load·V_dd / I_Dsat` — the transistor's term. **Inversely ∝ `I_Dsat`**, which
  is the number the whole existing chain (CD → `V_t` → `I_Dsat`, plus F2's `R_series`) already computes.
- **Wire delay** `τ_wire = R_wire·C_wire ∝ ρ_eff·ε·L²/(W·H)` — the interconnect's term.
  **`∂τ_wire/∂I_Dsat = 0`.** It is *blind to the transistor entirely*.

`τ_total = τ_gate + τ_wire`. Past the crossover (`τ_wire > τ_gate`), **halving the gate delay less than
halves the chip delay** — the transistor stops setting speed. That is the payload, and it is the first
output in the sim the transistor chain does not set.

## The consumer — an assumption already in the tree, stated verbatim, that F4 falsifies

This is what makes F4 pass the bar without inventing a reader. `fab_game/spec.py:SpeedBin` **already**
bins parts by drive current as a speed proxy, and says so in its own docstring:

> "Parts are binned by drive current as a **speed proxy** (clock speed ∝ drive current → ∝ `I_Dsat`):
> a faster die (higher `I_Dsat`) sorts into a higher bin (premium)."

`SpeedBins.assign(i_dsat_mA)` takes `I_Dsat` **directly**. That premise is *era-appropriate and false*:
it is exactly the pre-1997 assumption, and it is sitting in the tree as a **house grading policy**
(ADR 0005 §1 — binning is policy, not physics), which is precisely where an era assumption *should* live
and precisely what a later era gets to overturn. F4 re-bins on `τ_total`.

**The statistical payload the binning consumer delivers for free (and the reason this consumer is the
right one):** `τ_wire` is a **common-mode additive floor** — the same for every die on the wafer, because
it depends on the metal and the geometry, not on that die's transistor. So once `τ_wire` dominates:

- the **across-wafer `I_Dsat` spread stops mapping to a speed spread** — the premium bin collapses toward
  typical even though the transistor histogram is *unchanged*;
- **tightening CD control stops buying speed grades** (G6's existing tight-vs-loose σ contrast, re-scored);
- and it re-uses the **device-targets discipline**: re-score the *same wafer* against a different reading,
  **never re-fab** (`fab_game/targets.py` precedent).

The G6 demo's own tight/loose histograms become the exhibit: same silicon, same `I_Dsat`, and the value
of transistor process control evaporates. A scalar "wires are slow" cannot produce that.

## The seam

| State | Binning input | Delay output | vs today |
|-------|--------------|--------------|----------|
| **knob absent (default)** | `i_dsat_mA` (as today) | not emitted | **byte-for-byte identical** ← the seam |
| **Al (opt-in)** | `τ_total` | `τ_gate + τ_wire` | the pre-1997 era: wire-limited at the crossover |
| **Cu (opt-in)** | `τ_total` | `τ_wire` down ~40% in ρ | the 1997 escape |

The default `SpeedBins` is already a **single open `"pass"` bin** (every die passes, nothing graded), so
the seam is clean: knob off ⇒ `assign()` keeps reading `i_dsat_mA` and every banked demo is unchanged.

## The three traps this plan exists to not walk into

1. **No wire length exists in the sim ⇒ `L` is a house lump ⇒ the headline must be prefactor-free.**
   `τ_wire ∝ L²`, and *nothing* in the journey carries a wire length (checked: `metallization_history.py`
   B6 carries `t_Al`, a contact-metallization **thickness**, not a line length — no geometry to reuse).
   `L` is therefore the analogue of F2's `CONTACT_LENGTH_UM` and F3's `J0_REFERENCE`. **The payload must
   be the crossover and the ratio `τ_wire/τ_gate`, never absolute picoseconds** — a ratio cancels the
   house constant, exactly as F3's `leakage_decades_saved` contains no calibrated constant at all.

2. **The Ru-beats-Cu claim is sign-inverted from bulk resistivity** — the F3-IL sign trap, again. See
   "Model class" below; this is the single most important thing in this plan.

3. **Pin the scaling scenario or the crossover is an artifact.** *Whether `τ_wire` grows as you scale*
   depends entirely on an assumption that is easy to leave unstated. **Local** wires scale with the node
   (`L` shrinks with the cross-section ⇒ `τ_wire` ≈ flat); **global** wires stay ~chip-sized while `W·H`
   shrinks ⇒ `τ_wire` **explodes**. The crossover is a *global-wire* statement. **Pin it: a
   representative fixed-length global wire whose cross-section scales with the node**, and say so on the
   figure. This is the honest simplest choice, and it is the historical one (global wires stopped scaling).

## Model class — the two-limit structure, and the Ru sign trap

**The bulk era (Al→Cu, 1997) is a genuine `ρ₀` win.** Cu's bulk resistivity really is below Al's, wires
were far wider than the electron mean free path `λ`, so `ρ_eff → ρ₀` and the ordering is the bulk
ordering. IBM's own reported numbers (below) are ~40% less resistance → ~15% chip speed → PowerPC
300→400 MHz. **This half is straightforward and citable.**

**The scaled era (Cu→Ru, 3 nm) is NOT a `ρ₀` win, and asserting it is ships the sign backwards.**
Ru's bulk `ρ₀ ≈ 7.1 µΩ·cm` is **~4× *higher* than Cu's 1.68**. Two mechanisms, neither of them bulk `ρ`:

- **The size effect and the `ρ₀λ` figure of merit (the F3 κ↔gap echo).** Below `λ`, surface/grain-boundary
  scattering dominates: `ρ_eff ≈ ρ₀·(1 + C·λ/d)`, so in the narrow limit `ρ_eff → C·ρ₀λ/d` — the material
  enters **only** through the product `ρ₀λ`, which is the **cited screening figure of merit** for
  interconnect metals. Buying a low `ρ₀` costs you a long `λ`, so the metric that ranks metals at 3 nm is
  **not the metric that ranked them at 250 nm** — structurally the same finding as F3's "buying κ costs
  barrier", and the same shape as F2's two `R_sh` exponents.
  **But parity is where it stops:** `ρ₀λ` ≈ Cu 65, Ru 77 (µΩ·cm·nm) — Ru is ~17% **worse**, matching the
  literature's "Mo, Co and Ru *approximately match* Cu in the narrow-wire limit". So the short `λ` buys Ru
  **viability, not a win**: it cancels Ru's ~4× bulk-`ρ` penalty and brings it to rough parity — a
  **necessary, not sufficient** condition. **The size effect alone never justifies Ru.** (Al ≈ 58 lands
  *below both* — the FOM ordering is not the bulk ordering. **Keep this out of any headline until Al's
  `ρ₀` and `λ` are re-sourced**: "Al beats Cu on the scaling FOM" is spicy enough to draw a citation
  fight, and it currently rests on one source. Al lost 1997 on bulk ρ at wide wires, and separately on
  electromigration.)
- **The barrier is the BEOL's interfacial layer — and it is what tips parity into a win.** Cu needs a Ta/TaN
  diffusion barrier that **does not scale below ~2–3 nm**; at sub-10 nm trench widths it "consumes a
  disproportionate fraction of the available conductor cross-section". Ru needs **none**. So the
  conducting width is `W_eff = W − 2·t_barrier` — a **fixed** thickness eating a **shrinking** budget,
  with a hard geometric floor at `W = 2·t_barrier` where `W_eff → 0` and the wire is **all barrier**.

  **This is structurally F3's IL, and it should be built as F3's IL was:** a fixed parasitic layer, a hard
  prefactor-free floor, and a figure of merit that decides the sign. It is also A4's lesson (the negative-
  resist swelling floor): **the win is GEOMETRIC, not a materials ride.** "Ru wins below ~20 nm CD" is
  cited — and it is a *barrier-geometry* claim, not a resistivity claim.

**The honest headline for S4 — two steps, both load-bearing (the F3-IL structure exactly):** `ρ₀λ` parity
makes Ru **viable** (necessary); barrierless-ness **tips that already-near-parity metal over** below
~20 nm CD (sufficient, *given* parity). The metal with the **worst bulk ρ and the worst `ρ₀λ` of the three
still wins at 3 nm** — and **neither currency alone gets that sign right**: bulk ρ says "never", the size
effect says "only a tie", and only the barrier geometry on top of the tie says "wins". Do **not** collapse
this to "Ru wins because of the liner" (drops the necessary condition) or to "Ru has a shorter mean free
path" (the sign error this plan exists to prevent).

## Verification ledger (web-verified 2026-07-17 — the F3 discipline: cite, don't recall)

**VERIFIED:** Cu `ρ₀`=1.68 µΩ·cm, `λ`≈38.7–39 nm · Ru `ρ₀`=7.1 µΩ·cm, `λ`=10.8 nm · `ρ₀λ` is the cited
screening FOM, and Ru ≈ Cu on it · barrier min ~2–3 nm, disproportionate below 10 nm, barrierless Ru
lowest R at CD **<~20 nm** · IBM **Sept 1997**, CMOS **7S**, **0.22 µm**, first dual-damascene flow;
PowerPC 300→400 MHz (~33%); Cu ~40% less resistance → ~15% speed · crossover history: gate-dominated
mid-1980s → **roughly equal mid-1990s** → Cu+low-κ introduced at **250 nm** → below **130 nm** wire delay
worsens further; interconnect delay ∝ 1/pitch².

**VERIFIED — and promoted to a TIGHT leg (it is the headline, not an afterthought):** `c_pul ≈ 2 pF/cm`
(≡ 200 aF/µm), **and its near-invariance**: "the capacitances per unit length of all electrical
transmission or interconnect lines are very similar, **within factors of order unity**" — a ~1 cm-diameter
50 Ω coax is ~1.5 pF/cm and an **80 nm**-pitch on-chip line is ~2 pF/cm. **Seven orders of magnitude of
geometry, the same `c_pul`.** The mechanism is why it is tight and not a lump: `C` per length depends on
**ratios** of dimensions, not absolute size (and on-chip, line-to-line coupling cap rises as area cap
falls, holding the total). **Use the total per-length `C`, never an area-only parallel-plate `C`** — the
latter omits coupling, understates `C`, and *misplaces the crossover*, which is fatal for S3.
**⇒ The crossover is driven by `R`, not `C`:** `R ∝ 1/(W·H)` rises as the cross-section shrinks while
`C ∝ L` sits still. Same source confirms trap #3 outright: *"if the interconnect length and interconnect
pitch scale identically, the wire delay will remain constant with technology scaling"* — i.e. **the
crossover is a global-wire (fixed-`L`) statement**, exactly as pinned above. Low-κ lowering `c_pul` (hence
delay) is confirmed as the named-not-built edge.

**FLAGGED / verify at build:** Al `ρ₀` (~2.65–2.7, handbook, not pinned by the search) and Al `λ` (~22 nm,
single source) — the Al `ρ₀λ`≈58 claim rests on both, so **do not headline it until re-sourced** · the
Elmore `0.38·RC` distributed-line factor · the Fuchs–Sondheimer / Mayadas–Shatzkes coefficient `C`.

**HOUSE LUMPS (name them like B6's `SPIKE_CONCENTRATION`):** wire length `L`, `C_load`, `V_dd`, the
node→(W,H) ladder.

## Slices (resist front-loading — this is the "biggest build of the promotable set")

- **S1 — `chip/interconnect.py`.** `R_wire`, `C_wire`, `τ_wire`, `τ_gate`, `τ_total`, the **crossover**;
  Al + Cu registry. Pure, cited, unit-tested. **`device.py` untouched** — it reads `I_Dsat` as a
  loose-coupled scalar (the F2/F3 precedent: plain scalars across the module boundary).
- **S2 — the game knob + the binning inversion. ✅ BUILT.** `DeviceKnobs.interconnect` (`"Al"`|`"Cu"`,
  `None` = seam) → `Die.delay` → `spec.DelayBins` (a `SpeedBins` sibling in the inverse currency), wired
  at `device_step` (where `I_Dsat` and `C_ox` already are — there is no BEOL step, and inventing one
  would claim more than F4 models). **Metal-only knob**: geometry stays the module default, since the
  payload holds at fixed geometry and S3's ladder sweeps `chip.interconnect` directly (anti-front-load).
  **A three-rung seam:** knob off (nothing emitted) → knob on + `delay_bins=None` (the delay is emitted
  and **read by no one** — still byte-for-byte, the `bv_V`/`t_rr`/`j_gate` additive discipline) → knob on
  + delay binning (the inversion). It is the **pair** that overturns the premise, never the knob alone.
- **S3 — the B9 history mode + demo. ✅ BUILT.** `chip/demo_beol_history.py` + 11 tests; the **9th**
  timeline rung. **No `beol_history.py` wrapper** — the period physics is already in `interconnect.py`
  (Al and Cu are both in `METALS`); the node ladder is a *demo recipe*, not physics, so the demo rides the
  base module (the B7/B8 pattern), as F3's slice-3 finding requires. Three panels:
  **the wall** (the node ladder — τ_gate a flat line, τ_wire ∝ 1/W² climbing past it, a crossing that
  exists *with no help from the transistor*; the metals are **parallel**, a better metal shifts the line
  and does not bend it) · **the payload** (at 250 nm, the premise's `f ∝ I_Dsat` diagonal vs the damped
  reality, slope = 1 − wire_share exactly; a +3% transistor is worth **+0.7%** on an Al line) · **the
  escape and its ceiling** (`W_x/W_x(Cu) = √(ρ/ρ_Cu)` — **prefactor-free**; 0.64 of a node, then nothing).
  **The ladder is capped at W = 0.20 µm** and the cap is *binding, not cosmetic*: `interconnect.py` is
  bulk-ρ only, Cu's `bulk_regime_ok` refuses below `5λ` ≈ **0.194 µm**, and **the next real node (0.18 µm)
  is already inside that refusal** — which the figure draws as a shaded zone with the 0.18 rung sitting in
  it. That is the cleanest possible hand-off to S4 and it matches cited history (the size effect became a
  **copper** problem at sub-200 nm). Walking past the cap would fabricate exactly the number S4 exists to
  compute — the F3 magnitude trap.
  **Open question 4, DECIDED: a demo-local, WIRE-ONLY sweep** — the ladder scales the cross-section and
  the transistor is held fixed. It is *not* a house node→device table (that would have invented two more
  flagged lumps): the period device is a **real `device.py` read** (a 0.5 µm-era n-MOS, 10 nm gate oxide
  at the 3.3 V `V_DD_HOUSE`, `N_A` set to land a period-plausible `V_t` = 0.58 V — chosen on device
  grounds, **not** to place the crossover). Freezing the gate is what isolates the claim, and the middle
  panel **prices** the freeze instead of hiding it (`W_x ∝ √I_Dsat`).
  **The landing is a CONSISTENCY check, never a prediction** (advisor): `W_x ∝ L`, *and the device recipe
  is a second lump-carrier* — `W_x(Al)` moved 0.49 → 0.38 µm across a plausible `N_A` range (~¾ of a node).
  That an **untuned** 1 mm line + a period-plausible transistor land `W_x(Al)` ≈ **0.45 µm** — the
  mid-1990s, where the cited history puts gate ≈ interconnect — has exactly the status of the IBM ~40%
  check. **Lead with the shape and the 1.26 shift.**
  **The featured 250 nm rung is `WireGeometry()`'s default byte-for-byte** — the same line S2's game knob
  runs, so the demo and the binning inversion are about one wire. (`wire_share` still differs from S2's
  ≈0.71: same wire, a *different transistor* — which is the point, not a discrepancy.)
  **Checked at S2, and S3 stayed clear of it: don't rework-then-read-bins.** `rework_litho` re-runs
  `device_step`, so a reworked die's delay **is** refreshed with the knob on — but rework **never
  re-packages**. Pre-existing and **identical for both currencies**, so F4 adds no asymmetry — but a demo
  that reworks and then reads a bin histogram would silently under-count either way. (B9 is chip-side and
  reads no bins at all, so this never arose.)
- **S4 — the honest ceiling: size effect + barrier fraction → Ru. ✅ BUILT.** `interconnect.py` §6:
  `effective_resistivity` (FS/MS `ρ_eff = ρ₀(1+Cλ/d)`), `conductor_width_um`/`conductor_floor_width_um`
  (the `W_eff = W − 2t_b` floor), `narrow_line_resistance`, `resistance_ratio` (challenger-first, with the
  `size_effect`/`barrier` switches that *run* the three-rung ladder), `size_effect_ratio_limit` and
  `barrier_only_flip_width_um` (the two impossibility results), `equal_resistance_width_um`/`_nm`. Ru joins
  `METALS`; `BULK_ERA_METALS` gates the game knob; `NARROW_WIRE_METALS` is **derived** from `METALS` so a
  new metal cannot be silently missing and Al cannot silently appear. The demo gains a **fourth panel on
  its own sub-60 nm axis** — deliberately *not* a continuation of the 0.20 µm ladder, so the era seam stays
  visible (advisor). Everything in the status block above is the finding; the slice that makes the arc
  real, exactly as F3's IL did. **No new game knob** — the demo is the consumer and `fab_game` gains only
  the refusal, which is the F3-slice-4 shape.

**Gallery/manifest note:** both gallery manifests are **glob-anchored** — the demo file and its rungs must
land in the **same commit** or `assert_manifest_complete()` fails (F3 slice 3's trap).

## Scope discipline (the honest NO's)

- **Low-κ ILD: NAME, DON'T BUILD.** It is the **C-side mirror of high-κ** (F3 bought `t_phys` with κ; low-κ
  buys `C_wire` by *lowering* ε) and the symmetry is a genuine teaching point worth one sentence — but it
  is a separate era knob with the same currency, and building it here dilutes the single clean
  wire-vs-gate payload. Historically it arrived *with* Cu at 250 nm; note that, don't model it.
- **Electromigration: NAME, DON'T BUILD.** Cu's *other* win over Al (and a real reason Al died). It is a
  **reliability/lifetime mechanism, not a delay observable** — wrong currency for this module's consumer,
  the same reason F3 kept gate leakage out of `lifetime.py`.
- **CMP: NOT HERE.** `future-steps.md` explicitly gates **F8 to unblock *after* F4**. Do not pull it in;
  F4's job is to *give it a consumer* (wire cross-section → RC), not to build it.
- **Repeater / buffer insertion: NAME LOUDLY.** Real chips break long wires with repeaters, which makes
  delay ∝ `L`, **not** `L²`. Without naming this the model silently claims wire delay is unfixable and
  overstates the wall. This is the F3 "trap-limited floor" analogue — the mechanism that stops the
  extrapolation being real.
- **No crosstalk, no inductance, no multi-level RC stack, no via resistance.** Named edges.
- **`I_Dsat` keeps its meaning.** `τ_gate` is computed *at the delay read*, never written back — the F2
  (`die.R_s` access-only) / F3 (`die.t_ox_um` = what the furnace grew) discipline.

## Open questions — 1–3 DECIDED at S2; 4 DECIDED at S3 (see the S3 slice above). None open.

1. **Where the delay output lives.** ✅ **`Die.delay` (s) + `Die.delay_ps`** — *not* `tau_ps`: `Die.tau`
   is already the minority-carrier **lifetime** (G4b), and `tau_ps` next to it would read as "the
   lifetime, in ps". Different quantity, different name. `None` when the knob is off (gap-vs-fake-zero).
2. **Does `SpeedBins` gain a `τ` mode, or does the knob feed a τ-derived pseudo-`I_Dsat`?** ✅ **Neither
   — a separate `DelayBins`/`DelayBin` pair.** A mode flag would put four optional edges on one bin class;
   the pseudo-`I_Dsat` would overload a documented field (the overload F3 rejected). A sibling keeps
   `SpeedBin`'s mA bands honest *as the era artifact they are* — the false premise stays legible in the
   tree, and `DelayBins.from_speed_bins` is the bridge. **The bound swap is the trap**: `lo_mA` (the fast
   edge) → `hi_ps`, since the currency inverts. Get it backwards and every part mis-grades while the
   histogram still looks like a clean partition.
3. **`C_load`: the real `C_ox·W·L`, or a house lump?** ✅ **The real one** (fan-out-1, off the die's own
   `C_ox` and printed CD) — it makes `τ_gate` a genuine CV/I read of the existing chain, costs nothing,
   and is what exposed the withdrawn S1 crossover claim above. `V_dd` and `L` remain house lumps.
4. **Does the node ladder drive `die.t_ox_um`/CD upstream** (F3 slice 3's move) or is it a demo-local
   geometry sweep? ✅ **Demo-local, and WIRE-ONLY** — the ladder scales the cross-section; the transistor
   is a fixed **real `device.py` read**, not a house table. The node→`W` mapping is the only new house
   assumption (`W` = the node number, `H` = 2`W`), and it is a mild one: pre-2000 the node name *was*
   roughly the metal half-pitch, so the rungs (1.0/0.7/0.5/0.35/0.25 µm) are the **real** node ladder
   rather than an invented one. The aspect ratio is flagged and cancels in every headline ratio. Driving
   the device upstream would have added a fabricated node→(t_ox, CD) table **and** cost the panel its
   cleanest claim — that the crossover happens *with no help from the transistor*. See the S3 slice above
   for the consistency-check discipline the frozen device requires.
