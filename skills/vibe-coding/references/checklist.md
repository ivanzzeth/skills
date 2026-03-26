# Vibe Coding Checklist

Quick reference checklist for AI-assisted coding workflow.

## Pre-Coding Checklist

### Intent Understanding
- [ ] Restated requirement in own words
- [ ] Identified tech stack (or asked)
- [ ] Clarified input/output format
- [ ] Identified edge cases to handle
- [ ] Asked about error handling expectations
- [ ] No assumptions made - all unclear points asked

### Planning
- [ ] Module/function breakdown documented
- [ ] Key abstractions identified
- [ ] Edge cases and risks listed
- [ ] Dependencies noted (external + internal)

## Code Quality Checklist

### DRY (Don't Repeat Yourself)
- [ ] No duplicated logic
- [ ] Repeated patterns extracted to functions
- [ ] Constants used instead of magic numbers
- [ ] Common operations abstracted

### Input Validation
- [ ] All function parameters validated
- [ ] Nil/null checks at entry points
- [ ] Type assertions verified
- [ ] Bounds checking for arrays/slices
- [ ] String format validation where needed

### Error Handling
- [ ] All errors returned (not swallowed)
- [ ] No `_ = xxx` ignoring error returns
- [ ] Errors propagated with context
- [ ] No hardcoded fallback values on failure
- [ ] Constructors (`NewXXX`) return error

### Robustness
- [ ] Thread-safe if concurrent access possible
- [ ] Resource cleanup (close files, connections)
- [ ] Graceful shutdown handling
- [ ] Timeout handling for I/O operations
- [ ] Interface nil → panic (expose bugs)

### Code Clarity
- [ ] Self-documenting names
- [ ] Single responsibility per function
- [ ] Functions < 50 lines
- [ ] No dead code
- [ ] Comments only for non-obvious logic
- [ ] No Chinese characters

## Self-Review Checklist

After generating code, verify:

| Category | Question | Pass? |
|----------|----------|-------|
| DRY | Any duplicated logic? | |
| Validation | All inputs validated? | |
| Errors | All errors propagated? | |
| Guards | Edge cases handled? | |
| Clarity | Names self-explanatory? | |
| Simplicity | Could this be simpler? | |

## Test Coverage Checklist

Must provide tests for:
- [ ] Happy path (normal input)
- [ ] Empty/null/zero input
- [ ] Boundary values (min, max)
- [ ] Invalid input (error cases)
- [ ] Concurrent access (if applicable)

## Iteration Checklist

Before finalizing:
- [ ] Asked if implementation meets expectations
- [ ] Suggested possible enhancements
- [ ] Offered to handle additional edge cases
- [ ] Asked about missing requirements

## Output Structure Checklist

Every response must include:
- [ ] `<summary>` - Requirement restatement
- [ ] `<plan>` - Architecture and modules
- [ ] `<code>` - Production-ready implementation
- [ ] `<review>` - Self-review results
- [ ] `<tests>` - Test cases with input/output
- [ ] `<next>` - Iteration options

## Anti-Pattern Detection

Red flags to watch for:
| Anti-Pattern | Detection |
|--------------|-----------|
| Bare code dump | Missing `<plan>` and `<summary>` tags |
| Assumption made | "I'll assume..." without asking |
| Ignored error | `_ = funcThatReturnsError()` |
| Hardcoded fallback | `value, err := get(); if err != nil { return defaultValue }` |
| Silent failure | Error logged but not returned |
| Over-engineering | More abstraction than needed |
| Missing tests | No `<tests>` section |
| No iteration | Missing `<next>` section |

## Quick Validation Commands

```bash
# Go - check for ignored errors
grep -r "_ =" *.go | grep -v "_ = " # false positive filter

# Go - check for fmt.Print without error handling
grep -rn "fmt.Print" *.go

# Check for TODO without tracking
grep -rn "TODO" *.go

# Check for Chinese characters
grep -rP "[\x{4e00}-\x{9fff}]" *.go
```
