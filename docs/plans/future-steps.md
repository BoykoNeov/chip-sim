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
| **F3** | **High-κ gate dielectric** | 2007 (45nm): SiO₂ → HfO₂ | **gate tunneling leakage** (exp in `t_phys`) vs **`C_ox`** (linear in EOT) — one thickness, two currencies | **🔨 SLICES 1–2 BUILT (2026-07-15/17)** (`chip/high_k.py` + the `dielectric` knob/wiring) — EOT identity + per-material WKB tunneling, now proved end-to-end through the untouched `device.py`. Remaining: history mode + demo, IL slice |
| **F4** | **BEOL interconnect (RC delay)** | Al → **Cu damascene (1997)** → Ru (3nm) | **new output: chip speed limited by wire RC, not the transistor** | **PROMOTABLE — best history arc, biggest build** |
| **F5** | **SiGe strained source/drain** | ~2004 (90nm): strain era | **mobility → `I_Dsat`** (~2 GPa @ 20% Ge → up to 100% hole-µ) | PROMOTABLE — needs a µ-model in `device.py`; advanced-node |
| **F6** | **Epitaxy (buried layer / retrograde well)** | bipolar epi; CMOS wells | retrograde profile — **overlaps implant F1** | COUPLED to F1 — defer standalone |
| **F7** | **Isolation: LOCOS → STI** | LOCOS (1970s) → STI (1998) | bird's-beak narrows active width → geometry; latchup | **✅ bird's-beak BUILT (2026-07-10) as historical-mode B5** (`locos_history.py`); STI/latchup still deferred |
| **F8** | **CMP / planarity** | enables Cu damascene | nothing reads layer thickness — **unblocks only after F4** | DEFERRED (backlog D2) — reevaluate post-F4 |
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
3. **F3 — high-κ / metal gate**, *or* **F4 — BEOL interconnect** — the first genuinely *new output*
   decision:
   - **F3** modernises the oxide stage: it adds a **gate-tunneling-leakage** observable (why SiO₂ stopped
     scaling at ~1.2 nm → HfO₂ at higher physical thickness, same EOT). Contained, teaches the `SiO₂→high-κ`
     contrast, reuses the oxide/`t_ox` machinery.
   - **F4** adds a **back-end output the sim has never had**: chip speed set by interconnect `RC`, not the
     transistor — plus the richest history arc (subtractive Al → Cu dual-damascene 1997 + CMP → Ru
     semi-damascene at 3 nm). Bigger build; also *unblocks CMP (F8)* by giving layer-thickness a consumer.
4. **F5 — SiGe strained S/D** once a mobility model exists in `device.py` (strain → µ → `I_Dsat`).

Recommendation: **F1 → F2 → F3 → F4**, deciding F3-vs-F4 order at the time by whether we want the
contained oxide-successor (F3) or to open the back-end (F4). F2 is unambiguously the right second step —
its consumer is already wired.

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

- **CMP (F8), FinFET/GAA (F9), EUV (F10)** — deferred for want of a discriminating consumer *today*. F8
  unblocks after F4 (multi-metal gives layer thickness a reader); F9 needs the 3-D engine (B1); F10 adds
  no observable litho doesn't already have.
- **LOCOS/STI (F7) — bird's-beak now BUILT (2026-07-10) as historical-mode B5** (`locos_history.py`): under
  the 2026-07-03 pedagogical-consumer reframing, the **active-pitch wall** (min active pitch ∝ field-oxide;
  STI clears it) *is* the consumer that the "geometry-only" framing had marked as too weak. The 2-D engine's
  2nd consumer. **Still deferred:** the STI process itself and a latchup electrical observable.
- **Alloy / grown / mesa historical *device structures*** — deferred: they are device *geometries* with no
  planar-observable consumer. The history they carry is delivered by the **predep→implant profile
  contrast (F1)**, not by new structures — the same reasoning that keeps the backlog's device-geometry
  edges deferred.
