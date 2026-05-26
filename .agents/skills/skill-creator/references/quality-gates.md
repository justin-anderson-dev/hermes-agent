# Skill Quality Gates

Use this checklist before shipping a skill.

## 1. Trigger Quality

- `name` is lowercase hyphen-case and specific.
- `description` states both capability and trigger contexts.
- Description includes concrete task types, not generic "help with X" language.
- At least one near-miss prompt is identified (should not trigger).

## 2. Scope and Structure

- `SKILL.md` covers only core workflow and decision points.
- Variant-heavy detail is moved to `references/`.
- Repetitive deterministic steps are moved to `scripts/`.
- Output artifacts/templates are placed in `assets/`.

## 3. Context Efficiency

- No duplicate content between `SKILL.md` and references.
- `SKILL.md` is concise and navigable.
- Reference files are directly linked from `SKILL.md` (one-hop discoverability).

## 4. Operational Reliability

- Script entry points are executable and tested.
- File paths in instructions are correct.
- Validation passes via:
  - `scripts/quick_validate.py <skill-path>`

## 5. Real-World Behavior

Run at least three prompt tests:

1. Typical in-scope request
2. Edge-case in-scope request
3. Near-miss request (should avoid triggering)

Capture failures and update:

- frontmatter trigger wording
- workflow ordering/branching
- script coverage
- reference organization

## 6. Packaging Readiness

- Folder contains only needed execution files.
- No process-only docs (`README.md`, `CHANGELOG.md`, etc.).
- Package can be generated:
  - `scripts/package_skill.py <skill-path> [output-dir]`
