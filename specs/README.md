# Specs Folder

This folder stores feature-level specifications and delivery plans.

## Why This Folder Starts Empty

`aisdlc init` creates `specs/` intentionally without feature files because specs are project-specific.
You create each feature spec when work begins.

## What You Should Expect Here

After running the Spec Kit workflow for a feature, you'll typically see:

```text
specs/<feature-name>/
  spec.md
  plan.md
  tasks.md
  context/
    promotion-log.md
    scratch/        # optional temporary working files
```

You may also add supporting notes or checklists for that feature.

`context/promotion-log.md` is the durable bridge back into `docs/`. It captures what later feature work discovered that might need promotion into product, architecture, context, pattern, or decision docs.

## How Specs Get Created

Use your agent commands in order:

1. `/speckit.specify`
2. `/speckit.clarify`
3. `/speckit.plan`
4. `/speckit.tasks`
5. `/speckit.implement`

`specs/` is project-owned content and should be kept in version control.
