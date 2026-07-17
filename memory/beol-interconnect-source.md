---
name: beol-interconnect-source
description: "F4 BEOL interconnect RC: cited c_pul≈2 pF/cm AND its geometry-invariance (coax↔80nm line), Al/Cu/Ru ρ₀+λ, the ρ₀λ scaling FOM (Ru≈Cu, NOT better), the 2-3nm barrier floor, IBM 1997 dual-damascene, the mid-90s gate≈wire crossover"
metadata:
  node_type: memory
  type: reference
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

* **S4 IS NOT A Ru-ONLY SLICE (caught at S1 review).** The `bulk_regime_ok` guard **fires on copper's own
  crossover**: Cu's operating point is ~0.167 µm but the bulk model wants W > ~0.19 µm (5λ) ⇒ the size
  effect is already a ~20% correction there. Physically right and historically exact — **the size effect
  became a *copper* problem at sub-200 nm, long before Ru was on any roadmap.** S1 may still speak about
  the Al→Cu **era** (250 nm, comfortably bulk); S4 owns sub-200 nm, **for Cu as well as Ru**.

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
