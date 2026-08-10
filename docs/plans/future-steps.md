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
| **F5** | **SiGe strained source/drain** | ~2004 (90nm): strain era | **mobility → `I_Dsat`** (~2 GPa @ 20% Ge → up to 100% hole-µ) | PROMOTABLE — needs a µ-model in `device.py`; advanced-node |
| **F6** | **Epitaxy (buried layer / retrograde well)** | bipolar epi; CMOS wells | retrograde profile — **overlaps implant F1** | COUPLED to F1 — defer standalone |
| **F7** | **Isolation: LOCOS → STI** | LOCOS (1970s) → STI (1998) | bird's-beak narrows active width → geometry; latchup | **✅ bird's-beak BUILT (2026-07-10) as historical-mode B5** (`locos_history.py`); STI/latchup still deferred |
| **F8** | **CMP / planarity** | enables Cu damascene | post-CMP thickness → `R ∝ 1/(W·H)` → `τ_wire` → the delay bins — **the reader F4 built** | **UNBLOCKED by F4 (2026-08-10)** — the D2 trigger fired. Remaining gate is narrower: F4's wire geometry is one house line, so CMP needs the cross-section to become a **per-die** quantity |
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
5. **F5 — SiGe strained S/D** — **now the head of the queue**, once a mobility model exists in `device.py`
   (strain → µ → `I_Dsat`).
6. **F8 — CMP / planarity** — **unblocked by F4**, which gave layer thickness its first reader. Its
   remaining gate is structural rather than conceptual: F4's wire geometry is a module-level house line
   (the game knob is metal-only), so a per-die dishing/erosion variation needs the cross-section to become
   a per-die quantity first.

Recommendation: **F1 → F2 → F3 → F4** — all four shipped. **F5 or F8 is next**, and the choice is a real
one: F5 is the next *era* rung and needs new device physics; F8 is cheaper and now has the consumer F4
just built for it.

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
- **CMP (F8) — no longer on this list (2026-08-10).** It was fenced behind "nothing reads a layer
  thickness"; the F4 build made `R ∝ 1/(W·H)` electrical, so the trigger recorded for backlog D2 has
  fired and F8 moved up to the promotable section. Its remaining gate is a *shape* problem rather than a
  missing consumer: F4's geometry is one house line, so per-die dishing/erosion needs the cross-section to
  become a per-die quantity. Kept written down here because a released gate is worth as much as a set one.
- **LOCOS/STI (F7) — bird's-beak now BUILT (2026-07-10) as historical-mode B5** (`locos_history.py`): under
  the 2026-07-03 pedagogical-consumer reframing, the **active-pitch wall** (min active pitch ∝ field-oxide;
  STI clears it) *is* the consumer that the "geometry-only" framing had marked as too weak. The 2-D engine's
  2nd consumer. **Still deferred:** the STI process itself and a latchup electrical observable.
- **Alloy / grown / mesa historical *device structures*** — deferred: they are device *geometries* with no
  planar-observable consumer. The history they carry is delivered by the **predep→implant profile
  contrast (F1)**, not by new structures — the same reasoning that keeps the backlog's device-geometry
  edges deferred.
