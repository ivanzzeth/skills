# Good ARCHITECTURE.md Examples

This document shows examples of well-structured ARCHITECTURE.md files that effectively communicate system design.

## Example 1: Layered Monolith (Go Backend)

```markdown
# System Architecture

## Overview

Authentication service providing JWT-based auth, OAuth2 integration, and user management.
Built as a layered monolith with strict dependency boundaries enforced by linters.

## Business Domains

- **Authentication** - JWT, SIWE, OAuth2 flows
- **Authorization** - RBAC, permission checks
- **User Management** - CRUD, account linking
- **Audit** - Immutable event log

## Architectural Layers

Strict unidirectional dependency flow:

```
Types → Config → Repo → Service → Runtime → UI
         ↑
     Providers (cross-cutting)
```

### Layer Definitions

**Types** (`pkg/types/`)
- Purpose: Data structures, interfaces, domain models
- Dependencies: None
- Examples: `User`, `JWTClaims`, `OAuthProvider`

**Config** (`internal/config/`)
- Purpose: Configuration schemas, validation
- Dependencies: Types
- Examples: `DatabaseConfig`, `JWTConfig`

**Repo** (`internal/repo/`)
- Purpose: Data access, database queries
- Dependencies: Types, Config
- Examples: `UserRepository`, `SessionStore`

**Service** (`internal/service/`)
- Purpose: Business logic, orchestration
- Dependencies: Types, Config, Repo, Providers
- Examples: `AuthService`, `UserService`

**Runtime** (`cmd/`, `internal/app/`)
- Purpose: Application initialization, HTTP server
- Dependencies: All layers
- Examples: `main.go`, HTTP router setup

**Providers** (`internal/providers/`)
- Purpose: Cross-cutting concerns (auth context, telemetry, feature flags)
- Dependencies: Types, Config (limited)
- Examples: `AuthProvider`, `TelemetryProvider`

## Dependency Rules

✅ **Allowed**:
- Lower → Higher (Types → Config → Repo → Service)
- Any layer → Providers
- Runtime → All

❌ **Forbidden**:
- Higher → Lower (Service cannot import Types directly from Repo)
- Cross-domain without interface
- Direct use of cross-cutting (must go through Providers)

## Enforcement

**Custom linters**:
- `scripts/lint/layer_dependencies.go` - Validates import directions
- `scripts/lint/cross_domain.go` - Checks cross-domain boundaries

**Structural tests**:
```go
// tests/architecture/layers_test.go
func TestLayerDependencies(t *testing.T) {
    assertLayerDoesNotImport(t, "types", []string{"config", "repo", "service"})
    assertLayerDoesNotImport(t, "config", []string{"repo", "service"})
}
```

## Cross-Domain Communication

Domains communicate through explicit interfaces in `pkg/`:

```go
// pkg/auth/provider.go
type AuthProvider interface {
    GetCurrentUser(ctx context.Context) (*User, error)
}

// internal/service/billing/service.go
type BillingService struct {
    authProvider auth.AuthProvider  // ✅ Interface dependency
}
```

❌ Don't:
```go
import "github.com/org/project/internal/service/auth"  // Crosses domain boundary
```

## Technology Choices

- **Go 1.21+** - Type safety, performance, good stdlib
- **Gin** - Lightweight HTTP framework
- **GORM** - ORM with migration support
- **PostgreSQL** - Relational data with ACID
- **Redis** - Session storage, rate limiting

Rationale: "Boring" technology - well-understood, stable, good agent support.

## Scalability

- **Stateless services** - JWT in headers, sessions in Redis
- **Horizontal scaling** - Multiple instances behind load balancer
- **Database** - Read replicas for queries, write to primary
- **Cache** - Redis for hot data (sessions, nonces)

## See Also

- Security model: [docs/SECURITY.md](./docs/SECURITY.md)
- Deployment: [docs/RELIABILITY.md](./docs/RELIABILITY.md)
- Design decisions: [docs/design-docs/](./docs/design-docs/)
```

**Why this is good**:
- ✅ Concise overview (2 sentences)
- ✅ Clear layer definitions with examples
- ✅ Explicit dependency rules (what's allowed, what's forbidden)
- ✅ Enforcement mechanisms documented
- ✅ Technology choices have rationale
- ✅ Cross-links to related docs

---

## Example 2: Microservices (TypeScript)

