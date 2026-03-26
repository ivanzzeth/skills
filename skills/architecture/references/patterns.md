# Architecture Patterns Reference

Common architecture patterns with use cases and trade-offs.

## Structural Patterns

### 1. Layered Architecture

```
┌────────────────────────┐
│   Presentation Layer   │  ← HTTP, gRPC, CLI
├────────────────────────┤
│   Application Layer    │  ← Use cases, orchestration
├────────────────────────┤
│     Domain Layer       │  ← Business logic, entities
├────────────────────────┤
│  Infrastructure Layer  │  ← DB, cache, external APIs
└────────────────────────┘
```

**When to Use:**
- Clear separation of concerns needed
- Multiple presentation formats (API, CLI, web)
- Team organized by layer expertise

**Trade-offs:**
| Pros | Cons |
|------|------|
| Clear boundaries | Can become bureaucratic |
| Easy to understand | Cross-cutting concerns tricky |
| Testable layers | Changes often touch all layers |

---

### 2. Clean Architecture (Onion)

```
        ┌─────────────────────┐
        │   External World    │
        │  (UI, DB, Services) │
        ├─────────────────────┤
        │  Interface Adapters │
        │ (Controllers, Repos)│
        ├─────────────────────┤
        │   Application Core  │
        │    (Use Cases)      │
        ├─────────────────────┤
        │      Entities       │
        │  (Domain Objects)   │
        └─────────────────────┘

Dependencies point INWARD only
```

**When to Use:**
- Long-lived applications
- Complex business logic
- Need to swap infrastructure

**Trade-offs:**
| Pros | Cons |
|------|------|
| Business logic isolated | More boilerplate |
| Infrastructure swappable | Mapping between layers |
| Highly testable | Learning curve |

---

### 3. Hexagonal Architecture (Ports & Adapters)

```
            ┌─────────────┐
    ┌───────┤   Adapter   │
    │       │   (HTTP)    │
    │       └──────┬──────┘
    │              │
    │       ┌──────▼──────┐
    │       │    Port     │
    │       │ (Interface) │
    │       └──────┬──────┘
    │              │
    │       ┌──────▼──────┐
    │       │   Domain    │◄────┐
    │       │   Core      │     │
    │       └──────┬──────┘     │
    │              │            │
    │       ┌──────▼──────┐     │
    │       │    Port     │     │
    │       │ (Interface) │     │
    │       └──────┬──────┘     │
    │              │            │
    │       ┌──────▼──────┐     │
    └───────┤   Adapter   ├─────┘
            │(PostgreSQL) │
            └─────────────┘
```

**When to Use:**
- Multiple input sources (HTTP, CLI, events)
- Multiple output targets (different DBs)
- High testability requirement

**Trade-offs:**
| Pros | Cons |
|------|------|
| Easy to test with mocks | More interfaces to define |
| Flexible integrations | Initial setup overhead |
| Clear dependency flow | Can feel over-engineered |

---

### 4. Microservices

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Service │  │ Service │  │ Service │
│    A    │  │    B    │  │    C    │
│  (Go)   │  │ (Node)  │  │(Python) │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │
          ┌───────▼───────┐
          │  Message Bus  │
          │   (Kafka)     │
          └───────────────┘
```

**When to Use:**
- Large teams (> 20 developers)
- Different scaling needs per component
- Polyglot technology requirement
- Independent deployment needed

**Trade-offs:**
| Pros | Cons |
|------|------|
| Independent scaling | Operational complexity |
| Technology flexibility | Network latency |
| Team autonomy | Distributed debugging |
| Fault isolation | Data consistency challenges |

---

### 5. Modular Monolith

```
┌──────────────────────────────────────────┐
│              Single Deployment           │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│ │ Module  │ │ Module  │ │ Module  │     │
│ │    A    │ │    B    │ │    C    │     │
│ └────┬────┘ └────┬────┘ └────┬────┘     │
│      │           │           │          │
│      └───────────┼───────────┘          │
│                  │                       │
│           ┌──────▼──────┐               │
│           │ Event Bus   │               │
│           │ (in-memory) │               │
│           └──────┬──────┘               │
│                  │                       │
│           ┌──────▼──────┐               │
│           │  Database   │               │
│           └─────────────┘               │
└──────────────────────────────────────────┘
```

**When to Use:**
- Medium teams (5-20 developers)
- Uncertain future scaling needs
- Want microservices boundaries without complexity
- Planning future extraction to services

**Trade-offs:**
| Pros | Cons |
|------|------|
| Simple operations | Still single deployment |
| Clear module boundaries | Shared database |
| Easy local development | Discipline required |
| Future-proof | Can degrade to monolith |

---

## Communication Patterns

### 6. Event-Driven Architecture

```
┌─────────┐     ┌─────────────┐     ┌─────────┐
│ Service │────►│  Event Bus  │────►│ Service │
│    A    │     │   (Kafka)   │     │    B    │
└─────────┘     └──────┬──────┘     └─────────┘
                       │
                       ▼
                ┌─────────────┐
                │  Event Store│
                │  (optional) │
                └─────────────┘
