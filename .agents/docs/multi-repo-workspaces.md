# Multi-Repo Workspaces

> **⚠️ Advanced Feature** - Skip this if you're using a single repository. See the [Getting Started Guide](getting-started.md) for standard setup.

Use a workspace context repo as root when you need shared docs/specs across multiple code repos.

## Initialize

```bash
aisdlc workspace init my-workspace --repos frontend,backend,infrastructure
cd my-workspace
aisdlc workspace setup
```

## Agent Integrations

Choose agents interactively or pass `--agents` explicitly.

```bash
aisdlc workspace init my-workspace --repos frontend,backend --no-prompt --agents all
```

## Skills

`skill-creator` is preinstalled by `aisdlc init` at `.agents/skills/skill-creator`.

Install additional skills outside AISDLC with `npx skills`:

```bash
npx skills add https://github.com/anthropics/skills --skill <skill-name>
```

## Standalone Repo Mode (Optional)

Only run `aisdlc init --here` inside each repo if those repos are regularly opened standalone.

---

## Maintenance

To update workspace assets, see [Maintenance & Updates](maintenance.md).

## Single Repo Setup

If you're using a single repository, skip this guide and follow the [Getting Started Guide](getting-started.md) instead.