```markdown
# System Architecture

## Overview

E-commerce platform split into microservices:
- **API Gateway** - Entry point, auth, routing
- **Product Service** - Catalog, inventory
- **Order Service** - Cart, checkout, fulfillment
- **Payment Service** - Stripe integration
- **Notification Service** - Email, SMS

## Service Boundaries

```
┌─────────────┐
│ API Gateway │◄───── External clients
└──────┬──────┘
       │
   ┌───┴────┬─────────┬──────────┐
   ▼        ▼         ▼          ▼
┌─────┐ ┌───────┐ ┌─────┐ ┌────────────┐
│Prod.│ │ Order │ │ Pay.│ │Notification│
└─────┘ └───────┘ └─────┘ └────────────┘
   │        │        │
   └────┬───┴────────┘
        ▼
   ┌─────────┐
   │PostgreSQL│ (per-service databases)
   └─────────┘
```

### Communication

- **Synchronous**: REST over HTTP (service-to-service)
- **Asynchronous**: RabbitMQ for events
- **No shared databases** - Each service owns its data

## Internal Structure (Per Service)

Each service follows the same layering:

```
src/
├── types/          # Domain models, DTOs
├── config/         # Config schemas
├── repositories/   # Data access
├── services/       # Business logic
├── controllers/    # HTTP handlers
└── providers/      # Auth, logging, etc.
```

Dependency direction: `types → config → repositories → services → controllers`

## Service Catalog

| Service | Port | Database | Queue | Purpose |
|---------|------|----------|-------|---------|
| API Gateway | 3000 | Redis | - | Auth, routing |
| Product | 3001 | product_db | RabbitMQ | Catalog |
| Order | 3002 | order_db | RabbitMQ | Checkout |
| Payment | 3003 | payment_db | RabbitMQ | Stripe |
| Notification | 3004 | - | RabbitMQ | Email/SMS |

## Data Ownership

- **Product Service owns**: products, categories, inventory
- **Order Service owns**: orders, cart, order_items
- **Payment Service owns**: transactions, payment_methods
- **No joins across services** - Use API calls or events

## Event-Driven Patterns

**Example**: Order placement

1. Order Service creates order → Publishes `order.created` event
2. Payment Service listens → Charges card → Publishes `payment.succeeded`
3. Notification Service listens → Sends confirmation email
4. Product Service listens → Decrements inventory

**Event Schema** (in docs/events/order-created.json):
```json
{
  "event": "order.created",
  "order_id": "123",
  "user_id": "456",
  "total": 99.99,
  "timestamp": "2026-04-08T10:00:00Z"
}
```

## Deployment

Each service deployed independently in Kubernetes:
- **Development**: minikube (1 replica per service)
- **Production**: k3s (2-3 replicas, auto-scaling)

See [docs/RELIABILITY.md](./docs/RELIABILITY.md) for SLOs and monitoring.

## Technology Decisions

**TypeScript** - Type safety, good for JSON APIs
**Express** - Mature, well-understood HTTP framework
**TypeORM** - Database abstraction with migrations
**RabbitMQ** - Reliable message queue
**PostgreSQL** - Per-service relational databases

See [docs/design-docs/why-microservices.md](./docs/design-docs/why-microservices.md) for rationale.
```

**Why this is good**:
- ✅ ASCII diagram shows service boundaries
- ✅ Clear data ownership rules
- ✅ Event-driven pattern with example
- ✅ Service catalog table (quick reference)
- ✅ Technology choices with rationale links
- ✅ Deployment information without detail

---

## Example 3: Monorepo with Shared Libraries

```markdown
# System Architecture

## Overview

Frontend + Backend monorepo with shared TypeScript types and utilities.

## Repository Structure

```
packages/
├── types/          # Shared TypeScript types
├── utils/          # Shared utilities (validation, formatting)
├── api-client/     # Generated API client
├── backend/        # Express REST API
└── frontend/       # React SPA
```

## Dependency Graph

```
types ◄─┬─── utils
        ├─── api-client
        ├─── backend
        └─── frontend

utils ◄─┬─── backend
        └─── frontend

api-client ◄─── frontend

