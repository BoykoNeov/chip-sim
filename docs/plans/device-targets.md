# Plan — device targets ("good is relative": multi-target specs + disposition)

Today every wafer in `fab_game` is judged against **one** notion of "good" — a single `DEFAULT_SPECS`
(`fab_game/spec.py`): a fast-logic MOSFET (high `I_Dsat`, tight low-ish `V_t`, thin oxide). This plan adds
the lesson the user asked for: **"good" is application-relative.** The *same* physical property that ruins a
part for one product is a *feature* for another — high `V_t` (slow logic, but low-leakage mobile), thick
oxide (starved logic drive, but high-voltage I/O tolerance), short carrier lifetime (junction leakage for
logic, fast reverse-recovery for a power rectifier). Pedagogically this is the central DTCO lesson; in the
game it is a **declare-a-target** strategy layer plus a **disposition/salvage** mechanic on the drifted tail.

Decided in conversation **2026-06-15** (user steer + advisor pressure-test). This is a **phased** build,
deliberately *not* clumped onto the oxide stage — the sign-inverting properties are spread across **growth,
diffusion, oxidation, and contamination** (see the inversion table). New physics is permitted (the user
asked for variety/richness) but **rationed one slice at a time**, and every new device output stays *cited*
(Sze), not house-fudged, to match the repo's cited-physics-vs-flagged-numbers discipline.

## What's already graded (this is NOT pure pass/fail)

Three graded layers already sit under the binary verdict — worth stating so the new work doesn't reinvent
them:

- **Yield** is continuous (per-die Poisson defects; the ok→rework→fail *spatial* spectrum — edge rings /
  centre cores from the journey stages).
