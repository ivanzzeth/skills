# End-to-End Example

This example shows a complete workflow: building an authentication microservice from scratch with agent-first structure, Git hooks, observability, and CI/CD.

## Scenario

**Goal**: Build `auth-service` - a JWT authentication microservice for a Web3 platform

**Requirements**:
- User registration and login
- JWT token generation with 24h expiry
- Rate limiting (5 attempts/min per IP)
- Prometheus metrics exposure
- Structured JSON logging
- Health check endpoints for Kubernetes
- <200ms p95 latency
- 95% test coverage

## Step-by-Step Execution

### 1. Initialize Repository (2 minutes)

```bash
# Create project
mkdir auth-service && cd auth-service
git init

# Install openai-harness skill (if not installed)
npx skills add ivanzzeth/skills

# Initialize harness structure
~/.claude/skills/openai-harness/scripts/init_harness.sh auth-service .

# Install Git hooks
~/.claude/skills/openai-harness/scripts/install_hooks.sh
```

**Output**:
```
✓ Created AGENTS.md (45 lines)
✓ Created ARCHITECTURE.md
✓ Created docs/ structure (8 subdirectories)
✓ Created validation scripts
✓ Installed 3 Git hooks (pre-commit, commit-msg, pre-push)
```

### 2. Define Architecture (5 minutes)

Edit `AGENTS.md`:
```markdown
# Auth Service

JWT authentication microservice for Web3Gate platform.

**Critical constraints**:
- All tokens expire in <24h (compliance requirement)
- Rate limit: 5 login attempts/min per IP
- Never log sensitive data (passwords, tokens)
- All endpoints require request ID for tracing

See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design.
See [docs/design-docs/core-beliefs.md](./docs/design-docs/core-beliefs.md) for golden principles.
```

Edit `ARCHITECTURE.md`:
```markdown
## Business Domains

### auth
Authentication logic - JWT generation, validation, refresh

### user  
User management - registration, profile, password reset

### session
Session tracking - active sessions, device fingerprinting

## Layer Rules

```
Types → Config → Repo → Service → Runtime → API
         ↑
     Observability (cross-cutting: metrics, logging)
```

**Dependency enforcement**:
- Service layer CANNOT import Runtime/API
- Repo layer CANNOT import Service
- Config loaded once at startup, never mutated

## Technology Stack

- **Language**: Go 1.21+
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Observability**: Prometheus + Grafana + Loki
```

Edit `docs/design-docs/core-beliefs.md`:
```markdown
# Golden Principles

1. **Explicit Error Handling** - Never use `_ = xxx`
2. **Input Validation** - All user inputs validated at entry points  
3. **DRY Principle** - Zero code duplication
4. **Structured Logging** - JSON format with trace IDs
5. **Metrics First** - Expose /metrics before implementing features
6. **Health Checks** - /health/liveness and /health/readiness required
```

### 3. Document Infrastructure (3 minutes)

Create `docs/infrastructure/INVENTORY.md`:
```markdown
# Infrastructure Inventory

## Observability Stack

### Prometheus
- **Endpoint**: http://prometheus.internal:9090
- **Scrape interval**: 15s
- **Retention**: 30 days
- **Usage**: Service metrics collection

### Grafana  
- **Endpoint**: https://grafana.web3gate.xyz
- **Dashboards**: 
  - `auth-service-overview` (latency, throughput, error rate)
  - `auth-service-business` (login success rate, active users)

### Loki
- **Endpoint**: http://loki.internal:3100
- **Usage**: Centralized log aggregation
- **Query with**: LogQL via Grafana

## Kubernetes Cluster

- **Context**: `production` (k3s on Vultr Tokyo)
- **Namespace**: `web3gate`
- **Ingress**: Traefik with cert-manager (Let's Encrypt)

## Redis
- **Endpoint**: redis-master.web3gate.svc.cluster.local:6379
- **Usage**: Session storage, rate limiting

## PostgreSQL
- **Endpoint**: postgres.web3gate.svc.cluster.local:5432  
- **Database**: `auth_service`
- **Migrations**: Managed by `golang-migrate`
```

