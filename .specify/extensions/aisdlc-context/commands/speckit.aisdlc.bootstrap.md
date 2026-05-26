---
description: Bootstrap durable AI-SDLC context for an existing codebase.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Shared Contract

Follow `.specify/extensions/aisdlc-context/references/context-analyzer.md` when it is available in the target project. If that file is not available, apply the same rules directly.

## Outline

1. Inspect the current repository as a brownfield codebase.
   - Review top-level README files, manifests, lockfiles, CI config, test config, infra config, schema files, API contracts, migration files, and existing architecture/product docs.
   - Identify the primary runtime(s), entrypoints, test commands, deployment surfaces, and integration boundaries.

2. Build an evidence-backed inventory for durable project context.
   - Prefer current source-of-truth files over assumptions.
   - Track source paths for every durable statement you make.
   - Record confidence as `high`, `medium`, or `low`.

3. Ensure the durable context scaffold exists.
   - Primary deliverables:
     - `docs/product/overview.md`
     - `docs/architecture/overview.md`
     - `docs/product/glossary.md`
     - `docs/context/repo-map.md`
     - `.specify/memory/constitution.md`
     - `docs/context/bootstrap-report.md`
   - Support files for later AI-SDLC phases:
     - `docs/context/index.yaml`
     - `docs/context/gaps.md`
   - Reference scaffolds to preserve unless the user removes them intentionally:
     - `docs/architecture/adr/template.md`
     - `docs/architecture/adr/0001-example-decision.md`
     - `docs/architecture/database-schema-example.md`

4. Populate or refresh the scaffold without overwriting curated content unnecessarily.
   - Preserve high-quality existing docs.
   - Fill obvious gaps with concise, repo-specific content.
   - Treat untouched scaffold or sample files as reference material, not as authoritative repo evidence.
   - Capture unknowns and weak signals in `docs/context/gaps.md` instead of inventing certainty.

5. Build `docs/context/index.yaml` as the context manifest for later commands.
   - Each entry must include:
     - `id`
     - `category`
     - `path`
     - `summary`
     - `source_paths`
     - `confidence`
     - `last_verified`

6. Refresh `.specify/memory/constitution.md`.
   - Keep only durable, project-wide rules and terminology.
   - Base the constitution on repo evidence and the durable docs created or refreshed in this pass.

7. End with a required summary:

```md
### Bootstrap Summary

- Durable docs created or refreshed:
  - ...
- Context manifest updated: yes/no (`docs/context/index.yaml`)
- Constitution refreshed: yes/no (`.specify/memory/constitution.md`)
- Key gaps recorded:
  - ...
- Highest-risk assumptions:
  - ...
```
