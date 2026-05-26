# Implementation Decisions

This directory documents durable implementation decisions that are important to future work but do not rise to the level of a full architecture decision record.

## Purpose

Use `docs/decisions/` for decisions that are:

- implementation-focused
- durable enough to outlive one feature branch
- useful to future maintainers or agents trying to understand why the code looks the way it does

## How This Differs From Nearby Folders

- `docs/architecture/adr/`: long-lived architecture choices with broad or expensive-to-reverse impact
- `docs/patterns/`: reusable defaults that future work should follow by default
- `docs/decisions/`: narrower durable choices, tradeoffs, or transitions that are worth keeping visible

## When to Add a Decision

Add a decision file when:

1. a technical choice has durable consequences
2. the reasoning is not obvious from the code alone
3. future work may need to know why this option won over another

## Suggested Template

Create files as `{YYYY-MM-DD}-{decision-name}.md`.

**Size guidance**: Aim for 100-300 words. Keep it brief and actionable.

```markdown
# {Decision Title}

## Date
{YYYY-MM-DD}

## Context
What situation led to this choice?

## Decision
What was chosen and what was explicitly not chosen?

## Rationale
Why was this option preferred over alternatives?

## Consequences
What became easier, harder, or more constrained because of this choice?

## Related
- Links to related code, PRs, ADRs, or specs
```

## Updating Decisions

If the reasoning changes materially, prefer creating a new decision file that supersedes the older one instead of rewriting history in place.
