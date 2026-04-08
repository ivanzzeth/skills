# OpenAI Harness Engineering Principles

Source: OpenAI "Harness engineering: leveraging Codex in an agent-first world" (Feb 11, 2026)

## Core Philosophy

**Humans steer. Agents execute.**

Building software where AI agents write 100% of the code requires fundamentally rethinking the engineering role:
- Humans design environments, specify intent, and build feedback loops
- Agents execute tasks, open PRs, respond to reviews, and merge changes
- The constraint forces focus on what maximizes human time and attention

## Key Architectural Principles

### 1. Repository Knowledge as System of Record

**Anti-pattern**: One giant AGENTS.md file
- Context is scarce → crowds out task/code/docs
- Too much guidance → nothing is prioritized
- Rots instantly → stale rules accumulate
- Hard to verify → drift is inevitable

**Pattern**: AGENTS.md as table of contents (~100 lines)

```
AGENTS.md           # Map, not encyclopedia
ARCHITECTURE.md     # Top-level domain/package structure
docs/
├── design-docs/
│   ├── index.md
│   ├── core-beliefs.md
│   └── ...
├── exec-plans/
│   ├── active/
│   ├── completed/
│   └── tech-debt-tracker.md
├── generated/
│   └── db-schema.md
├── product-specs/
│   ├── index.md
│   └── feature-name.md
├── references/
│   ├── design-system-reference-llms.txt
│   └── ...
├── DESIGN.md
├── FRONTEND.md
├── PLANS.md
├── PRODUCT_SENSE.md
├── QUALITY_SCORE.md
├── RELIABILITY.md
└── SECURITY.md
```

### 2. Progressive Disclosure

Agents start with a small, stable entry point and are taught where to look next:
1. **AGENTS.md** - Always in context (~100 lines)
2. **Domain docs** - Loaded when agent works in specific area
3. **References** - Loaded as needed for specific tasks

Benefits:
- Agents navigate intentionally vs. pattern-matching locally
- Documentation is mechanically verifiable (cross-links, freshness, coverage)
- Updates are localized, not scattered across monolithic file

### 3. Agent Legibility is the Goal

**Core principle**: What the agent can't access in-context effectively doesn't exist.

Knowledge must be:
- **Repository-local** - Not in Google Docs, Slack, or human heads
- **Versioned** - Co-located with code in git
- **Discoverable** - Cross-linked and indexed
- **Machine-readable** - Markdown, not prose-heavy PDFs

Examples of making systems legible:
- App bootable per git worktree → agent tests each change in isolation
- Chrome DevTools Protocol integrated → agent drives UI, captures screenshots
- Observability stack per worktree → agent queries logs (LogQL), metrics (PromQL), traces (TraceQL)
- Database schemas in `docs/generated/` → agent knows data structures

### 4. Enforce Architecture, Not Implementation

**Rigid architectural boundaries**:
- Each business domain divided into fixed layers:
  `Types → Config → Repo → Service → Runtime → UI`
- Cross-cutting concerns (auth, telemetry, feature flags) enter through **Providers**
- Custom linters enforce dependency directions
- Structural tests validate invariants

**Freedom within boundaries**:
- Agents choose libraries (e.g., model prefers Zod for validation, not mandated)
- Implementation details flexible as long as invariants hold
- Code style may differ from human preferences → that's acceptable

### 5. Golden Principles to Combat Drift

**Problem**: Agents replicate existing patterns, including suboptimal ones → drift over time

**Solution**: Encode "golden principles" + automated cleanup

Examples:
- Prefer shared utility packages over hand-rolled helpers
- Validate data at boundaries, don't probe "YOLO-style"
- Use typed SDKs, not guessed shapes
- No hardcoded values → use config

**Enforcement**: Recurring background agents scan for violations, open fix PRs
- Functions like garbage collection for technical debt
- Human taste captured once, enforced continuously
- Prevents compound interest on tech debt

### 6. Throughput Changes Merge Philosophy

In high-throughput agent systems:
- **Corrections are cheap** → waiting is expensive
- Minimal blocking merge gates
- Short-lived PRs (hours, not days)
- Test flakes addressed with follow-up runs, not indefinite blocking
- Agent-to-agent review preferred over human review

This would be irresponsible in low-throughput environments, but with 3.5+ PRs/engineer/day, the math changes.

### 7. Plans as First-Class Artifacts

**Lightweight plans**: Ephemeral, for small changes
**Execution plans**: Complex work with:
- Progress tracking
- Decision logs
- Versioned in repository
- Active/completed/tech-debt all co-located

Allows agents to operate without external context (Jira, Slack, Google Docs).

### 8. Mechanical Enforcement

Custom linters with agent-friendly error messages:
- Structured logging requirements
- Naming conventions (schemas, types)
- File size limits
- Platform-specific reliability rules

Error messages inject remediation instructions → agent self-corrects

CI jobs validate:
- Documentation up-to-date
- Cross-links valid
- Structure correct

"Doc-gardening" agent:
- Scans for stale/obsolete documentation
- Compares docs to actual code behavior
- Opens fix-up PRs

## What Changes for Human Engineers

Traditional role:
- Write code directly
- Review PRs manually
- Maintain architecture through discipline

Agent-first role:
- Design environments that enable agent productivity
- Identify missing capabilities when agents struggle
- Build feedback loops: testing, validation, review automation
- Translate user feedback → acceptance criteria
- Validate outcomes, not implementations

**Key insight**: When agents struggle, don't "try harder" → ask "what capability is missing, and how do we make it legible and enforceable?"

## Increasing Autonomy Over Time

As environment matures, agents can:
1. Validate current codebase state
2. Reproduce reported bugs
3. Record video demonstrating failure
4. Implement fix
5. Validate fix by driving application
6. Record video demonstrating resolution
7. Open PR
8. Respond to agent/human feedback
9. Detect and remediate build failures
10. Escalate to human only when judgment required
11. Merge change

This requires significant investment in tooling, documentation structure, and feedback loops.

## Technology Selection Criteria

Prefer technologies that are:
- **Fully internalizable** - Agent can reason about behavior in-repo
- **"Boring"** - Composable, API-stable, well-represented in training data
- **Transparent** - Not opaque upstream behavior

Sometimes cheaper to reimplement subsets than work around opaque libraries.
Example: Custom `map-with-concurrency` helper instead of `p-limit` → integrated with OpenTelemetry, 100% test coverage, exact runtime behavior.

## Open Questions

As of Feb 2026, still unknown:
- How architectural coherence evolves over years in fully agent-generated systems
- Where human judgment adds most leverage as models improve
- How to encode judgment so it compounds over time
- How systems evolve as models become more capable

**Core lesson**: Building software still demands discipline, but discipline shows up in scaffolding (tooling, abstractions, feedback loops), not in code.
