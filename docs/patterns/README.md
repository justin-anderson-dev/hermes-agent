# Code Patterns

This directory documents reusable patterns in the codebase that future work should follow for consistency.

**Pattern status legend**:

- **Established**: proven pattern, use by default
- **Experimental**: being validated, use with caution
- **Deprecated**: no longer recommended; link the replacement

## Purpose

Patterns capture reusable approaches such as:

- module structure
- testing conventions
- integration boundaries
- error handling or validation approaches

## How This Differs From Nearby Folders

- `docs/patterns/`: reusable defaults future work should apply
- `docs/decisions/`: one-off durable implementation choices and tradeoffs
- `docs/architecture/adr/`: high-impact architecture decisions

## When to Add a Pattern

Add a pattern file when:

1. the same approach should be reused in multiple places
2. future contributors or agents would benefit from an explicit default
3. code examples or file layouts would save repeated rediscovery

## Suggested Template

Create files as `{pattern-name}.md`:

```markdown
# {Pattern Name}

**Status**: Established | Experimental | Deprecated
**Last Updated**: YYYY-MM-DD

## Overview
Brief description of the pattern and when to use it.

## Structure
Optional file or module layout when it helps.

## Example
Provide a real repo-specific example when possible.

## When to Use
- Scenario 1
- Scenario 2

## When NOT to Use
- Anti-pattern scenario

## Related
- Links to related patterns, decisions, or ADRs
```

Prefer one real repo-specific pattern doc over several empty placeholders.
