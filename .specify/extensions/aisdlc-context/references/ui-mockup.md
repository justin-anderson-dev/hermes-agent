# UI Mockup Generation Reference

Use this reference for `speckit.aisdlc.mockup`.

## Target Resolution

Resolve the target feature directory as `FEATURE_DIR` in this order:

1. If `$ARGUMENTS` is a feature directory, use it.
2. If `$ARGUMENTS` is a spec file, use its parent directory.
3. If `$ARGUMENTS` is `latest`, use the most recently modified `specs/*/spec.md`.
4. If `$ARGUMENTS` is blank, inspect the current git branch for a numeric prefix such as `001-*` and use the matching `specs/001-*` directory when exactly one match exists.
5. Otherwise use the most recently modified `specs/*/spec.md`.

If no feature directory with a readable `spec.md` can be found, stop and report the missing input. Do not create files. If `spec.md` exists but is empty or malformed, attempt to identify story and requirement text from headings, lists, and acceptance criteria. If there is still not enough information to classify UI relevance, stop with a low-confidence explanation and do not create mockups.

## Context To Read

Read `FEATURE_DIR/spec.md` as the source of truth. Also read these files when present and relevant:

- `FEATURE_DIR/plan.md`
- `FEATURE_DIR/research.md`
- `.specify/memory/constitution.md`
- `PRODUCT.md`
- `DESIGN.md`
- `.impeccable/`
- `package.json`
- `tailwind.config.*`
- frontend token, theme, route, layout, and component files under common paths such as `src`, `app`, and `components`

Use existing product and design context before inventing visual direction. Use Impeccable context and local frontend-design guidance when present, but do not require either. Never fail merely because Impeccable or frontend-design is unavailable.

## Story Classification

A story is UI-relevant when it includes one or more of:

- A user-facing screen, page, route, dashboard, form, modal, view, wizard, table, or navigation element.
- Human interaction through visible controls such as input, search, filter, sort, select, edit, drag/drop, upload, approve, configure, save, cancel, or submit.
- Visual or interaction requirements such as responsive layout, accessibility, empty states, loading states, error states, validation states, or success states.
- A frontend/client workflow that needs product or design review.

A story is not UI-relevant when it is purely backend API behavior, data migration, background jobs, integration plumbing, infrastructure, logging, telemetry, monitoring, or internal service behavior with no user-facing surface.

When no UI stories are detected, report that no UI mockup is needed, list the stories reviewed, explain why each is non-UI, and do not create a fake mockup.

When a feature mixes UI and non-UI stories, generate mockups only for the UI-relevant stories and include the non-UI classification notes in the final report or `ui-brief.md` notes.

## Files To Generate

When UI stories are detected, create `FEATURE_DIR/mockups/` with:

- `index.html`
- `ui-brief.md`
- `traceability.md`
- `README.md`

Do not edit production application source code and do not add package dependencies.

If `FEATURE_DIR/mockups/` already exists, inspect it before writing. Replace only the four generated files listed above. Do not delete unrelated files. Report that existing generated files were updated. If an existing file appears hand-authored and overwriting would lose important review notes, stop and ask for direction instead of overwriting.

## ui-brief.md Structure

```md
# UI Mockup Brief: <Feature Name>

## Source
- Spec: ../spec.md
- Generated from: speckit.aisdlc.mockup
- Generated at: <timestamp when available>

## UI Story Inventory
| Story | UI Surface | User Goal | Required States | Notes |
|---|---|---|---|---|

## Screen Map
| Screen | Stories Covered | Primary Actions | States Included |
|---|---|---|---|

## Interaction Notes
- ...

## Design Direction
- Audience:
- Product tone:
- Layout principles:
- Typography:
- Color:
- Motion:
- Accessibility:

## Assumptions
- ...

## Open Questions
- ...

## Implementation Handoff
- Components likely needed:
- Data needed by screen:
- Events/interactions:
- Validation rules:
- Responsive behavior:
```

## traceability.md Structure

```md
# UI Mockup Traceability

| Spec Story / Requirement | Mockup Screen | Mockup Element | State | Covered? |
|---|---|---|---|---|
```

Every visible area in the mockup must trace back to a story, acceptance criterion, requirement, or explicitly labeled assumption.

## index.html Requirements

The mockup must be self-contained HTML, CSS, and minimal JavaScript. It must be openable directly in a browser and must not use external CDNs, external images, external fonts, package dependencies, tracking, or secrets.

Clearly mark the HTML as a concept mockup, not production implementation. Base it on the spec, not invented product requirements. Use semantic markup where practical, responsive CSS, keyboard-conscious controls, accessible labels, visible focus states, and adequate contrast.

The file may include multiple screens using tabs, sections, a sidebar, or a simple screen switcher. Include visible representations of relevant default, empty, loading, error, success, validation, permission, disabled, and mobile/responsive states when those states are implied by the spec.

Avoid random purple SaaS gradients, decorative glassmorphism, nested cards inside cards, low contrast labels, decorative gradient text, placeholder marketing copy, and UI chrome that does not serve the user story. Prefer product clarity, task flow, and traceability.

## README.md Structure

```md
# UI Mockups

Open `index.html` in a browser.

These mockups were generated from `../spec.md` and are intended for product/design review before implementation planning.

## Files

- `index.html`: static mockup
- `ui-brief.md`: screen and design brief
- `traceability.md`: mapping from spec requirements to UI elements

## Review Checklist

- [ ] Screens cover each UI-relevant user story
- [ ] Empty, loading, error, and success states are represented where needed
- [ ] Responsive behavior is clear
- [ ] Accessibility concerns are documented
- [ ] Open questions are captured before planning
```

## Required Final Report

End by reporting:

- Resolved `FEATURE_DIR`
- UI stories detected, or non-UI classification summary
- Files created or skipped
- Product/design context used
- Assumptions and open questions
- Recommended review path before planning

Before the final report, validate that all generated files exist, required headings and table headers are present, and `index.html` does not reference external `http`, `https`, CDN, image, font, script, or stylesheet resources. Reopen `index.html` textually and check that it is marked as a concept mockup.
