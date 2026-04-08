# Good AGENTS.md Examples

This document shows examples of well-structured AGENTS.md files that follow OpenAI Harness principles.

## Example 1: Minimal Navigation Map (Ideal)

```markdown
# Project Name

Brief (2-3 sentence) description of what this project does and who uses it.

## Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System structure
- **[docs/DESIGN.md](./docs/DESIGN.md)** - Design philosophy
- **[docs/SECURITY.md](./docs/SECURITY.md)** - Security requirements
- **[docs/QUALITY_SCORE.md](./docs/QUALITY_SCORE.md)** - Quality metrics

## Tech Stack

- Language: Go 1.21+
- Database: PostgreSQL
- Cache: Redis

## Critical Constraints

1. All data validation at API boundaries
2. Dependency direction: internal/ → pkg/, never reverse
3. Test coverage: 95%+ for core business logic
4. No manual code - all code is agent-generated

## Quick Start

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
2. Check [docs/exec-plans/active/](./docs/exec-plans/active/) for current work
3. Review [docs/QUALITY_SCORE.md](./docs/QUALITY_SCORE.md) for problem areas

## References

- Design decisions: [docs/design-docs/](./docs/design-docs/)
- Active work: [docs/exec-plans/active/](./docs/exec-plans/active/)
- Tech debt: [docs/exec-plans/tech-debt-tracker.md](./docs/exec-plans/tech-debt-tracker.md)
```

**Why this is good**:
- ✅ 89 lines - well under 100-line target
- ✅ Navigation map only - no detailed content
- ✅ Clear pointers to where information lives
- ✅ Critical constraints are truly critical (4 items, not 20)
- ✅ Quick Start guides agents to right docs

---

## Example 2: Team-Based Agent Workflow

```markdown
# Service Name

{2-3 sentence description}

## Agent Team

| Agent | Role | Skill |
|-------|------|-------|
| **backend-dev** | Go development, API implementation | go-backend-dev |
| **security-auditor** | Security review | security-audit |
| **qa-engineer** | E2E testing | qa-testing |

## Workflows

**Security Fix**:
1. backend-dev implements fix + tests
2. security-auditor reviews
3. qa-engineer validates
4. devops deploys

**Feature Development**:
1. Read spec from docs/product-specs/
2. backend-dev implements
3. qa-engineer tests
4. security-auditor reviews if auth-related

## Communication

Agents use `SendMessage`:
- backend-dev → security-auditor: code review request
- qa-engineer → backend-dev: bug reports

## Documentation

- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Core beliefs: [docs/design-docs/core-beliefs.md](./docs/design-docs/core-beliefs.md)
- Security: [docs/SECURITY.md](./docs/SECURITY.md)
- Quality: [docs/QUALITY_SCORE.md](./docs/QUALITY_SCORE.md)

## Golden Principles

See [docs/design-docs/core-beliefs.md](./docs/design-docs/core-beliefs.md)

Key rules:
- Explicit error handling (no `_ = xxx`)
- Boundary validation (all inputs)
- 95%+ test coverage for auth logic
```

**Why this is good**:
- ✅ 116 lines - slightly over but acceptable
- ✅ Focuses on agent workflow (how agents work together)
- ✅ Golden Principles referenced, not detailed
- ✅ Clear communication protocol
- ✅ Workflows are concise (5 lines each)

---

## Example 3: Progressive Disclosure with Context Sources

```markdown
# Project Name

{Description}

## Core Principle

Humans steer. Agents execute. Repository is source of truth.

## Documentation Structure

```
ARCHITECTURE.md          # System structure (read first)
docs/
├── design-docs/        # Why decisions (architecture, trade-offs)
├── exec-plans/         # Active work + completed work
├── product-specs/      # What to build (features, requirements)
├── references/         # External docs (APIs, RFCs)
├── DESIGN.md           # Design philosophy
├── QUALITY_SCORE.md    # Quality tracking
└── SECURITY.md         # Security invariants
```

## Context Sources for Agents

Agents read context from:
- Documentation (design docs, specs, plans)
- .claude/agents/ (agent role definitions)
- .claude/skills/ (agent capabilities)
- CLAUDE.md (project overview, current priorities)

**What agents can't see doesn't exist.** No Slack, no Google Docs.

## Quick Start for Agents

1. **Read CLAUDE.md** - current priorities
2. **Check docs/exec-plans/active/** - ongoing work
3. **Read ARCHITECTURE.md** - system structure
4. **Check docs/QUALITY_SCORE.md** - known issues

## For Humans

Never write code directly. Instead:
- Update documentation (specs, design docs)
- Review pull requests
- Validate end-to-end behavior

## References

- Full architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Design decisions: [docs/design-docs/](./docs/design-docs/)
- Active work: [docs/exec-plans/active/](./docs/exec-plans/active/)
```

