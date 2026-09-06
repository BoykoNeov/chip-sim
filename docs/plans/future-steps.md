# Roadmap — future fab steps, triaged by consumer (post-backlog-exhaustion)

## Context

The scope-edge backlog (`docs/plans/scope-edge-backlog.md`) is **exhausted** — every remaining named
edge was deferred for *lack of a consumer*, and device-targets + the journey cost side are complete. So
the next moves are **new unit processes**, not edges fitted to old consumers. This doc triages the
candidate future steps under the **same load-bearing discipline** the backlog enforces: *no regime
without a named consumer that discriminates* (the v1.6 "build explicit, NOT 2-D" lesson). The spine here,
as in the backlog, is the **NO's** — which steps honestly lack a planar-observable consumer and stay
deferred. A step is only PROMOTABLE if it produces an observable the current model cannot.

The user set the standing consumer on **2026-07-03**: **the game — historical processes, education.**
That reframes "consumer" to include *pedagogical discrimination* — a step earns its place if it teaches a
contrast the current sim can't show (e.g. surface-peaked vs buried doping) — but it must still be
grounded in a real device/yield observable, not decoration.

## What the sim currently is (the baseline the history is told against)

A **~1968 thermal-predep planar line**: Czochralski boule → planar oxide passivation (Hoerni 1959) →
photolith → **predep + drive-in doping** (surface-peaked `erfc`) → etch/depo → planar MOSFET (`V_t`,
`I_Dsat`, breakdown, lifetime/leakage, reverse-recovery) → package/bin. The doping route is pre-implant;
isolation is implicit; interconnect stops at the transistor terminals; the gate dielectric is thermal
`SiO₂`. Each of those is a place a *later era* modernised — which is exactly where the future steps live.

## The triage at a glance