### 4. Create Product Spec (5 minutes)

Create `docs/product-specs/001-user-authentication.md`:
```markdown
# User Authentication

## Overview
Email + password authentication with JWT tokens.

## Requirements

### Functional
- POST /register - Create new user account
- POST /login - Authenticate and issue JWT
- POST /refresh - Refresh JWT token
- POST /logout - Invalidate token

### Non-Functional
- <200ms p95 latency
- Rate limit: 5 attempts/min per IP
- JWT expires in 24h
- Bcrypt password hashing (cost=12)

## Success Criteria
- [ ] All endpoints return <200ms p95
- [ ] Metrics exposed on /metrics
- [ ] Structured logs with trace IDs
- [ ] 95% test coverage
- [ ] Rate limiting functional

## Security Checklist
- [ ] Passwords never logged
- [ ] SQL injection prevention (parameterized queries)
- [ ] CSRF protection on state-changing endpoints
- [ ] TLS required in production
```

### 5. Agent Implementation (30 minutes)

Prompt agent with:
```
Implement the user authentication system defined in:
- docs/product-specs/001-user-authentication.md
- ARCHITECTURE.md (follow layer rules)
- docs/design-docs/core-beliefs.md (enforce golden principles)

Requirements:
1. Follow Go project layout (cmd/, internal/, pkg/)
2. Add Prometheus metrics (/metrics endpoint)
3. Add structured logging (JSON with trace IDs)
4. Add health checks (/health/liveness, /health/readiness)
5. Write tests (target 95% coverage)
6. Use conventional commits
```

Agent implements:
```
internal/
  ├── config/       # Configuration loading
  ├── repo/         # Database access
  ├── service/      # Business logic
  ├── runtime/      # HTTP server
  └── observability/ # Metrics, logging
cmd/
  └── auth-service/ # Main entry point
pkg/
  └── types/        # Shared types
```

### 6. Validate Implementation (2 minutes)

```bash
# Check observability integration
python ~/.claude/skills/openai-harness/assets/custom-linters/validate_observability.py .
```

**Output**:
```
✅ Metrics endpoint /metrics found
✅ Prometheus client library detected
✅ Structured logging detected (15 files)
✅ Health check endpoints found
✅ Liveness probe endpoint found
✅ Readiness probe endpoint found
✅ Infrastructure inventory found (docs/infrastructure/INVENTORY.md)
```

```bash
# Check golden principles compliance
python ~/.claude/skills/openai-harness/assets/custom-linters/golden_principles_linter.py . \
  --docs docs/design-docs/core-beliefs.md
```

**Output**:
```
✅ No error swallowing (_ = xxx) found
✅ Input validation present at API boundaries
✅ No code duplication detected
✅ Structured logging validated
```

```bash
# Check architecture compliance
python ~/.claude/skills/openai-harness/assets/custom-linters/layer_dependencies_linter.go .
```

**Output**:
```
✅ No layer violations detected
✅ Service layer doesn't import Runtime/API
✅ Repo layer doesn't import Service
```

### 7. Code Review (Agent-to-Agent)

```bash
# Scan for TODOs before commit
python scripts/lint/code_todos.py .
```

**Output**:
```
Code Annotations Summary
Total: 3 annotations

Medium Priority (TODO) - 3 items
  internal/service/auth.go (2 items)
    45: [TODO] Add OAuth2 providers (Google, GitHub)
    78: [TODO] Implement password strength checker

  internal/repo/user.go (1 items)
    23: [TODO] Add pagination support

⚠️ 3 TODO items found (non-blocking)
```

### 8. Commit with Git Hooks (1 minute)

```bash
git add .
git commit -m "feat(auth): implement JWT authentication with observability"
```