- **Speed binning** (`SpeedBins`/`SpeedBin` in `spec.py`, priced in `scoring.py`): a die that passes every
  window is graded by `I_Dsat` into **premium / typical / value**, or **binned out** (a *working but
  out-of-grade* part that doesn't ship). That bin-out **is** "functional but suboptimal" — already built, as
  a single-axis grade on `I_Dsat`.

So the user's *first* idea ("functional but suboptimal") exists. The **new** lever is the *second* one:
multiple product targets with **different — partially inverted — spec windows** scoring the *same* wafer.

## The real-world line (the honest framing — advisor-confirmed 2026-06-15)

The user probed "declare-a-primary + harvest-the-tail — is that real?" It is, with a correction that
*sharpens* the feature rather than killing it. Four claims, graded by reality:

- **Declare-a-primary (pick a flavor up front, tune the recipe for it): real.** Foundries ship process
  *variants* (low-power / high-perf / general-purpose families); the customer commits at tapeout. This is
  the spine and matches the user's "up-front declaration" choice.
- **Down-bin within the declared product: real and ubiquitous** (speed bins, fuse-down). Already built
  (`SpeedBins`).
- **Re-grade an *off-target lot* to a different spec of the *same device family*: real — but the salvage /
  exception path,** not the main loop. It is literally *engineering disposition / material-review-board*
  ("use-as-is or re-grade rather than scrap").
- **Reassign a *finished* wafer to a *fundamentally different device* (logic wafer → power rectifier): NOT
  real.** The mask set commits the device structure from lithography on. You cannot post-hoc decide a logic
  wafer is a vertical power diode.

**Consequence → a two-level declaration** (this is the design's backbone):

1. **Device family** — sets the mask / structure / downstream. **Committed up front; cannot be salvaged
   across.** (the MOSFET family vs the power-device family.)
2. **Flavor within a family** — logic ↔ low-power ↔ HV-I/O share a base flow, differ by oxide + implants +
   junction. An off-target lot **can** be dispositioned to a sibling flavor. **This is where "harvest the
   tail" honestly lives.** A genuinely different device (the power rectifier) is its own **declared run**,
   never a harvest of a logic wafer.

## The inversion table (the variety — spread across steps, not clumped on oxide)

All five sign-claims were advisor-checked (real, citable). They deliberately land on different stages:

| step | property (already modeled) | logic wants | the other target wants | kind |
|------|----------------------------|-------------|------------------------|------|
| **Growth** (melt doping, G2) | substrate resistivity / `N_A` | low-R | **high-resistivity** → high breakdown (HV / power / RF) | cross-target |
| **Growth** (oxygen, C1) | interstitial `O_i` / thermal donors | low (no `V_t` shift) | **high** → internal gettering (cleaner device) | **dual-use** |
| **Diffusion** (S/D, Ph4) | junction depth `x_j` | shallow (short channel) | **deep** → higher breakdown, lower R | cross-target |
| **Oxidation** (Ph5) | `t_ox` | thin (drive) | **thick** → HV tolerance, low gate leakage | cross-target |
| **Lifetime** (G4b) | deep-level metals / τ | killer → leakage | **short τ** → fast reverse recovery (rectifier) | cross-target |

**Two *kinds* of inversion — keep them separate (advisor's structural catch).** The **cross-target** rows
(resistivity / junction / oxide / lifetime) are *market segmentation* — good for A, bad for B — and they
power the multi-target mechanic. The **dual-use** row (oxygen: thermal-donors-*bad* **and**
internal-gettering-*good* **within one device**) is a *process-trade-off* lesson, **not** segmentation.
Filing it under the same mechanic muddies the design; it gets its own slice and its own framing.

**Physics tripwire for the new outputs (advisor).** When breakdown lands: do **not** conflate **gate-oxide
dielectric breakdown** (~10 MV/cm in SiO₂) with **junction avalanche breakdown** (BV ∝ `N^(−3/4)`, `E_crit`
~3×10⁵ V/cm in Si). Both point "thicker / lighter doping = more robust" for the HV target, but they are
*different mechanisms*. Both are citable (Sze); reverse recovery `t_rr ∝` minority-carrier lifetime (Sze).
Keep them cited models with their own source memories, not house numbers.

## The two empirical gates (verify FIRST, the way phase 5's two-sided window was verified)

Before building any mechanic on top, prove these two — they are what make the feature *teach* instead of
*decorate*, and each is the **first test** of its slice:

1. **The target windows genuinely *cross*** — partially disjoint, **not** nested. If logic ⊂ low-power, the
   re-grade is trivial (every logic-good die is also low-power-good) and teaches nothing. Concretely: logic
   `V_t ∈ [0.45, 0.68]`, low-power `V_t ∈ [0.60, 0.85]` — overlap only `[0.60, 0.68]`. A `V_t = 0.75` wafer
   is low-power-**premium** / logic-**reject**; a `V_t = 0.50` wafer is logic-**good** / low-power-**reject**
   (too leaky). Assert the **crossing region exists**, not just the bounds.
2. **The up-front declaration actually *moves the recipe optimum*** — a different declared target → a
   different best (cut depth / oxide time / predep dose). If the optimum doesn't move, declaration is
   cosmetic relabeling, not strategy. (e.g. low-power's optimum *wants* the deeper cut / thicker oxide that
   logic punishes — the phase-5 over-oxidation corner that *starves logic* is the low-power/HV sweet spot.)

## Agency & mode (the user's steer, 2026-06-15)

- **Maximize player agency now; narrow later.** "Easier to limit choices later than to reapply them
  retroactively." The player **picks** the disposition (the pick is where "good is relative" lands) and
  **declares** the target up front.
- **Don't leave the player alone — guide in educational mode.** The educational `guide.py` panel explains
  each readout *relative to the declared target* (a `V_t` that's "high" is good or bad depending on the
  flavor) and walks the disposition choice. Hardcore stays byte-identical (presentation-only, the established
  two-flag pattern).

## Staged build (one journey-phase-sized slice each — no clumping)

| Slice | Adds | New physics? | Headline |
|-------|------|--------------|----------|
| **1** | `DeviceTarget` abstraction + up-front declaration + disposition readout | **none** | the spine — built on the *proven* logic↔low-power `V_t`/`t_ox` crossing |
| **2** | HV-I/O flavor + cited junction **avalanche breakdown** output | one cited output | the junction-depth axis (diffusion step) |
| **3** | substrate-**resistivity** inversion at the growth step | reads existing `N_A` (+ BV) | high-res for HV / RF |
| **4** | the oxygen **dual-use** trade-off (donors-bad vs gettering-good) | a gettering / lifetime-robustness output | the *process-trade-off* lesson, kept distinct from segmentation |
| **5** | the **power-rectifier family** — own declared run, lifetime-killer-as-feature | cited `t_rr ∝ τ` reverse-recovery | the richest inversion, last |

**Slice 1 is the zero-new-physics spine** and the only one fully specified here; later slices are
fill-in-the-blanks once the spine lands and the user reacts to the whole loop.

**Build status (2026-06-15):** Slices **1 and 2 BUILT.** Slice 2 (HV-I/O + cited junction avalanche `BV`,
`chip/breakdown.py`) landed with a structural correction worth recording: in this **long-channel** device
model the junction-depth axis does **not** cross fast-logic (a deeper junction is fast-logic-neutral-to-good
*and* HV-good — the table's "shallow = logic" rationale is the short-channel effect `device.py` omits). The
reframe (advisor): **`x_j` is not the crossing axis — it is the axis that *decouples* `BV` from `V_t`** (the
curvature term lets two wafers with identical `V_t` have different `BV`). So the fast-logic↔HV cross rides
the V_t/oxide axis (HV is the highest-`V_t` flavor, crossing low-power from above), and `BV` is an
*orthogonal* acceptance floor gated by the diffusion drive-in. `BV` was **derived from first principles**
(the cited ionization integral over the cylindrical field), not an empirical curvature fit — see
`memory: avalanche-breakdown-source`. **Slice 3 next** = the substrate-resistivity inversion (turns `BV`'s
*other* knob, `N_A`, for a genuine high-voltage part).

### Slice 1 — the spine (zero new physics)

- **`DeviceTarget`** (new, `fab_game/targets.py` or extend `spec.py`): a named target = a `SpecSet` + a
  `SpeedBins` policy + a price curve (`scoring.py`-style, flagged house $) + a **recipe-optimum hint** (which
  knob direction this target rewards). The incumbent `DEFAULT_SPECS` becomes the **`FAST_LOGIC`** target;
  add **`LOW_POWER`** with the *crossing* `V_t` window above.
- **Up-front declaration**: the player/`GameConfig`/journey declares a target; `finish`/`score_wafer` score
  against the **declared** target's windows + bins + prices (today they hardcode `DEFAULT_SPECS` +
  `BIN_PRICES`).
- **Disposition readout**: score the finished wafer against the *sibling flavors too*, and surface "your lot
  drifted off `FAST_LOGIC`; it dispositions to `LOW_POWER` at X% yield / $Y" — the player **picks** the SKU.
  Whole-wafer unit (the honest re-grade unit; not die-cherry-picking across products — see the real-world
  line above).
- **Tests = the two gates first** (crossing region exists; declared optimum moves), then bookkeeping
  (disposition revenue closes, monotonicity) and the **seam** (declaring `FAST_LOGIC` with the default bins
  reproduces today's score bit-for-bit — the G1–G7 banked demos unchanged).

## Deferred / open (explicit)

- **Slices 3–5** — specified only at the table granularity above; each built when the spine has landed and
  the loop has been reacted to (the repo's one-slice-at-a-time discipline). (Slices 1–2 built.)
- **Cited-source memories** for the new outputs — avalanche BV **written** (`avalanche-breakdown-source`,
  slice 2); reverse recovery / internal gettering to come with their slices (the repo's `*-source` pattern).
- **The economics overlap** — `docs/plans/fab-journey.md`'s #1 open item (the per-pass / throughput cost
  side) intersects here: per-target price curves are part of the cost side. Coordinate so the two don't
  diverge.
- **On-die multi-V_t libraries** (HVT/SVT/LVT on one die via implant masks) are **design-time**, not
  post-hoc disposition — a *different* mechanism; explicitly **not** this plan's salvage loop.

## References

- ADR 0005 — the fab-game layering (`fab_game → chip`, one-way).
- `docs/plans/fab-journey.md` — the staged journey (phases 1–5 built; the stages whose outputs invert).
- `docs/plans/fab-game.md` — the G1–G7 line build (the physics being re-scored).
- `docs/plans/scope-edge-backlog.md` — the anti-over-build bar (new physics needs a consumer; here the
  consumer is the multi-target score).
- `fab_game/spec.py` (`SpecSet`/`SpeedBins`), `fab_game/scoring.py` (the priced bins) — the existing
  single-target machinery this generalizes.
- memory: `gradual-failure-preferred`, `fab-game`, `fab-journey`. Cited-physics to come: Sze (avalanche BV,
  reverse recovery), the existing C1 oxygen / G4b lifetime source memories.
