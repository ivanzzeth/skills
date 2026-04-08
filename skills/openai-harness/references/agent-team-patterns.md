# Agent Team Collaboration Patterns

Based on real-world experience from web3-opb-auth Prometheus integration (4 agents, 3 rounds, 6 issues fixed).

## Overview

Agent teams dramatically improve output quality through specialization and peer review. One agent working alone may miss edge cases; a team of specialists catches them through iteration.

**Key insight**: Quality emerges from iteration, not perfection on first attempt.

## Pattern 1: Generator-Validator (生成-验证)

**Best for**: Tasks with objective quality standards (code, documentation, infrastructure config)

### Team Structure

- **Generator agents** (1-2): Focus on rapid implementation
- **Validator agents** (1-2): Focus on finding issues
- **Orchestrator** (1): Coordinates iteration cycles

### Workflow

```
1. Generator implements feature
2. Validator tests/reviews → finds issues
3. Generator fixes issues
4. Validator re-validates
5. Repeat until validator approves
```

### Real Case Study: Prometheus Integration

**Team**: backend-dev (generator), qa-engineer (validator), security-auditor (validator), devops (infrastructure)

**Round 1 - Initial Implementation**:
- backend-dev: Implemented 5 Prometheus metrics
- qa-engineer: Found 1 critical issue
  - Issue #1: ActiveSessions Gauge only increments, never decrements (stale data)
  - Recommendation: Use Counter instead (TokensIssuedTotal with token_type label)

**Round 2 - Fix & Expand**:
- backend-dev: Refactored to TokensIssuedTotal Counter, added tests
- qa-engineer: Found 5 more issues
  - Issue #2: RefreshToken double-counts metrics
  - Issue #3: BindAuth internal verification inflates JWT metrics
  - Issue #4: OIDC login flow missing metrics
  - Issue #5: 404 requests use actual path (high cardinality)
  - Issue #6: Metrics unit tests missing

**Round 3 - Final Polish**:
- backend-dev: Created VerifyTokenInternal() to avoid double counting, fixed all issues
- qa-engineer: Verified all fixes → APPROVED
- devops: Updated Grafana dashboard with new metrics

**Outcome**: 
- Production-ready in 3 rounds (vs. 10+ rounds if working solo)
- 6 issues caught before production
- All tests passing, comprehensive coverage

### Key Principles

**1. QA runs after EVERY change, not just at the end**
- Catching issues early reduces fix cost
- Each round validates previous fixes didn't break anything

**2. Validators provide specific reproduction steps**
- ❌ Bad: "Metrics seem wrong"
- ✅ Good: "RefreshToken calls GenerateToken() which records 'jwt' token, then records 'refresh' token → double counting"

**3. Generators create internal APIs to avoid instrumentation conflicts**
```go
// Public: Records metrics
func GenerateToken(userID string) string {
    token := generateTokenInternal(userID)
    metrics.TokensIssuedTotal.WithLabelValues("jwt").Inc()
    return token
}

// Internal: No metrics (for internal calls)
func generateTokenInternal(userID string) string {
    return jwt.Sign(...)
}

func RefreshToken(oldToken string) string {
    // Use internal method → no double counting
    token := generateTokenInternal(userID)
    metrics.TokensIssuedTotal.WithLabelValues("refresh").Inc()
    return token
}
```

## Pattern 2: Pipeline (流水线)

**Best for**: Sequential tasks where output of one stage feeds next stage

### Team Structure

- **Stage 1 agent**: Produces artifact A
- **Stage 2 agent**: Consumes A, produces B
- **Stage N agent**: Consumes N-1, produces final output

### Example Use Cases

**Documentation pipeline**:
1. Analyst agent → extracts requirements from user stories
2. Architect agent → designs system based on requirements
3. Writer agent → produces technical documentation from design

**Code generation pipeline**:
1. Schema agent → generates database schema from spec
2. Backend agent → generates API from schema
3. Frontend agent → generates UI from API spec

### Key Principles

**1. File-based handoff**
- Each stage writes output to `_workspace/{phase}_{agent}_{artifact}.ext`
- Next stage reads from well-known path
- Preserves audit trail

