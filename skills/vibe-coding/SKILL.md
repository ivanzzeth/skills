---
name: vibe-coding
version: 1.1.0
description: >
  Structured AI-assisted coding workflow. Transforms vague intent into production-ready code
  through plan-first, specs-driven, iterative process. Supports both simple inline coding
  and complex multi-component agentic workflows. Use when user asks to write code, implement
  features, generate functions, or describes what they want built. Triggers include: "write code",
  "implement", "generate", "build", "create function", "vibe coding", "plan first", "specs first".
---

# Vibe Coding - AI-Assisted Coding Workflow

Transform "vibe" (intent/description) into production-ready code through a structured, iterative engineering process.

## Core Philosophy

**Vibe Coding is NOT:**
- Random code generation
- Copy-paste without understanding
- Skipping validation and tests
- One-shot, no-iteration output
- Manual sequential work when parallelism is possible

**Vibe Coding IS:**
- Intent → Specs → Plan → Code → Review → Test → Iterate
- Explicit about assumptions (or ask to clarify)
- Self-reviewing for DRY, validation, robustness
- Context-aware across conversation
- Agentic when complexity requires parallel execution

## Phase 0: COMPLEXITY ASSESSMENT (NEW)

**Before starting, assess task complexity:**

| Complexity | Criteria | Approach |
|------------|----------|----------|
| **Simple** | 1-2 files, single component, < 200 lines | Inline coding (Steps 1-6) |
| **Medium** | 3-5 files, 2-3 components, clear boundaries | Sequential with TodoWrite |
| **Complex** | 5+ files, multiple components, cross-cutting | Agentic parallel execution |

**Decision Tree:**
```
Is it 5+ files OR multiple independent components?
├── YES → Use Task tool for parallel subagents
│         └── Decompose into subtasks, launch in parallel
└── NO → Is it 3+ files OR multi-phase?
         ├── YES → Use TodoWrite for tracking
         └── NO → Inline coding workflow
```

## Mandatory Workflow (7 Steps)

### Step 1: INTENT → Understand the Vibe

**Before writing ANY code, MUST:**

1. **Restate the requirement** in your own words
2. **Identify ambiguities** - what's unclear?
3. **Assess complexity** - Simple/Medium/Complex?
4. **Ask clarifying questions** if:
   - Tech stack not specified
   - Input/output format unclear
   - Edge cases not defined
   - Performance requirements unknown
   - Error handling expectations unclear

```
<summary>
User wants: [restate in your own words]
Tech stack: [specified or ask]
Complexity: [Simple/Medium/Complex]
Input: [what goes in]
Output: [what comes out]
Unclear points: [list questions if any]
</summary>
```

**NO ASSUMPTIONS** - If unclear, ASK. Never guess critical details.

### Step 2: PLAN FIRST → Architecture Sketch

**Output a detailed plan before coding:**

```
<plan>
## Technical Approach
- Tech stack: [languages, frameworks, libraries]
- Architecture pattern: [MVC, Clean, Layered, etc.]
- Complexity level: [Simple/Medium/Complex]

## Module/Function Breakdown
1. [Module A] - responsibility - [can parallelize: yes/no]
2. [Module B] - responsibility - [can parallelize: yes/no]
3. [Module C] - responsibility - [depends on: Module A]

## Execution Strategy
- [ ] Parallel execution possible? → Use Task tool with multiple agents
- [ ] Sequential dependencies? → Order accordingly
- [ ] Use TodoWrite? → Yes if 3+ tasks

## Key Abstractions
- Where will code repeat? → Extract to [helper/util]
- Where is validation needed? → [input points]
- Where are side effects? → [I/O, network, DB]

## Edge Cases & Risks
- Edge case 1: [scenario] → [handling]
- Edge case 2: [scenario] → [handling]
- Risk: [potential issue] → [mitigation]

## Dependencies
- External: [packages needed]
- Internal: [existing code to use]
</plan>
```

**For Complex tasks:** After planning, proceed to Step 2.5 (Agentic Execution).

### Step 2.5: AGENTIC EXECUTION (For Complex Tasks)

**When task has 5+ files or multiple independent components, use parallel agents:**

1. **Decompose** into independent subtasks (one per component/layer)
2. **Create TodoWrite** entries for all planned tasks
3. **Launch agents** using Task tool with `run_in_background: true`
4. **Launch in parallel** - use single message with multiple Task calls
5. **Monitor and integrate** - check agent outputs, resolve conflicts

**Example parallel launch:**
```
<task_launch>
## Parallel Agents (launch all in ONE message)
Task 1: "Implement storage layer" → subagent_type: general-purpose
Task 2: "Add interface definitions" → subagent_type: general-purpose
Task 3: "Create REST handlers" → subagent_type: general-purpose
Task 4: "Implement TUI view" → subagent_type: general-purpose
Task 5: "Write unit tests" → subagent_type: general-purpose
</task_launch>
```

**Agent prompt template:**
```
Implement [component] at [file path].

Based on the design: [brief design context]

Requirements:
1. [Specific requirement 1]
2. [Specific requirement 2]

Reference files for patterns:
- [existing file 1] - for [pattern X]
- [existing file 2] - for [pattern Y]

IMPORTANT: This is a code writing task. Create/modify the file.
```