| # | Step | Era / history arc | Consumer observable it discriminates | Verdict |
|---|------|-------------------|--------------------------------------|---------|
| **F1** | **Ion implantation** | 1970s: predep → implant | **buried/retrograde peak** predep can't make; `device.py:78` V_t-adjust; damage→leakage (`lifetime.py`) | **✅ BUILT (2026-07-06 — all 4 slices)** (`ion-implantation.md`) |
| **F2** | **Silicide / contact resistance** | 1980s salicide | **series R** → `I_Dsat` (the journey's `R_series_ohm` seam already exists!) | **✅ BUILT (2026-07-10) as historical-mode B7** (`contact_resistance.py`); two-term access+TLM-contact, bottleneck flips access→contact |
| **F3** | **High-κ gate dielectric** | 2007 (45nm): SiO₂ → HfO₂ | **gate tunneling leakage** (exp in `t_phys`) vs **`C_ox`** (linear in EOT) — one thickness, two currencies | **✅ BUILT (2026-07-17 — all 4 slices) as historical-mode B8** (`chip/high_k.py` + the `dielectric` knob + `demo_highk_history.py`); EOT identity (`device.py` untouched), per-material WKB tunneling, and the interfacial layer on **both** currencies → the honest EOT floor. **Roadmap card graduated** |
| **F4** | **BEOL interconnect (RC delay)** | Al → **Cu damascene (1997)** → Ru (3nm) | **new output: chip speed limited by wire RC, not the transistor** | **✅ BUILT (2026-08-10 — all 4 slices) as historical-mode B9** (`chip/interconnect.py` + the `interconnect` knob + `spec.DelayBins` + `demo_beol_history.py`); two terms with no shared variable ⇒ `∂ln f/∂ln I_Dsat = 1 − wire_share`; Cu bought 0.64 of a node; then the **axis changed** — size effect + an unscalable barrier put barrierless Ru ahead below ~13 nm with 4× Cu's bulk ρ. **Roadmap card graduated** |
| **F5** | **Strained silicon** (card: SiGe S/D) | 2003–04 (90nm): strain era | **mobility → `I_Dsat`** — the one factor in `I_Dsat` no process step has ever moved | **✅ BUILT (2026-08-10 — all 4 slices) as historical-mode B10** (`chip/strain.py` + the `strain` knob + `demo_strain_history.py`); `device.py` untouched (`mu_eff` defaulted since P4 — the seam predates the slice); carrier-generic enhancement factors with the hole leg **refused** on the n-channel device; the first game knob that re-grades the wafer on its own; and the era's ending — a delivered-drive **bracket** between two cited endpoints, decaying with `L`, against a model whose elasticity is 1 at every `L`. **Roadmap card graduated** |
| **F6** | **Epitaxy (buried layer / retrograde well)** | bipolar epi; CMOS wells | **SPLIT THREE WAYS on re-check (2026-09-06)** — see below | **① resistance leg BUILT** (B12's `epi_substrate_resistance_ohm`, under-claimed by its own disclaimer); **② retrograde-well leg STILL DEFERRED** (genuinely overlaps F1 — the stated gate holds); **③ out-diffusion leg PROMOTABLE** — the handle's dopant diffuses up into the growing layer over `√(Dt) ≈ 0.05–0.7 µm`, while B12's modelled floor sits at **0.025 µm**, 12× thinner than the thinnest layer it sweeps ⇒ **out-diffusion is the only floor that can bind**. |
| **F7** | **Isolation: LOCOS → STI** | LOCOS (1970s) → STI (1998) | bird's-beak narrows active width → geometry; latchup | **✅ BUILT — bird's beak (2026-07-10) as B5, and the latchup observable (2026-09-06) as B12** (`chip/latchup.py` + the `isolation` knob + `demo_latchup_history.py`; `latchup-isolation-f7.md`). The STI *process* (trench etch/fill) remains named-not-built: it would add no observable this does not already deliver. |
| **F8** | **CMP / planarity** | enables Cu damascene | post-CMP thickness → `R ∝ 1/(W·H)` → `τ_wire` → the delay bins — **the reader F4 built** | **✅ BUILT (2026-08-19 → 2026-09-06 — all 4 slices) as historical-mode B11** (`chip/cmp.py` + the `cmp` knob + `demo_cmp_history.py` + `fab_game/demo_cmp_grading.py`; `cmp-planarity-f8.md`): the `s/(1−s)` forced overpolish, the wire's first per-die spread (one transistor, many delays), the damascene-only refusal, the short graded by radius, the window closing at `s_crit = L/(2+L)`, and — S4 — the **second** F4 clause to go: a per-die wire withdraws the rescue F4's common-mode wire gave the slow tail, so the wire now costs **parts**, not just grades. The published gate was **false on re-check** (the geometry was already an argument). **Roadmap card graduated** |
| **F9** | **FinFET / GAA** | 2011 / 2022: 3-D channel | needs the **3-D engine** (deferred B1) + `device_2d` extension | DEFERRED — no 3-D consumer yet |
| **F10** | **EUV / multipatterning** | 2019 (7nm) | extends litho; **no new observable** (litho already rich) | DEFERRED — no discriminating consumer |

## The recommended sequence (after F1 ships)

1. **F1 — ion implantation** *(✅ BUILT 2026-07-06, all 4 slices).* The buried peak; carries the predep→implant
   history. Slices: Pearson-IV skew, channeling tail, damage→leakage (`diffusion_dopant.py` §5 + `lifetime.py`).
2. **F2 — silicide / contact resistance** *(✅ BUILT 2026-07-10 as historical-mode B7).* Cheapest
   promotable: the journey *already* had an additive `R_series_ohm` on `I_Dsat` (the Ph4 seam). Built as
   the two-term series-R (`chip/contact_resistance.py`): access `R_sh·n_□` (linear) + TLM contact
   `√(ρ_c·R_sh)/W·coth` (sublinear); salicide shunts the sheet so the bottleneck flips access→contact.
   `device.py` untouched. Cited: TLM coth form, `ρ_c` / sheet-R bounds (`silicide-contact-source.md`).
3. **F3 — high-κ / metal gate** *(✅ BUILT 2026-07-17, all 4 slices, as historical-mode B8).* The first
   genuinely *new output*: gate-tunnelling leakage (`chip/high_k.py`). The EOT route turned out to be an
   **identity** (`ε_SiO₂/EOT ≡ ε₀κ/t_phys`), so `device.py` was never touched — the split is that one
   thickness feeds `C_ox` **linearly** and `J_g` **exponentially**. Slices: the module, the `dielectric`
   knob, the B8 demo, and the **interfacial layer** — series capacitance *and* series tunnel barrier at
   once, which is what makes `EOT > t_IL` (for any κ) the honest floor under the whole escape. Cited:
   Robertson's κ/φ_B table + the κ↔gap inverse correlation, Ando's additive EOT
   (`high-k-dielectric-source.md`).
4. **F4 — BEOL interconnect** *(✅ BUILT 2026-08-10, all 4 slices, as historical-mode B9).* The first
   **back-end** output, and the first the transistor chain does not set: `τ_total = τ_gate(I_Dsat) +
   τ_wire`, where `∂τ_wire/∂I_Dsat = 0`. Slices: the module, the game knob + the binning inversion
   (`DelayBins` re-grades the *same* wafer on delay and the premium grade collapses — a **grading** loss,
   never a yield one), the B9 demo, and the **narrow-wire era** — the size effect and a barrier that
   stopped scaling, which together put barrierless Ru ahead below ~13 nm despite 4× copper's bulk ρ.
   Neither mechanism alone gets that sign right, and both failures are closed forms. Cited: `c_pul ≈
   2 pF/cm` **and its geometry-invariance**, the `ρ₀λ` screening FOM, the 2–3 nm barrier floor, IBM 1997
   (`beol-interconnect-source.md`).
5. **F5 — strained silicon** — **✅ BUILT 2026-08-10, all four slices** (`strained-silicon-f5.md`). Its
   gate turned out to be already lifted: `saturation_current(..., mu_eff=MU_N_EFF)` has carried a defaulted
   mobility argument since P4, so the seam predates the slice and `device.py` stays untouched for the
   **fourth** consecutive slice. Two things the plan settles up front: the **carrier fork** (SiGe S/D is a
   *pMOS* technique and the sim is n-channel-only, so the module returns carrier-generic **enhancement
   factors** and the *wired* leg is the nMOS tensile nitride cap — both legs cited from the same Intel 90 nm
   paper), and the **magnitude bound** (the long-channel form carries a µ→I elasticity of 1; the source
   measures **≈0.5 on both carriers**, so the drive-current read is an upper bound ~2× high at 90 nm and
   looser as `L` shrinks — velocity saturation named-not-built, and explicitly **no** elasticity knob).
   Slices: the module, the game knob (the first here that re-grades the wafer *alone*, because strain moves
   a term `SpeedBins` already graded — and the win costs yield against a ceiling written for the unstrained
   line), the B10 demo, and **why the era ended**: the lever is pulled once and what it delivers decays
   (elasticity 0.500 at 90 nm, 0.35 at 25 nm), reported as a **bracket between two cited endpoints and
   never a curve through them** — while this model's own elasticity is 1 at *every* channel length, since
   `W`, `L`, `C_ox` and `V_t` all cancel in the ratio. The quantity that ended the era has no route into
   the device model, which is why the axis changed to geometry (F9).
6. **F8 — CMP / planarity** — **✅ BUILT, all four slices, 2026-08-19 → 2026-09-06** as historical-mode
   B11 (`cmp-planarity-f8.md`). The gate written above ("the cross-section has to become a per-die
   quantity first") was **already released when re-checked against the tree**: `delay()` took the
   geometry as an argument and `Die` carried `radius_frac`, so the work was a die field and a call-site
   change — the third roadmap gate found already-open by someone going to build. What the slices
   settled: the forced overpolish `s/(1−s)` (no house constant; exactly zero for a uniform polish, so
   dishing is bought by non-uniformity and the fix is uniformity, never polishing less); Preston's `V`
   barred from carrying a radial signature (`|v_rel| = ω·d` everywhere at matched speeds, derived) so
   pressure must; at the sim's pitch the loss is **erosion** (the cited dishing trend crosses zero at
   ~1 µm); the game knob that gives the wire its first per-die spread — one transistor, many delays — with
   the under-polish short graded by radius in closed form and CMP refused by name on a subtractively
   etched (Al) line; and the two-sided window that closes at `s_crit = L/(2+L)`. **S4** took the second
   of the two live candidates — the composition with the game's grading — and it ends a *second* F4
   clause. F4 concluded that grading on the true delay currency is *“a grading loss, never a yield
   loss”*, because a common-mode wire can only pull a die **toward** typical: it **rescues** the slow tail
   from the bin-out. A polished wire adds a strictly positive term with no `I_Dsat` in it, so the rescue
   can be cancelled. On one wafer: **2** bin-outs under the old drive-current policy → **0** under F4's
   currency → **8** with a real polisher (yield 0.978 → 1.000 → 0.910). Neither the transistor tail nor
   the polisher costs a part alone. And only **1** of those 8 was the rescue being withdrawn — the other
   **7 were sellable under both prior policies**, one of them graded *typical*, so the polished wire
   creates bin-outs **no** grading policy had rather than merely clawing back F4's margin. Nor does it
   add a signature alongside the transistor's — it **reverses** the wafer's speed
   gradient (radius vs delay −0.09 → +0.45), so the parts it costs sit where the transistor said the dies
   were fast. At the knob's default spread it still costs nothing: the sign is structural, the threshold
   is a house number, and the figure draws the curve rather than quoting the point. The card graduated
   with it.

Recommendation: **F1 → F2 → F3 → F4 → F5 → F8** — all six shipped. F5 was chosen over F8 (2026-08-10)
and built the same day, on the reading that F8's remaining gate was a **refactor** (F4's wire geometry
being a module-level house line). **That reading was wrong, and going to build F8 is what found it:**
`delay()` had always *taken* the geometry as an argument and `Die` already carried `radius_frac`, so the
work was a die field and a call-site change. That is the **third** roadmap gate on this page found already
released by someone picking the slice up, and never by a test — the standing instruction to re-check a
gate against the tree before building comes from exactly this pattern.

**That was true on 2026-09-06 — for about an hour.** The re-triage happened, the user picked F7's
remainder off it, and going to build **again** found half the gate already released: `sti_active_um` had
been in `locos_history.py` since B5, so the LOCOS→STI *geometry* contrast needed no code. The **fourth**
gate on this page found open by someone going to build, and the fourth found by a person rather than a
test. What was genuinely missing was the electrical observable, and that is what B12 built.

**The list's honest state now:** F6's recorded trigger was **settled on 2026-09-06** — see the F6
re-check section below; the card is now split three ways (one leg built, one still deferred on the
original reason, one promotable). F7's remainder is **built**; only the trench *process* is left, and it
adds no observable. F9 still wants the 3-D engine — checked against the tree on 2026-09-06 and the gate
**genuinely stands** (`engines/diffusion/` holds only `diffusion1d.py` and `diffusion2d.py`). F10 still
adds no observable litho lacks.

## The F6 re-check (2026-09-06) — the trigger settled, and the card split three ways

B12 recorded a trigger against F6 ("latchup trigger current reads substrate resistance ⇒ re-check F6's
gate") without arguing it. This is that argument. **The verdict is not the house released-gate pattern**
— this is the fifth time a card has been picked up, but unlike F8's and F7's, F6's *stated* gate was
**not** found released. It was found to be **aimed at only one of three legs**.

### The gate holds where it was aimed

F6's stated deferral reason is *"retrograde profile — **overlaps implant F1**"*. B12's consumer reads
**resistance**, not profile — and `chip/latchup.py:325` already says so in its own words ("It is not an
epitaxy *process* and it is not F6. Nothing about the doping profile the device sees changes"). Two
different quantities. So the recorded trigger fires on something the stated gate never covered, and the
**retrograde-well leg stays deferred on its original, still-correct reason**. Nothing here promotes it.

### What the re-check actually found — the floor B12 asserted cannot bind

`epi_substrate_resistance_ohm` keeps two terms, `ρ_epi·t_epi/A + ρ_handle·path/A`, and B12's finding was
that the second is a **floor**: thinning the grown layer stops paying. That is true, and it is derived,
not asserted. But **where** it stops paying was never computed. Setting the two terms equal:

    ρ_epi·t_epi = ρ_handle·path   ⇒   t_epi = 0.01 Ω·cm × 25 µm / 10 Ω·cm = **0.025 µm**

`EPI_SWEEP_UM` runs 0.3 → 40 µm. The floor sits **12× below the thinnest layer the figure plots**, and at
that thinnest point the trigger current (77.5 mA) is still only **7.7 % of the floor-limited value**
(1008 mA). So across the entire range anyone would grow, the reward for thinning is steep, monotone and
**unopposed** — the model contains no mechanism that stops a player from asking for an arbitrarily thin
layer and collecting the immunity.

**The demo caption overstates this, and is corrected as part of this finding.** Panel C of
`demo_latchup_history.py` annotates the floor line with *"thinning the layer stops paying here"* — a
horizontal line the plotted curve never comes within a factor of 13 of. Not an error (the floor is real
and the asymptotic claim is right); an annotation that reads as though the floor were the operative limit
inside the plotted window, when it is 12× outside it.

### The promotable leg: out-diffusion is the only floor that can bind

Real epitaxy cannot deliver the thin layer the model rewards, and the reason is a *doping-profile* effect
with a *resistance* consumer — which is why it belongs to neither existing leg. While the layer grows at
~1050–1150 °C, the heavily-doped handle underneath is a near-infinite dopant source diffusing **up** into
it. Using the tree's own Fair Arrhenius `D(T)` (`chip/diffusion_dopant.py`) and the v1.3 charge-state
`D(N)` for a handle at 1e19–1e20 cm⁻³ (`chip/diffusion_highconc.py`):

| handle dopant | `√(Dt)` over 1050–1150 °C, 10–30 min, N = 1e19–1e20 |
|---|---|
| **Sb** (the real buried-layer dopant) | **0.013 – 0.27 µm** |
| **B** | **0.055 – 0.69 µm** |

**What is robust here is the gap, not any single number.** The growth temperature and time are house
choices, and a floor value quoted from them would be a fitted number dressed as a derived one. The claim
that survives that objection is the **order of magnitude**: out-diffusion reaches 0.05–0.7 µm while the
modelled floor is 0.025 µm, and *no* plausible T/t closes 12×. The **dopant split is the discriminator**
and it is self-validating — antimony out-diffuses least, which is precisely why antimony is the dopant
real fabs use for buried layers. A model that reproduces "Sb barely creeps, B creeps far more" is reading
the physics that chose the process, not fitting the answer.

**Consumer:** the existing latchup trigger current, unchanged. **New observable:** a *minimum usable
grown-layer thickness* — and with it the honest ceiling on substrate-borne latchup immunity that B12's
own figure currently shows as unbounded. **Overlap with F1: none.** An implant puts a buried peak into a
uniform wafer; this is up-diffusion from a semi-infinite source into a **growing** layer (a moving
boundary, the shape `chip/coupling.py` already handles for oxidation), and its consumer is a *thickness
floor*, not a profile shape.

**Still gated, and honestly:** no source is cited for epi out-diffusion yet, and the growth T/t need a
citation before they stop being house numbers. **This section promotes the leg; it does not build it.**

## The historical/educational spine (the game's timeline)

Every promotable step is *also* an era transition — the game can teach fab history as a sequence of
"what broke, and what replaced it," each grounded in an observable the sim now computes:

- **Doping:** grown-junction (TI 1954) → alloy → double-diffused mesa (Fairchild 1957) → **planar +
  oxide passivation (Hoerni 1959) = today's model** → **ion implant (F1)** = surface-peaked → buried.
- **Contacts:** direct metal → **self-aligned silicide (F2)** = lower series R.
- **Gate dielectric:** thermal SiO₂ (today) → **high-κ/metal gate (F3, 2007)** = leakage wall → HfO₂.
- **Interconnect:** subtractive Al → **Cu dual-damascene (F4, 1997)** → Ru semi-damascene (3 nm) = the RC-delay wall.
- **Channel strain:** relaxed Si → **SiGe S/D (F5, ~2004)** = mobility boost.
- **Device geometry:** planar → FinFET (2011) → GAA nanosheet (2022) — **F9, gated on the 3-D engine.**

Building F1–F4 in order lets the educational mode walk the student from 1959 to ~2010 as *process
modernisation*, each step motivated by a wall the previous era hit — history delivered through physics
the sim actually runs, not narrated decoration.

## Deferred, and why (the spine — honest NO's)

- **FinFET/GAA (F9), EUV (F10)** — deferred for want of a discriminating consumer *today*. F9 needs the
  3-D engine (B1); F10 adds no observable litho doesn't already have.
- **CMP (F8) — promoted off this list 2026-08-10, and BUILT 2026-09-06.** It was fenced behind "nothing
  reads a layer thickness"; the F4 build made `R ∝ 1/(W·H)` electrical, so the trigger recorded for
  backlog D2 fired and F8 moved up to the promotable section. The *second* gate written here after that
  — "F4's geometry is one house line, so per-die dishing needs the cross-section to become a per-die
  quantity" — **was false when re-checked against the tree**: `delay()` already took the geometry as an
  argument. Kept written down because the pattern is the lesson: a released gate is worth as much as a
  set one, and **both** of this entry's gates were found released by someone going to build, never by a test.
- **LOCOS/STI (F7) — COMPLETE (2026-09-06).** The latchup observable shipped as B12, and with it the
  reason the remainder sat here at all. What the build settled that the prose above did not: latchup is a
  **wafer** property in this model, not a die one — the only condition that discriminates rides substrate
  resistivity, one number per wafer — and the *gain* condition never discriminates at all, so the
  isolation scheme moves a quantity that cannot cost a part. **Still deferred:** the STI trench
  etch/fill process itself, now for a sharper reason than "no consumer" — it would add no observable
  B12 has not already delivered. Original entry:
- **LOCOS/STI (F7) — bird's-beak BUILT (2026-07-10) as historical-mode B5** (`locos_history.py`): under
  the 2026-07-03 pedagogical-consumer reframing, the **active-pitch wall** (min active pitch ∝ field-oxide;
  STI clears it) *is* the consumer that the "geometry-only" framing had marked as too weak. The 2-D engine's
  2nd consumer. **Still deferred:** the STI process itself and a latchup electrical observable.
- **Alloy / grown / mesa historical *device structures*** — deferred: they are device *geometries* with no
  planar-observable consumer. The history they carry is delivered by the **predep→implant profile
  contrast (F1)**, not by new structures — the same reasoning that keeps the backlog's device-geometry
  edges deferred.
