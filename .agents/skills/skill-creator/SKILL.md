---
name: skill-creator
description: Create, review, and improve agent skills using concrete examples, progressive disclosure, and reusable resources. Use when asked to build a new skill, refactor an existing skill, improve trigger metadata, or validate/package a skill for reuse.
license: Complete terms in LICENSE.txt
---

# Skill Creator

> Notice: This file is derived from Anthropic's upstream `skill-creator` and has been modified by AI-SDLC maintainers.

Build skills that are easy to trigger, easy to maintain, and reliable in real use.

## Core Outcomes

1. Translate real user requests into a clear skill scope and trigger description.
2. Decide what belongs in `SKILL.md` versus `scripts/`, `references/`, and `assets/`.
3. Produce a concise, high-signal skill that passes validation and real usage tests.

Script tooling note: bundled Python scripts require `python3`; validation/packaging helpers also require `PyYAML`.

## Design Principles

### 1) Start from concrete examples

Collect 3-5 realistic prompts the skill must handle. Good skills are grounded in usage, not abstractions.

When examples are missing, ask targeted questions first. Keep questions minimal and high leverage.

### 2) Use the right degree of freedom

- High freedom: pure guidance for variable, judgment-heavy tasks.
- Medium freedom: guidance + pseudocode or partial templates.
- Low freedom: deterministic scripts and strict sequence for fragile operations.

### 3) Protect context budget

Use progressive disclosure:

1. `name` + `description` frontmatter (always loaded)
2. `SKILL.md` body (loaded when triggered)
3. `scripts/`, `references/`, `assets/` (loaded only as needed)

Keep `SKILL.md` concise. Move detailed references out of the core body.

### 4) Keep files purposeful

Include only files needed for execution:

- `SKILL.md` (required)
- optional `scripts/`, `references/`, `assets/`

Do not add process artifacts like `README.md`, `CHANGELOG.md`, or installation guides.

## Skill Creation Workflow

Follow these steps in order unless there is a strong reason to skip one.

### Step 1: Understand usage and trigger intent

Capture:

- user goals
- trigger phrases
- expected outputs
- constraints (tools, formats, environment)

Use at least one positive example and one near-miss example (similar request that should not trigger this skill).

### Step 2: Extract reusable components

For each example, identify repeated work:

- repeated logic -> `scripts/`
- deep domain knowledge -> `references/`
- reusable artifacts/templates -> `assets/`

Use `references/workflows.md` when designing multi-step or branching workflows.
Use `references/output-patterns.md` when output format consistency matters.

### Step 3: Define frontmatter for reliable triggering

Frontmatter drives trigger quality. `description` must include:

- what the skill does
- when to use it
- concrete contexts/file types/task categories

Avoid vague descriptions that match everything.

### Step 4: Initialize or audit the skill

For new skills, run:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

For existing skills, audit current content first:

- frontmatter quality (`name`, `description`)
- duplication between body and references
- missing scripts for repeated deterministic tasks

### Step 5: Implement resources first, then SKILL.md

Build reusable resources before finalizing the core instructions.

When writing `SKILL.md`:

- use imperative style
- reference files directly (`scripts/...`, `references/...`)
- keep one-hop navigation (avoid deep reference chains)

### Step 6: Validate and stress test

Run validation:

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

Then run usage stress tests with representative prompts:

1. straightforward in-scope request
2. edge-case in-scope request
3. near-miss request that should not trigger

Use `references/quality-gates.md` as the final review checklist.

### Step 7: Package and iterate

Create distributable artifact:

```bash
scripts/package_skill.py <path/to/skill-folder> [output-directory]
```

Iterate from real usage:

1. run the skill on real tasks
2. note confusion, failures, or token bloat
3. update SKILL/resources
4. revalidate and retest

## Resource Decision Matrix

Use this matrix when deciding where content belongs:

- `SKILL.md`: brief workflow, decision points, file navigation, critical constraints.
- `scripts/`: deterministic operations or repeated code generation.
- `references/`: detailed, occasionally-needed docs (schemas, API details, long examples).
- `assets/`: files used in outputs but not meant for context loading.

## Definition of Done

Before considering a skill complete:

1. Trigger description is specific and testable.
2. `SKILL.md` is concise and free of duplicated reference content.
3. Scripts (if any) execute successfully.
4. Validation passes.
5. Stress-test prompts produce expected behavior.

## Quick Links

- `references/workflows.md` - sequential and conditional workflow patterns
- `references/output-patterns.md` - template and example-driven output patterns
- `references/quality-gates.md` - final quality checklist
