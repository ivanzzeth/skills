---
name: review-diff
description: Review uncommitted git changes from three expert perspectives (Senior Developer, Test Engineer, Architect). Use when user wants to review code changes, validate implementation against requirements, check test coverage, or ensure code quality before committing. Triggers include "/review-diff", "review my changes", "check my diff", "review before commit".
---

# Review Diff

Review uncommitted git changes from three expert perspectives to ensure code quality, test coverage, and alignment with requirements.

## Workflow

### Step 1: Gather Context

First, collect the necessary information:

1. **Requirements**: Ask user to describe the requirements OR specify a requirements file path
2. **Scope**: Ask if reviewing all changes or specific files/paths
3. **Additional context**: Any relevant background (e.g., related issues, architectural decisions)

If any information is unclear or insufficient, ask clarifying questions before proceeding.

### Step 2: Get the Diff

Execute the appropriate git command based on scope:

```bash
# All uncommitted changes (staged + unstaged)
git diff HEAD

# Specific file or path
git diff HEAD -- <path>

# Only staged changes
git diff --cached
```

Also run `git status` to understand the full picture of changes.

### Step 3: Three-Perspective Review

Review the diff from each perspective. See [references/checklist.md](references/checklist.md) for detailed checklist items.

#### 3.1 Senior Developer Perspective

Focus on code quality and implementation correctness:
- Logic correctness and edge case handling
- Error handling (no ignored errors, proper propagation)
- Naming clarity and code readability
- No hardcoded fallback values on failure
- Null/nil safety (fail loudly, not silently)
- Security (no injection vulnerabilities, no sensitive data exposure)

#### 3.2 Test Engineer Perspective

Focus on test coverage and quality assurance:
- Unit tests exist for new/modified functions
- Integration tests for cross-component changes
- Edge cases and boundary conditions covered
- Error paths tested
- Test data represents realistic scenarios
- No flaky test patterns

#### 3.3 Architect Perspective

Focus on design and system impact:
- Changes align with existing architecture patterns
- No unnecessary complexity or over-engineering
- Performance implications considered
- Backward compatibility (or explicit breaking change)
- Proper separation of concerns
- Scalability considerations

### Step 4: Generate Report

Output a structured report in this format:

```markdown
# Code Review Report

## Summary
[Brief overview: what was changed, whether it meets requirements]

## Requirements Alignment
- [ ] Requirement 1: [status and notes]
- [ ] Requirement 2: [status and notes]

## Developer Review
### Issues Found
1. [Issue description, file:line, severity: Critical/Major/Minor]

### Suggestions
1. [Suggestion description]

## Test Review
### Coverage Assessment
- New code test coverage: [assessment]
- Edge cases covered: [yes/no, details]

### Issues Found
1. [Missing test, untested scenario]

## Architecture Review
### Design Assessment
[Overall design quality assessment]

### Issues Found
1. [Design concern]

## Questions for Clarification
[List any unclear points that need user input]

## Action Items
- [ ] [Required fix 1]
- [ ] [Required fix 2]
- [ ] [Recommended improvement 1]
```

## Key Principles

1. **Explicit errors**: Every error must be handled or propagated — never ignored
2. **No silent defaults**: Fail explicitly rather than falling back to hardcoded values
3. **TDD**: Tests should be written alongside or before implementation
4. **Input validation**: Validate at system boundaries
5. **Security first**: OWASP Top 10 awareness in every review

> **Tip:** If your project has a CLAUDE.md with additional rules, the review should
> also enforce those project-specific conventions.

## When to Ask Questions

Always ask before proceeding when:
- Requirements are vague or incomplete
- Multiple valid interpretations exist
- Changes seem to contradict stated requirements
- Architectural decisions have significant trade-offs
- Test coverage expectations are unclear
