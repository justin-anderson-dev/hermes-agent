# Architecture Decision Records (ADRs)

Use ADRs to capture *why* important technical decisions were made.

## When to Write an ADR

Write an ADR when making decisions with long-term impact:

✅ **Good candidates for ADRs:**
- Choosing a database (PostgreSQL vs MongoDB vs DynamoDB)
- Selecting an authentication strategy (JWT vs sessions vs OAuth)
- Adopting a new framework or major library (React vs Vue, Express vs Fastify)
- Changing deployment architecture (monolith → microservices)
- Data modeling decisions (event sourcing vs CRUD, normalization strategy)
- Technology stack changes (Python → Node.js)
- API design approach (REST vs GraphQL vs gRPC)

❌ **Not ADR material:**
- Bug fixes (use PR description)
- Refactoring a single component (too granular)
- Code style choices (use linter/style guide)
- Routine dependency updates

**Rule of thumb**: If reversing this decision would require significant rework across multiple components, write an ADR.

---

## Naming / Numbering

Use a simple sequence:

- `0001-short-title.md`
- `0002-another-decision.md`
- `0003-yet-another.md`

Keep titles brief and descriptive:
- ✅ `0001-use-postgresql.md`
- ✅ `0002-adopt-jwt-auth.md`
- ❌ `0001-database.md` (too vague)
- ❌ `0002-authentication-decision-for-api.md` (too long)

---

## Template

Copy `template.md` for new decisions.

The included `0001-example-decision.md` is an optional reference scaffold for manual build-out. Keep it if it helps, but do not treat it as a real project ADR until it is adapted to the repo.

---

## Referencing ADRs

Link to ADRs from other documentation and code:

**In code comments:**
```javascript
// Authentication uses JWT tokens (see ADR-0002)
const token = jwt.sign(payload, secret);
```

**In other documentation:**
```markdown
Authentication approach documented in [ADR-0002: JWT Authentication](adr/0002-jwt-auth.md)
```

**In spec plans:**
```markdown
## Architecture Decisions

This feature builds on:
- [ADR-0001: PostgreSQL Database](docs/architecture/adr/0001-postgresql.md)
- [ADR-0003: REST API Design](docs/architecture/adr/0003-rest-api.md)
```

---

## ADR Lifecycle

ADRs can have different statuses:

- **Proposed**: Under discussion, not yet decided
- **Accepted**: Decision made and implemented
- **Deprecated**: No longer recommended, but still in use
- **Superseded**: Replaced by a newer decision (link to new ADR)

Update the "Status" field when circumstances change.

---

## Examples

See `0001-example-decision.md` for a completed example showing the expected structure.
