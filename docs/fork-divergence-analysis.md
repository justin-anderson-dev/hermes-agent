# Fork Divergence Analysis: `custom/main` vs `main`

**Date:** 2026-05-31
**Author:** Claude Code (analysis), for review with Justin
**Scope:** Catalog the difference between the local `custom/main` branch and the
upstream `main` branch, identify what drives merge-conflict pain, and lay out
pathways to minimize divergence so future upstream pulls are simpler.

> **Note on naming.** In this repo, the branch the request calls `main` resolves
> to `origin/main` (there is no local `main`). All commands below use
> `origin/main`. See [§1](#1-repository-topology-the-most-important-finding) —
> `origin/main` is **not** the pristine public upstream; it is itself a
> customized fork-integration branch. This distinction matters for the plan.

---

## 0. TL;DR

- The diff is **212 files, +23,459 / −4 lines**, but this number is misleading.
- **209 of 212 files are brand-new additions** that live in dedicated, fork-only
  directories. They cause **almost no real git conflicts** today.
- The divergence is really **two unrelated things stacked in two commits**:
  1. **`a2b1b20e5` — the AI-SDLC / Spec-Kit framework** (210 files, +23,242).
     Vendored tooling/scaffolding. **Regenerable** from a tool config.
  2. **`02650f4b1` — ALF-264** (2 files, ~+200). A genuine, well-scoped product
     code change to the webhook adapter. Worth keeping; a clean PR candidate.
- **Only 3 files are *modified* (not added)** and those are the entire recurring
  conflict surface:
  - `AGENTS.md` (framework appends a marked block; upstream edits this file often)
  - `gateway/platforms/webhook.py` (ALF-264 product change)
  - `tests/gateway/test_webhook_adapter.py` (ALF-264 tests — **also** edited by
    the `origin/main` fork layer, so it conflicts on essentially every rebase)
- **Biggest lever:** stop committing the 23k-line framework into the same branch
  you rebase, and stop appending to upstream-owned `AGENTS.md`. That removes the
  bulk of the noise and one of three real conflict points, leaving only the small
  ALF-264 patch to carry forward.

---

## 1. Repository topology (the most important finding)

There is **no `upstream` remote** configured. The relevant refs are:

| Ref | What it actually is |
|---|---|
| Public upstream | Tracked via tags (`v2026.4.x` … `v2026.5.16`). 11 tags present. |
| `origin/main` | **Fork integration branch.** = upstream tag **+ a layer of "custom fork patches"** (test infra, kanban, Slack fixes, `pnpm-lock.yaml`, website docs — 31 files, +3,603/−707 in commit `5ea3ae0fa`). It is **periodically rebased** onto new upstream tags (see commit message: *"custom fork patches rebased onto upstream v2026.5.16"*). |
| `custom/main` (HEAD) | = `origin/main` **+ AI-SDLC framework + ALF-264**. |

```
public upstream (tags vX) ──► origin/main (= upstream + "custom fork patches",
                                            REBASED each release)
                                   │
                                   └──► custom/main (= origin/main
                                                     + ai-sdlc-framework
                                                     + ALF-264)
```

**Implication.** You have **two stacked customization layers**, and they touch
**overlapping files** (notably `tests/gateway/test_webhook_adapter.py`, edited by
*both* layers). Every time the fork owner rebases `origin/main` onto a new
upstream tag, the SHAs change and `custom/main` must be re-based onto the new
`origin/main`. Because the layers overlap, that re-base re-conflicts on the same
handful of files each time. **This stacking is the structural source of the
"increasing conflicts," far more than the 23k-line framework.**

### Merge-base sanity check

```
merge-base(origin/main, custom/main) = b4da4444a
origin/main  ahead by 2 commits   (5ea3ae0fa, ee63a93b6)
custom/main  ahead by 2 commits   (a2b1b20e5, 02650f4b1)
```

The merge-base is recent because `origin/main` was rebased recently; the "2 vs 2"
is an artifact of that rebase, not a measure of true divergence.

---

## 2. Full catalog of the diff (`origin/main...custom/main`)

### 2.1 By change type

| Type | Count |
|---|---|
| Added (A) | **209** |
| Modified (M) | **3** |
| Deleted (D) | 0 |

The 4 "deletions" in the diffstat are line-deletions inside modified files, not
removed files.

### 2.2 The 3 modified files — the real conflict surface

| File | Source commit | Nature | Conflict risk |
|---|---|---|---|
| `AGENTS.md` | framework | Appends an `<!-- AI-SDLC:AGENTS START/END -->` block (+80 lines) at end of file | **Medium.** Upstream edits `AGENTS.md` regularly (recent upstream commits #29016, #24226, #25302 touch it). Append-at-end usually merges clean, but it keeps `AGENTS.md` in the conflict set. **Regenerable / removable.** |
| `gateway/platforms/webhook.py` | ALF-264 | Real feature: Linear `webhookDeliveryId` extraction + self-actor pre-flight filter (~+45 lines, contiguous) | **Low–Medium.** Genuine product code; conflicts only if upstream churns the same regions. Keep it. |
| `tests/gateway/test_webhook_adapter.py` | ALF-264 | Appends 2 new test classes (+177 lines) | **High (recurring).** This file is **also** modified by the `origin/main` fork layer (ALF-245, PR #14, INSECURE_NO_AUTH fix). Two layers appending to the same test file ⇒ conflicts on most rebases. |

### 2.3 The 209 added files — the framework (commit `a2b1b20e5`)

All net-new, almost entirely in **fork-only directories that do not exist
upstream** (`.specify/`, `.agents/`, `.claude/`, `specs/`, `CLAUDE.md`).
Insertions by area:

| Area | +lines | Exists upstream? | Collision risk |
|---|---|---|---|
| `.specify/extensions` | 3,942 | no | none today |
| `.claude/skills` | 3,724 | no (`.claude/` absent upstream) | none today |
| `.github/agents` | 3,517 | **`.github/` exists** (subdir new) | latent |
| `.specify/templates` | 3,372 | no | none today |
| `.specify/scripts` | 2,732 | no | none today |
| `.specify/presets` | 2,311 | no | none today |
| `.agents/skills` | 1,058 | no | none today |
| `docs/architecture`, `docs/context`, `docs/product`, `docs/patterns`, `docs/decisions`, `docs/README.md` | ~1,000 | **`docs/` exists** (only a PDF + `plans/`; these files new) | latent |
| `.github/prompts`, `.github/chatmodes`, `.github/instructions`, `.github/copilot-instructions.md` | ~300 | **`.github/` exists** (subdirs new) | latent |
| `AGENTS.md` block, `CLAUDE.md`, `.specify/init-options.json`, `.specify/extensions.yml` | ~150 | mixed | `CLAUDE.md` new; `AGENTS.md` = §2.2 |

**Key point:** because git only conflicts when both sides touch the same path,
these 209 files generate **zero conflicts today** — upstream has no files at
those paths. The only *latent* risk is the framework writing into shared dirs
(`.github/`, `docs/`) where upstream could later add a colliding path. No such
collision exists right now (verified: no `docs/README.md`, no `.github/agents/`,
etc. upstream).

### 2.4 The framework is regenerable, not hand-authored

`.specify/init-options.json` records exactly how it was produced:

```json
{ "ai": "claude", "integration": "claude", "preset": "aisdlc-core",
  "context_file": "CLAUDE.md", "speckit_version": "0.8.11", "ai_skills": true,
  "branch_numbering": "sequential", "script": "sh", "here": true }
```

Framework version is pinned (`0.13.1`, per `CLAUDE.md` / `AGENTS.md` block). This
means the entire 23k-line tree can be **reconstructed by re-running the
generator** rather than carried as committed source — which is what makes the
"don't track it on the rebase branch" options below viable.

---

## 3. Where the conflicts actually come from

Ranked by real impact:

1. **Stacked-layer overlap (structural).** `custom/main` sits on top of a
   `origin/main` that is itself rebased. Overlapping files
   (`tests/gateway/test_webhook_adapter.py`, potentially `webhook.py`) re-conflict
   each release. *This is the dominant cause.*
2. **Appending to upstream-owned `AGENTS.md`.** Keeps a hot upstream file in the
   conflict set unnecessarily — the same content could live in fork-owned files.
3. **A giant single commit on the rebase path.** Replaying a 23k-line commit
   during every rebase is slow, noisy, and obscures the 3 lines that actually
   matter, making real conflicts hard to spot.
4. **Latent path collisions** in shared dirs (`.github/`, `docs/`). Not biting
   yet; will eventually if upstream adds Copilot/agents tooling or top-level docs.

---

## 4. Pathways to minimize divergence

Options are grouped; they are **composable**, not mutually exclusive. Each lists
effort, payoff, and tradeoffs. Recommended combination at the end.

### Group A — Separate the two concerns (low effort, high clarity)

> The framework and the product change are unrelated and should never share a
> commit or a lifecycle.

- **A1. Keep ALF-264 as a thin, cherry-pickable patch series.** It already is its
  own commit. Always keep product patches *on top* so a rebase replays a tiny,
  legible stack. **Effort: trivial. Payoff: high legibility.**
- **A2. Upstream ALF-264.** The Linear `webhookDeliveryId` + self-actor filter is
  generically useful and self-contained. Submitting it to the public repo (or the
  fork's `origin/main` layer) makes it merge *away* — divergence that deletes
  itself. **Effort: low (PR). Payoff: permanent removal of 1–2 conflict files.**

### Group B — Get the framework off the rebase path (high effort-payoff ratio)

> The framework is regenerable tooling. It does not need to live on the branch you
> rebase against upstream. Pick **one**:

- **B1. Gitignore it / keep it untracked locally.** Add `.specify/`, `.agents/`,
  `.claude/`, `specs/`, `CLAUDE.md`, framework `.github/*` subdirs, and framework
  `docs/*` to `.gitignore`; regenerate via the pinned generator when needed.
  - *Pro:* `custom/main` becomes `origin/main` + just ALF-264 → near-zero
    conflict. *Con:* framework not shared via git; teammates must regenerate;
    `.gitignore` itself is upstream-owned (small, low-collision edit).
- **B2. Dedicated, never-merged branch for the framework** (e.g. `tooling/aisdlc`),
  or a **`git worktree`** so the files are present on disk but on a branch that is
  never in the rebase path.
  - *Pro:* still version-controlled; isolated. *Con:* two branches to manage.
- **B3. Separate repo + submodule / npm-style install.** Move the framework to its
  own repo; pull it in via submodule or the generator's package.
  - *Pro:* cleanest separation, shareable, versioned independently. *Con:* most
    setup; submodules add their own friction.
- **B4. Keep it committed but quarantine it.** Leave files tracked, but (a) stop
  touching shared files (see Group C) and (b) keep it as the **bottom** commit so
  the ALF-264 patch rides on top. Lowest-change option if you want it in-tree.
  - *Pro:* no workflow change. *Con:* still replays 23k lines each rebase; latent
    `.github/`/`docs/` collisions remain.

### Group C — Stop modifying upstream-owned files (low effort, removes conflict points)

- **C1. Don't append to `AGENTS.md`.** Move the AI-SDLC block into the fork-owned
  `CLAUDE.md` (or a new `docs/aisdlc/README.md`) and have `CLAUDE.md` link to it.
  The block is marker-delimited and tool-generated, so this is a generator-config
  or one-time edit. **Removes `AGENTS.md` from the conflict set entirely.**
- **C2. Relocate framework `docs/*` and `.github/*` into a non-shared namespace**
  (e.g. everything under `.specify/` / `.agents/`, nothing under top-level `docs/`
  or `.github/`). Eliminates all *latent* collisions. Depends on what the
  generator allows; may need a post-generate move script.

### Group D — Make the rebase itself cheaper (process)

- **D1. `git rerere`.** Enable `git config rerere.enabled true` so repeated
  conflict resolutions (e.g. the recurring `test_webhook_adapter.py` conflict)
  are auto-replayed. **Effort: one command. Payoff: immediate for B4/status-quo.**
- **D2. Document a fixed rebase runbook** (`origin/main` rebased → fetch → rebase
  `custom/main` → cherry-pick ALF-264). Reduces per-release thrash regardless of
  other choices.
- **D3. Split the ALF-264 test additions into a *new* test file**
  (`tests/gateway/test_webhook_alf264.py`) instead of appending to
  `test_webhook_adapter.py`. Removes the single highest-frequency conflict file,
  since the fork layer keeps editing the shared file. **Effort: low. Payoff:
  high.**

---

## 5. Recommended combination (for discussion)

A pragmatic, low-risk sequence that attacks the dominant causes first:

1. **D3 + D1 now (today):** move ALF-264 tests to their own file; enable
   `rerere`. Kills the most frequent conflict and auto-handles the rest. *Minutes.*
2. **C1 (this week):** stop appending to `AGENTS.md`; relocate the block to
   `CLAUDE.md`. Removes a second conflict file. *~30 min.*
3. **A2 (when ready):** PR ALF-264 to upstream / the fork layer so it eventually
   merges away. *Removes the patch entirely over time.*
4. **B1 or B2 (the big one):** take the regenerable framework off the rebase
   path. After steps 1–3, `custom/main` is essentially `origin/main` + a tiny
   patch, so a clean upstream pull becomes routine.

After steps 1–4, a release pull is: *fetch new `origin/main` → rebase → replay
one small patch (or nothing, once A2 lands) → regenerate framework if desired.*

---

## 6. Open questions to resolve before committing to a plan

1. **Is `origin/main` your branch to change, or someone else's?** If you own the
   fork layer, the cleanest fix is to fold ALF-264 *into* the `origin/main` patch
   set (A2) rather than stack a third layer.
2. **Does the AI-SDLC framework need to be shared via git** with teammates/CI, or
   is it personal dev scaffolding? This decides B1 (ignore) vs B2/B3 (tracked but
   isolated). If CI runs Spec-Kit, it must remain reachable.
3. **Does the generator (`aisdlc` v0.13.1 / Spec-Kit 0.8.11) support** (a)
   emitting the `AGENTS.md` content to a different file, and (b) confining output
   to non-shared dirs? That determines how clean C1/C2 can be.
4. **How do you currently pull upstream** — rebase or merge `custom/main`, and is
   it ever force-pushed? Confirms the workflow the runbook (D2) should encode.
5. **Is keeping a pristine local `main`** (mirroring true public upstream, distinct
   from the customized `origin/main`) worthwhile, so you can see *real* upstream
   divergence separately from the fork layer?

---

---

## ✅ Agreed plan & execution status (updated 2026-05-31)

After reviewing the catalog above, we refined the topology understanding and made
concrete decisions. **`origin/main` is the fork's own integration branch and its
"custom fork patches" layer was a mistake** — going forward `main` should mirror
pristine public upstream (`nousresearch/hermes-agent`) and *all* customization
lives on `custom/main`. The genuine fork customizations turned out to be a
15-commit series (ALF-225 → ALF-268) on top of the v2026.5.16 base
(`a84cec61c`), of which we keep only two.

### Decisions

| Group | Decision | Rationale |
|---|---|---|
| ai-sdlc framework | **Remove from VC** (keep on disk, gitignore) | Regenerable tooling; not yet used; was 209 of 212 changed files |
| pnpm migration (E) | **Revert to upstream** | Perpetual npm/pnpm conflict source; not worth it |
| conftest/test-infra (F) | **Revert to upstream** | High-churn shared file; heavy conflict risk |
| Slack threading fixes (A) | **Revert (drop)** | Only relevant with `reply_in_thread=false`, which we don't run |
| execute_code emoji (G) | **Revert (drop)** | Cosmetic; needless conflict point |
| kanban tests (C), docs (H) | **Revert to upstream** | Not essential |
| **ALF-263 launchd (D)** | **KEEP** | Deployment necessity (launchd fd limit); ~zero conflict |
| **ALF-264 webhook (B)** | **KEEP** | Genuine feature; builds cleanly on upstream scaffolding |
| Execution style | **Revert-forward** (no force-push on `custom/main`) | It's the shared default branch |

### What was executed (on review branch `cleanup/minimize-fork-divergence`)

`custom/main` was **not** modified. A review branch was cut from it with three commits:

1. `docs: add fork divergence analysis report`
2. `chore: untrack ai-sdlc-framework, keep on disk via .gitignore` — 209 files `git rm --cached`, kept on disk, gitignored
3. `revert: restore non-essential fork customizations to upstream` — 30 files reconciled to the upstream base; `webhook.py`/`test_webhook_adapter.py` rebuilt as *upstream + ALF-264 only* (ALF-245/PR#14 hunks stripped)

**Resulting divergence from pristine upstream (`a84cec61c`): 6 files** —
`gateway/platforms/webhook.py` + `tests/gateway/test_webhook_adapter.py` (ALF-264),
`hermes_cli/gateway.py` + `tests/hermes_cli/test_gateway_service.py` (ALF-263),
`.gitignore` (framework ignores), and this report. Down from 212.

### Verification status

- **Structural: PASS.** ALF-263 and ALF-264 both cherry-pick onto pristine
  upstream with **zero conflicts**; the kept test files are taken verbatim from
  those clean cherry-picks; the final tracked diff vs upstream is *exactly* the
  four keep-files (line counts match the original commit stats).
- **Test run: NOT performed locally.** The codebase requires Python ≥3.10
  (runtime `str | object`), and this machine only has Xcode's Python 3.9.6 (no
  Homebrew/pyenv). **Run the suite — or let CI — before fast-forwarding
  `custom/main`.**

### Execution log — COMPLETED 2026-05-31

1. ✅ **Reviewed** the `cleanup/minimize-fork-divergence` branch.
2. ✅ **Ran the full suite** (25,048 tests): 99.8% pass; all 50 failures proven
   byte-identical to pristine upstream (environmental — cloud creds, ambient
   creds, Linux-only systemd/WSL). **Zero regressions.** Both kept features pass.
   This also cleared the **ALF-329 caveat**: `custom/main` is green (modulo
   environment) without `origin/main`'s "fix 19 failing tests" commit, so that
   commit was patching the redundant-squash breakage, not real upstream fixes.
3. ✅ **Fast-forwarded `custom/main`** `02650f4b1 → cfc1a9de1` and **pushed** to
   `origin/custom/main`.
4. ✅ **Added the `upstream` remote** (`nousresearch/hermes-agent`) and fetched.
5. ✅ **Reset `origin/main` to pristine `a84cec61c`** (v2026.5.16 base) via
   `--force-with-lease`. `custom/main` now sits cleanly on top of it; divergence
   is exactly the 6 files above.
6. ✅ **Enabled `git rerere`.**

### Remaining (optional / when ready)

- **Branch protection (GitHub settings, your task):** keep default branch =
  `custom/main`; protect `main` as fast-forward-only / no direct commits.
- **Adopt the latest release (Phase E):** public upstream is at **`b3aaf2676`
  (v2026.5.29.2)**, ahead of the `v2026.5.16` base `main` now points to. When
  ready: `git fetch upstream && git checkout main && git merge --ff-only
  upstream/main && git push origin main`, then `git checkout custom/main && git
  merge main` (only the 4 ALF files can conflict), test, push.
- **Steady-state rule:** never commit to `main`; never rebase `custom/main`;
  merge `main` → `custom/main` per release.
- **Framework on disk:** the gitignored ai-sdlc files were removed from disk
  during the branch switch (recoverable from `a2b1b20e5` or `aisdlc init`);
  restore on request.

---

## Appendix — commands used

```bash
git merge-base origin/main custom/main
git rev-list --left-right --count origin/main...custom/main
git diff --name-status origin/main...custom/main          # 209 A / 3 M
git diff --numstat   origin/main...custom/main            # sizing by area
git show --stat a2b1b20e5   # framework commit (210 files, +23,242)
git show --stat 02650f4b1   # ALF-264 (2 files)
git show --stat 5ea3ae0fa   # origin/main "custom fork patches" layer
git log --oneline origin/main -- tests/gateway/test_webhook_adapter.py  # overlap proof
git show custom/main:.specify/init-options.json           # regenerator config
```
