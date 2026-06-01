# Maintaining this fork & syncing upstream

This repo is a fork of [`nousresearch/hermes-agent`](https://github.com/nousresearch/hermes-agent).
This runbook is how we stay close to upstream while carrying a small set of
intentional customizations. (For the full history/rationale of how we got here,
see [fork-divergence-analysis.md](fork-divergence-analysis.md).)

## Branch model

```
nousresearch/hermes-agent ──(remote: upstream)──► main ──merge per release──► custom/main
        (public upstream)        pristine mirror           default branch, what we run
                                  FF-only, never commit       = upstream + our customizations
```

- **`main`** — a pristine mirror of public upstream. It only ever **fast-forwards**
  to `upstream/main`. **Never commit to it, never rebase it.** Protected by the
  GitHub ruleset `main-fast-forward-only` (`non_fast_forward` + `deletion`).
- **`custom/main`** — the **default branch**, what everyone runs and cuts feature
  branches from. It is `upstream + our customizations`. **Never rebase it** (it's
  shared); integrate upstream by **merging `main` into it**.

## One-time setup (fresh clone)

```bash
git remote add upstream https://github.com/nousresearch/hermes-agent.git
git fetch upstream --tags
git config rerere.enabled true        # auto-replays known conflict resolutions
```

Dev env (Python ≥3.11; the repo uses `uv`):

```bash
uv venv .venv --python 3.11
uv pip install -e ".[all,dev,messaging]"
```

## Per-release upstream sync (the routine)

```bash
# 1. Mirror the new release onto main (fast-forward only)
git fetch upstream --tags
git checkout main
git merge --ff-only upstream/main
git push origin main

# 2. Merge it into our line
git checkout custom/main
git merge main
#    → conflicts, if any, are almost always confined to the customization
#      files below. rerere replays past resolutions. Resolve = keep BOTH our
#      change and the upstream change (see notes per file).

# 3. Validate, then publish
bash scripts/run_tests.sh -j "$(sysctl -n hw.ncpu 2>/dev/null || nproc)"
git push origin custom/main
```

> **Local test failures on macOS are expected and not regressions.** The suite is
> built for Linux CI. ~45 tests fail locally from environment, not code: Linux-only
> `systemd`/WSL, cloud-integration tests needing creds (Bedrock/Modal/Vercel),
> ambient-credential leakage (Anthropic token resolution), and a few subprocess/TUI
> timing tests. To confirm a failure isn't ours:
> `git diff upstream/main HEAD -- <failing_test_file>` — an empty diff means the file
> is identical to upstream, so it fails there too. Only failures in the
> customization files below could be real regressions.

## Our intentional customizations (preserve these on every merge)

The **entire** divergence from upstream is these files — keep it that way:

| File(s) | What | Ticket |
|---|---|---|
| `gateway/platforms/webhook.py`, `tests/gateway/test_webhook_adapter.py` | Linear `webhookDeliveryId` (body) extraction for idempotency + Alfred self-action pre-flight filter (`self_actor_id`) to prevent webhook feedback loops | ALF-264 |
| `hermes_cli/gateway.py`, `tests/hermes_cli/test_gateway_service.py` | launchd `Soft/HardResourceLimits` NumberOfFiles = 65536 in the generated plist (avoids `EMFILE` on macOS) | ALF-263 |
| `.gitignore` | ignores for the gitignored ai-sdlc framework (below) | — |
| `docs/fork-divergence-analysis.md`, `docs/upstream-sync.md` | this documentation | — |

**Conflict-resolution notes:**
- `webhook.py` — upstream owns the `delivery_id` chain and webhook auth. Keep our
  body `webhookDeliveryId` fallback **and** any upstream header additions (e.g.
  `svix-id`) in the same `or`-chain; keep the `self_actor_id` pre-flight block.
- `.gitignore` — keep upstream's new entries **and** our framework block.

If upstream ever implements ALF-263/ALF-264 itself, drop ours and shrink the diff.

## The ai-sdlc / Spec-Kit framework

It is **gitignored and kept out of version control** (it was a large, regenerable
vendored tree that dominated the fork diff). Regenerate locally with `aisdlc init`
(config in `.specify/init-options.json`, recoverable from git history). If we adopt
it for real later, confine it to `.specify/` and do **not** append to the
upstream-owned `AGENTS.md`.

## Rules of thumb

- Never commit to `main`; never rebase `custom/main`.
- All customizations land on `custom/main` (or feature branches cut from it).
- Keep the divergence minimal — small diff = cheap merges. Prefer upstreaming a
  change over carrying it.
