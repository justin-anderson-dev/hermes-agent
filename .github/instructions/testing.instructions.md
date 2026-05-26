---
applyTo: "**/*.test.{ts,tsx,js,jsx},**/*.spec.{ts,tsx,js,jsx},**/tests/**/*"
---

# Testing Standards

When writing or modifying tests, consult:

your preinstalled `skill-creator` guidance first, then any installed testing skills (`npx skills`).

Key patterns:
- AAA pattern (Arrange-Act-Assert)
- Descriptive test names: "should {behavior} when {condition}"
- Mock external dependencies
- Test edge cases and error paths
- Aim for 80%+ coverage on business logic

Install skills:
- https://skills.sh/
- Preinstalled in this repo: `.agents/skills/skill-creator`
- `npx skills add https://github.com/anthropics/skills --skill <skill-name>`
