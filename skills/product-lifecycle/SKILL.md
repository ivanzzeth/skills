---
name: product-lifecycle
description: >
  One-person company product lifecycle orchestrator. Guides products through 6 stages:
  DISCOVER → DEFINE → DESIGN → DEVELOP → DELIVER → GROW. Each stage routes to
  specialized skills, enforces gate checks before advancing, and tracks state in
  .product-lifecycle/{product}/. Designed for solo founders running stateless
  microservices on K3s clusters.
  Triggers: "product lifecycle", "new product", "产品全流程", "从零开始",
  "product pipeline", "launch a product", "start a new project", "产品生命周期".
---

# Product Lifecycle Orchestrator

Guide a product from idea to growth through 6 gated stages, delegating work to specialized skills.

## Quick Start

```
/product-lifecycle new <product-name>              # Start a new product from DISCOVER
/product-lifecycle import <product-name> <stage>   # Import existing project at a stage
/product-lifecycle status <product-name>           # Check current stage + iteration
/product-lifecycle <stage> <product-name>          # Jump to a specific stage
/product-lifecycle gate <product-name>             # Run gate check for current stage
/product-lifecycle cycle <product-name>            # Complete iteration, start new cycle
```

## How It Works

```
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ DISCOVER │──▶│  DEFINE  │──▶│  DESIGN  │──▶│ DEVELOP  │──▶│ DELIVER  │──▶│   GROW   │
    │          │   │          │   │          │   │          │   │          │   │          │
    │ 市场调研  │   │ 产品定义  │   │ 技术设计  │   │ 软件开发  │   │ 生产交付  │   │ 增长运营  │
    └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
         Gate 1         Gate 2         Gate 3         Gate 4         Gate 5
              ▲                                                                    │
              └────────────────────── cycle (new iteration) ◀──────────────────────┘
```

Each gate is a checklist. All items must be confirmed before advancing.
You can always jump back to an earlier stage if needed.
After GROW, use `cycle` to archive the current iteration and start a new one from DISCOVER (e.g., for the next feature).

## Dependencies

This skill orchestrates other skills. Before entering a stage, check that the
required skills are installed. If any are missing, guide the user to install them.

Run `bash scripts/check-deps.sh <stage>` to verify. It will output install commands
for any missing skills.

| Stage | Required Skills |
|-------|----------------|
| DISCOVER | `competitive-intelligence-analyst`, `marketing-psychology` |
| DEFINE | `product-marketing-context`, `marketing-ideas`, `write-a-prd` |
| DESIGN | `architecture`, `api-design`, `prd-to-plan`, `prd-to-issues` |
| DEVELOP | `review-diff`, `refactor`, `test-strategy` + lang-specific (e.g. `golang-pro`, `golang-testing`) + built-in: `testing`, `simplify` |
| DELIVER | `security-review`, `woodpecker-ci`, `docker-expert`, `multi-stage-dockerfile`, `kubernetes-specialist`, `monitoring-observability`, `changelog-generator` + project skills: `k3s-ops`, `netbird` |
| GROW | `seo-audit`, `copywriting`, `email-sequence`, `landing-page-design`, `lead-research-assistant`, `startup-financial-modeling` |

## State Directory

All state lives in `.product-lifecycle/{product-name}/` at the repo root:

```
.product-lifecycle/{product-name}/
├── lifecycle.md          # Current stage + gate status
├── 01-discovery.md       # Market research findings
├── 02-prd.md             # Product Requirements Document
├── 03-design.md          # Technical design + ADRs
├── 04-dev-log.md         # Development progress (optional)
├── 05-deploy-checklist.md # Deployment verification
└── 06-growth-plan.md     # Growth strategy + metrics
```

## Initialization

When user says "new product" or "product lifecycle new":

1. Run `bash scripts/lifecycle.sh init <product-name>` to scaffold the directory
2. Open `lifecycle.md` and confirm the product name with the user
3. Enter Stage 1: DISCOVER

## Stage Overview

Read the corresponding `references/stage-*.md` file for detailed instructions
when entering each stage. **Only load the reference for the current stage.**

### Stage 1: DISCOVER — Market & User Research

**Goal:** Validate that a real market opportunity exists.

**Skills to invoke:**
- `/competitive-intelligence-analyst` — Analyze competitors, find gaps, market landscape
- `/marketing-psychology` — Understand target user psychology and buying triggers

**Output:** `.product-lifecycle/{product}/01-discovery.md`

