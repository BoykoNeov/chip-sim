# 0005 — The fab-line game: layering, the one-way boundary, and no game engine

Status: Accepted — 2026-06-12
Scope: A new direction — a gamified full-line fabrication simulator (sand → packaged
chip) built **on top of** chip-sim. Governs where the game code lives relative to the
validated physics, the dependency direction, the test discipline split, and the UI
technology. The plan is `docs/plans/fab-game.md`.

## Context

chip-sim today is a **physics-validation-first library**: every fab step is a cited,
triad-tested module (`chip/`), reusing the separately-validated `engines/diffusion`
spine, governed by ADRs 0001–0004. Its whole identity — and its test gate — is *"every
number is anchored to an independent fact, asserted tight, with the scope edge named."*

The new direction is a **gamified, full-production-line simulator**: silicon
purification → Czochralski crystal growth → wafer prep → the existing fab flow (oxidation,
lithography, diffusion, etch/deposition) → device → packaging/test, with the repeated
litho/etch cycles collapsed to one representative each. Every step can **fail**; a failed
or marginal step **propagates** its damage downstream as real physics carried in a shared
wafer state; outcomes have a **stochastic** spread; the payoff is **yield**. It ships as a
roguelike (a wafer/boule's journey) with a sandbox mode now and a possible tycoon mode
later. (The synced vision is recorded in the plan.)

This introduces concerns that are **alien to a physics library** and cannot be validated
the way physics is:

- **Orchestration.** A pipeline / state machine chaining steps. *chip-sim has none today*
  — `device.py` consumes scalar consequences (`N_A`, `t_ox`, CD); the actual chaining
  lives only inside `demo_device.py`. The driver is net-new.
- **A mutable wafer state** that accumulates physical defects and parameters as it flows.
- **Spec limits, a stochastic variation layer, yield, binning, scoring, rework rules,
  narrative, and a UI** — game design, balance, and fun, none of which has a *cited*
  ground truth to assert against.

Two structural questions must be settled before any code: **(1)** where does the game
live relative to the validated physics, and **(2)** what technology owns the interactive
surface. A wrong answer to either corrodes the thing that makes chip-sim trustworthy — its
test gate.

## Decision

**A two-layer architecture, in one repo to start, with a one-way dependency and a
Python-native thin UI.**

### 1. Two layers, clean concerns

- **Physics layer — `chip/`, `engines/` (chip-sim, unchanged in kind).** Stays the
  validated physics library and *grows* the new process physics — purification, Czochralski
  (the **Scheil** axial-segregation closed form), wafer prep, etch/deposition, packaging —
  each as a **cited, triad-tested module**, the existing "deepening" rhythm. It also gains
  the **physical variation models** (process-variation magnitudes, defect statistics) that
  feed the stochastic layer — validated where a cited number exists, flagged-calibrated
  where it does not.
- **Game layer — a new `fab_game/` subpackage.** Owns everything the physics layer must
  not: the `WaferState`/boule/die-map objects, the pipeline state machine, spec windows,
  the stochastic spread + yield + binning, the rework rules, scoring, narrative, and the UI.

The new *process physics* lives in the **physics layer**, never in `fab_game` — so it stays
under the validation gate and reusable by anything else. `fab_game` only holds what *cannot*
be physics-validated: spec limits, balance, fun.

### 2. The dependency is one-way: `fab_game → chip/engines`, never the reverse

`fab_game` imports and calls the physics layer; nothing under `chip/` or `engines/` may
import `fab_game`. Enforced by a test (an import-direction guard), not just convention.
This keeps the physics core free of game/UI dependencies and keeps the existing gate
meaning exactly what it means today.

### 3. In-repo subpackage first; split to its own repo only once mature

Do **not** start `fab_game` as a separate repository. Two reasons, both from this project's
own governance:

- **Rule-of-three / freeze-before-reuse.** Don't stabilize an interface across a repo
  boundary until it has ≥3 consumers. The game is consumer #1, and the chip-sim API it
  calls (the `WaferState` shape, the per-step signatures) will churn hard while we discover
  what the game needs. A repo boundary freezes that churn into release/version friction at
  the worst time.
- **The program's own history is the template.** BigSim was a monorepo (steel + chip +
  planet + shared engines) and was split into standalone repos *only once mature*
  (2026-06-10). Same move here: promote `fab_game/` to its own repo when its consumed API
  stops moving — not before.

