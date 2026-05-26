# Getting Started

This guide is the shortest reliable path from `aisdlc init` to usable, repo-specific context.

## What AI-SDLC Adds

After initialization, the repo contains:

- `.agents/` for framework-managed docs, prompts, and shared skills
- `.specify/` for the pinned Spec Kit core plus AI-SDLC overlays
- `docs/` for project-owned context
- `specs/` for feature specs, plans, tasks, and promoted context
- tool-native integration files for the agents you selected

Ownership model:

- Framework-managed and refreshable: `.agents/`, generated agent integration files, most `.specify/` templates/scripts
- Project-owned: `docs/`, `specs/`, `.specify/memory/constitution.md`

## Primary Bootstrap Path

The primary bootstrap path is one AI-SDLC-managed prompt:

```text
.agents/prompts/bootstrap-context-repo.md
```

Point your coding agent at that file and tell it to follow the prompt to completion.

Example:

```text
Open `.agents/prompts/bootstrap-context-repo.md` and complete the bootstrap for this repository. Create or update the requested files, refresh `docs/context/index.yaml` and `docs/context/gaps.md`, label assumptions clearly, and leave `docs/context/bootstrap-report.md` ready for review.
```

The prompt is designed for both:

- existing projects, where code and tests are the primary evidence
- new projects, where briefs, specs, ADRs, and starter code may be the main evidence

## Optional Community Extensions

During `aisdlc init`, AI-SDLC can optionally install a curated set of third-party Spec Kit community extensions:

- `spec-kit-bugfix`
- `spec-kit-iterate`
- `spec-kit-azure-devops`
- `spec-kit-jira`

Default recommendation:

- `spec-kit-bugfix`
- `spec-kit-iterate`

These are optional and community-maintained. AI-SDLC pins the curated install sources, but it does not audit or support extension code.

Anything outside that curated init list should be installed later with:

```bash
aisdlc extension add <extension-name>
```

`spec-kit-brownfield` is intentionally not part of the curated init flow because AI-SDLC already provides its own bootstrap path through `.agents/prompts/bootstrap-context-repo.md`.

## What the Bootstrap Produces

The bootstrap prompt creates or updates this primary context set:

- `docs/product/overview.md`
- `docs/architecture/overview.md`
- `docs/product/glossary.md`
- `docs/context/repo-map.md`
- `.specify/memory/constitution.md`
- `docs/context/bootstrap-report.md`

It also refreshes the support files later AI-SDLC phases depend on:

- `docs/context/index.yaml`
- `docs/context/gaps.md`

`docs/context/bootstrap-report.md` is the review artifact. It should record:

- evidence sources used
- assumptions made
- missing or stale context
- follow-up questions for a human reviewer

## Existing Repo Bootstrap

Use the bootstrap prompt immediately after `aisdlc init` when the repo already contains meaningful code.

The agent should derive context primarily from:

- source files
- tests
- manifests and scripts
- CI or workflow configuration
- current docs and ADRs

Expected human review:

1. Read `docs/context/bootstrap-report.md`.
2. Confirm or correct the listed assumptions.
3. Tighten any product or architecture statements that need human judgment.
4. Commit the resulting docs and constitution before starting feature work.

## New Project Bootstrap

If the repo is mostly briefs, specs, ADRs, or starter code, use the same bootstrap prompt.

For new projects, the agent should prefer:

1. the README or product brief
2. open specs and ADRs
3. manifests and starter code
4. any setup or workflow notes already in the repo

If the repo is too thin to support a credible bootstrap, the prompt instructs the agent to stop and ask for a minimal intake brief instead of inventing core product facts.

## After Bootstrap: Start Feature Work

Once bootstrap has created `.specify/memory/constitution.md`, use `/speckit.aisdlc.triage` first when work starts as raw intake such as feedback, bug reports, call notes, brainstorming notes, or sales summaries.

Then run the normal feature loop:

1. `/speckit.specify`
2. Optional: `/speckit.aisdlc.mockup` when UI-relevant stories need product/design review before planning
3. `/speckit.clarify`
4. `/speckit.plan`
5. `/speckit.tasks`
6. `/speckit.analyze`
7. `/speckit.implement`
8. `/speckit.checklist`
9. `/speckit.aisdlc.promote`

Use `/speckit.constitution` manually when:

- bootstrap has not been run yet
- the constitution needs an intentional rewrite
- the team wants to revise project principles independent of a bootstrap pass

## Rerun Guidance

Rerun the bootstrap prompt when:

- the repo’s architecture changes materially
- domain language or product scope changes
- a major integration or workflow is added
- the current docs are clearly stale

Use `/speckit.aisdlc.promote` after major feature work so durable learnings flow back into `docs/` and feature context logs without rerunning the full bootstrap every time.

## Advanced: Manual Recovery

If you intentionally do not want the one-shot bootstrap path, you can still recover docs manually:

- update `docs/product/overview.md`
- update `docs/architecture/overview.md`
- update `docs/product/glossary.md`
- update `docs/context/repo-map.md`
- update `docs/context/index.yaml`
- update `docs/context/gaps.md`
- update `.specify/memory/constitution.md`
- add a short `docs/context/bootstrap-report.md` explaining evidence, assumptions, and open questions

This is the fallback path, not the recommended one.

## Skills

`aisdlc init` preinstalls `skill-creator` at:

```text
.agents/skills/skill-creator
```

Use it when you want to create project-specific skills on top of the AI-SDLC workflow.