**Gate 1 checklist** → see `references/stage-discover.md`

---

### Stage 2: DEFINE — Product Definition

**Goal:** Crystallize what we're building and for whom.

**Skills to invoke:**
- `/product-marketing-context` — Define positioning, ICP, messaging
- `/marketing-ideas` — Brainstorm GTM approaches
- `/write-a-prd` — Write PRD and submit as GitHub Issue

**Output:** `.product-lifecycle/{product}/02-prd.md` + GitHub Issue

**Gate 2 checklist** → see `references/stage-define.md`

---

### Stage 3: DESIGN — Technical Architecture

**Goal:** Design a system that is stateless, scalable, and deployable on K3s.

**Skills to invoke:**
- `/architecture` — System design with trade-off analysis
- `/api-design` — API contract design
- `/prd-to-plan` — Break PRD into phased implementation plan
- `/prd-to-issues` — Create vertical-slice GitHub Issues

**Mandatory check:** Stateless microservice validation (see `references/stage-design.md`)

**Output:** `.product-lifecycle/{product}/03-design.md` + ADR + GitHub Issues

**Gate 3 checklist** → see `references/stage-design.md`

---

### Stage 4: DEVELOP — Build & Test

**Goal:** Implement the design with quality.

**Skills to invoke:**
- `/test-strategy` — Layered testing: unit → integration → E2E → smoke
- `/testing` — TDD workflow: write tests first, then implement (built-in)
- `/review-diff` — Code review before commit
- `/refactor` — Code smell detection, DRY/SOLID enforcement
- `/simplify` — Review and simplify changed code (built-in)
- Language-specific: `/golang-pro` + `/golang-testing` (Go), or equivalent for Python/Rust/TS

**Output:** Code + Tests (unit + integration) + PRs

**Gate 4 checklist** → see `references/stage-develop.md`

---

### Stage 5: DELIVER — Ship to Production

**Goal:** Containerize, deploy to K3s, verify health.

**Skills to invoke:**
- `/security-review` — **Multi-round security audit (mandatory before production)**
- `/woodpecker-ci` — CI/CD pipeline management, triggering, status checking
- `/k3s-ops` — Cluster architecture, ingress, scheduling (read before deploying)
- `/netbird` — VPN mesh connectivity (read before deploying)
- `/docker-expert` — Dockerfile best practices
- `/multi-stage-dockerfile` — Optimized multi-stage builds
- `/kubernetes-specialist` — K8s/K3s deployment manifests
- `/monitoring-observability` — Metrics, alerts, dashboards
- `/changelog-generator` — Generate release changelog
- `/test-strategy` — Post-deploy smoke tests (Layer 3)

**Output:** `.product-lifecycle/{product}/05-deploy-checklist.md` + security audit report

**Gate 5 checklist** → see `references/stage-deliver.md`

**Security audit is a hard gate:** Services MUST pass at least Round 1-3 of `/security-review`
before production deployment. Round 4 (adversarial) required for public-facing services.

---

### Stage 6: GROW — Acquire & Retain Users

**Goal:** Drive awareness, acquisition, and retention.

**Skills to invoke:**
- `/seo-audit` — SEO optimization
- `/copywriting` — Marketing copy
- `/email-sequence` — Email marketing flows
- `/landing-page-design` — Landing page creation
- `/lead-research-assistant` — Find potential customers
- `/startup-financial-modeling` — Unit economics, projections

**Output:** `.product-lifecycle/{product}/06-growth-plan.md`

---

## Stage Navigation

The user can:
- **Advance:** Complete gate → move to next stage
- **Jump:** `/product-lifecycle design my-product` — go directly to any stage
- **Go back:** `/product-lifecycle discover my-product` — re-enter earlier stage
- **Skip gate:** Say "skip gate" to advance without completing all checklist items (logged in lifecycle.md)

## Important Rules

1. **Only load one stage's reference at a time** — don't read all 6 references upfront
2. **Always check lifecycle.md first** — know where the product currently is
3. **Gate checks are advisory, not blocking** — user is the sole decision-maker
4. **Don't duplicate skill logic** — invoke the skill, don't re-implement its workflow
5. **All state in .product-lifecycle/** — never write lifecycle state to other directories
6. **Commit after every stage** — when a stage's work is done (fixes, tests, config changes), commit immediately. Don't accumulate uncommitted changes across stages. Don't ask whether to commit — just do it.
