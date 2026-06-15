---
name: reverse-recovery-source
description: "device-targets S5: cited diode reverse-recovery t_rr ∝ τ — DERIVED from the charge-control ODE dQ/dt=−Q/τ−I_R, Q(0)=I_F·τ → storage time t_s=τ·ln(1+I_F/I_R) (Kingston 1954 / Sze §2.5 / Baliga); proportionality + lifetime-killing direction cited, operating point I_F/I_R + fall time t_f flagged/named. chip/reverse_recovery.py"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4d93ad43-9467-46de-9662-71747db4e5f3
---

**Cited model behind `chip/reverse_recovery.py` (device-targets slice 5 — the lifetime inversion).** A p-n
rectifier switched forward→reverse cannot block until its stored minority charge recombines, so its
**reverse-recovery time `t_rr ∝ τ`** (minority-carrier lifetime). **DERIVED, not a remembered fit** (the S2
breakdown discipline — like `∫α dr=1`): the **charge-control** equation `dQ/dt = −Q/τ + i(t)` (Sze,
*Physics of Semiconductor Devices* §2.5 device dynamics; Baliga, *Fundamentals of Power Semiconductor
Devices*) with steady forward `Q_F = I_F·τ`, then a constant reverse sweep `i = −I_R`, gives
`Q(t) = (I_F+I_R)τ·e^(−t/τ) − I_R·τ`; the **storage phase** ends at `Q(t_s)=0`:

  **`t_s = τ·ln(1 + I_F/I_R)`**   (the cited Kingston 1954, *Proc. IRE* 42:829, "Switching time in junction
  diodes and junction transistors" form; textbook in Sze/Baliga).

So `t_s` is **linear in `τ`** with slope `K = ln(1+I_F/I_R)`. The total `t_rr = t_s + t_f` adds a
depletion-capacitance/transit **fall time `t_f`** that does **not** scale with `τ`; the lifetime-controlled
device output modelled is the storage-dominated `t_rr ≈ t_s ∝ τ`.

**CITED (asserted tight, the form + direction):** the proportionality `t_rr ∝ τ`; the charge-control
derivation (the ODE solution closes on the charge-zero crossing — the analytic leg); the **lifetime-killing
direction** — *shorter* `τ` → *faster* recovery, why fast/soft rectifiers are made by **gold/platinum
doping or electron irradiation** that deliberately kill lifetime (Sze, Baliga). **FLAGGED/named (loose):**
the operating-point ratio `I_F/I_R` (`IF_OVER_IR_DEFAULT=1.0` → `K=ln2≈0.69`, an O(1) house value); the
fall time `t_f`; the constant-`I_R` switching idealization; the single low-injection `τ` (high-level
injection in a conductivity-modulated power diode is out).

**THE inversion it powers (S5):** `t_rr` reads the **same `τ`** the G4b junction leakage `J_gen ∝ 1/τ`
reads ([[fab-game-g4b]]), in the **opposite** direction — a short `τ` is a *leaky logic reject* but a *fast
rectifier feature*. Zero new lifetime physics (`τ` is the G4b reading); `t_rr` is the one cited consequence.
`chip/reverse_recovery.py` (`reverse_recovery_time`/`storage_factor`/`diode_recovery`), triad-tested
(`chip/tests/test_reverse_recovery.py`). Units: `τ` in s, `t_rr` in s (reported ns). [[device-targets-plan]]
[[avalanche-breakdown-source]] [[internal-gettering-source]]
