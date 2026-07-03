# Plan — ion implantation (the buried peak predep physically cannot make)

**The discriminating observable, stated first (the build's licence):** thermal predep lays a
**monotonic, surface-peaked** profile — `N(x) = N_s·erfc(x/2√Dt)`, maximum *at the surface*, falling
away with depth. It is physically incapable of putting the dopant peak *below* the surface. Ion
implantation embeds ions at a **controlled depth** `R_p`, producing a **buried / retrograde** peak with
zero-slope-then-rising concentration near the surface. That buried peak — and the retrograde well and
V_t-adjust profile it enables — is an observable predep *cannot produce at all*, not a redundant second
route to the same `x_j`. This is why implant clears the repo's standing bar (**no regime without a
consumer that discriminates**, the v1.6 "build explicit, NOT 2-D" lesson) rather than being a big,
citable, but redundant gap.

Decided in conversation **2026-07-03** (user steer + advisor pressure-test). The user set the consumer
explicitly: **the game — historical processes, education.**

## The consumer (why this passes the bar)

Three consumers, in priority order:

1. **An educational game stage where you dope by implant (`dose` × `energy`) and *see* the buried
   profile.** The teaching payload *is* the contrast: the same recipe run through the old predep route
   vs the implant route yields visibly different profiles (surface-peaked vs buried), and only implant
   can hit a retrograde/V_t-adjust target. This is the game/education consumer the user named.
2. **`device.py:78`, a consumer the codebase already flagged as missing.** The comment reads *"A uniform
   substrate doping (a real V_t-adjust implant is …)"* — the current V_t model **fakes** the threshold-
   adjust implant with a uniform substrate offset. A real shallow buried implant is the honest source of
   that ΔV_t. This is a named, in-code consumer waiting for the feature — the single strongest
   justification.
3. **Damage → leakage**, wired through the **existing** `lifetime.py` channel (the same generation-
   leakage plug A1/G4b already use). Implantation damages the lattice; incomplete anneal leaves
   residual traps → reverse leakage. New contributor, existing observable surface.

## The historical framing (folded in, NOT a separate track)

The simulator, as it stands, **is a ~1968 thermal-predep planar line**: every doping step is predep +
drive-in (solid-solubility Dirichlet surface → sealed Neumann redistribution). That is exactly the
pre-implant process. Ion implantation (production silicon, early 1970s) is *the* step that modernised
it — "unlike diffusion, which results in surface-peaked profiles, implantation embeds at controlled
depths." So the predep→implant contrast **is** the historical/educational lesson; building implant
*delivers* the history rather than requiring separate alloy/grown/mesa-transistor modules (those are
device *structures* with no consumer in the current planar observables — they would fail this same bar).
The timeline the game can now teach: grown-junction (TI 1954) → alloy → double-diffused mesa
(Fairchild 1957) → **planar + oxide passivation (Hoerni 1959) = what we model today** → **ion implant =
the step this build adds.**

## Model class (citations pinned at build, named here)

- **Range statistics — LSS theory.** Lindhard–Scharff–Schiøtt: nuclear + electronic stopping give the
  first two moments — **projected range `R_p`** and **straggle `ΔR_p`**. Tabulated for B/P/As/Sb vs
  energy in **Gibbons, Johnson & Mylroie, *Projected Range Statistics*** (the canonical range tables).
  A first-cut profile is the **symmetric Gaussian** `N(x) = (Q/√(2π)ΔR_p)·exp(−(x−R_p)²/2ΔR_p²)`.
- **Profile shape — Pearson-IV.** The real as-implanted profile is skewed; the four-moment **Pearson
  distribution** family (moments = `R_p`, `ΔR_p`, **skewness γ**, **kurtosis β**) captures it, Pearson-IV
  being the workhorse branch for implanted dopants (B skews toward the surface). Start Gaussian (2
  moments), name Pearson-IV skew as the tightened form.
- **Channeling tail.** Along low-index axes ions penetrate far deeper than `R_p` → an exponential deep
  tail. A real **failure mode** (deeper-than-target junction → punchthrough), not a knob — modelled as a
  flagged deep-exponential add-on, suppressed by tilt (7° convention) / screen oxide / pre-amorphization.
- **Damage → leakage.** Displacement damage ∝ dose·(nuclear energy loss); residual after anneal feeds
  `1/τ += C·N_damage` in `lifetime.py` → `J_gen`. Amplitude flagged.
- **Anneal = the machinery we already have.** Post-implant drive/activation is the **E1/RTA thermal-
  budget path** (`DiffusionKnobs.drivein_program`, the `∫D dt` budget). Implant produces the *initial
  condition*; the existing drive-in redistributes and activates it. **No new solver.**

## The seam (byte-identical default; implant is a new initial condition)

`diffusion_dopant.py`'s drive-in already "starts from *that actual* profile" (the predep `erfc`), then
redistributes it through the sealed engine. **Implant slots in as an alternative initial condition:** a
buried Gaussian/Pearson peak at `R_p` replaces the surface `erfc`, and the **identical** drive-in solver
consumes it unchanged. The knob is **opt-in** (`DiffusionKnobs.implant=None` → the predep path runs
bit-for-bit; set `Implant(dose, energy, species, tilt)` → the buried IC). Default off ⇒ the entire
existing suite is byte-identical (the established seam discipline — cf. `drivein_program`, `boost=None`,
`Q_ox=0`).

## Triad tiers (the honesty ladder)

- **Tight (exact/analytic):** dose conservation `∫N dx = Q` through the buried-Gaussian IC (no-flux
  drive-in conserves it); the **seam** (implant=None ⇒ predep byte-identical); the Gaussian-IC → drive-in
  warm-start reduces to a known broadened Gaussian; the **buried-peak topology** (peak at depth > 0, `dN/dx
  > 0` shallower than `R_p`) — the discriminator, sign-robust.
- **Flagged (magnitude, house/calibrated):** absolute `R_p(E)`, `ΔR_p(E)` numbers (vs Gibbons tables —
  benchmark, coefficient-flagged); the channeling-tail amplitude; the damage→τ coefficient; Pearson-IV
  skew magnitude. Named, not asserted exact.

## Phasing (one slice at a time, anti-over-build)

1. **Slice 1 — buried Gaussian IC + seam + dose conservation + the buried-peak discriminator.** The core
   observable and the byte-identical default. Wire the game stage + `device.py` V_t-adjust consumer.
2. **Slice 2 — Pearson-IV skew** (the tightened profile form; B surface-skew).
3. **Slice 3 — channeling tail** as a failure mode (deep-tail → junction-too-deep), tilt/screen-oxide
   suppression.
4. **Slice 4 — damage → leakage** via `lifetime.py` (residual-after-anneal).

Each slice: cited model class, triad tiers, seam preserved, demo = the predep-vs-implant contrast figure.

## Scope edges (named, deferred — no consumer yet)

- **2-D lateral implant straggle under a mask edge** — would read `device_2d.py`; deferred until the game
  needs lateral profile (the 1-D depth profile is the teaching payload first).
- **Dose-dependent damage / amorphization threshold + solid-phase epitaxial regrowth kinetics** — deferred
  to the damage slice's flagged coefficient; full SPE regrowth has no consumer.
- **Pearson-IV → dual-Pearson (channeling + primary as two populations)** — deferred; single tail suffices.
- **Alloy/grown/mesa historical device *structures*** — deferred (no planar-observable consumer; the
  history is carried by the predep→implant profile contrast, not by new device geometry).
