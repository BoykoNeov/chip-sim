# Plan — historical modes (the backward axis: period limitations of what we already model)

**The discriminating observable, stated first (the axis's licence):** every process in the sim runs in
its *modern* configuration. A **historical mode** re-runs an existing process (or adds a period process)
under the **limitation that motivated its successor**, and the deliverable **is that contrast** —
"here is the period result, here is the wall it hit, here is why the modern version replaced it." A
historical mode earns its place iff the limitation is **observable in a quantity the sim already
computes** (CD, `x_j`, `V_t`, leakage, active width, thermal budget). If the period variant produces the
same numbers as the modern one, or the difference shows up in nothing, it is a footnote in a source
memory — **not code**.

Decided in conversation **2026-07-10** (user steer + this plan). This is the **complement** of
`future-steps.md`: that doc modernises *forward* (each step adds a newer observable); this doc looks
*backward* (each mode shows an older limitation on an observable we already have). They share one
timeline spine — the game's "what broke and what replaced it."

## The consumer discipline, relaxed (the answer to "modes with no consumer")

The standing bar — *no regime without a consumer that discriminates* (the v1.6 "build explicit, NOT 2-D"
lesson) — does **not** disappear for history; it **relaxes into a weaker, shared consumer**. The bar was
never "consumer or don't build," it was "**observable by something, or dead capability.**" A deferred
*engine regime* (3-D) with no consumer is dead — nothing can see it work. A historical *mode's* entire
deliverable is a **displayable contrast** — cheap to show, worthless if unshown. So three tiers:

- **Tier 1 — has a real device/yield consumer already.** Build anytime; the limitation is read by an
  existing observable (e.g. HCl-oxidation → `Q_ox` → `V_t`; Al spiking → `x_j` → leakage). Same bar as
  any physics slice.
- **Tier 2 — no dedicated consumer, but the limitation is displayable.** Build **only after** the shared
  consumer exists. That shared consumer is the **era display surface (Chunk H0)** — a
  history/"why-it-was-replaced" gallery page + notebook cell that reads the contrast. Standing it up once
  retroactively justifies *every* Tier-2 mode: each stops being "no consumer" and becomes "feeds the
  timeline." **This is the honest way to build the consumer-less modes** — you pay for the consumer once,
  up front.
- **Tier 3 — no consumer and the limitation is not observable.** **Do not build.** If a period variant
  can't be made to *show* its limitation in a quantity the sim computes, it's pure completeness — the
  trap. It stays a named NO (see the deferred list).

**Ordering rule that falls out:** H0 first (it legitimises the Tier-2 modes the user asked about), then
Tier-1 modes (real consumers, buildable regardless), then Tier-2 modes (surface-fed).

## The seam (every mode is opt-in; modern default is byte-identical)

Established discipline, unchanged (cf. `implant=None`, `boost=None`, `Q_ox=0`, `drivein_program`): each
historical mode is an **opt-in flag whose default reproduces the modern result bit-for-bit**. A period
mode is never a global switch — it is a parameter on the relevant process (`OxidationKnobs.ambient`,
`Litho.tool`, `Resist.chemistry`, `Metal.barrier`, …) that defaults to the current behaviour. Default off
⇒ the entire existing suite is byte-identical.

## Triad tiers (the honesty ladder, per mode)

- **Tight:** the seam (mode=modern ⇒ byte-identical); any conservation the reused engine already
  guarantees (dose, oxidant mass); the **sign/topology of the limitation** (proximity blur *widens* the
  image; swelling *degrades* CD; spiking *shorts* the shallower junction) — the discriminator,
  sign-robust.
- **Flagged:** the period *magnitudes* — gap-blur amplitude, swelling factor, spiking depth coefficient,
  HCl gettering efficiency — house-calibrated against cited period data, named not asserted exact.

---

## The chunks

Each chunk is independent after H0. Tier-1 chunks (A3, B6, A1) can be built before H0 if desired; Tier-2
chunks (A2, A4, B5) are gated on H0.

### H0 — Era display surface (the shared consumer) · Tier-0, build first

The one piece with **no physics** — a display surface that reads any historical-mode contrast and lays it
on the timeline. Consumer for every Tier-2 mode.

- **Deliverable:** a `history`/timeline gallery page (`docs/history.html` + `.local.html`, from a new
  `chip/history_gallery.py` or a `fab_game/` section — decide at build against the existing gallery
  split) + a notebook cell. Renders, for each built mode, the **modern-vs-period** figure and the
  one-line "wall it hit / what replaced it."
- **Reuses:** the existing gallery machinery (`chip/gallery.py`, `fab_game/gallery.py`) and its
  golden-test harness — a *fourth* page pair alongside the two galleries (keep the public/`.local` split;
  golden-test it; don't mix github↔localhost — the standing gallery rule).
- **Seam:** additive; no existing page changes. Golden test the new pages.
- **Why first:** it is the shared consumer that converts the user's "modes with no consumer" from
  un-buildable into buildable. Without it, A2/A4/B5 have nothing to read them.

### A1 — Pre-implant diffusion doping: the dose-control wall · Tier-1 (implant-contrast consumer) — ✅ BUILT (2026-07-10)

Reuses the diffusion engine + Trumbore solubility (`N_s` Dirichlet) + the predep dose identity. The sim
**already** is a ~1968 predep line, so the surface-peaked-vs-buried *depth* contrast is *already delivered
by implant* (`ion-implantation.md`). A1 delivers the distinct, sharper limitation:

- **The dose-control wall (the discriminator — NOT depth).** The two-step predep→drive-in *can* partly
  decouple dose from junction depth (predep sets `Q`, the sealed drive-in deepens `x_j` at ~fixed `Q`), so
  the earlier "dose∝depth can't decouple" framing was **loose** — depth is not the wall. The real wall is
  **dose *controllability***: the surface floods at the solid-solubility limit `N_s` (a Trumbore material
  constant, *not* a free knob), so a constant source cannot reproducibly meter a **light** dose — laying
  `Q = 5e11` of boron at `N_s = 3e20` needs a sub-millisecond predep. `demo_implant.py` "matched" that light
  dose only by tuning `N_s` *below* solubility (the cheat); A1 is the honest accounting. Implant meters
  dose electrically (beam charge), depth set *independently* by energy — the decoupling that won.
- **Honesty:** the wall is a **FLAGGED controllability proxy** (`predep_dose_floor = 1.128·N_s·√(D·t_min)`),
  sign-robust only across an explicit `(T_predep, t_min)` box (the demo/tests state it: `{800,900}°C ×
  {0.1,1}s` → boron floor `7e11…1.1e13`, above the `5e11` target with margin). The **tight** legs are the
  predep dose identity and the **seam** (a constant source at solubility reproduces `predeposit` bit-for-bit).
- **Historical source variants** (period texture): `DopingSource` registry — POCl₃/BBr₃ (constant, pinned
  at solubility) + spin-on-glass (limited/finite source, meters a lower dose — the pre-implant *workaround*,
  but imprecise, no independent depth). The *one* real physics axis is constant vs limited source.
- **Built as** a pure additive consumer: `chip/doping_history.py` + `chip/demo_doping_history.py`
  (`chip-doping-history.png`) + `chip/tests/test_doping_history.py`; gallery card `hist·A1`. **Consumer:**
  the implant contrast (real) + (later) the H0 era surface. No engine change; no existing behaviour touched.

### A3 — Oxidation ambient variants · Tier-1 (real `Q_ox`→`V_t` and budget consumers)

Reuses Deal–Grove (`oxidation.py`). Two period ambients, each with a **real** consumer:

- **HCl / chlorine-added oxidation (1970s):** chlorine getters mobile Na at the interface → **lowers
  `Q_ox`** → feeds the *existing* Na→`Q_ox`→`V_t` chain (G4a). This is a real device consumer, not just
  the surface. The limitation it cures: pre-HCl gate oxides drifted (mobile-ion instability).
- **High-pressure oxidation:** `B ∝ pressure` → same oxide at **lower thermal budget** → feeds the
  existing `∫D dt` budget (E1). The limitation it addresses: thick isolation oxides cost too much
  diffusion budget at 1 atm.
- **Consumer:** `Q_ox`→`V_t` (HCl) and `∫D dt` budget (HP) — both real. **Seam:** `ambient="dry"/"wet"`
  default (no Cl, 1 atm) ⇒ current Deal–Grove bit-for-bit. **Cited:** Cl gettering efficiency (flagged),
  HP linear-rate pressure scaling.

### B6 — Aluminum junction spiking · Tier-1 (real `x_j`→leakage consumer)

The coupling is the payload: Al–Si eutectic (577 °C) → Al consumes Si → **spikes through shallow
junctions**, and *the shallower the junction (which implant enables), the worse the spike* → junction
short → leakage. Motivates Al–Si, then barrier metals, then damascene Cu.

- **Model:** spiking depth as a function of anneal `T`/time and local Si solubility in Al; if spike depth
  > `x_j` → the junction shorts. Reads `junction.junction_depth` (from diffusion/implant), writes through
  `lifetime.py`'s leakage channel (the shorted-diode failure, mirror of the A1 dislocation / G4b metal
  plugs).
- **Consumer:** `x_j` → `device_leakage.j_leak` (real). **Seam:** `barrier="none"` default *modern* =
  barrier metal present ⇒ no spiking, current result; `barrier=None`/period-Al opt-in enables it.
  **Cited:** Al–Si eutectic T, Si solubility in Al; spiking-depth coefficient flagged.

### A2 — Lithography tool & wavelength progression · Tier-2 (surface + CD/NILS)

Reuses the aerial-image / partial-coherence model (`litho.py`). The period ladder, each rung a wall:

- **Printing mode:** contact (mask wear, defect printing) → proximity (**gap-diffraction blur** `≈√(λg)`
  degrades CD) → projection (today). The proximity blur is the displayable limitation on the existing CD
  observable.
- **Wavelength ladder:** g-line 436 → i-line 365 → KrF 248 → ArF 193 → 193i → EUV 13.5 — each moves the
  Rayleigh CD floor the sim already computes (`k₁λ/NA`). The contrast: same feature, different era
  wavelength, different printability.
- **Consumer:** era surface + the CD / NILS observables litho already computes. **Seam:** `tool="projection"`,
  current `λ`/NA default ⇒ litho bit-for-bit. **Cited:** gap-blur form, the wavelength/NA table per node.

### A4 — Photoresist generations · Tier-2 (surface + CD)

Reuses the PEB/CAR machinery (`litho.py` §8/§9). The resist ladder:

- **Negative resist (Kodak KTFR):** solvent-development **swelling** distorts and bridges fine features →
  a resolution floor. The swelling is the displayable limitation on CD.
- **Positive DQN/novolak:** no swell → better CD → the successor. **CAR (v1.9, already built):** the DUV
  successor (amplification for dose).
- **Consumer:** era surface + CD. **Seam:** `chemistry="car"`/positive default ⇒ current develop
  bit-for-bit; `chemistry="negative"` opt-in adds the swelling term. **Cited:** swelling factor (flagged),
  the negative→positive→CAR generational contrast.

### B5 — LOCOS isolation & the bird's beak · Tier-2 (surface + active-width geometry; feeds the 2-D engine)

The one chunk that gives the **underused 2-D oxidation/diffusion regime** (v1.8/v1.11) a consumer.
Oxidation under a nitride mask → lateral oxidant encroachment → the classic **bird's beak** that eats
active area → motivated STI (F7 in `future-steps.md`, deferred there for want of a consumer — B5 is its
*historical/displayable* form).

- **Model:** 2-D Deal–Grove under a masked edge; the lateral encroachment length narrows the drawn active
  width. Reuses `engines.diffusion/diffusion2d.py` + the oxidation constants.
- **Consumer:** era surface + active-width geometry (the weak-but-displayable geometry consumer F7
  lacked). **Seam:** planar (no nitride mask) ⇒ current 1-D oxide bit-for-bit. **Cited:** bird's-beak
  encroachment ratio vs field-oxide thickness (flagged).

---

## Phasing (chunks, anti-over-build)

1. **Tier-1 (real consumers — buildable *without* H0, since each ships its own `chip/demo_*.py` and
   surfaces in the glob-anchored physics gallery):** **A1** (doping-source dose-control wall → implant
   contrast) — ✅ BUILT; **A3** (HCl/HP oxidation → `Q_ox`/budget); **B6** (Al spiking → leakage).
2. **H0 — era display surface.** The shared consumer that unblocks the Tier-2 chunks; debuts *justified by
   built content* (A1 + implant + whatever Tier-1 landed), not one recycled figure.
3. **Tier-2 (surface-fed, gated on H0):** **A2** (litho tool/wavelength), **A4** (resist generations),
   **B5** (LOCOS bird's beak — also the 2-D engine's consumer).

**Recommended sequence (revised 2026-07-10 — A1-first, the anti-over-build ordering):**
**A1 ✅ → A3 → B6 → H0 → A2 → A4 → B5.** *(Superseded the earlier "H0 first": H0 only needs to precede the
Tier-2 chunks, not A1 — a Tier-1 mode surfaces in the physics gallery with no history page, so leading with
H0 would have made the first deliverable a display surface over one recycled figure, exactly the over-build
this repo rejects. Build the Tier-1 content first; stand up H0 once it has real tenants.)*

Each chunk: cited model class, triad tiers, opt-in seam, demo = the **modern-vs-period contrast figure**,
wired into H0's timeline.

## The historical/educational spine (shared with future-steps.md)

The forward axis (`future-steps.md`) and this backward axis meet in one timeline the game can walk:

- **Doping:** grown/alloy/mesa → planar predep (**A1 dose-control wall** — solubility-pinned, can't meter a
  light dose) → implant (F1, the successor). ← the two axes' handoff.
- **Oxidation:** drifting pre-HCl oxide → **HCl-gettered oxide (A3)**; 1-atm budget → high-pressure (A3).
- **Litho:** contact → proximity → projection; g-line → EUV (**A2**). Resist: negative-swell → positive →
  CAR (**A4**).
- **Isolation:** planar/implicit → **LOCOS bird's beak (B5)** → STI (F7 forward).
- **Metal:** period Al **spiking (B6)** → barrier metal → Cu damascene (F4 forward).

Backward axis shows *the wall each modern step was built to clear*; forward axis *builds the step*. Same
observables, opposite direction.

## Deferred, and why (Tier-3 — the honest NO's)

- **Grown-junction / alloy / mesa / point-contact device *structures*** — device *geometries* with no
  planar-observable consumer (same reasoning as `future-steps.md` and the implant plan). The doping
  history is carried by A1's profile/limitation contrast, not by new device geometry.
- **Germanium-era devices** — a different material system; no observable in the Si planar line reads it.
  A footnote, not a mode.
- **Tool mechanics with no observable difference** (specific aligner kinematics, wafer sizes, batch vs
  single-wafer) — production-history colour that changes no computed quantity. Source-memory footnotes.
- **Any period variant whose numbers equal the modern mode's** — fails the Tier-3 test by definition.
