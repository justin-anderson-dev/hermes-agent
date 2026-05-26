---
name: "speckit-aisdlc-triage"
description: "Analyze raw intake against repo context and related work, then recommend the smallest justified next action."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "aisdlc-framework"
  source: ".specify/templates/commands/aisdlc.triage.md"
user-invocable: true
disable-model-invocation: false
argument-hint: "Paste intake such as feedback, bug reports, notes, or summaries to triage"
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

## Purpose

Use this command when the user has raw intake and wants help deciding what it means for the product, backlog, or durable project context before they open or refine a feature spec.

This command is:

- read-only
- advisory
- markdown-only in its output

This command must **not**:

- create or edit backlog items
- edit roadmap systems
- write triage files into the repo
- update durable docs
- auto-run follow-up commands

## Recommended Intake Types

These are the most natural inputs for this command:

- customer feedback email
- customer bug report
- meeting transcript or call notes
- product brainstorming notes
- sales call summaries

If the input is a different artifact type, do not reject it purely for that reason. Attempt triage using the same reasoning model, then lower confidence and explain limits when the signal is weak or the artifact shape makes routing ambiguous.

## Intake Handling Rules

1. Treat the text supplied with the command as the primary intake artifact.
2. If the user references file paths and they are accessible in the current environment, read only the files that are relevant to the intake.
3. If the intake contains multiple unrelated topics, identify that ambiguity explicitly and prefer `needs-clarification` over pretending there is one clean recommendation.
4. Summarize the intake briefly before making any recommendation.

## Evidence Search Order

Review evidence in this order:

1. durable context
   - `docs/context/index.yaml`
   - `docs/context/gaps.md`
   - `.specify/memory/constitution.md`
   - relevant durable docs under `docs/`
2. repo evidence relevant to the intake
   - high-signal source files
   - tests
   - manifests, scripts, and workflow config
   - current entrypoints, modules, contracts, or integration adapters related to the intake
3. current feature artifacts under `specs/`
4. accessible backlog or roadmap systems when the current environment exposes them through CLI tools, repo scripts, MCP, or connector surfaces

If backlog or roadmap systems are not accessible, continue without them and lower confidence on overlap claims.

If the durable context scaffold is missing or stale, run in degraded mode:

- inspect high-signal repo surfaces directly
- explain that confidence is reduced
- explicitly recommend `/speckit-aisdlc-bootstrap` as a follow-up when better durable context would materially improve future triage

## Recommendation Model

You must produce exactly one primary recommendation:

- `new-feature-candidate`
- `enhance-existing-item`
- `bug-candidate`
- `already-covered`
- `needs-clarification`
- `no-action`

You may also include zero, one, or both secondary signals:

- `priority-signal`
- `context-promotion`

## Decision Boundaries

- `bug-candidate`: the intake suggests current behavior is incorrect relative to observed behavior, stated intent, or tracked expectations
- `enhance-existing-item`: the current direction appears intentional, but the intake adds scope, evidence, acceptance detail, or a usability gap
- `already-covered`: the repo evidence or accessible related-work evidence already appears to cover the request closely enough that new work is not the default next step
- `needs-clarification`: the intake is too ambiguous, mixed, or incomplete to route safely
- `no-action`: the intake is valid but does not justify backlog or durable-context changes right now
- `priority-signal`: additive signal that existing work may deserve higher attention
- `context-promotion`: additive signal that durable docs may need an update after human review

If overlap with existing work is partial, never present it as an exact duplicate. Describe the partial match and the gap.

If you find likely overlap with existing work, recommend linking the evidence only. Do not suggest exact field edits or automatic mutations.

## Source Authority Rules

1. Do not let one intake artifact override verified repo behavior.
2. Treat code, tests, and runtime configuration as the source of truth for what the system does today.
3. Treat accessible backlog records as the source of truth for whether work is already tracked, when those systems are available.
4. Treat durable docs and roadmap artifacts as the source of truth for intended direction unless they are stale or contradicted by stronger evidence.
5. When evidence conflicts, surface the conflict explicitly instead of synthesizing a false certainty.
6. When confidence is weak, say so plainly.

## Output Contract

Return a markdown-only report with exactly these sections:

### Intake Summary

- 2-4 bullets summarizing the incoming signal

### Primary Recommendation

- one line naming the primary recommendation
- one short paragraph explaining why

### Secondary Signals

- list `priority-signal` and/or `context-promotion` only when they apply
- if none apply, say `- none`

### Evidence Reviewed

- list the highest-signal sources you actually used
- include accessible backlog or roadmap systems only if you actually searched them

### Related Work Or Overlap

- describe likely overlap, exact matches, partial matches, or say that nothing credible was found
- if backlog or roadmap systems were unavailable, state that clearly

### Confidence And Gaps

- provide a confidence level: `high`, `medium`, or `low`
- explain what missing evidence or ambiguity lowered confidence

### Recommended Next Step

Recommend one next action, such as:

- open or refine a spec with `/speckit-specify`
- review backlog or roadmap priority manually
- link the intake as evidence to an existing item
- run `/speckit-aisdlc-promote` if durable context appears stale or incomplete
- gather clarification before routing the intake further

## Constraints

- Keep the response concise and decision-oriented.
- Do not emit JSON.
- Do not assume exhaustive semantic understanding of the entire codebase.
- Prefer targeted repo paths and high-signal evidence over broad speculative analysis.
