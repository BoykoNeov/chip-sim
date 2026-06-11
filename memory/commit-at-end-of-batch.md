---
name: commit-at-end-of-batch
description: "Standing preference — always commit AND push at the end of a work batch, without being asked again"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c438a374-74f6-4a68-a971-19a793538ac4
---

**Always commit at the end of a work batch** (stated 2026-06-10, after the v1.3 build). When a coherent
batch of work is complete and verified, commit it — do **not** wait to be asked each time. This is
durable authorization that overrides the harness default ("commit only when the user asks").

**Why:** the user works in batches and wants each finished batch landed as a commit so the history
stays clean and nothing sits uncommitted. Asking "should I commit?" every time is friction they've
explicitly removed.

**How to apply:** at the natural end of a batch (feature/fix done, the relevant gate green), stage and
commit without prompting. For **chip-sim**, commit **directly to `main`** — that matches the repo's
history (a solo standalone educational-sim repo; recent chip/docs/test commits land on main, no PR
flow), so the "branch first on the default branch" default does *not* apply here. Use a clear
conventional-commit message (e.g. `chip(vX): …`) ending with the `Co-Authored-By: Claude Opus 4.8`
trailer; run the fast lane first so the commit is green.

**Always push, too** (stated 2026-06-10 — *"always push commits"* — supersedes the earlier "do NOT push
unless asked"). After committing a batch, `git push origin main` without prompting. Opening **PRs** is
still ask-first — but chip-sim is direct-to-`main` with no PR flow, so in practice push = publish here.
Likely a general cross-project preference (not just chip-sim); recorded here because this is the
available memory store.
