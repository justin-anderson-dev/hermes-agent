# Architecture Overview

Document the actual runtime shape of this repo.

Prefer concrete file paths, execution flow, and integration boundaries over abstract architecture language.

Exclude target-state redesign ideas, generic architecture filler, and untouched sample content that has not been adapted to this repo.

## System Shape

Describe the current system or runtime surface:

- what kind of software this repo contains
- the primary execution entrypoints
- the main user, maintainer, or automation flow

## Key Modules and Responsibilities

List the major files, directories, or components and what each one owns.

Use real repo paths where possible.

## Important Flows

Capture the highest-signal flow or two, such as:

- startup or invocation path
- request or job processing flow
- action or CLI execution flow
- test or packaging flow

Call out notable edge cases when code or tests prove them.

## Integrations and Platform Surfaces

Record the important external or platform-facing boundaries, such as:

- APIs
- CI workflows
- action metadata
- environment variables
- generated artifacts

## Build, Test, and Delivery

Document the commands, scripts, and workflow files that matter for:

- install
- build or packaging
- automated tests
- release or deployment

## Observed Evidence

List the source files, tests, scripts, manifests, and workflow files that support this architecture summary.

## Assumptions and Open Questions

If the repo leaves something ambiguous, record it explicitly so a reviewer can confirm or correct it.
