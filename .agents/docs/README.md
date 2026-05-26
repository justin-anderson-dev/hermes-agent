# AI-SDLC Framework Documentation

Welcome to the AI-SDLC Framework. This bootstrap gives your repo shared project context, a Spec Kit workflow, and a clean place to keep durable guidance for your coding agents.

## Start Here

**→ [Getting Started Guide](getting-started.md)** - Complete setup and onboarding flow (start here)

## Additional Resources

- **[Maintenance & Updates](maintenance.md)** - Keep framework assets fresh
- **[Multi-Repo Workspaces](multi-repo-workspaces.md)** - Advanced: Managing multiple repos with shared context

## Optional Community Extensions

AI-SDLC can also install a small curated set of optional Spec Kit community extensions during init for bugfix flow, iteration, and enterprise tracker integration.

Anything outside that curated set is installed later with:

```bash
aisdlc extension add <extension-name>
```

## External Skills

`skill-creator` is preinstalled by `aisdlc init` at `.agents/skills/skill-creator`.

Extend your AI agents with additional skills:

```bash
npx skills add https://github.com/anthropics/skills --skill <skill-name>
```

See: https://skills.sh/

---

**Questions?** See the Getting Started Guide for the bootstrap workflow, feature loop, and troubleshooting.
