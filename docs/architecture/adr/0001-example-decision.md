> Sample scaffold file. Keep this example if it helps your team build ADRs manually, but do not treat it as a real project decision until you replace the sample details with repo-specific content.

# ADR-0001: Use PostgreSQL for Primary Database

## Status

Accepted

## Context

We need a database for storing user data, products, orders, and payments. This is a new project with no existing database choice.

**Requirements:**
- ACID transactions (critical for payment processing)
- Complex relational queries for reporting and analytics
- Budget constraint: < $100/month for first year (small user base)
- Team has SQL experience but limited NoSQL experience

**Current situation:**
- No database selected yet
- Early stage (0-1000 users expected in first 6 months)
- Need to move quickly but make sound long-term choice

## Decision

Use **PostgreSQL** as the primary database, hosted on AWS RDS.

Configuration:
- Single instance (db.t3.micro to start)
- Multi-AZ deployment for production
- Automated daily backups with 7-day retention

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **PostgreSQL** (chosen) | Strong ACID, excellent JSON support, cost-effective on RDS, team experience | Requires schema management | ✅ **Accepted**: Best fit for requirements |
| MongoDB | Flexible schema, good for rapid iteration | Weak transactions (critical for payments), higher RDS Atlas cost | ❌ Rejected: Transaction guarantees insufficient |
| MySQL | Mature, well-supported, slightly cheaper | Weaker JSON support, less extensible | ❌ Rejected: PostgreSQL JSON features needed |
| DynamoDB | Serverless, scales automatically | Complex for relational queries, no joins, harder to reason about | ❌ Rejected: Relational model better fits domain |

## Rationale

PostgreSQL was chosen because:

1. **ACID guarantees** are non-negotiable for financial transactions
2. **Relational model** fits our domain (users, products, orders are naturally relational)
3. **JSON support** (JSONB) gives us schema flexibility when needed
4. **Cost-effective** on AWS RDS compared to managed MongoDB Atlas
5. **Team experience** with SQL reduces learning curve
6. **Ecosystem maturity**: Excellent tooling (Prisma ORM, pgAdmin, extensions)

The primary tradeoff is schema management overhead, but this is outweighed by transaction safety and query expressiveness.

## Consequences

**Positive:**
- Strong data consistency guarantees for payments
- Rich query capabilities for reporting
- Well-understood operational model
- Prisma ORM provides type-safe database access

**Negative:**
- Schema migrations required (managed via Prisma)
- Need to plan for scaling (vertical first, read replicas later)
- Less flexible than schemaless databases (acceptable tradeoff)

**Follow-up work:**
- Set up Prisma ORM for schema management
- Configure automated backups and monitoring (CloudWatch)
- Document connection pooling strategy for API services
- Create initial schema migration for core entities

## Related

- Implementation PR: #42 (Prisma setup)
- Schema documentation: `docs/architecture/database-schema-example.md` (to be created)
- Deployment config: `infrastructure/terraform/rds.tf`

## How to Adapt This Sample

When turning this into a real ADR:

1. replace the sample domain, requirements, and hosting details with repo-specific facts
2. link to the real code, specs, issues, or infrastructure paths that support the decision
3. update the status and consequences to match the current repo state
4. delete this adaptation guidance once the ADR is project-specific