**2. Clear contracts**
- Define exact format/schema for each artifact
- Validator at stage boundaries ensures contract compliance

**3. Parallel when possible**
- If Stage 2 and 3 don't depend on each other, run in parallel

## Pattern 3: Expert Pool (专家池)

**Best for**: Tasks requiring different domain expertise (security, performance, accessibility)

### Team Structure

- **Coordinator agent**: Routes work to appropriate expert
- **Domain experts** (3-5): Specialized knowledge areas
- **Integrator agent**: Combines expert feedback

### Workflow

```
1. Coordinator analyzes task → identifies required experts
2. Experts work in parallel on their domain
3. Integrator combines recommendations
4. Generator implements consolidated feedback
```

### Example: Security Audit

**Experts**:
- OAuth2 security expert → reviews authentication flow
- SQL injection expert → reviews database queries
- Crypto expert → reviews key management
- CORS expert → reviews cross-origin policies

**Outcome**: Comprehensive security review in 1/4 the time (parallel execution)

### Key Principles

**1. Experts focus ONLY on their domain**
- OAuth expert doesn't comment on SQL
- Avoids scope creep and conflicting advice

**2. Integrator resolves conflicts**
- If experts disagree, integrator makes final call
- Explains rationale for chosen approach

## Pattern 4: Hierarchical Delegation (层级委托)

**Best for**: Large tasks that need to be broken down recursively

### Team Structure

- **Lead agent**: Breaks task into subtasks
- **Sub-team leads**: Further decompose assigned subtasks
- **Implementers**: Execute leaf tasks

### Example: Microservice Migration

**Level 1 - Lead**:
- Subtask A: Extract user service
- Subtask B: Extract auth service
- Subtask C: Update API gateway

**Level 2 - Sub-team A Lead**:
- A1: Define service boundaries
- A2: Implement new service
- A3: Migrate database
- A4: Update clients

**Level 3 - Implementers**:
- Agent A2.1: Implement REST API
- Agent A2.2: Write unit tests
- Agent A2.3: Write integration tests

### Key Principles

**1. Clear ownership**
- Each subtask has exactly one owner
- Owner responsible for delegation and integration

**2. Bottom-up integration**
- Leaf tasks complete first
- Sub-team leads integrate
- Lead does final integration

## Choosing the Right Pattern

| Scenario | Recommended Pattern | Why |
|----------|-------------------|-----|
| Code that needs quality validation | Generator-Validator | Catches bugs through iteration |
| Multi-stage transformation | Pipeline | Clear data flow, audit trail |
| Requires diverse expertise | Expert Pool | Parallel execution, deep knowledge |
| Large complex project | Hierarchical Delegation | Scales through decomposition |
| Simple feature implementation | Single agent | Don't over-engineer |

## Anti-Patterns to Avoid

### ❌ Too Many Agents
**Problem**: 7+ agents, excessive coordination overhead

**Solution**: Merge similar roles. Do you really need separate "backend-dev" and "api-dev"?

### ❌ Unclear Handoff Points
**Problem**: Agent A assumes Agent B will do something, but B doesn't know

**Solution**: Explicit task assignments via TaskCreate, file-based contracts

### ❌ Validator Without Authority
**Problem**: QA finds issue, dev ignores it

**Solution**: Validator has veto power. Generator must fix ALL issues before proceeding.

### ❌ No Iteration Budget
**Problem**: Trying to get perfection in round 1

**Solution**: Plan for 2-3 rounds. Round 1 = working, Round 2 = correct, Round 3 = polished

## Measuring Team Effectiveness

**Good signs**:
- Issues found in Round 1-2, not production
- Each round finds fewer issues (converging)
- Validators approve by Round 3

**Bad signs**:
- Same issues repeated across rounds (unclear communication)
- Round 5+ still finding basic bugs (need better generator)
- Validators rubber-stamping (not actually validating)

## Next Steps

After choosing a pattern:
1. Define team structure in `CLAUDE.md` (see project example)
2. Create agent definitions in `.claude/agents/`
3. Document handoff format in agent definitions
4. Set up quality gates (what must validator check?)
5. Run first iteration, measure time and quality
6. Adjust team size/roles based on bottlenecks
