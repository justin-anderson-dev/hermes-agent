# AI-SDLC Framework v0.13.1

This file provides instructions for GitHub Copilot. All essential guidance is included inline for cloud agent compatibility.

## Quick Reference

### Before Any Implementation
1. Check for existing specs in `specs/{feature-name}/`
2. Review project context in `docs/README.md` (if available)
3. Use preinstalled `skill-creator` from `.agents/skills/skill-creator`

### Add More Skills
- https://skills.sh/
- `npx skills add https://github.com/anthropics/skills --skill <skill-name>`

### Spec-Kit Commands
Use these prompts for spec-driven development:
- `/speckit.specify` - Create or update a specification
- `/speckit.plan` - Create a technical implementation plan
- `/speckit.analyze` - Analyze plan/spec/task consistency against repo context
- `/speckit.tasks` - Break plan into actionable tasks
- `/speckit.implement` - Implement tasks following the plan
- `/speckit.checklist` - Pre-completion quality checklist
- `/speckit.aisdlc.bootstrap` - Bootstrap durable project context for a brownfield repo
- `/speckit.aisdlc.mockup` - Generate static UI mockups for UI-relevant specs
- `/speckit.aisdlc.promote` - Promote durable decisions into docs and feature context

## Quality Gates (Always Apply)

Before completing any implementation:
- [ ] All acceptance criteria from the spec are met
- [ ] Tests written and passing (aim for 80%+ coverage on business logic)
- [ ] Documentation updated if public APIs changed
- [ ] No linting errors (`npm run lint` or equivalent)
- [ ] Self-review completed
- [ ] Security considerations addressed

## Security Essentials

- Validate and sanitize all user input
- Use parameterized queries (prevent SQL injection)
- Never commit secrets, API keys, or credentials
- Encode output appropriately (prevent XSS)
- Apply principle of least privilege
- Log security-relevant events (without sensitive data)

## Testing Patterns

- Use AAA pattern: Arrange-Act-Assert
- Test naming: "should {expected behavior} when {condition}"
- Mock external dependencies
- Test edge cases and error paths
- Aim for 80%+ coverage on business logic

## Code Review Categories

When reviewing code, use these categories:
- **[BLOCKER]** - Must fix before merge (security, correctness, data loss)
- **[SUGGESTION]** - Would improve code quality
- **[QUESTION]** - Need clarification on intent
- **[NIT]** - Minor style/preference issue

## Project Constitution

If `.specify/memory/constitution.md` exists, it contains project-specific principles and constraints that override general guidance.

## Extended Reference

For VS Code Copilot Chat users with full repository access:
- Architecture decisions: `docs/architecture/adr/`
- Business context: `docs/README.md`
- Framework assets: `.agents/`

## Managed Context

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
once it has been generated.
<!-- SPECKIT END -->

---
*This file is managed by the AI-SDLC Framework. Run `aisdlc init --here --force` to update.*