```

**When to Use:**
- Loose coupling between components
- Asynchronous processing acceptable
- Audit trail needed
- Multiple consumers for same event

**Trade-offs:**
| Pros | Cons |
|------|------|
| Loose coupling | Eventual consistency |
| Scalable consumers | Debugging complexity |
| Natural audit log | Message ordering |
| Resilient | Infrastructure dependency |

---

### 7. CQRS (Command Query Responsibility Segregation)

```
         ┌────────────────┐
         │   Commands     │
         │ (Write Model)  │
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │    Domain      │
         │    (Write)     │
         └───────┬────────┘
                 │
         ┌───────▼────────┐         ┌────────────┐
         │   Event Store  │────────►│ Read Model │
         └────────────────┘         │  (Views)   │
                                    └─────┬──────┘
                                          │
                                    ┌─────▼──────┐
                                    │  Queries   │
                                    │(Read Model)│
                                    └────────────┘
```

**When to Use:**
- Read/write patterns very different
- Complex domain with simple queries
- High read scalability needed
- Event sourcing beneficial

**Trade-offs:**
| Pros | Cons |
|------|------|
| Optimized read/write | Complexity increase |
| Scalable reads | Eventual consistency |
| Flexible views | More infrastructure |
| Good with events | Learning curve |

---

### 8. Saga Pattern (Distributed Transactions)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Order   │────►│ Payment │────►│ Shipping│
│ Service │     │ Service │     │ Service │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     │    Failure    │               │
     │◄──────────────┤               │
     │               │               │
     │  Compensate   │  Compensate   │
     │──────────────►│──────────────►│
```

**When to Use:**
- Cross-service transactions
- Long-running processes
- Need compensation on failure
- Eventual consistency acceptable

**Trade-offs:**
| Pros | Cons |
|------|------|
| Distributed transactions | Complex implementation |
| Fault tolerant | Compensating actions needed |
| Scalable | Eventual consistency |
| Clear failure handling | State management |

---

## Data Patterns

### 9. Repository Pattern

```go
// Interface in domain layer
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, user *User) error
    Delete(ctx context.Context, id string) error
}

// Implementation in infrastructure layer
type PostgresUserRepository struct {
    db *sql.DB
}

func (r *PostgresUserRepository) FindByID(ctx context.Context, id string) (*User, error) {
    // SQL implementation
}
```

**When to Use:**
- Abstract data access
- Multiple data sources possible
- Domain should not know persistence details
- Testing with mocks needed

---

### 10. Unit of Work Pattern

```go
type UnitOfWork interface {
    Begin() error
    Commit() error
    Rollback() error
    Users() UserRepository
    Orders() OrderRepository
}

// Usage
func (s *Service) TransferFunds(from, to string, amount float64) error {
    uow := s.uowFactory.Create()
    if err := uow.Begin(); err != nil {
        return err
    }
    defer uow.Rollback()  // No-op if committed

    // Multiple operations in same transaction
    fromUser, _ := uow.Users().FindByID(from)
    toUser, _ := uow.Users().FindByID(to)

    fromUser.Balance -= amount
    toUser.Balance += amount

    uow.Users().Save(fromUser)
    uow.Users().Save(toUser)

    return uow.Commit()
}
```

**When to Use:**
- Multiple repositories in one transaction
- Need to ensure atomicity
- Complex business operations

---

## API Patterns

### 11. API Gateway

```
┌────────────────────────────────────────────┐
│                API Gateway                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   Auth   │ │Rate Limit│ │ Routing  │  │
│  └──────────┘ └──────────┘ └──────────┘  │
└───────────────────┬────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌────────┐    ┌────────┐    ┌────────┐
│Service │    │Service │    │Service │
│   A    │    │   B    │    │   C    │
└────────┘    └────────┘    └────────┘
```

**When to Use:**
- Multiple backend services
- Cross-cutting concerns (auth, logging)
- API versioning needed
- Request/response transformation

---

### 12. Backend for Frontend (BFF)

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│   Web    │  │  Mobile  │  │   IoT    │
│  Client  │  │  Client  │  │  Client  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐
│Web BFF │   │Mobile  │   │IoT BFF │
│        │   │  BFF   │   │        │
└────┬───┘   └────┬───┘   └────┬───┘
     │            │            │
     └────────────┼────────────┘
                  │
           ┌──────▼──────┐
           │  Services   │
           └─────────────┘
```

**When to Use:**
- Different clients need different data shapes
- Mobile vs web optimization
- Client-specific logic needed

---

## Quick Reference

| Pattern | Scale | Complexity | Use Case |
|---------|-------|------------|----------|
| Layered | Small-Large | Low | General purpose |
| Clean/Onion | Medium-Large | Medium | Complex domain |
| Hexagonal | Medium-Large | Medium | Multiple interfaces |
| Microservices | Large | High | Large teams, scale |
| Modular Monolith | Medium | Medium | Growing products |
| Event-Driven | Medium-Large | Medium | Async, decoupling |
| CQRS | Medium-Large | High | Read/write split |
| Saga | Large | High | Distributed tx |

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Big Ball of Mud | No structure | Apply layered architecture |
| Distributed Monolith | Microservices + tight coupling | True service boundaries |
| Anemic Domain | Logic in services, not entities | Rich domain models |
| God Class | One class does everything | Split by responsibility |
| Circular Dependencies | A→B→C→A | Dependency injection, events |
| Premature Optimization | Complex before needed | Start simple, evolve |