**After agents complete:**
- Verify each output with `go build ./...`
- Run relevant tests
- Resolve any conflicts or inconsistencies

### Step 3: SPECS → CODE Generation

**Generate code following these principles:**

| Principle | Enforcement |
|-----------|-------------|
| **DRY** | No repeated logic - extract to functions |
| **Input Validation** | ALL inputs validated at entry point |
| **Robust Guards** | Defensive checks, no silent failures |
| **SRP** | Each function does ONE thing |
| **KISS** | Simplest solution that works |
| **YAGNI** | No speculative features |
| **Explicit Errors** | Return errors, never swallow them |

```
<code language="[lang]">
// Production-ready code here
// With comments for non-obvious logic only
</code>
```

**Code Quality Checklist (MUST satisfy):**
- [ ] All parameters validated
- [ ] All errors handled and propagated
- [ ] No hardcoded fallbacks on failure
- [ ] No `_ = xxx` ignoring returns
- [ ] Constructor functions return error
- [ ] Interface nil → panic (expose bugs)
- [ ] No Chinese characters in code

### Step 4: SELF-REVIEW → Improve Before Delivery

**Mandatory self-review after code generation:**

```
<review>
## DRY Check
- [ ] No duplicated logic? [yes/no, details]

## Validation Check
- [ ] All inputs validated? [yes/no, details]
- [ ] All errors propagated? [yes/no, details]

## Robustness Check
- [ ] Edge cases handled? [yes/no, details]
- [ ] Nil/null safety? [yes/no, details]

## Naming & Clarity
- [ ] Clear function names? [yes/no, details]
- [ ] Self-documenting code? [yes/no, details]

## Improvements Found
1. [improvement 1 - applied or suggested]
2. [improvement 2 - applied or suggested]
</review>
```

**If issues found → FIX IMMEDIATELY, don't just report.**

### Step 5: TEST → Verify Correctness

**Provide test cases for every code delivery:**

```
<tests>
## Unit Test Cases

### Test 1: [Happy path - normal input]
Input: [specific input]
Expected: [specific output]

### Test 2: [Edge case - empty/null]
Input: [edge input]
Expected: [expected behavior]

### Test 3: [Edge case - boundary values]
Input: [boundary input]
Expected: [expected behavior]

### Test 4: [Error case - invalid input]
Input: [invalid input]
Expected: [error type/message]

### Test 5: [Concurrent/Stress - if applicable]
Scenario: [description]
Expected: [behavior under load]

## How to Run
```bash
[test command]
```
</tests>
```

### Step 6: VERIFY → Incremental Build & Test

**After each phase/component (MANDATORY):**

1. **Build check**: `go build ./...` (or equivalent)
2. **Test check**: `go test ./path/to/package/...`
3. **If tests hang**: Use binary search debugging

```
<verification>
## Build Status
$ go build ./...
[output or "✓ Success"]

## Test Status
$ go test ./path/... -v
[summary: X passed, Y failed]

## Issues Found
- [Issue 1]: [resolution]
- [Issue 2]: [resolution]
</verification>
```

**Debugging hung tests (binary search approach):**
```bash
# If full test suite hangs, isolate the problem:
timeout 30 go test ./pkg1/... # Works? ✓
timeout 30 go test ./pkg2/... # Hangs? ✗
# → Problem in pkg2, investigate further
timeout 30 go test ./pkg2/... -run "TestA" # Works?
timeout 30 go test ./pkg2/... -run "TestB" # Hangs?
# → Problem in TestB
```

### Step 7: ITERATE → Continuous Improvement

**Always end with iteration prompt:**

```
<next>
## Current Status
- [x] Core functionality implemented
- [x] Self-reviewed and improved
- [x] Test cases provided
- [x] Build verified

## Suggested Enhancements
1. [optional enhancement 1]
2. [optional enhancement 2]

## Questions for You
- Is this implementation what you expected?
- Should I add [feature X]?
- Any edge cases I missed?
- Ready to proceed or need changes?
</next>
```

## Progress Tracking (MANDATORY for 3+ tasks)

Use **TodoWrite** to track all implementation tasks:

```
<progress_tracking>
## When to Use TodoWrite
- Any task with 3+ subtasks
- Multi-phase implementations
- Complex features spanning multiple files

## How to Use
1. Create todos at START with all planned tasks
2. Mark `in_progress` BEFORE starting each task
3. Mark `completed` IMMEDIATELY after finishing
4. Never batch completions - mark as you go
5. Update todos when scope changes

## Example
TodoWrite([
  {content: "Implement storage layer", status: "completed"},
  {content: "Add interface definitions", status: "completed"},
  {content: "Create REST handlers", status: "in_progress"},
  {content: "Write unit tests", status: "pending"},
  {content: "Run full test suite", status: "pending"}
])
</progress_tracking>
```

## Output Format Template

Every coding response MUST use this structure:

