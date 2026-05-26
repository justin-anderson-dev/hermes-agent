# Bootstrap the AI-SDLC Context Repo

You are bootstrapping the durable AI-SDLC context for this repository.

Your job is to inspect the repository, derive the highest-signal project context from real evidence, and create or update the durable context set that later Spec Kit and agent workflows will rely on.

## Primary Deliverables

Create or update exactly these primary files:

- `docs/product/overview.md`
- `docs/architecture/overview.md`
- `docs/product/glossary.md`
- `docs/context/repo-map.md`
- `.specify/memory/constitution.md`
- `docs/context/bootstrap-report.md`

Do not replace this file set with a different context system unless the human explicitly asks for it.

## Support Files For Later AI-SDLC Phases

If this repository contains `.specify/presets/aisdlc-core/` or `.specify/extensions/aisdlc-context/`, later AI-SDLC phases expect these support files to exist:

- `docs/context/index.yaml`
- `docs/context/gaps.md`

If they already exist, update them.
If they do not exist yet, create them with minimal repo-specific content.
Do not create any other durable docs unless repo evidence clearly justifies them or the human asks.

## Operating Rules

- Prefer observed repo evidence over polished but generic prose.
- For existing repos, prefer code, tests, manifests, scripts, CI config, and current docs over aspiration or guesswork.
- For thin repos, prefer the most explicit current brief, spec, ADR, or setup artifacts over starter comments.
- Read existing files before editing them.
- Preserve accurate project-authored content. Refine or reorganize it rather than rewriting it unnecessarily.
- Replace scaffold starter text, placeholder rows, and generic example content only when you can replace it with repo-specific content.
- Treat untouched sample files such as `docs/architecture/adr/0001-example-decision.md` and `docs/architecture/database-schema-example.md` as reference material, not as authoritative repo evidence.
- If a statement is not directly supported by repo evidence, label it as an assumption or open question.
- Keep durable project context in `docs/` and `.specify/memory/constitution.md`, not in always-loaded agent files.
- Do not auto-populate `docs/patterns/`, `docs/decisions/`, or `docs/architecture/adr/` during bootstrap unless the repo already contains clear evidence for a stable pattern or accepted decision.

## First: Classify The Repository

Classify the repo before writing docs.

### Existing project

Treat the repo as an existing project when there is meaningful implementation evidence, such as:

- source code
- tests
- package manifests or dependency files
- CI or workflow configuration
- scripts
- infrastructure config
- current docs or ADRs

### New or thin project

Treat the repo as new or thin when implementation evidence is sparse and the repo mostly contains briefs, starter code, specs, ADRs, or setup files.

For a thin repo, prefer these sources in order:

1. README or product brief
2. current specs and ADRs
3. manifests and starter code
4. issue context or project notes

If the evidence is too thin to produce credible durable context without inventing core product facts, stop and ask the human for a minimal intake brief instead of fabricating details.

## Evidence Collection Rules

Before writing, inspect the highest-signal repo surfaces that exist. Prioritize:

- main source entrypoints and core modules
- highest-signal tests
- package manifests, lockfiles, and scripts
- CI workflows, release config, and deployment metadata
- current docs, ADRs, and architecture notes

When sources disagree:

- for existing repos, prefer code and tests over prose
- for thin repos, prefer the most recent explicit product or spec artifacts over vague starter comments

For every durable claim you make, know which file paths support it.
Use those file paths in evidence sections and in `docs/context/bootstrap-report.md`.

## File Contracts

### `docs/product/overview.md`

Purpose:

- capture what the project does today
- capture who it serves or what workflow it supports
- capture implementation-relevant domain rules and constraints

Include:

- current scope and outcomes
- primary users, operators, or consuming systems
- implementation-relevant rules that show up in code, tests, configs, or workflows
- `Observed Evidence`
- `Assumptions and Open Questions`

Exclude:

- roadmap language
- marketing copy
- speculative product intent
- implementation tree dumps

### `docs/architecture/overview.md`

Purpose:

- capture the real system shape of this repo

Include:

- primary execution entrypoints
- major modules and responsibilities
- important runtime or execution flows
- external integrations and platform surfaces
- build, test, and delivery mechanics
- `Observed Evidence`
- `Assumptions and Open Questions`

Exclude:

- abstract architecture filler
- target-state redesigns that are not in the repo
- feature-specific implementation plans