**Why this is good**:
- ✅ 110 lines - acceptable
- ✅ Explains "agent-first" philosophy clearly
- ✅ ASCII directory tree is compact
- ✅ Clear distinction: docs for agents, process for humans
- ✅ Progressive disclosure principle explained

---

## Common Anti-Patterns

### ❌ Anti-Pattern 1: Detailed Implementation in AGENTS.md

```markdown
## Authentication Flow

When a user logs in:
1. Frontend sends POST /api/v1/auth/login with email/password
2. Backend validates credentials against bcrypt hash
3. If valid, generate JWT with HS256 algorithm
4. JWT payload includes:
   - user_id (uint64)
   - email (string)
   - roles ([]string)
   - issued_at (unix timestamp)
   - expires_at (unix timestamp + 24h)
5. Return JWT in response
6. Frontend stores in localStorage
7. Frontend includes JWT in Authorization header for subsequent requests
8. Backend middleware validates JWT signature and expiry
9. If invalid, return 401 Unauthorized
10. If valid, extract user_id and inject into request context
... [continues for 100+ lines]
```

**Why this is bad**:
- ❌ This is implementation detail, not navigation
- ❌ Should be in docs/design-docs/authentication.md
- ❌ AGENTS.md becomes 500+ lines
- ❌ Content rots as implementation changes

**Fix**: Replace with:
```markdown
## Authentication

See [docs/design-docs/authentication.md](./docs/design-docs/authentication.md) for full flow.

Key constraint: JWT tokens expire in 24h (configurable).
```

---

### ❌ Anti-Pattern 2: Duplicating ARCHITECTURE.md Content

```markdown
## System Architecture

The system is divided into three layers:

### Presentation Layer
Handles HTTP requests, validates input, serializes responses...
[50 lines of detail]

### Business Logic Layer
Contains domain services, implements business rules...
[50 lines of detail]

### Data Access Layer
Interfaces with PostgreSQL, manages transactions...
[50 lines of detail]
```

**Why this is bad**:
- ❌ ARCHITECTURE.md exists for this
- ❌ Duplicated content gets out of sync
- ❌ Wastes AGENTS.md space

**Fix**:
```markdown
## Architecture

Layered architecture: Presentation → Business Logic → Data Access.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for details.
```

---

### ❌ Anti-Pattern 3: Too Many "Critical" Constraints

```markdown
## Critical Constraints

1. All errors must be logged
2. All inputs must be validated
3. All database queries must use prepared statements
4. All API responses must include correlation ID
5. All tests must run in under 10 seconds
6. All commits must follow conventional commit format
7. All PRs must have at least one approval
8. All code must pass linter
9. All functions must have JSDoc comments
10. All environment variables must have defaults
11. All database migrations must be reversible
12. All third-party dependencies must be reviewed
13. All API changes must be backwards compatible
14. All logs must be JSON format
15. All secrets must be in environment variables
... [continues]
```

**Why this is bad**:
- ❌ If everything is critical, nothing is
- ❌ Agents can't prioritize
- ❌ Most are standard practices, not constraints

**Fix**:
```markdown
## Critical Constraints

1. **Zero trust auth**: All endpoints validate JWT, no exceptions
2. **Fail-closed**: Invalid config/secrets → service refuses to start
3. **Audit trail**: User actions logged to immutable audit DB
4. **Test coverage**: Auth logic requires 95%+ coverage

(Standard practices like input validation, prepared statements, etc. 
are in docs/design-docs/core-beliefs.md)
```

---

## Size Guidelines

| Lines | Assessment |
|-------|------------|
| < 100 | ✅ Ideal - concise navigation map |
| 100-150 | ✅ Acceptable - still focused |
| 150-200 | ⚠️ Warning - consider moving content to docs/ |
| 200-300 | ❌ Too long - agent context crowded |
| 300+ | ❌ Monolithic - defeats progressive disclosure |

## Quick Self-Assessment

Ask yourself for each section:

1. **Is this navigation or detail?**
   - Navigation → Keep in AGENTS.md
   - Detail → Move to docs/

2. **Is this truly critical?**
   - Critical (project-specific, non-obvious) → Keep
   - Standard practice (every project has this) → Remove or move to docs/design-docs/core-beliefs.md

3. **Will this change frequently?**
   - Stable (team structure, tech stack) → Can keep
   - Changes often (current priorities, active work) → Link to docs/exec-plans/

4. **Does this duplicate existing docs?**
   - Yes → Replace with link
   - No → Keep if navigational

## Testing Your AGENTS.md

1. **Line count test**: `wc -l AGENTS.md` - Should be <150
2. **Link test**: Count `](` - Should have 10+ links to docs/
3. **Detail test**: Count code blocks - Should have 0-2 small examples
4. **Duplication test**: Search for architecture/design terms - Should point to docs/, not explain inline
