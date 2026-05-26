---
name: "speckit-aisdlc-preflight"
description: "Build a concise repo-specific context briefing before core Spec Kit phases."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "aisdlc-framework"
  source: ".specify/templates/commands/aisdlc.preflight.md"
user-invocable: true
disable-model-invocation: false
argument-hint: "Optional context or focus for the AI-SDLC preflight briefing"
---

When a hook command name contains dots, convert it to the matching skill name by replacing dots with hyphens.
Example: `speckit.aisdlc.preflight` -> `/speckit-aisdlc-preflight`.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Shared Contract

Follow `.specify/extensions/aisdlc-context/references/context-analyzer.md` when it is available in the target project. If that file is not available, apply the same rules directly.

## Outline

1. Determine the active feature context when possible:
   - If `.specify/feature.json` exists, read `feature_directory`.
   - If a current feature directory is available, note `specs/{feature}/context/` and `specs/{feature}/context/promotion-log.md` if they exist.

2. Review the durable project context in this priority order:
   - `docs/context/index.yaml`
   - `docs/context/gaps.md`
   - `.specify/memory/constitution.md`
   - `docs/README.md`
   - `docs/architecture/overview.md`
   - `docs/product/overview.md`
   - `docs/product/glossary.md`
   - `docs/patterns/`
   - `docs/context/`
   - `docs/decisions/`
   - `docs/architecture/adr/`

3. If `docs/context/index.yaml` is missing or obviously stale, inspect current source-of-truth files directly.
   - top-level README files
   - dependency manifests and lockfiles
   - test and CI configuration
   - schema, contract, migration, and infra files
   - module or service entrypoints relevant to the request

4. Select only the repo-specific context that is relevant to the current phase and user request.
   - Prefer established terminology, patterns, and constraints over generic suggestions.
   - Surface missing or stale context explicitly instead of silently filling gaps with generic assumptions.

5. Produce a concise briefing with exactly these sections:
   - `## Governing Constraints`
   - `## Existing Patterns To Reuse`
   - `## Terminology To Preserve`
   - `## Relevant Source Paths`
   - `## Missing Or Stale Context`

6. Do not edit files in this hook. The goal is to make the next command context-aware.

7. If the durable context scaffold is missing, explicitly recommend running `/speckit-aisdlc-bootstrap` before relying on generic recommendations.
