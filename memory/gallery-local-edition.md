---
name: gallery-local-edition
description: "why there are TWO gallery files — docs/index.html (public/GitHub/Pages) + docs/index.local.html (localhost JupyterLab launch); don't \"clean up\" the second"
metadata: 
  node_type: memory
  type: project
  originSessionId: 46062994-ca8c-4c57-9bd5-6c52d51f3d31
---

**project (2026-06-12, commit `5d5f97e`):** the gallery now renders **two** committed pages from
`chip/gallery.py` (`render_html(local: bool)`, `python -m chip.gallery` writes both):

- **`docs/index.html`** — the PUBLIC page (GitHub blob/tree links, served by GitHub Pages). **Unchanged**
  by this work, kept byte-for-byte identical (verified via empty `git diff --stat -- docs/index.html`).
- **`docs/index.local.html`** — a second render whose ~21 links point at a **running JupyterLab**
  (`http://localhost:8888/lab/tree/<repo-relative-path>`) instead of GitHub, so the teaching-notebook
  card is a **real click→live-notebook launch** (sliders and all) — the one thing GitHub's read-only
  `.ipynb` viewer can't do. Source/doc links open in the lab too; launch links carry `target="_blank"`
  (open alongside the gallery, not replace it).

**Why two files:** the user (standalone-JupyterLab user, NOT VS Code) wanted index.html to have *zero*
GitHub links and clicking to *launch* locally. But making the committed index.html all-local **kills the
public Pages gallery** (localhost/file links dead-end for any remote visitor — the "visual front door"
built 2 commits earlier). User was shown that consequence and chose **keep public + add a separate local
page** (not "torch index.html"). So: don't relitigate "but they said THE index.html."

**Hard constraint (don't re-hunt for a magic launcher):** a browser click **cannot spawn** a `jupyter lab`
process — security boundary. `vscode://file/<abs>` was the only "launch a process" scheme and it's out
(non-VS-Code user). The localhost link only **reaches an already-running** server; the caveats live in the
card text — server must be up, **launched from the repo root** (so `chip/chip.ipynb` resolves under
`/lab/tree/`), **port 8888**, same browser that holds the token cookie.

**Determinism preserved** (the gallery's founding principle, `gallery.py` header): fixed localhost strings
= no machine path, so BOTH pages stay golden-tested. Guards in `chip/tests/test_gallery.py`:
`test_committed_local_html_is_current` (currency), `test_local_edition_is_all_local_no_github` (local has
**zero** `github.com` + the notebook launch link), `test_public_edition_still_points_to_github` (public
keeps GitHub, no `localhost`).

**How to apply:** edit `chip/gallery.py` (never hand-edit the HTML), regenerate BOTH with
`python -m chip.gallery`, commit both. **Do NOT delete `docs/index.local.html`** (intentional + golden-tested),
do NOT put `localhost` into the public page or `github` into the local one (tests fail both ways). The
standalone-Jupyter user interacts with the notebook **via the local edition**. Smoke test (only the
user can run it): `jupyter lab` from repo root → open `docs/index.local.html` → click the notebook card →
opens `chip/chip.ipynb` live. Earlier same-day fix `261becd` had reworded the *public* notebook card to
surface the `jupyter lab chip/chip.ipynb` command (still GitHub-linked) — this supersedes that for local use.
