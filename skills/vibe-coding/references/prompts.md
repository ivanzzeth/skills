# Vibe Coding Prompt Patterns

Common prompt patterns for different coding scenarios.

## Activation Prompts

### Full Workflow Activation
```
VIBE CODING MODE: PLAN FIRST → SPECS → CODE → SELF-REVIEW → TESTS → ITERATE
```

### Quick Activation
```
Use vibe coding workflow for this request.
```

### Strict Mode
```
STRICT VIBE CODING: No assumptions, ask all unclear points, full validation required.
```

## Scenario-Specific Prompts

### New Feature Implementation
```
Implement [feature description].

Requirements:
- [Requirement 1]
- [Requirement 2]

Constraints:
- Tech stack: [languages/frameworks]
- Must integrate with: [existing systems]

Use vibe coding workflow with full planning phase.
```

### Bug Fix
```
Fix: [bug description]

Current behavior: [what happens now]
Expected behavior: [what should happen]

Provide:
1. Root cause analysis
2. Fix with minimal changes
3. Regression test to prevent recurrence
```

### Refactoring
```
Refactor [component/function] to [goal].

Current issues:
- [Issue 1]
- [Issue 2]

Requirements:
- No behavior changes
- Maintain all existing tests
- Show before/after diff
```

### Code Review Request
```
Review this code using vibe coding quality standards:

[code block]

Check for:
- DRY violations
- Missing validation
- Error handling issues
- Robustness concerns
```

### Test Generation
```
Generate comprehensive tests for:

[code block]

Cover:
- Happy path
- Edge cases (empty, null, boundary)
- Error conditions
- Concurrent access (if applicable)

Use table-driven tests where appropriate.
```

## Iteration Prompts

### Request Changes
```
Modify the previous implementation:
- Change: [what to change]
- Keep: [what to preserve]
- Add: [new requirements]
```

### Add Feature
```
Extend previous code with:
- [New feature 1]
- [New feature 2]

Maintain backward compatibility.
```

### Performance Optimization
```
Optimize for performance:
- Current bottleneck: [description]
- Target: [performance goal]
- Constraints: [memory/CPU limits]

Show before/after benchmarks.
```

### Add Error Handling
```
Improve error handling:
- Add proper error types
- Include error context
- Ensure all errors propagate
- Add recovery where appropriate
```

## Clarification Prompts

### Tech Stack Clarification
```
Before proceeding, clarify:
1. Go version? (1.21+, 1.20, etc.)
2. Framework? (stdlib, gin, echo, chi)
3. Database? (PostgreSQL, MySQL, MongoDB)
4. Deployment? (Docker, Kubernetes, bare metal)
```

### Requirements Clarification
```
Need more details:
1. Input format/schema?
2. Expected output?
3. Error handling preference?
4. Performance requirements?
5. Security considerations?
```

### Edge Case Clarification
```
How should these edge cases be handled?
1. Empty input: [error / default / skip]
2. Invalid format: [error / attempt parse / skip]
3. Timeout: [retry / fail fast / circuit break]
4. Concurrent access: [lock / queue / fail]
```

## Quality Enforcement Prompts

### Strict Validation
```
Enforce strict validation:
- All inputs MUST be validated
- All errors MUST be returned
- NO silent failures
- NO hardcoded fallbacks
```

### DRY Enforcement
```
Check for DRY violations:
- Extract any repeated logic
- Create helper functions for common patterns
- Use constants for magic values
```

### Test Coverage
```
Ensure minimum test coverage:
- All public functions tested
- All error paths tested
- All edge cases covered
- Table-driven tests where 3+ similar cases
```

## Context Preservation Prompts

### Reference Previous
```
Based on the [component] we implemented earlier:
- Extend with [new feature]
- Keep the same patterns
- Maintain consistency with existing naming
```

### Show Changes
```
Show changes as diff:
- BEFORE: [original code reference]
- AFTER: [modified code]
- WHY: [reason for each change]
```

### Track Progress
```
Current implementation status:
- [x] [Completed item 1]
- [x] [Completed item 2]
- [ ] [Pending item 3]

Continue with next pending item.
```

## Output Format Requests

### Minimal Output
```
Provide only:
1. Brief summary
2. Code (no explanation)
3. Key test case
```

### Full Documentation
```
Provide complete documentation:
1. Overview and purpose
2. Installation/setup
3. API reference
4. Usage examples
5. Error handling guide
```

### Diff Format
```
Show changes in diff format:
```diff
- old line
+ new line
```
Include file paths and line numbers.
```

## Emergency/Quick Prompts

### Quick Fix
```
QUICK: Fix [specific issue] in [code reference].
Minimal change, show diff only.
```

### Quick Test
```
QUICK: Add test for [specific scenario].
Single test function, no full suite.
```

### Quick Review
```
QUICK: Is this safe?
[code block]
Yes/No + critical issues only.
```