Use concrete repo paths where possible.

### `docs/product/glossary.md`

Purpose:

- keep repo-specific terminology consistent across docs, specs, and prompts

Include:

- domain terms that matter for future work
- repo-specific concepts
- names used in code, configs, tests, workflows, and durable docs
- synonyms to avoid when precision matters
- abbreviations or acronyms that are repo-relevant

Exclude:

- generic programming vocabulary
- terms with no durable value
- invented terminology not used by the repo

Every retained term should have evidence or notes.

### `docs/context/repo-map.md`

Purpose:

- give humans and agents the fastest high-signal orientation path through the repo

Include:

- key source entrypoints
- key test files
- key manifests and configs
- important scripts and workflow files
- important durable docs that should be read first
- one short note for why each path matters

Exclude:

- full tree dumps
- low-signal directories
- transient feature files unless they are central to navigation
- untouched sample or example docs that have not been adapted for this repo

This should be the quickest durable “where to look first” file.

### `.specify/memory/constitution.md`

Purpose:

- define durable project-wide rules, principles, and workflow guardrails

Include:

- rules that are project-wide, durable, and actionable
- terminology and constraints that later Spec Kit phases should preserve
- guidance grounded in the repo’s actual shape and documentation

Exclude:

- feature-specific decisions
- temporary workarounds
- generic filler
- long prose that belongs in `docs/`

If a constitution already exists:

- preserve useful project-specific guidance
- update it carefully instead of overwriting it wholesale
- keep versioning and amendment fields coherent if they already exist
- align it with the durable docs written in this pass

### `docs/context/bootstrap-report.md`

Purpose:

- record what happened during this bootstrap pass
- make human review easy
- separate snapshot review notes from durable project truth

Include:

- repo classification
- evidence sources used
- files created or updated
- assumptions made
- missing, stale, or conflicting context
- follow-up questions for a human reviewer
- any scaffold files left intentionally untouched and why

Exclude:

- durable product or architecture statements that belong in the canonical docs
- repeated prose copied from the overview docs

Treat this as a report for review, not as the canonical source of truth.

### `docs/context/index.yaml`

Purpose:

- act as the small routing manifest for later AI-SDLC phases

Each entry should include:

- `id`
- `category`
- `path`
- `summary`
- `source_paths`
- `confidence`
- `last_verified`

Minimum coverage:

- `docs/product/overview.md`
- `docs/architecture/overview.md`
- `docs/product/glossary.md`
- `docs/context/repo-map.md`
- `.specify/memory/constitution.md`

Keep it concise and machine-friendly.

### `docs/context/gaps.md`

Purpose:

- hold durable unresolved questions, stale areas, and weak signals

Include:

- important unknowns that later phases should not guess through
- stale docs or mismatches that need review
- unresolved conflicts between code, tests, and prose

Exclude:

- feature task lists
- implementation TODOs that belong in specs or tasks

## Brownfield Update Behavior

Before editing any existing durable doc:

1. Read the full existing file.
2. Preserve accurate project-authored content.
3. Remove or replace starter, template, or example text that is clearly not project-specific.
4. If a section is partly useful but partly stale, keep the verified parts and record the uncertainty in `docs/context/bootstrap-report.md` and `docs/context/gaps.md`.
5. Do not delete potentially valuable project content just because the repo evidence is incomplete. Mark uncertainty explicitly instead.

## Suggested Execution Order

1. Inspect the repo and classify it.
2. Gather high-signal evidence with source paths.
3. Build or update `docs/context/repo-map.md`.
4. Draft or update `docs/product/overview.md`.
5. Draft or update `docs/architecture/overview.md`.
6. Draft or update `docs/product/glossary.md`.
7. Draft or update `.specify/memory/constitution.md`.
8. Draft or update `docs/context/index.yaml` and `docs/context/gaps.md`.
9. Write `docs/context/bootstrap-report.md` last so it reflects the actual work, uncertainty, and follow-up items.

## Completion Standard

You are done when:

- the six primary deliverables exist
- support files required by later AI-SDLC phases exist and are repo-specific
- durable docs are grounded in evidence
- assumptions and uncertainty are labeled explicitly
- starter, template, and example text has been removed or intentionally left with explanation
- the bootstrap report makes review easy
- no obvious generic filler remains
