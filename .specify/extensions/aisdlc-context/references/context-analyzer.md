# AI-SDLC Context Analyzer Contract

Use this contract whenever AI-SDLC commands need repo-specific context.

## Purpose

The goal is to make Spec Kit outputs specific to the target codebase, not generic to a language or framework.

## Canonical Sources

Review sources in this order:

1. `docs/context/index.yaml`
2. `.specify/memory/constitution.md`
3. feature-scoped context under `specs/*/context/`
4. durable docs under `docs/`
5. current source-of-truth files in the repo

## Inventory Rules

When the context manifest is missing or stale, inspect:

- top-level README files
- dependency manifests and lockfiles
- test and CI configuration
- infrastructure and deployment config
- API contracts, schemas, and migrations
- service entrypoints, module boundaries, and integration adapters

## Manifest Requirements

`docs/context/index.yaml` entries should include:

- `id`
- `category`
- `path`
- `summary`
- `source_paths`
- `confidence`
- `last_verified`

## Freshness Rules

Mark context as stale when:

- the source paths changed materially after the last verification date
- the durable doc is missing for a required category
- the doc summary no longer matches repo evidence
- the doc still contains obvious scaffold markers, placeholder rows, or untouched sample content
- an optional sample file such as `docs/architecture/adr/0001-example-decision.md` or `docs/architecture/database-schema-example.md` has not been adapted to the repo

## Phase Focus

- bootstrap: create the durable context baseline
- preflight: select the most relevant context for the next phase
- promote: compare planned or implemented changes against the durable baseline

## Output Rule

When confidence is weak, record the gap explicitly. Do not replace missing repo knowledge with generic best-practice filler.
Treat untouched scaffold and sample docs as templates to adapt, not as durable repo truth.
