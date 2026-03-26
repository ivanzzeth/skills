# Stage 2: DEFINE — Product Definition

## Goal

Crystallize what we're building, for whom, and how we'll position it in the market.

## Workflow

### Step 1: Product positioning

Invoke `/product-marketing-context` to create/update `.agents/product-marketing-context.md`.

This defines:
- Product name and one-liner
- Target audience / ICP (Ideal Customer Profile)
- Key differentiators
- Messaging framework
- Competitive positioning

### Step 2: GTM brainstorm

Invoke `/marketing-ideas` to brainstorm go-to-market approaches.

Select 2-3 channels that match:
- One-person company constraints (time, budget)
- Target audience behavior
- Product type (dev tool, SaaS, API, etc.)

Document selected channels in `02-prd.md` under a **GTM Strategy** section.

### Step 3: Write the PRD

Invoke `/write-a-prd`.

This skill will:
1. Interview you about the problem and solution
2. Explore the codebase (if applicable)
3. Define modules and interfaces
4. Write a structured PRD
5. Submit as a GitHub Issue

Save a copy of the PRD to `02-prd.md`.

### Step 4: Validate scope

Review the PRD and ask:
- Is this achievable as a one-person team in the target timeline?
- Is the MVP scope small enough to ship in 2-4 weeks?
- Are there features that should be cut to Phase 2?

Update `02-prd.md` with final scope decisions.

## Gate 2 Checklist

Before advancing to DESIGN, confirm:

- [ ] Product positioning document exists (`.agents/product-marketing-context.md`)
- [ ] PRD written and submitted as GitHub Issue
- [ ] MVP scope is achievable in 2-4 weeks
- [ ] User stories are comprehensive
- [ ] Out-of-scope items explicitly listed
