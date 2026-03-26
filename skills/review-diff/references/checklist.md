# Code Review Checklist

Detailed checklist for three-perspective code review.

## Senior Developer Checklist

### Logic & Correctness
- [ ] Algorithm logic is correct
- [ ] Edge cases handled (empty input, null, zero, negative, max values)
- [ ] Boundary conditions validated
- [ ] Loop termination conditions correct
- [ ] Off-by-one errors checked
- [ ] Race conditions considered (for concurrent code)
- [ ] Resource cleanup (close files, connections, etc.)

### Error Handling
- [ ] No ignored error returns (e.g., `_ = xxx` in Go, unchecked exceptions)
- [ ] Errors propagated to caller, not just logged
- [ ] Error messages are descriptive and actionable
- [ ] No panic/throw for recoverable errors
- [ ] No fallback to hardcoded values on failure
- [ ] Constructors/factories return explicit errors where applicable

### Nil / Null Safety
- [ ] Nil/null pointer dereference protected
- [ ] Interface/dependency nil checks fail loudly (not silent skip)
- [ ] Optional dependencies explicitly documented

### Code Quality
- [ ] Clear and descriptive naming
- [ ] No magic numbers (use named constants)
- [ ] No dead code or commented-out code
- [ ] No unnecessary TODO without tracking
- [ ] Single responsibility per function
- [ ] Functions not too long (< 50 lines guideline)

### Security
- [ ] No SQL injection vulnerabilities
- [ ] No command injection vulnerabilities
- [ ] No XSS vulnerabilities (for web code)
- [ ] Sensitive data not logged or exposed
- [ ] No hardcoded credentials or secrets
- [ ] Input validation at system boundaries
- [ ] Proper authentication/authorization checks

### Configuration
- [ ] No silent defaults for important settings
- [ ] Configuration errors reported explicitly
- [ ] Sensitive files (.env, config.yaml) not committed
- [ ] .gitignore updated for new sensitive files

## Test Engineer Checklist

### Test Coverage
- [ ] Unit tests exist for new public functions
- [ ] Unit tests exist for modified functions
- [ ] Private functions tested through public interface
- [ ] Mock/stub used for external dependencies

### Edge Cases & Boundaries
- [ ] Empty/null input tested
- [ ] Zero values tested
- [ ] Maximum/minimum values tested
- [ ] Invalid input tested
- [ ] Timeout scenarios tested (if applicable)

### Error Paths
- [ ] Error conditions tested
- [ ] Exception handling tested
- [ ] Failure recovery tested
- [ ] Network failure scenarios (if applicable)

### Test Quality
- [ ] Test names describe expected behavior
- [ ] One assertion concept per test (focused tests)
- [ ] No test interdependencies
- [ ] No hardcoded test data paths
- [ ] Test data is realistic
- [ ] No flaky patterns (sleep, random without seed)
- [ ] Cleanup after test (no test pollution)

### Integration Tests
- [ ] Cross-component interactions tested
- [ ] Database transactions tested (if applicable)
- [ ] API contracts validated
- [ ] End-to-end happy path covered

### Regression Prevention
- [ ] Bug fix includes reproducing test
- [ ] Previously passing tests still pass
- [ ] No test removed without justification

## Architect Checklist

### Design Alignment
- [ ] Follows existing architectural patterns
- [ ] Consistent with codebase conventions
- [ ] Proper layer separation (presentation/business/data)
- [ ] Dependencies flow in correct direction

### Complexity Management
- [ ] No over-engineering
- [ ] No premature abstraction
- [ ] No unnecessary design patterns
- [ ] Complexity justified by requirements
- [ ] YAGNI principle followed

### Performance
- [ ] No obvious performance issues (N+1 queries, etc.)
- [ ] Appropriate data structures used
- [ ] Caching considered where beneficial
- [ ] Batch operations for bulk data
- [ ] Async/concurrent processing where appropriate

### Scalability
- [ ] Stateless design where possible
- [ ] No single point of failure introduced
- [ ] Resource limits considered
- [ ] Horizontal scaling not blocked

### Maintainability
- [ ] Code is readable and self-documenting
- [ ] Proper separation of concerns
- [ ] No circular dependencies
- [ ] Clear module boundaries
- [ ] TODO comments for unfinished work

### Backward Compatibility
- [ ] API changes are backward compatible OR
- [ ] Breaking changes are documented and justified
- [ ] Migration path provided for breaking changes
- [ ] Deprecation warnings added (not immediate removal)

### Security Architecture
- [ ] Principle of least privilege followed
- [ ] Data flow doesn't expose sensitive info
- [ ] Authentication/authorization at correct layer
- [ ] Audit logging for sensitive operations

## Severity Guidelines

### Critical (Must Fix)
- Security vulnerabilities
- Data loss or corruption risk
- Ignored errors that hide failures
- Incorrect business logic
- Missing required tests for critical paths

### Major (Should Fix)
- Missing error handling
- Missing edge case coverage
- Performance issues
- Architectural violations
- Incomplete test coverage

### Minor (Nice to Fix)
- Code style inconsistencies
- Naming improvements
- Documentation gaps
- Minor refactoring opportunities
