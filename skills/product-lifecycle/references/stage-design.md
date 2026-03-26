# Stage 3: DESIGN — Technical Architecture

## Goal

Design a stateless, horizontally scalable system deployable on K3s.

## Workflow

### Step 1: System architecture

Invoke `/architecture` with the PRD as input.

The architecture skill will walk through:
1. Requirements clarification (functional + NFRs)
2. High-level design (layers, components)
3. Diagrams (C4, sequence)
4. Alternatives with trade-offs
5. Recommendation
6. Risk analysis

Save the output to `03-design.md`.

### Step 2: Stateless microservice validation

**This is mandatory.** Before proceeding, verify the design against these criteria:

```
## Stateless Microservice Checklist

- [ ] No local file storage — use object storage (S3/MinIO) or database
- [ ] No in-memory session state — use Redis or JWT tokens
- [ ] No sticky sessions required — any replica can handle any request
- [ ] Horizontally scalable — safe to run N replicas behind load balancer
- [ ] Graceful shutdown — handle SIGTERM, drain connections
- [ ] Health check endpoint — GET /healthz returns 200
- [ ] Readiness check endpoint — GET /readyz returns 200
- [ ] All config via environment variables — 12-factor app
- [ ] No local cron jobs — use K8s CronJob or external scheduler
- [ ] Logs to stdout/stderr — not to local files
```

If any item fails, redesign that component before proceeding.
Update `03-design.md` with the completed checklist.

### Step 3: API design

Invoke `/api-design` for the public-facing API.

Document:
- Endpoints, methods, request/response schemas
- Authentication/authorization approach
- Rate limiting strategy
- Versioning strategy

Append to `03-design.md`.

### Step 4: Implementation plan

Invoke `/prd-to-plan` to break the PRD into phased vertical slices.

This creates a plan file in `plans/` with:
- Architectural decisions
- Phased implementation with acceptance criteria

### Step 5: Create work items

Invoke `/prd-to-issues` to create GitHub Issues from the PRD.

Each issue is a thin vertical slice (tracer bullet) that cuts through all layers.

## Gate 3 Checklist

Before advancing to DEVELOP, confirm:

- [ ] System architecture documented with diagrams
- [ ] **All stateless microservice checklist items pass**
- [ ] API contracts defined
- [ ] Implementation plan created (phased vertical slices)
- [ ] GitHub Issues created for each work item
- [ ] ADR written for key architectural decisions (in `docs/architecture/decisions/`)
