# Memory index

Per-project memories for **chip-sim** (microchip simulator), extracted 2026-06-10 from the BigSim
program's shared memory at the monorepo split. Cross-cutting *program* memories stayed
in the BigSim archive, so some `[[links]]` in topic files dangle here by design.

One line per memory: a hook for relevance triage — full detail lives in each topic file. **Keep it
that way:** if a line starts carrying the finding instead of pointing at it, move the prose into
the topic file and cut the line back (this index has a hard read limit).

## Ways of working

- [Commit at end of batch](commit-at-end-of-batch.md) — **feedback (2026-06-10):** always commit AND push at batch end unasked; chip-sim → direct `git push origin main` (solo repo). Conventional msg + Co-Authored-By, fast lane green first; PRs still ask-first.
- [Gradual failure preferred](gradual-failure-preferred.md) — **feedback (2026-06-14):** model graded failure over a cliff when realistic; honest move = spatial non-uniformity of the offending quantity, the fudge = inflating an unrelated variable.
- [Chip notebook flake](chip-notebook-flake.md) — **project:** the slow `chip.ipynb` smoke test hangs ~80% in CI — an nbclient↔ipykernel-7.x race. `skipif(CI)` stays; THE PIN = `-n auto` fast lane only, full gate serial (never the notebook under xdist). Don't re-explore fewer workers.

## Engine & physics library

- [Engine unfrozen](engine-unfrozen.md) — **project (2026-06-10; framing RETIRED 2026-06-14):** `engines.diffusion` UNFROZEN (ADR 0004), then contract/seal ceremony DROPPED → plain tested library. Amendments: v1.5 `D(u)` Picard, v1.6 explicit θ=0, v1.8 2-D. 3-D = only deferred regime.
- [Engine explicit stepping v1.6](engine-explicit-stepping-v16.md) — **project (2026-06-11):** explicit `forward_euler` (θ=0) — real content = conditional-CFL invariant `dt_crit=1/max|diagᵢ|` (NOT textbook Δx²/2D). Advisor: build explicit, not 2-D (anti-over-build).
- [Lateral diffusion 2-D v1.8](lateral-diffusion-2d.md) — **project (2026-06-12):** the 2-D regime — `diffusion2d.py`, BE-only 5-point FV, the engine's LAST deferred regime. Additive; 34 invariants unmodified. Lateral/vertical ratio = LOOSE.
- [Chip coupling v1.2](chip-coupling-v12.md) — **project (v1.2):** Phase 1↔2 back-coupling (OED + dopant segregation) — both fit WITHIN the engine (OED=`D(t)`; segregation=Neumann flux). Swept-sliver edge retired via consumer-side receding mesh.
- [Chip high-conc D(N) v1.3](chip-highconc-v13.md) — **project (v1.3):** conc-dependent `D(N)` — numerics SUPERSEDED by v1.5 native `D(u)` Picard. Full-activation cap → physical ×42.
- [Chip 2-D device cross-section v1.11](chip-device-2d-v111.md) — **project (2026-06-12):** 2-D MOSFET cross-section (`chip/device_2d.py`) wires the v1.8 engine into Phase-4; `L_eff=L_drawn−2ΔL`. A VALIDATION deepening, not new physics; DIBL guarded out.
- [Chip defocus v1.4](litho-defocus-v14.md) — **project (v1.4):** defocus/DOF/Bossung (`litho.py` §7) — defocus = pure pupil PHASE, z=0 bit-for-bit seam. Assert the FUNDAMENTAL `4c₀c₁cosφ` → at φ=π/2 the image frequency-doubles.
- [Litho PEB v1.7](litho-peb-v17.md) — **project (2026-06-11):** PEB acid-diffusion blur (`litho.py` §8) — the resist back-end rides `engines.diffusion` (CN, consumer). σ=0 seam; the PEB window closes where the lens out-resolves the bake → why BARC.
- [Litho CAR v1.9](litho-car-v19.md) — **project (2026-06-12):** CAR reaction–diffusion PEB (`litho.py` §9) — INVERTS v1.7: a coupled two-field problem doesn't fit the single-field engine → consumer-side operator splitting (BE not CN). Develop on `1−m`.
- [Litho Zernike v1.10](litho-zernike-v110.md) — **project (2026-06-12):** Zernike aberrations (`litho.py` §10) — aberration = pupil PHASE. Trap: coma & defocus share `4c₀c₁cosφ`; the discriminator is `fundamental_complex` PHASE → coma = placement error. No Strehl.