```markdown
<summary>
[Requirement restatement + complexity assessment]
</summary>

<plan>
[Detailed architecture, modules, and execution strategy]
</plan>

[For Complex tasks: <task_launch> with parallel agents]

<code language="xxx">
[Production-ready code]
</code>

<review>
[Self-review checklist results]
</review>

<tests>
[Test cases with inputs/outputs]
</tests>

<verification>
[Build and test results]
</verification>

<next>
[Iteration options and questions]
</next>
```

## Context Preservation Rules

### Within Conversation
- Reference previous decisions explicitly
- Track what has been implemented vs planned
- Maintain consistent naming across iterations

### Across Files
- When modifying existing code, show BEFORE → AFTER diff
- Explain what changed and WHY
- Verify changes don't break existing functionality

### Changelog Format
```
<changelog>
## Changes Made
1. [file:line] - [what changed] - [why]
2. [file:line] - [what changed] - [why]

## Impact
- Affects: [list affected components]
- Breaking: [yes/no, details]
</changelog>
```

## Anti-Patterns (NEVER DO)

1. **NO bare code dumps** - Always wrap in workflow structure
2. **NO assumptions** - Ask if unclear, don't guess
3. **NO skipping validation** - Every input must be validated
4. **NO ignoring errors** - Propagate all errors
5. **NO one-shot delivery** - Always offer iteration
6. **NO context loss** - Reference previous conversation
7. **NO untested code** - Always provide test cases
8. **NO over-engineering** - KISS + YAGNI strictly enforced
9. **NO Chinese in code** - English only for code artifacts
10. **NO hardcoded fallbacks** - Fail explicitly, never silently
11. **NO late verification** - Build/test incrementally, not just at end
12. **NO manual parallel work** - Use Task tool for parallel execution
13. **NO forgetting TodoWrite** - Track all tasks for complex features

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                 VIBE CODING WORKFLOW v1.1               │
├─────────────────────────────────────────────────────────┤
│  0. ASSESS    → Simple/Medium/Complex?                  │
│  1. INTENT    → Restate + Ask clarifying questions      │
│  2. PLAN      → Architecture + Modules + Execution      │
│  2.5 AGENTIC  → Parallel agents for Complex tasks       │
│  3. CODE      → DRY + Validate + Guard + SRP + KISS     │
│  4. REVIEW    → Self-check all quality criteria         │
│  5. TEST      → 3-5 test cases with input/output        │
│  6. VERIFY    → Build + Test incrementally              │
│  7. ITERATE   → Ask feedback + suggest enhancements     │
├─────────────────────────────────────────────────────────┤
│  TOOLS: TodoWrite (tracking) | Task (parallel agents)   │
│  VERIFY: go build → go test → binary search debug       │
└─────────────────────────────────────────────────────────┘
```

## Integration with Project Rules (from CLAUDE.md)

This skill enforces all CLAUDE.md principles:

| CLAUDE.md Rule | Vibe Coding Enforcement |
|----------------|------------------------|
| DRY | Self-review checks for duplication |
| Input validation | Step 3 checklist item |
| Explicit errors | No swallowed errors, propagate all |
| No hardcoded fallbacks | Step 3 checklist item |
| Constructor returns error | Step 3 checklist item |
| Interface nil → panic | Step 3 checklist item |
| TDD | Step 5 provides test cases first |
| No Chinese in code | Step 3 checklist item |

## Integration with Other Skills

| Skill | When to Use Together |
|-------|---------------------|
| `architecture` | Complex features needing design docs first |
| `debugging` | When tests fail or behavior unexpected |
| `testing` | For comprehensive TDD workflow |
| `git-management` | For committing completed work |
| `performance` | When optimization needed |
| `refactor` | For library extraction and code deduplication |

## Special Case: Refactoring / Library Extraction

When the task involves extracting reusable code or reducing duplication, follow the **refactor** skill's design-first approach:

### Key Differences from New Code

1. **Design must be reviewed before implementation**
   - Show proposed module structure
   - Get user approval on design
   - Iterate on design based on feedback

2. **Composability over Integration**
   - Create independent, standalone modules
   - Let callers decide how to combine
   - Avoid "god" modules that do too much

3. **Common Design Feedback Patterns**
   | Feedback | Response |
   |----------|----------|
   | "Too coupled" | Split into independent modules |
   | "Too generic name" | Make name more specific |
   | "Why not reuse X?" | Check framework for existing types |
   | "Unnecessary module" | Remove, let strategy control directly |

4. **Design Iteration Example**
   ```
   v1: InventoryManager (coupled) → "Too coupled"
   v2: threshold + skew + behavior → "Behavior unnecessary"
   v3: threshold + skew only → "Zone too generic"
   v4: ThreeZone + Linear/Exponential/Step → Approved!
   ```

### Refactoring Checklist
- [ ] Analyzed duplication patterns first
- [ ] Proposed modular design for review
- [ ] Used specific names (not generic)
- [ ] Reused existing framework types
- [ ] Got design approval before implementing
- [ ] Replaced old code incrementally
- [ ] Verified at each step

## Example Workflow

See [references/workflow-example.md](references/workflow-example.md) for a complete example of the vibe coding workflow in action.