### 4. No game engine as the authority — Python-native sim, thin UI

The simulation is the source of truth and stays Python/NumPy/SciPy. The UI is a **thin
skin**, per the repo's standing principle (*a figure is never in the correctness path*; the
notebook is sugar over validated modules — ADR 0002). A real-time game engine
(Unity/Godot/Unreal) wants to own the main loop and the state, which inverts that and forces
cross-language marshaling of sim state, with the standing temptation to creep physics onto
the engine side. None of a game engine's reason-to-exist (renderer, scene graph, sprites,
collision runtime) is needed for a turn-based *choose recipe → run step → watch it ripple*
loop. The UI ladder, lightest first: **notebook + ipywidgets → a Textual TUI → a web app**.
A real game engine (Godot is the light, open-source pick) is reconsidered **only** for a
possible tycoon future, and even then the Python sim stays the authority and the engine is a
pure front-end.

### 5. The test discipline splits along the layer boundary

- **Physics layer** keeps the **cited validation triad** (analytic limit + conservation +
  published benchmark) for every new process module — unchanged.
- **Game layer** is tested for **mechanics invariants**, not cited magnitudes: the
  import-direction guard; **determinism** (a fixed seed + recipe → identical outcome, so the
  physics core is reproducible and all randomness flows from one seeded RNG); **propagation
  is actually wired** (a strictly-worse inherited field never yields a strictly-better
  downstream observable where the physics says it shouldn't); **state bookkeeping** (good +
  bad dies = total; provenance append-only; rework accounting closes); and a **seam test**
  (nominal knobs + zero variation reproduce the existing demo numbers bit-for-bit — the
  harness does not change the physics). Heavy / live-kernel / UI tests take the `slow` marker
  (ADR 0003).

Net: **"is the physics right?"** is answered in the physics layer by citations and triads;
**"is the game fair and does propagation work?"** is answered in `fab_game` by mechanics
tests. The two questions never blur.

## Consequences

- `+` Clean separation of concerns *and* of validation discipline — the physics gate keeps
  its meaning while the game grows beside it under a different, appropriate kind of test.
- `+` No repo-split friction during the high-churn early phase; the new process physics
  stays inside chip-sim's gate and reusable by any consumer.
- `+` The one-way import guard keeps game/UI dependencies out of the physics core, so a
  headless physics checkout stays light and the fast lane stays fast.
- `+` Python-native throughout — no cross-language boundary, no heavyweight runtime, the
  notebook/TUI are thin skins over the validated modules.
- `−` chip-sim's single repo now hosts two test disciplines (cited triads vs mechanics
  invariants). Mitigated by folder separation (`fab_game/tests/`), the `slow` marker, and the
  import-direction guard that makes the boundary mechanical, not just documented.
- `−` A subpackage inside the physics repo invites game concerns to creep into `chip/`.
  Mitigated by the import guard + this ADR; the creep is *caught*, not merely discouraged.
- `−` Deferring the repo split means the game ships under chip-sim's versioning until mature.
  Accepted — it matches the BigSim monorepo→split precedent and trades a cosmetic for the
  real win of churn-friction-free iteration.

## Alternatives considered

- **A separate repo from day one.** Rejected: violates rule-of-three (consumer #1, churning
  API) and ignores the monorepo→split precedent; buys clean packaging at the cost of
  release/version friction during exactly the phase the interface is least stable.
- **Build the game inside `chip/` with no boundary.** Rejected: mixes balance/fun/stochastic
  yield (un-citable) into the cited modules and corrodes the test gate that is chip-sim's
  whole trustworthiness.
- **Put the new process physics in `fab_game` (so chip-sim stays "as it was").** Rejected:
  the new physics would escape the validation gate and stop being reusable — the opposite of
  the layering's point. New physics belongs in the validated layer; only un-citable game
  concerns belong in `fab_game`.
- **Adopt a real game engine (Unity/Godot) as the platform.** Rejected as the authority:
  inverts the thin-skin principle, forces cross-language state marshaling, and pulls in a
  real-time runtime none of a turn-based fab loop needs. Allowed only later as a *front-end*
  with the Python sim as the source of truth.
- **Skip the stochastic layer, keep deterministic-only.** Rejected per the synced vision
  ("both"): without process variation there is no honest yield, and yield is the payoff. The
  determinism requirement is preserved differently — the *physics* is deterministic given
  (seed, recipe); the variation is a seeded, reproducible layer on top.