## Roadmap slices (F) & historical modes

- [Historical-modes A1](historical-modes-a1.md) — **project (2026-07-10):** the NEW *backward* axis (period modes explain why the modern step won); 3-tier consumer bar; order A1→A3→B6→H0→A2→A4→B5. A1 = pre-implant **dose-control wall** (solubility-pinned `N_s` can't meter a light dose; NOT depth).
- [Historical-modes A2](historical-modes-a2.md) — **project (2026-07-10):** `litho_history.py`, the 1st Tier-2. §A wavelength ladder g-line→EUV, tight = `R=k₁λ/NA` ratio-monotone. §B proximity `√(λg)` blur rides `peb_blur` **BE** (Gibbs-ring trap); the wall is contrast/NILS **not** CD.
- [Historical-modes A3](historical-modes-a3.md) — **project (2026-07-10):** `oxidation_history.py`. §A HCl gettering → mobile-Na `Q_ox`↓ → `V_t` recovery (polarity INVERTED vs A1). §B high-pressure → **exact** `1/P` collateral `∫D dt` budget (equal exponent=1 → `A` invariant).
- [Historical-modes A4](historical-modes-a4.md) — **project (2026-07-10):** `resist_history.py` — negative-resist swelling → CD floor. Advisor: swelling is **GEOMETRIC, not an engine ride** (a blur ride would hide a free contour = a [[gradual-failure-preferred]] fudge). Headline (⊥A2): floor ≈ thickness, **optics-independent**.
- [Historical-modes B5](historical-modes-b5.md) — **project (2026-07-10; that plan COMPLETE — 7 modes):** `locos_history.py` — LOCOS bird's beak, the 2-D engine's **2nd** consumer. 2-D solve **load-bearing for MERGE TOPOLOGY, flagged for magnitude**. Seam landmine (`√Dt`≠`√Bt`) → normalized modulation `m∈[0,1]`. Primary data overruled the advisor → earlier pinch-off **qualitative only**. Headline: min pitch ∝ field-oxide.
- [Historical-modes B6](historical-modes-b6.md) — **project (2026-07-10):** `metallization_history.py` — Al junction spiking; `S(T)` spikes short the **shallower** `x_j`. GRADED via shorted-**AREA** ([[gradual-failure-preferred]]). Ohmic short at CURRENT level, NOT `1/τ`.
- [Historical-modes B7](historical-modes-b7.md) — **project (2026-07-10):** F2 silicide/contact-R, built as B7 (`contact_resistance.py`) — `R_series` = **two terms, different `R_sh` exponents**: access LINEAR + TLM contact SUBLINEAR. Salicide shunts the sheet → bottleneck flips access→contact. Robust leg = contact-share↑ as `R_sh`↓; the flip is calibrated.
- [High-κ gate F3](high-k-gate-f3.md) — **project (2026-07-15 → COMPLETE 2026-07-17, 4 slices; card PULLED):** one thickness, two currencies — `C_ox` LINEAR in EOT vs `J_g` EXPONENTIAL in `t_phys`. **`device.py` untouched: `ε_SiO₂/EOT ≡ ε₀κ/t_phys` is an IDENTITY.** κ↔gap INVERSE ⇒ per-material `α∝√(m*φ_B)`. S4 = the **IL**: both currencies **additive over series layers** ⇒ the IL is the *better barrier* yet **a pure loss** (capacitance-only flips the sign); floor `EOT>t_IL` for ANY κ. **Next = F4.**
- [Historical-modes H0](historical-modes-h0.md) — **project (2026-07-10):** the **era-timeline display surface** (`history_gallery.py` → `docs/history.html`+`.local`, the 3rd gallery) — `demo_*_history.py` figures re-cut along the spine (period→wall→successor); glob-anchored.

## Implant (F1)

- [Implant Pearson-IV skew](implant-pearson-skew.md) — **project (2026-07-03):** slice 2 (`shape="pearson"` opt-in; default gaussian = seam). Boron −γ → peak DEEPER than `R_p` + surface tail; the closed form reproduces mean/var, type-IV guard.
- [Implant channeling tail](implant-channeling-tail.md) — **project (2026-07-06):** slice 3 (`channel=None` seam). Two-population `(1−f)·primary+f·Q·tail` (dose-conserving); the deep exp deepens the ANNEALED junction; tilt suppresses `f=f0·e^(−tilt/τ)`.
- [Implant damage→leakage](implant-damage-leakage.md) — **project (2026-07-06; slice 4 = LAST, plan COMPLETE):** displacement damage (NRT/Kinchin–Pease) → traps → `lifetime.py` leakage. Discriminator = RECOVERY (a separate Arrhenius, NOT the dopant `∫D dt`); `damage_trap_density=0` seam.

## Fab-line game

- [Fab-line game](fab-game.md) — **project (2026-06-12 → 2026-06-14):** gamified sand→chip fab LAYERED on chip-sim (ADR 0005; physics `chip/`+`engines/`, game `fab_game/`, one-way import). G1–G7 + CG-1/2/3 + promotions BUILT; backlog exhausted. Remaining = tycoon design.
- [Fab journey](fab-journey.md) — **project (2026-06-14; Phase 6 BUILT 2026-06-15):** staged sand→chip journey front-end (decide→observe→forecast→commit). Phases 1–5 purify/grow/cut/diffuse/oxidize; Phase 6 = cost → net-profit max.
- [Device targets plan](device-targets-plan.md) — **project (2026-06-15, ALL 5 SLICES BUILT — COMPLETE):** "good is application-relative" — re-score the SAME wafer vs inverted specs (`fab_game/targets.py`, never re-fabs). S1 V_t, S2 avalanche BV, S3 native substrate, S4 O gettering, S5 lifetime.
- [Scope-edge backlog](scope-edge-backlog.md) — **project (2026-06-14):** `docs/plans/scope-edge-backlog.md` triages named-but-unbuilt edges BY CONSUMER. BUILT: C1, D1, A2, A1, E1. Heat-mode FALSIFIED chip-side. Next promotable = NONE.
- [Fab-game G1](fab-game-g1.md) — **project (2026-06-12):** the `fab_game/` harness on the validated back end, ZERO new physics. Finding: defocus's casualty = NILS not CD.
- [Fab-game G2](fab-game-g2.md) — **project (2026-06-12):** `czochralski.py` Scheil. Fix: parameterize by seed-end `N_seed`, not melt `C_0` (float trap). Boron k=0.8 → V_t 0.55→0.75.
- [Fab-game G3](fab-game-g3.md) — **project (2026-06-13):** wafer prep — cited yield `Y=exp(−D₀A)` + TTV/bow; per-die Poisson → the law. `defect_density=0` seam.
- [Fab-game G4a](fab-game-g4.md) — **project (2026-06-13):** Si purification — cited Pfann zone refining. Conservation REFRAMED (single-pass ∫C falls short). Na→Q_ox→V_t DOWN; `grade="clean"` seam.
- [Fab-game G4b](fab-game-g4b.md) — **project (2026-06-13):** `chip/lifetime.py` SRH + generation leakage — deep-level Fe/Cu = the device consequence net doping can't carry. Metals never touch V_t.
- [Fab-game G5](fab-game-g5.md) — **project (2026-06-13):** etch & deposition (`etch_deposition.py`), the first flagged-phenomenology tier. Etch bias shrinks CD; voids when gap AR > AR_crit.
- [Fab-game G6](fab-game-g6.md) — **project (2026-06-13):** back end — assembly-yield funnel `Y=Πyᵢ` + speed binning. Trap: binning = grading POLICY, not physics.
- [Fab-game G7](fab-game-g7.md) — **project (2026-06-13):** the roguelike shell (`scoring.py`+`game.py`), additive. One boule = one run; the G2 Scheil V_t drift IS the difficulty curve.
- [Fab-game CG-1](fab-game-cg1.md) — **project (2026-06-13):** Czochralski #1 — cited Burton–Prim–Slichter `k_eff`. Pull rate lifts `k_eff`→1 → flattens Scheil drift. Honest: boron barely moves.
- [Fab-game CG-2](fab-game-cg2.md) — **project (2026-06-13):** #2 — Voronkov `V/G` defect criterion (ξ>ξ_t ⇒ void killers), feeds G3's map. Finding: CG-1's benefit is flat → CG-2 alone sets the pull.
- [Fab-game CG-3](fab-game-cg3.md) — **project (2026-06-13, last CG):** Stefan balance supplies CG-2's gradient G; `ξ=V/G_s` saturates at `ξ_max≈0.32` (caps vacancy cost). Closed-form.
- [Fab-game C1](fab-game-c1.md) — **project (2026-06-14):** crucible O → thermal donors (§1e) — cited `∝[O_i]⁴`; donors compensate the p-substrate → V_t down. Seam by BOTH paths.
- [Fab-game D1](fab-game-d1.md) — **project (2026-06-14):** under-etch (§3) — closes G5's over/under pair. Residual bridges gate lines → SHORT (the mirror of the void OPEN); mutual-exclusion guard.
- [Fab-game A2](fab-game-a2.md) — **project (2026-06-14):** OSF ring = CG-2 made RADIAL (§1f). Finding: void_density peaks at CENTRE → dead vacancy CORE + clean rim. `boost=None` → CG-2 byte-for-byte.
- [Fab-game A1](fab-game-a1.md) — **project (2026-06-14):** the interstitial side of Voronkov (§1g) — slow pull → dislocations → junction LEAKAGE. Two-sided window, optimum AT ξ_t. ρ_disl=0 seam.
- [Fab-game E1](fab-game-e1.md) — **project (2026-06-14):** spike/RTA — heat-mode FALSIFIED (T is a setpoint); `D(t)` budget BUILT (§4). Budget collapses near peak (top 50°C = 84%) → why RTA. Seam bit-for-bit.

## Doc surfaces

- [Gallery local edition](gallery-local-edition.md) — **project (2026-06-12 → 2026-06-14):** TWO galleries, each public + local (4 pages) from `chip/gallery.py` + `fab_game/gallery.py`. All golden-tested; don't mix github↔localhost.
- [Roadmap page](roadmap-page.md) — **project (2026-07-14; rule first FIRED 2026-07-17):** `docs/roadmap.html` — the 4th page, PLANNED-slice schematics stamped in-image "not simulator output", verdicts verbatim with `future-steps.md`. **Graduation rule = the card comes OFF when the slice ships** — F3 went first; the manifest guard pins card↔schematic, so `SLICES`+`FIGURES` cut together.

## Cited sources (and the claims they license)

- [Deal–Grove oxidation source](deal-grove-oxidation-source.md) — **P2:** cited linear-parabolic constants (wet/dry; orientation; 0.44 Si ratio); thin-dry edge → [[massoud-thin-oxide-source]].
- [Massoud thin-oxide source](massoud-thin-oxide-source.md) — **P2 v1.1:** cited thin-dry rapid-growth constants (`oxidation.py` §5); COHERENT-SET rule + τ SIGN-TYPO (`exp(+E/kT)`); plain DG stays default.
- [Dopant diffusivity source](dopant-diffusivity-source.md) — **P1a:** Fair/Plummer intrinsic Arrhenius `D(T)` for B/P/As/Sb + erfc/Gaussian forms + the predep dose identity.
- [Dopant charge-state diffusivity source](dopant-charge-state-diffusivity-source.md) — **v1.3:** cited Fair `D(N)=D⁰+D⁻(n/nᵢ)+D⁼(n/nᵢ)²` + B/P/As/Sb table + nᵢ(T) + carrier cap.
- [Dopant mobility source](dopant-mobility-source.md) — **P1a:** Masetti 1983 μ(N) = the `R_s` conductance-integral integrand (independent of Irvin → a non-circular cross-check).
- [Irvin sheet-resistance source](irvin-sheet-resistance-source.md) — **P1a:** Irvin 1962 `R_s·x_j` benchmark; GRAPHICAL not callable — the code computes `R_s` via the independent μ(N).
- [Dopant solid solubility source](dopant-solid-solubility-source.md) — **P1a:** Trumbore 1960 solubility limits = the predep Dirichlet surface `N_s`.
- [Dopant segregation source](dopant-segregation-source.md) — **v1.2:** cited `m=solubility_Si/solubility_SiO₂` (the DEFINITION is load-bearing — inverting it flips deplete↔pile-up); flux BC.
- [OED source](oed-source.md) — **v1.2:** cited half-power supersaturation `Δ∝(dx_ox/dt)^0.5` + `f_I`; `D_eff/D_inert=1+f_I·Δ`, amplitude CALIBRATED-flagged.
- [Lateral diffusion source](lateral-diffusion-source.md) — **v1.8:** lateral/vertical junction ratio ≈ 0.75–0.85 (Kennedy–O'Brien 1965); model ~5–10% high → LOOSE.
- [Range statistics source](range-statistics-source.md) — **implant slice 1:** LSS `Rp(E)`/`ΔRp(E)` for B,P (~10%); tight = monotone `Rp(E)` + B-deeper-than-P.
- [MOS threshold-voltage source](mos-threshold-voltage-source.md) — **P4:** cited V_t formula + CGS constants + the MIT 6.012 worked example (the conservation cross-check) `device.py` reproduces.
- [Litho aerial-image source](litho-aerial-image-source.md) — **P3:** cited Rayleigh k₁ (0.25 two-beam / 0.5 coherent) + the NILS printability rule `litho.py` benchmarks against.
- [PEB acid-diffusion source](peb-acid-diffusion-source.md) — **v1.7:** cited `σ=√(2Dt)` blur + sealed-film Neumann BC, standing-wave period λ/2n; CAR = a named scope edge.
- [Litho tool/proximity source](litho-tool-proximity-source.md) — **A2:** cited `b_min≈√(λg)` → blur `σ=k√(λg)`, `k≈1` FLAGGED; node λ real, per-node NA REPRESENTATIVE.
- [LOCOS bird's-beak source](locos-birds-beak-source.md) — **B5:** cited beak/field-oxide ≈ **0.85×** + the mechanism (TU Wien, web-verified). CORRECTION: dropped unverified §-numbers carried from recall.
- [Aluminium spiking source](aluminium-spiking-source.md) — **B6:** cited Al–Si eutectic **577 °C** + **~1.5 wt%** max Si solubility + the alloy→barrier→Cu fix ladder; Arrhenius `S(T)` FLAGGED.
- [Silicide/contact source](silicide-contact-source.md) — **F2/B7:** cited TLM coth form + two limits; ρ_c bounds Al–Si ~1e-6, TiSi₂ ~1e-7–3e-7 Ω·cm². `CONTACT_LENGTH_UM` FLAGGED.
- [High-κ dielectric source](high-k-dielectric-source.md) — **F3:** cited EOT + κ/gap/CB-offset table (Robertson, web-verified); LOAD-BEARING = κ↔gap **inverse**. `m*` FLAGGED/fit-extracted (HfO₂ 0.08–0.2 → 3.9–9.5 dec). Non-circular: predicts the ~2 Å slope. **+ Ando 2012** (IL): additive `EOT=EOT_IL+EOT_HK`, the ~0.4–0.5 nm IL practical floor, independent corroboration of both. Lit matched-EOT win = **~2–6 dec** (corrects "~3–5").
- [BEOL interconnect source](beol-interconnect-source.md) — **F4 (PLANNED):** cited `c_pul≈2 pF/cm` + its **invariance** (coax↔80nm line, 7 orders) ⇒ crossover driven by **R not C**; global-vs-local scaling is load-bearing. **SIGN TRAP:** Ru's bulk ρ is 4× *worse* than Cu and `ρ₀λ` (Cu 65 < Ru 77) only buys **parity** — the **barrier** (2–3nm, unscalable) tips it. `L` = house lump ⇒ headline is prefactor-free.
- [Avalanche breakdown source](avalanche-breakdown-source.md) — **device-targets S2:** Baliga planar `BV∝N^-3/4` + cylindrical curvature DERIVED from `∫α dr=1` (not a remembered fit); Sze 0.24 ~1%.
- [Internal gettering source](internal-gettering-source.md) — **device-targets S4:** cited DIRECTION — O precipitates getter Fe/Cu ABOVE [O_i]~12ppma (Tan 1990); O_crit=6e17, efficiency FLAGGED.
- [Reverse recovery source](reverse-recovery-source.md) — **device-targets S5:** `t_rr∝τ` DERIVED from the charge-control ODE → `t_s=τ·ln(1+I_F/I_R)`; lifetime-killing (Au/Pt) cited. Same τ as G4b, opposite way.
