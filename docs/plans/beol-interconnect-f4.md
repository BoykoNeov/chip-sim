# Plan — F4 BEOL interconnect (the delay the transistor doesn't set)

> **STATUS: SLICES 1–2 BUILT (2026-07-17)** — `chip/interconnect.py` + `chip/tests/test_interconnect.py`
> (29 tests); S2 wired the game consumer: `DeviceKnobs.interconnect`, `Die.delay`, `spec.DelayBins`, and
> `fab_game/tests/test_interconnect_binning.py` (13 tests). **Full gate green serially at 1105.**
> `device.py` still untouched. Cited constants → `memory/beol-interconnect-source.md`.
> Remaining: S3 (the B9 demo), S4 (size effects + barrier → Ru).
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
- **S3 — the B9 history mode + demo** (`chip/demo_beol_history.py`; the **9th** timeline rung, after B8).
  The node-scaling ladder into the crossover, then the Al→Cu escape — the mirror of F3's `t_ox` ladder
  into the leakage wall. **Cap it honestly** (the F3 magnitude-trap lesson: cap the ladder where the model
  is valid, lead with the *shape*, let curves exit the axis rather than print a fabricated number).
  Per F3's slice-3 finding, **no `beol_history.py` wrapper** unless it carries period physics
  `interconnect.py` lacks (the demo-rides-the-base-module pattern, B7/B8).
  **Checked at S2, for S3's benefit: don't rework-then-read-bins.** `rework_litho` re-runs `device_step`,
  so a reworked die's delay **is** refreshed with the knob on — but rework **never re-packages** (only
  front-end fails are re-attempted, and a recovered die carries `verdict.passed` with `bin=None`). That
  is pre-existing and **identical for both currencies**, so F4 adds no asymmetry — but a demo that reworks
  and then reads a bin histogram would silently under-count either way.
- **S4 — the honest ceiling: size effect + barrier fraction → Ru.** FS/MS `ρ_eff(d)`, the `ρ₀λ` FOM, the
  `W_eff = W − 2·t_b` floor. The slice that makes the arc real, exactly as F3's IL did.

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

## Open questions — 1–3 DECIDED at S2; 4 is S3's

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
   geometry sweep? **Still S3's to decide.** The latter is likely, since the sim has no node concept —
   but that means the node ladder is a **house geometry table**, and it must be flagged as one. S2 leaves
   this open by design: the knob is metal-only, so nothing in the game constrains S3's choice yet.
