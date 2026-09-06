---
name: latchup-source
description: "F7/B12 CMOS latchup — the two cited criteria (I·R>0.7 V trigger; β₁β₂>1 sustaining), the spacing→β sign trap, and why the gain condition does not discriminate in this model"
metadata: 
  node_type: memory
  type: reference
  originSessionId: b8a3cd30-8ce9-4a81-82ba-4c7854e2e482
  modified: 2026-09-06T11:05:26.662Z
---

**F7's remainder / historical mode B12** (`docs/plans/latchup-isolation-f7.md`, `chip/latchup.py`).
Web-verified 2026-09-06.

**Sources.** TU Graz (Hadley, *Latch-Up*, `lampz.tugraz.at/~hadley/psd/L13/latch-up/Latch-Up.html`) —
the primary; EDN/Planet Analog *Latchup and its prevention in CMOS* — the corroborator, and the
**discriminator** on one point below. STI depth (250–400 nm, 0.25/0.18 µm generations) from the
0.25/0.18 µm STI process literature.

**The two criteria, both cited verbatim, and they are INDEPENDENT:**
- **Sustaining:** `β_npn·β_pnp > 1` — "The product of the gains of the two parasitic transistors in
  the feedback loop, β₁×β₂, has to be greater than one to make latch-up possible."
- **Triggering:** `I·R_sub > 0.7 V` — "sufficient current flows through R_p to turn on the
  npn-transistor (I*Rp > 0.7 V)."

**THE LOAD-BEARING SEPARATION — do not couple them.** `R_sub` is injection-point→nearest **substrate
tap**; the spacing that sets β's base width is n⁺→well. *Different lengths*, and both sources list them
as separate levers. A model with `R_sub ∝ spacing` manufactures a sign reversal between the two
conditions that is an artifact of its own geometry lump. `chip/latchup.py` asserts the decoupling
mechanically (exact invariance both ways). See [[locos-birds-beak-source]] for the trap this mirrors.

**THE SIGN TRAP (recorded because it survives review).** TU Graz: *"Larger spacing … will increase the
base width and worsens the parasitic transistor."* "Worsens the parasitic transistor" = a **worse
transistor** = **LOWER β** = more immune. An automated summary of that page glossed it as *"thereby
increasing β"* — **inverted**. EDN settles it: *"Reduce beta by increasing device spacing."* A
plausible sentence about a real quantity pointing the wrong way.

**THE MODEL'S OWN ADMISSION (the S1 finding).** With emitter efficiency γ=1 and `W_B ≪ L`, the cited
transport form `β = 1/(cosh(W_B/L) − 1)` gives each β at 10²–10⁶ (product 10⁴–10¹²) against real
parasitic laterals of ~1–50. Cause is **physical, not numerical**: recombination is not what limits
these transistors — **geometry is** (the injected carrier goes *down*, not laterally; that collection
efficiency needs a 2-D structure the module lacks). So the **sustaining condition never discriminates**
and the **trigger condition is the binding one**. Agrees with the fact that every cited prevention
measure (epi substrate, guard rings, substrate taps) is a *resistance/collection* measure, not a
gain-killer — the module claims the agreement, **not** a derivation.

**Prevention directions, cited:** heavier substrate/well doping ⇒ lower R ⇒ higher trigger current
(retrograde wells named); epi = lightly-doped layer on a heavily-doped substrate; deep trenches "avoid
or weaken the parasitics"; guard rings and taps as carrier siphons. Holding voltage above supply ⇒
immune to *destructive* latchup — cited, **not computed** (needs the latched thyristor's on-state I–V).

**FLAGGED in the build:** `WELL_DEPTH_UM` (no well exists in this sim); `SUBSTRATE_TAP_PATH_UM` +
`TAP_CROSS_SECTION_UM2` (a calibration chosen so `R_sub` lands ≈940 Ω at 1e15 cm⁻³, trigger ≈0.75 mA)
⇒ **every headline must be a ratio in which they cancel**; the trench's `2×` detour on base width.

**The guard that rides with the lifetime axis:** a dirtier wafer has a weaker parasitic (`L=√(Dτ)`,
τ from [[fab-game-g4b]]) — but the *same* τ raises generation leakage, so latchup-vs-τ must **always**
be reported with the leakage at that τ. Immunity shown alone is a free lunch the model has not earned.