**Git hooks output**:
```
Running pre-commit checks...
✅ No secrets detected
✅ No large files (>5MB)
✅ AGENTS.md size OK (52 lines < 250 limit)
✅ No critical TODOs (BUG/FIXME) found
✅ No debug code found
✅ golangci-lint passed

Running commit-msg validation...
✅ Commit message validated (Conventional Commits)

[main 5a3c8f2] feat(auth): implement JWT authentication with observability
 47 files changed, 2847 insertions(+)
```

### 9. Pre-Push Validation (30 seconds)

```bash
git push origin main
```

**Git hooks output**:
```
Running pre-push checks...
✅ Tests passed (95% coverage)
✅ No critical TODOs found
✅ Documentation validated
✅ AGENTS.md within 250 line limit (52 lines)
✅ Security scan passed (no secrets in commits)

Counting objects: 47, done.
Delta compression using up to 8 threads.
Writing objects: 100% (47/47), 128.45 KiB | 0 bytes/s, done.
To github.com:web3gate/auth-service.git
   8f2d4a1..5a3c8f2  main -> main
```

### 10. CI/CD Pipeline (2 minutes)

GitHub Actions runs automatically:

```yaml
# .github/workflows/validate.yml
name: Validate
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Documentation Validation
        run: python scripts/lint/validate_docs.py
      
      - name: Observability Validation
        run: python ~/.claude/skills/openai-harness/assets/custom-linters/validate_observability.py .
      
      - name: Code TODOs Check
        run: python scripts/lint/code_todos.py . --priority high
      
      - name: Tests
        run: go test -v -coverprofile=coverage.out ./...
      
      - name: Coverage Report
        run: go tool cover -func=coverage.out
```

**CI output**:
```
✅ Documentation valid
✅ Observability integration validated
✅ No critical TODOs
✅ Tests passed (96.2% coverage)
✅ All checks passed
```

### 11. Deploy to Kubernetes (5 minutes)

```bash
# Deploy to production cluster
kubectl --context production apply -f k8s/
```

**Kubernetes manifests** (auto-generated by agent):
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: auth-service
        image: web3gate/auth-service:v1.0.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8080
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8080
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
spec:
  ports:
  - port: 80
    targetPort: 8080
    name: http
  - port: 9090
    targetPort: 9090
    name: metrics
  selector:
    app: auth-service
```

### 12. Verify Production (2 minutes)

```bash
# Check Prometheus metrics
curl https://auth.web3gate.xyz/metrics

# Output:
# auth_service_requests_total{method="POST",endpoint="/login",status="200"} 127
# auth_service_request_duration_seconds{endpoint="/login",quantile="0.95"} 0.142
# auth_service_active_sessions 45

# Check Grafana dashboard
open https://grafana.web3gate.xyz/d/auth-service-overview

# Check logs in Loki
# Query: {app="auth-service"} |= "login" | json
```

## Results

**Time investment**:
- Total: ~55 minutes (setup → production)
- Human time: ~15 minutes (docs, reviews)
- Agent time: ~40 minutes (implementation, tests)

**Deliverables**:
- ✅ Complete auth service (2,847 lines of code)
- ✅ 96.2% test coverage
- ✅ Full observability (metrics, logs, traces)
- ✅ Production deployment (3 replicas in K8s)
- ✅ CI/CD pipeline (automated validation)
- ✅ Documentation (architecture, specs, runbooks)
- ✅ Git hooks (automated quality checks)

**Token efficiency**:
- Without harness: Agent reads 15+ files repeatedly (8,000+ tokens per task)
- With harness: Agent reads navigation map + relevant docs (300 tokens per task)
- **96% token savings** via progressive disclosure

**Quality enforcement**:
- Zero error swallowing (pre-commit hook blocks `_ = xxx`)
- Zero unstructured logging (linter enforces JSON format)
- Zero layer violations (architecture linter enforces boundaries)
- Zero secrets committed (pre-commit hook blocks)

This example demonstrates the complete harness engineering workflow: humans define architecture and constraints, agents execute implementation, mechanical enforcement prevents drift, and progressive disclosure keeps context efficient.
