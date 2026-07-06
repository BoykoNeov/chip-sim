---
name: implant-channeling-tail
description: "ion-implant slice 3 — channeling tail (opt-in Channeling: fraction/length_um/tilt_deg); deep exponential past R_p deepens the ANNEALED junction → punchthrough; tilt (7°) suppresses"
metadata: 
  node_type: memory
  type: project
  originSessionId: 89c82527-f355-4c7a-8c0e-0cfe992c93dc
---

Ion-implantation **slice 3 = channeling tail** BUILT (2026-07-06, `chip/diffusion_dopant.py` §5c; plan
`docs/plans/ion-implantation.md` slice 3 marked done). The deep exponential a single-crystal lattice adds
past `R_p` — a **failure mode** (deeper junction → source/drain **punchthrough**), not a targeting knob.
Builds on slice 1 ([[range-statistics-source]]) / slice 2 ([[implant-pearson-skew]]).

**Seam:** new `Implant.channel` field, default `None` = slice-1/2 bit-for-bit (whole existing suite
byte-identical, the opt-in discipline cf. `implant=None`, `shape="gaussian"`). `implant_profile` was
restructured to compute `primary` (Gaussian *or* Pearson) then **early-return** it when `channel is None`
(no `(1−0)·primary+0·tail` arithmetic — that would break the bit-for-bit seam test). API: `Channeling`
frozen dataclass (`fraction`=f0, `length_um`=λ, `tilt_deg`=7.0 default; `.length_cm` prop),
`channeled_fraction(f0,tilt)→f`, `channeling_tail(x,R_p,λ_cm)→unit-area deep exponential`.

**The model — two-population PARTITION (not add-on):** `N = (1−f)·primary + f·Q·tail`, where
`tail = (1/λ)·e^(−(x−R_p)/λ)` for x≥R_p (Heaviside deep side, unit area ∫_{R_p}^∞=1), and
`f = f0·e^(−tilt/τ)`. The channeled ions come **out** of the primary → `∫N dx = Q` **analytically**
(adding-on-top would violate dose — advisor point 5). Scales the **whole** primary by (1−f), so rides on
either shape (gaussian/pearson). This is the standard channeling split; **single tail suffices** —
`dual-Pearson` (channel+primary as two full Pearson populations) stays the named deferred edge.

**The SIGN (cited, load-bearing) vs FLAGGED magnitude:** channeling **deepens the ANNEALED junction**
(the discriminator) and **tilt suppresses** it (7° convention → wafers implant off-axis). CITED:
Plummer/Deal/Griffin §8, Campbell §5 (channeling down ⟨110⟩/⟨100⟩; tilt/screen-oxide/pre-amorphization
break it). FLAGGED house-calibrated: f0, λ, and rate `_CHANNEL_TILT_SUPPRESSION_DEG=4.5` (τ, so 7°→~1/5,
e^(−7/4.5)≈0.21). Screen-oxide/pre-amorphization named but not built (tilt is the carried lever).

**Why deeper-x_j is sign-robust (advisor):** it is NOT "channel ≥ no-channel everywhere" — the (1−f)
scaling *lowers* the peak. It holds because a long tail (λ≫ΔR_p) dominates the **super-exponentially**
decaying Gaussian *in the deep-tail region where the junction lives* (the z≈3 / high-x regime
`junction_depth` assumes). So assert it (a) with **N_B in the tail** (high N_B near R_p can push x_j
*shallower* — the trap), and (b) through **`two_step`** (the punchthrough consumer is the *annealed*
junction; constant-D drive-in **linearity** carries the as-implanted tail-dominance through the anneal —
breaks under D(N)/Picard, so constant-D as the existing broadening test uses).

**Triad.** Tight/sign-robust: seam (`channel=None` bit-for-bit both shapes); dose (partition ∫=Q
analytic + sealed drive-in conserves grid-dose structurally); **deeper annealed x_j**; **tilt
monotonicity** (more tilt → shallower x_j — the second tight leg). Flagged: f0/λ/τ magnitudes; two-sided
(surface + deep-tail) grid-dose truncation (as Pearson).

**Consumer:** `junction.junction_depth` — the annealed x_j, deeper → punchthrough. Demo =
`chip-implant-channeling.png` (log as-implanted tail + annealed x_j 0.71→1.91 µm on-axis, 7° pulls back
to 1.52 µm; deep 4 µm domain so the channeled junction resolves). 9 new tests in `test_implant.py`.
**Slice 4 (damage→leakage via `lifetime.py`) BUILT 2026-07-06 → the plan is COMPLETE**
([[implant-damage-leakage]]). [[range-statistics-source]] [[implant-pearson-skew]] [[dopant-diffusivity-source]]
