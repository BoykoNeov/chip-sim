---
name: fab-game-g7
description: "fab-game G7 BUILT — roguelike framing + scoring (scoring.py/game.py); one boule = one run, Scheil V_t drift = difficulty curve; TUI deferred"
metadata: 
  node_type: memory
  type: project
  originSessionId: af9f62ce-8ebb-4040-af52-740987896b9f
---

**project (2026-06-13):** **G7 BUILT — framing + scoring; TUI DEFERRED.** The roguelike **game shell**
over the now-complete line ([[fab-game]] §6 G7), the **last** G-step. **Purely additive game policy** —
**no physics / `run_line` / `WaferState` / `Die` touched** → the 476 stay green *trivially*, **no seam to
break, no ADR** (executing ADR 0005, not deciding anew). Two new game-layer modules:

1. `fab_game/scoring.py` — the **economics**: `BIN_PRICES` (premium/typical/value/reject → $, flagged
   house), wafer/scrap/rework **costs**, `score_wafer(wafer) → ScoreCard` (`revenue = Σ price·count` over
   **shipped** = `verdict.passed` dies; `profit = revenue − cost`). Mechanics-tested: bookkeeping closes
   + **monotonicity** (a better bin mix never earns less — the economic image of "propagation wired").
2. `fab_game/game.py` — the **session**: immutable `GameSession` + `GameConfig`, `MARKET_BINS` (a *real*
   multi-grade `SpeedBins`, NOT the G6 seam default one-open-bin), `process_wafer`/`scrap_wafer`/`play`,
   `RunRecord` append-only history, `ReworkSpec` (folds the existing tested rework paths into a turn).

**THE framing (advisor-affirmed, physics-grounded NOT invented): one boule = one run, each wafer a
turn, and the [[fab-game-g2]] Scheil `V_t` drift IS the difficulty curve** — boron segregates down the
boule (`N_A`↑ → `V_t` walks 0.55→0.75, out the 0.68 ceiling by z≈0.8), so early slices are easy and the
**tail forces a decision**. Reuse `run_line` per wafer (advisor: **do NOT** refactor it into per-step
turns — big refactor, no gain); the session holds the cross-wafer state. Per-wafer seed = `seed +
wafer_index` from one session seed → a `(seed, recipe-seq, actions)` triple reproduces the playthrough.
Sandbox vs roguelike = **one mode flag** (the bankrupt gate), not two engines.

**The lever (advisor's "one design beat — give the player a real lever against the drift"):** **thin the
gate oxide** (lower `t_ox` → lower `V_t` AND higher `I_Dsat`) pulls the tail back into spec and into the
premium speed bin. Verified the schedule numerically first (≈ `20.5 − 5.5·z` min centres `V_t`).

**TWO honesty corrections during build (both the same standard — don't let the headline over-claim a
lever whose gain is unmodeled-cost-dependent):**
- *(mid-build, from the figure)* I first wrote the caveat as "the lever is one-sidedly good in-model
  (only *unmodeled* oxide-reliability bounds it)". **Wrong:** thinning raises `I_Dsat`, so over-thinning
  the **extreme tail** drives `I_Dsat` into its **spec ceiling** — the linear trim's last slice (z=0.9)
  sits at mean `I_Dsat ≈ 4.19` vs the 4.2 ceiling → variation tips half its dies over → adapt **fumbles**
  the last wafer. So a real **in-model** Goldilocks window exists. Embraced the fumble (honest > hiding).
- *(done-check, advisor)* the headline "adapt-or-die / rescue the tail" **mis-attributes adapt's win**.
  Read off the per-wafer profit: of adapt's **+$366** edge over naive, **+$336 (~90 %) is UPGRADING
  in-spec, never-in-danger wafers to premium** (thinner = faster = more valuable, the scaling lever) and
  only **+$30 (~10 %) is the actual doomed-tail rescue** — a premium **windfall**, not a rescue. And that
  windfall is free *only because oxide reliability is unmodeled* — the exact cost the caveat flags. Fixed
  the wording everywhere (demo/plot/plan): the **clean, cost-independent lesson is scrap-vs-naive** (cut
  the loss on the doomed tail); adapt is the caveated, **double-braked** windfall (I_Dsat ceiling in-model
  + gate-oxide reliability unmodeled). Code/data were always correct — only the framing over-claimed.

**The TUI is DEFERRED (advisor: defer, don't ask):** the user said "roguelike framing/**scoring**" — that
appositive scopes the plan bullet, so phrasing wins over the bullet, and deferring is low-regret (a
Textual app is untestable beyond smoke + a new dep, cheap to add later). **"Roguelike framing" is a
*session model*, not a UI** — everything built is headless/testable; a Textual front-end would be a thin
driver of this session. Named as the follow-on, **did NOT** fire an AskUserQuestion (asking when already
scoped erodes trust). Same defer-and-name precedent as CMP/rebond/tycoon.

Banked `demo_game`/`fab-game-g7.png` (3 panels: the V_t drift / the three score trajectories / per-wafer
profit) — three strategies down one boule: **naive** (process all → tail bleeds) **< scrap-the-tail** (cut
the loss) **< adapt** (thin the oxide → rescue the mid-boule for premium). Mechanics-tested (ADR 0005 §5):
determinism, bookkeeping closes (`budget = start + Σ profits`, append-only), monotonicity, sandbox-vs-
roguelike, the drift arc. Fast lane 476→**492** (+16: `test_scoring.py` 5, `test_game.py` 8,
`test_demo_game.py` 3); no engine amendment, no ADR, no chip gallery card. **Tycoon deferred** (same
harness, different objective). The fab line is now **complete sand→binned chip + a scored roguelike
shell**. [[fab-game-g6]] [[engine-unfrozen]]
