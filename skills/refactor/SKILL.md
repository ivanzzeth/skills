---
name: refactor
version: 1.0.0
description: >
  Code smell detection and systematic refactoring guidance. Identifies DRY violations,
  SOLID principle breaches, robustness issues, guard clause gaps, and maintainability problems.
  Specialized for extracting reusable libraries from duplicated code patterns.
  Use when: refactoring code, extracting libraries, reducing duplication, improving modularity.
---

# Refactoring Skill - Systematic Code Improvement

Transform tightly-coupled, duplicated code into modular, composable, reusable libraries through iterative design and user collaboration.

## Core Philosophy

**Refactoring is NOT:**
- Just moving code around
- One-shot design without validation
- Creating tightly-coupled "god" modules
- Ignoring existing framework types

**Refactoring IS:**
- Design-first, implement-after
- Iterative design with user feedback loops
- Creating independent, composable modules
- Reusing existing types and patterns

## Phase 0: ANALYSIS - Identify Refactoring Opportunities

**Before proposing any changes:**

1. **Scan for duplication patterns**
   - Use Grep/Glob to find similar code blocks
   - Identify copy-paste patterns across files
   - Note semantic similarities (same logic, different names)

2. **Categorize duplication types**
   | Type | Example | Action |
   |------|---------|--------|
   | **Exact** | Same code in multiple files | Extract to shared function |
   | **Structural** | Same pattern, different values | Extract with parameters |
   | **Semantic** | Same intent, different implementation | Abstract to interface |

3. **Quantify the problem**
   ```
   <analysis>
   ## Duplication Found
   - Pattern A: ~X lines duplicated across Y files
   - Pattern B: ~X lines duplicated across Y files

   ## Files Affected
   - file1.go: PatternA (lines 10-50), PatternB (lines 100-150)
   - file2.go: PatternA (lines 20-60), PatternB (lines 200-250)

   ## Estimated Reduction
   - Current: ~500 lines
   - After refactor: ~200 lines
   - Reduction: 60%
   </analysis>
   ```

## Phase 1: DESIGN - Propose Composable Architecture

**Critical Rule: Design must be reviewed BEFORE implementation**

### Design Principles for Library Extraction

1. **Independence over Integration**
   - Each module should work standalone
   - No circular dependencies
   - Minimal coupling between modules

2. **Composition over Inheritance**
   - Prefer combining small functions over large hierarchies
   - Strategy should control how modules combine
   - Avoid "behavior" modules that force specific combinations

3. **Specific Names over Generic**
   - "ThreeZone" not "Zone"
   - "LinearSkew" not "Skew"
   - Names should indicate what they do, not just the category

4. **Reuse Existing Types**
   - Check framework for existing types before creating new ones
   - Adapt to existing patterns, don't reinvent

### Design Template

```
<design version="1">
## Module Breakdown

### Module: [name]
- **Responsibility**: Single, clear purpose
- **Dependencies**: [list or "none"]
- **Inputs**: [types]
- **Outputs**: [types]
- **Can be used independently**: Yes/No

### Module: [name]
...

## Composition Example
```go
// How strategies will use these modules
result := moduleA.Calculate(input)
adjusted := moduleB.Apply(result, config)
// Strategy decides the combination
```

## Questions for Review
1. Is [X] too coupled with [Y]?
2. Should [Z] be split into multiple modules?
3. Is the naming specific enough?
</design>
```

### Handling Design Feedback

**Common feedback patterns and responses:**

| Feedback | Response |
|----------|----------|
| "Too coupled" | Split into independent modules, let caller combine |
| "Too generic name" | Make name more specific to actual behavior |
| "Why not reuse X?" | Check framework, adapt to existing types |
| "Unnecessary module" | Remove if strategy should control directly |

**Iterate design until approved:**
```
Design v1 → Feedback → Design v2 → Feedback → ... → Approved → Implement
```

## Phase 2: IMPLEMENT - Execute Approved Design

**Only after design approval:**

1. **Create package structure**
   ```
   lib/v1/
   ├── module_a/
   │   ├── api.go       # Public API
   │   └── api_test.go  # Tests
   ├── module_b/
   │   ├── api.go
   │   └── api_test.go
   └── strategy.go      # Entry point exports
   ```

2. **Implementation order**
   - Define types/interfaces first
   - Implement core functions
   - Write tests
   - Add to entry point
   - Refactor existing code to use new package

3. **Verification at each step**
   - `go build ./...` after each file
   - `go test ./...` after tests written
   - Integration test after refactoring existing code

## Phase 3: REFACTOR - Update Existing Code

**Systematic replacement:**

1. **Identify usage sites**
   ```bash
   grep -rn "duplicated_function" ./path/
   ```

2. **Replace incrementally**
   - One file at a time
   - Build after each file
   - Run tests after each file

3. **Delete old code**
   - Only after all usages replaced
   - Verify tests still pass

## Anti-Patterns (NEVER DO)

1. **NO implementing before design approval**
   - Always show design, get feedback, iterate

2. **NO tightly-coupled modules**
   - Modules should be independently usable

3. **NO generic names**
   - Be specific: "ThreeZone" not "Zone"

4. **NO reinventing types**
   - Check framework first, reuse existing types

5. **NO "behavior" modules that force combinations**
   - Let strategies decide how to combine modules

6. **NO big-bang refactoring**
   - Replace incrementally, verify at each step

## Checklist

### Design Phase
- [ ] Analyzed duplication patterns
- [ ] Proposed modular, composable design
- [ ] Used specific, descriptive names
- [ ] Checked for existing framework types to reuse
- [ ] Got user approval on design

### Implementation Phase
- [ ] Created independent modules
- [ ] Wrote comprehensive tests
- [ ] Added entry point exports
- [ ] Build passes

### Refactoring Phase
- [ ] Replaced old code incrementally
- [ ] Verified tests at each step
- [ ] Deleted old duplicated code
- [ ] All tests pass

## Example Workflow

```
User: "Refactor inventory management code"

1. ANALYZE
   → Found ~150 lines duplicated across 3 files
   → Zone classification + Skew calculation + Behavior decision

2. DESIGN v1
   → Proposed InventoryManager with combined logic

   Feedback: "Too coupled, can't compose"

3. DESIGN v2
   → Split into: threshold, skew, behavior modules

   Feedback: "Behavior module unnecessary, let strategy control"

4. DESIGN v3
   → threshold (ThreeZone classification)
   → skew (Linear/Exponential/Step calculators)

   Feedback: "Zone too generic"

5. DESIGN v4
   → threshold.ThreeZone
   → skew.Linear, skew.Exponential, skew.Step

   Approved!

6. IMPLEMENT
   → Create packages with tests
   → Add to strategy.go exports

7. REFACTOR
   → Replace duplicated code in each file
   → Verify builds and tests
   → Delete old code
```

## Integration with Other Skills

| Skill | When to Use |
|-------|-------------|
| `vibe-coding` | For implementing the extracted library |
| `architecture` | For complex refactoring requiring design docs |
| `testing` | For comprehensive test coverage |
| `debugging` | When refactoring breaks existing functionality |
