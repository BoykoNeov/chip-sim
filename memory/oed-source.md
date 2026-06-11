---
name: oed-source
description: Microchip v1.2 — cited OED parameterization (half-power supersaturation + fractional interstitialcy f_I) that coupling.py pins
metadata: 
  node_type: memory
  type: reference
  originSessionId: b15dfec1-90c9-4055-b898-964fda138764
---

Microchip v1.2 (the Phase 1↔2 back-coupling, `coupling.py`): the cited sources for
**oxidation-enhanced diffusion (OED)** — pinned at build, not carried from memory.

**Mechanism.** Thermal oxidation injects silicon **self-interstitials** at the Si/SiO₂
interface. Dopants with a significant **interstitialcy** diffusion component (B, P, As) are
**enhanced**; a near-pure **vacancy** diffuser (Sb) is **retarded** (oxidation-*retarded*
diffusion, ORD — the opposite-sign companion). Sources: IUE-Vienna (TU Wien) Wimmer dissertation
§3.2.3 "Oxidation Enhanced/Retarded Diffusion (OEDS/OED)"; **Antoniadis & Moskowitz, *J. Appl.
Phys.* 53(10):6788 (1982)** (the seminal point-defect-kinetics paper).

**The half-power law.** The interstitial supersaturation `Δ = (C_I/C_I* − 1)` scales with the
oxidation rate as `Δ ∝ (dx_ox/dt)^n`, **n ≈ 0.5** (the IUE OEDS analytical model: "approximately
a half-power dependence on the oxidation rate"). Literature spread **0.3–0.5** — named as the
exponent uncertainty. `coupling.py` uses `OED_RATE_EXPONENT = 0.5`.

**Fractional interstitialcy f_I** (the per-dopant factor that scales enhancement and discriminates
enhanced vs ORD), at ~1000–1100 °C, from the **dual interstitialcy–vacancy quantification of B/P/As/Sb
in Si** (IEEE, "Quantification of Diffusion Mechanisms of Boron, Phosphorus, Arsenic, and Antimony in
Silicon", DOI 10.1109/…5436609):
- **B = 0.30, P = 0.38** (interstitialcy-significant → enhanced; the demo pair)
- As = 0.35 (mixed I/V — doc only, not a demo dopant; absent from the `DOPANTS` registry)
- **Sb = 0.015** (near-pure vacancy → essentially un-enhanced by the form; true ORD retardation is
  the named scope edge)

**The form `coupling.py` uses:** `D_eff/D_inert = 1 + f_I·Δ`. Note B/P f_I are only ~0.3–0.4 (NOT
~1.0): boron is ~70% vacancy, yet OED-enhanced because the *interstitial supersaturation* during
oxidation is large. The **amplitude** `OED_SUPERSATURATION_AT_REF` (Δ at the reference rate) is
**CALIBRATED, flagged** — the OED magnitude carries a large literature spread (factors ~2–10), so it
is illustrative; the validated legs (degenerate recovery, effective-∫D dt, conservation) hold for
any amplitude. The half-power exponent + the f_I ordering are the cited content.

**Sb caveat (don't over-claim):** a positive `(dx_ox/dt)^n` form with f_I=0.015 gives factor ≈1.05 —
a small *wrong-sign* residual, NOT a retardation number. True ORD (`D_eff/D_inert < 1`) needs the
vacancy-undersaturation term `coupling.py` does not model. Sb = qualitative scope edge only.

Used by [[chip-coupling-v12]]. The segregation half = [[dopant-segregation-source]]. OED's variable-D
reuses the frozen engine's already-blessed `D(t)` case (contrast the unbuilt `D(N)` =
[[dopant-diffusivity-source]] scope edge).