backend ──────► (no deps on frontend)
```

**Rules**:
- `types` depends on nothing (bottom of graph)
- `backend` never imports from `frontend`
- Shared code only in `types`, `utils`, `api-client`

## Backend Architecture

Layered structure:

```
packages/backend/src/
├── types/       # Backend-specific types
├── config/      # Environment config
├── db/          # Database (Prisma)
├── services/    # Business logic
├── routes/      # Express routes
└── middleware/  # Auth, logging, error handling
```

## Frontend Architecture

Component-based structure:

```
packages/frontend/src/
├── components/  # Reusable UI components
├── pages/       # Route-level components
├── hooks/       # React hooks
├── services/    # API calls (uses api-client)
└── utils/       # UI utilities
```

## Code Generation

**API Client**: Generated from OpenAPI spec

```bash
# In packages/backend
npm run generate-openapi  # → docs/openapi.json

# In packages/api-client
npm run generate-client   # Reads docs/openapi.json
```

This ensures frontend always has type-safe API client matching backend.

## Monorepo Benefits

✅ **Type sharing** - No duplication of DTOs  
✅ **Atomic changes** - Update API + client in one PR  
✅ **Single source of truth** - OpenAPI spec drives both  
✅ **Dependency tracking** - Turborepo builds only what changed  

## Build & Deploy

**Development**:
```bash
npm run dev  # Runs both frontend + backend with hot reload
```

**Production**:
- Backend → Docker image → K8s deployment
- Frontend → Static build → CDN (Vercel/Cloudflare)

See [docs/RELIABILITY.md](./docs/RELIABILITY.md) for CI/CD pipeline.
```

**Why this is good**:
- ✅ Clear monorepo structure
- ✅ Dependency graph prevents cycles
- ✅ Code generation workflow documented
- ✅ Benefits explained (why monorepo?)
- ✅ Development vs production distinction

---

## Common Anti-Patterns

### ❌ Anti-Pattern 1: No Dependency Rules

```markdown
## Architecture

We have three main parts:
- Frontend (React)
- Backend (Node.js)
- Database (PostgreSQL)

The frontend calls the backend APIs. The backend queries the database.
```

**Why this is bad**:
- ❌ No layer definitions
- ❌ No dependency constraints
- ❌ Agents can't validate architecture
- ❌ No enforcement mechanism

**Fix**: Define layers with explicit dependencies, document enforcement.

---

### ❌ Anti-Pattern 2: Too Much Low-Level Detail

```markdown
## Database Schema

### users table
- id: BIGSERIAL PRIMARY KEY
- email: VARCHAR(255) NOT NULL UNIQUE
- password_hash: VARCHAR(255) NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- deleted_at: TIMESTAMP NULL
[... 500 lines of every column in every table ...]
```

**Why this is bad**:
- ❌ Schema details belong in docs/generated/db-schema.md
- ❌ Changes frequently, rots quickly
- ❌ Should be auto-generated from migrations

**Fix**: 
```markdown
## Data Model

See [docs/generated/db-schema.md](./docs/generated/db-schema.md) (auto-generated from migrations).

Key entities: Users, Sessions, OAuthBindings.
```

---

### ❌ Anti-Pattern 3: Missing "Why"

```markdown
## Technology Stack

- Frontend: React
- Backend: Go
- Database: PostgreSQL
- Cache: Redis
- Queue: RabbitMQ
```

**Why this is bad**:
- ❌ No rationale for choices
- ❌ Agents can't understand trade-offs
- ❌ Future changes lack context

**Fix**:
```markdown
## Technology Choices

- **React** - Component reusability, large ecosystem
- **Go** - Type safety, performance, good concurrency
- **PostgreSQL** - ACID transactions, complex queries
- **Redis** - Fast key-value for sessions/cache
- **RabbitMQ** - Reliable messaging, good Go client

See [docs/design-docs/tech-stack.md](./docs/design-docs/tech-stack.md) for full rationale.
```

---

## Size Guidelines

ARCHITECTURE.md can be longer than AGENTS.md (it's a reference document):

| Lines | Assessment |
|-------|------------|
| < 200 | ✅ Concise and focused |
| 200-400 | ✅ Acceptable for complex systems |
| 400-600 | ⚠️ Consider splitting by domain |
| 600+ | ❌ Too long - split into domain docs |

## Quick Self-Assessment

For each section, ask:

1. **Is this architecture or implementation?**
   - Architecture (layers, boundaries) → Keep
   - Implementation (specific functions) → Move to code or design docs

2. **Is this stable or frequently changing?**
   - Stable (system structure) → Keep
   - Changes often (schemas, APIs) → Auto-generate or link

3. **Does this help understand system structure?**
   - Yes → Keep
   - No → Remove

4. **Can this be visualized?**
   - ASCII diagrams > long prose
