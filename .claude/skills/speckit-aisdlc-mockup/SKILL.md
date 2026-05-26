---
name: "speckit-aisdlc-mockup"
description: "Generate static UI mockups and handoff notes for UI-relevant stories in the active Spec Kit feature spec."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "aisdlc-framework"
  source: ".specify/templates/commands/aisdlc.mockup.md"
user-invocable: true
disable-model-invocation: false
argument-hint: "Optional feature directory, spec file, latest, or blank to resolve the active feature"
---

When a hook command name contains dots, convert it to the matching skill name by replacing dots with hyphens.
Example: `speckit.aisdlc.preflight` -> `/speckit-aisdlc-preflight`.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Shared Contract

Follow `.specify/extensions/aisdlc-context/references/context-analyzer.md` when it is available in the target project. Follow `.specify/extensions/aisdlc-context/references/ui-mockup.md` when it is available. If either file is not available, apply the same rules directly.

## Purpose

Use this command after `/speckit-specify` to turn UI-relevant stories in a Spec Kit feature spec into static, reviewable concept mockups and handoff notes.

This command is:

- feature-spec driven
- static-output only
- product/design review oriented
- safe to run from Codex, Claude Code, or GitHub Copilot

This command must **not**:

- create a standalone `ui-mockup` extension
- modify Spec Kit core
- edit production application source code
- add package dependencies
- create decorative or irrelevant mockups for non-UI work
- require Impeccable, frontend-design, network access, or a particular AI assistant

## Outline

1. Resolve the target feature directory as `FEATURE_DIR`.
   - `$ARGUMENTS` may be a feature directory, a `spec.md` file, `latest`, or blank.
   - Prefer an explicit path, then `latest`, then the current git branch prefix such as `001-*`, then the most recently modified `specs/*/spec.md`.
   - Stop with a clear message if `FEATURE_DIR/spec.md` cannot be found or read.

2. Read the source and context.
   - Treat `FEATURE_DIR/spec.md` as the source of truth.
   - Read `FEATURE_DIR/plan.md`, `FEATURE_DIR/research.md`, `.specify/memory/constitution.md`, `PRODUCT.md`, `DESIGN.md`, `.impeccable/`, `package.json`, `tailwind.config.*`, and frontend token/theme/component files under `src`, `app`, and `components` when present.
   - Use established product, design, terminology, accessibility, and component context before inventing visual direction.
   - Continue in degraded mode when optional design context is missing.

3. Classify each story in `spec.md`.
   - Mark stories UI-relevant when they describe user-facing screens, routes, dashboards, forms, modals, views, wizards, tables, navigation, visible controls, frontend/client workflows, responsive behavior, accessibility, or visible states.
   - Mark stories non-UI when they are purely backend API behavior, data migration, background jobs, integration plumbing, infrastructure, logging, telemetry, monitoring, or internal service behavior with no user-facing surface.
   - Keep a classification note for every story reviewed.
   - If the spec is malformed, fall back to headings, requirements, acceptance criteria, and scenario text; if classification remains unsafe, stop without creating files.
   - For mixed specs, generate mockups only for UI-relevant stories and preserve non-UI classification notes in the final report.

4. If no UI stories are detected, do not create `mockups/`.
   - Report that no UI mockup is needed.
   - Explain which stories were reviewed and why each was classified as non-UI.
   - Do not create fake screens, decorative UI, or placeholder mockup files.

5. If UI stories are detected, create `FEATURE_DIR/mockups/`.
   - Generate `index.html`, `ui-brief.md`, `traceability.md`, and `README.md`.
   - If `mockups/` already exists, inspect it and replace only these four generated files; do not delete unrelated files.
   - Keep files static, self-contained, reviewable, and traceable to the spec.
   - Make `index.html` directly openable in a browser with inline CSS and minimal JavaScript only.
   - Do not use external CDNs, external images, external fonts, package dependencies, tracking, or secrets.

6. Build the mockup for review, not production.
   - Clearly label the HTML as a concept mockup.
   - Include relevant default, empty, loading, error, success, validation, permission, disabled, and responsive states when implied by the spec.
   - Use semantic markup, accessible names, visible focus states, keyboard-conscious controls, and adequate contrast where practical.
   - Avoid random purple SaaS gradients, decorative glassmorphism, nested cards inside cards, low contrast labels, decorative gradient text, placeholder marketing copy, and UI chrome that does not serve a story.

7. Write supporting documentation.
   - `ui-brief.md` must include Source, UI Story Inventory, Screen Map, Interaction Notes, Design Direction, Assumptions, Open Questions, and Implementation Handoff.
   - `traceability.md` must map each spec story or requirement to mockup screens, elements, states, and coverage.
   - `README.md` must explain how to open the mockup and include the review checklist.
   - Every visible area in `index.html` must trace back to a story, acceptance criterion, requirement, or explicitly labeled assumption.

8. Validate and end with a concise summary.
   - Check that all generated files exist, required headings and table headers are present, and `index.html` has no external resource references.
   - Reopen `index.html` textually and confirm it is clearly labeled as a concept mockup.
   - Resolved `FEATURE_DIR`
   - UI stories detected, or non-UI classification summary
   - Files created or skipped
   - Product/design context used
   - Assumptions and open questions
   - Recommended review path before planning
