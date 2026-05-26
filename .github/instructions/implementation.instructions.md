---
applyTo: "src/**/*"
---

# Implementation Standards

When working in source files, consult:

1. **Core SDLC skill** (preinstalled by AISDLC)
   - Preinstalled baseline: `.agents/skills/skill-creator`
   - Follow development workflow
   - Commit standards
   - Code organization

2. **Security skill** (installed with `npx skills` as needed)
   - Validate all inputs
   - Handle auth properly
   - Protect sensitive data

3. **Relevant optional skills** based on file type:
   - React files -> React skill guidance
   - API endpoints -> API design skill guidance

Install skills:
- https://skills.sh/
- `npx skills add https://github.com/anthropics/skills --skill <skill-name>`
