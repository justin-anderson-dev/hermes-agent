# Project Context

This `docs/` folder is project-owned. It holds the durable repo context that later AI-SDLC, Spec Kit, and agent workflows should read instead of rediscovering the same information on every task.

Use it to capture repo-specific product, architecture, navigation, and decision context that is worth maintaining over time.

## Bootstrap-First Workflow

Start here after `aisdlc init`:

1. Ask your agent to follow `.agents/prompts/bootstrap-context-repo.md`.
2. Review the refreshed core docs plus `docs/context/bootstrap-report.md` and `docs/context/gaps.md`.
3. Confirm or correct the assumptions, stale areas, and open questions the bootstrap surfaced.
4. Commit the first-pass context before starting feature work.

## Core Files to Keep Current

- [`product/overview.md`](product/overview.md): what the project does today, who it serves, and the implementation-relevant rules that matter
- [`architecture/overview.md`](architecture/overview.md): the real system shape, execution flow, integrations, and key delivery mechanics
- [`product/glossary.md`](product/glossary.md): repo-specific terminology, abbreviations, and synonyms to avoid
- [`context/index.yaml`](context/index.yaml): small routing manifest used by later AI-SDLC phases
- [`context/repo-map.md`](context/repo-map.md): high-signal source, test, config, and workflow entrypoints
- [`context/gaps.md`](context/gaps.md): unresolved questions, stale context, and weak signals that should not be guessed through
- [`context/bootstrap-report.md`](context/bootstrap-report.md): snapshot review artifact from the last bootstrap pass
- [`.specify/memory/constitution.md`](../.specify/memory/constitution.md): durable project principles and workflow guardrails

## Directory Structure

| Directory | Purpose |
|-----------|---------|
| [`architecture/`](architecture/overview.md) | System design, runtime shape, integrations, sample references, and ADRs |
| [`product/`](product/overview.md) | Business context, glossary, and implementation-relevant rules |
| [`patterns/`](patterns/README.md) | Reusable approaches that future work should follow by default |
| [`decisions/`](decisions/README.md) | Durable implementation decisions that are narrower than full ADRs |
| [`context/`](context/README.md) | Routing, repo navigation, uncertainty tracking, and bootstrap review context |

## Optional Sample Files

These files are included so teams can build out architecture docs manually if they do not want to run the bootstrap immediately:

- [`architecture/adr/0001-example-decision.md`](architecture/adr/0001-example-decision.md)
- [`architecture/database-schema-example.md`](architecture/database-schema-example.md)

Treat them as reference scaffolds until they are adapted to the real repo. Do not treat untouched sample content as project truth.

## Working Rules

- Prefer specific observed repo evidence over polished but generic prose.
- Keep durable docs short enough to maintain and concrete enough to guide feature work.
- Label assumptions when the repo does not prove something directly.
- Keep unresolved questions in `docs/context/gaps.md` instead of burying them in always-loaded agent files.
- Treat sample or example docs as reference material until they are clearly adapted for this repo.
- Use `/speckit.aisdlc.triage` when you need to turn raw intake into a repo-aware recommendation before opening a feature spec.
- Use `/speckit.aisdlc.mockup` after `/speckit.specify` when UI-relevant stories need static product/design review artifacts before planning.
- Use `/speckit.aisdlc.promote` after meaningful feature work so the docs stay current without rerunning the full bootstrap every time.
