# QA Agent Workflow

Systematic quality assurance workflow based on real bugs found in web3-opb-auth (6 issues across 3 verification rounds).

## Philosophy

**QA's job is NOT to confirm everything works. QA's job is to actively hunt for where it DOESN'T work.**

Think like an attacker: "How can I break this?"

## Three-Round Verification Method

### Round 1: Functional Verification

**Goal**: Does the feature work as specified?

**Checklist**:
- [ ] All new endpoints/functions have corresponding tests
- [ ] Happy path works (normal inputs)
- [ ] Error handling exists (what happens on bad input?)
- [ ] Integration points tested (if service calls another service)
- [ ] Documentation exists (API docs, README updates)

**Tools**:
```bash
# Run unit tests
make test

# Run E2E tests (if applicable)
make test-e2e

# Check test coverage
go test -cover ./...
```

**Example issues found** (from web3-opb-auth Round 1):
- ❌ Issue #1: ActiveSessions Gauge only increments, never decrements
  - **How found**: Asked "What happens when session expires?"
  - **Impact**: Stale data, dashboard shows wrong numbers
  - **Fix**: Replace with Counter (TokensIssuedTotal)

### Round 2: Boundary Testing

**Goal**: Does it work at the edges?

Most bugs hide at boundaries:
- Internal vs external calls
- Empty inputs vs large inputs
- First item vs last item
- Single-threaded vs concurrent

**Critical: Test "Internal Call" Boundaries**

When function A calls function B internally, check if instrumentation (metrics, logging) gets double-counted.

**Checklist**:
- [ ] Empty/null inputs handled gracefully
- [ ] Large inputs don't crash (pagination, limits)
- [ ] Concurrent calls don't race (mutex, atomic operations)
- [ ] Internal calls don't duplicate instrumentation
- [ ] Edge case values tested (0, -1, MAX_INT, empty string)

**How to find internal call issues**:
1. Grep for public functions that have metrics/logging
2. Grep for internal calls to those functions
3. Check if caller ALSO has metrics/logging
4. If yes → potential double counting

**Example issues found** (from web3-opb-auth Round 2):

**Issue #2: RefreshToken double-counts metrics**
```go
// ❌ BEFORE
func GenerateToken(userID string) string {
    token := jwt.Sign(...)
    metrics.TokensIssuedTotal.WithLabelValues("jwt").Inc()  // ← Count 1
    return token
}

func RefreshToken(oldToken string) string {
    token := GenerateToken(userID)  // ← Calls above (Count 1)
    metrics.TokensIssuedTotal.WithLabelValues("refresh").Inc()  // ← Count 2
    return token  // TOTAL: 2 counts for 1 refresh token!
}
```

**How found**: Read code flow, noticed nested calls

**Fix**: Create internal method without instrumentation:
```go
// ✅ AFTER
func GenerateToken(userID string) string {
    token := generateTokenInternal(userID)
    metrics.TokensIssuedTotal.WithLabelValues("jwt").Inc()
    return token
}

func generateTokenInternal(userID string) string {
    return jwt.Sign(...)  // No metrics
}

func RefreshToken(oldToken string) string {
    token := generateTokenInternal(userID)  // ← No double count
    metrics.TokensIssuedTotal.WithLabelValues("refresh").Inc()
    return token
}
```

**Issue #3: BindAuth internal verification inflates metrics**
- BindAuth called `VerifyToken()` to validate JWT
- VerifyToken recorded metrics
- BindAuth's verification should NOT count as a "token verification" event

**Fix**: Created `VerifyTokenInternal()` without metrics

**Issue #4: OIDC login flow missing metrics**
- New authentication path added (OIDC via SIWE)
- Forgot to add `metrics.RecordAuthAttempt("siwe_oidc", ...)`
- **How found**: Compared all auth paths, noticed OIDC missing

**Issue #5: 404 requests use actual path (high cardinality)**
```go
// ❌ BEFORE
endpoint := c.Request.URL.Path  // "/api/unknown-endpoint-12345"
metrics.RecordHTTPRequest(method, endpoint, 404, duration)
// Result: Unlimited unique labels → Prometheus OOM
```

**Fix**: Use fixed label for unmatched routes:
```go
// ✅ AFTER
endpoint := c.FullPath()  // Empty for 404
if endpoint == "" {
    endpoint = "unmatched"  // ← All 404s grouped
}
metrics.RecordHTTPRequest(method, endpoint, 404, duration)
```

**Issue #6: Metrics unit tests missing**
- **How found**: Ran `go test ./internal/metrics/` → no test file
- Added 4 tests covering all recording functions

### Round 3: Regression Testing

**Goal**: Did the fix break anything else?

**Checklist**:
- [ ] ALL tests pass (not just new tests)
- [ ] No new linter errors
- [ ] Documentation updated for changed behavior
- [ ] Previous issues still fixed (didn't regress)
- [ ] Performance didn't degrade (if measurable)

**Tools**:
```bash
# Run full test suite
make test-all

# Check for regressions in coverage
go test -cover ./... | tee coverage-new.txt
diff coverage-old.txt coverage-new.txt

# Lint check
make lint
```

## Bug Report Format

When you find an issue, report it clearly so generator can fix without back-and-forth.

### Template

```markdown
## Issue #{N}: {One-line description}

**Severity**: Critical | High | Medium | Low

**Location**: {file}:{line} or {function name}

**Current behavior**:
{What happens now - be specific}

**Expected behavior**:
{What should happen}

**Reproduction**:
1. Step 1
2. Step 2
3. Observe: {incorrect behavior}

**Root cause**:
{Why this happens - code flow explanation}

**Suggested fix**:
{How to fix - code snippet if possible}

**Impact if not fixed**:
{What breaks in production}
```

### Example

```markdown
## Issue #2: RefreshToken double-counts metrics

**Severity**: High

**Location**: internal/service/jwt.go:87 (RefreshToken function)

**Current behavior**:
When user refreshes token, `tokens_issued_total` increments by 2:
- Once in GenerateToken() → labels: token_type="jwt"
- Once in RefreshToken() → labels: token_type="refresh"

**Expected behavior**:
Refresh should only increment once with token_type="refresh"

**Reproduction**:
1. Call POST /api/v1/jwt/refresh with valid token
2. Query Prometheus: `tokens_issued_total{token_type="jwt"}`
3. Observe: counter increased (should NOT increase for refresh)

**Root cause**:
RefreshToken calls public GenerateToken() which has metrics instrumentation.
Then RefreshToken adds its own metrics. Nested instrumentation.

**Suggested fix**:
Create `generateTokenInternal()` without metrics:
```go
func generateTokenInternal(userID string) string { ... }
func GenerateToken(userID string) string {
    token := generateTokenInternal(userID)
    metrics.TokensIssuedTotal.WithLabelValues("jwt").Inc()
    return token
}
func RefreshToken(oldToken string) string {
    token := generateTokenInternal(userID)  // No double count
    metrics.TokensIssuedTotal.WithLabelValues("refresh").Inc()
    return token
}
```

**Impact if not fixed**:
Metrics dashboards show inflated token issuance (2x actual rate).
Capacity planning based on these metrics will be wrong.
```

## Testing Strategies

### Strategy 1: Cross-Boundary Verification

**What**: Check consistency across system boundaries

**Example** (API ↔ Database):
```bash
# API says user created
curl -X POST /api/users -d '{"name":"alice"}'
# → Response: {"id": 123, "name": "alice"}

# Database check - does it actually exist?
psql -c "SELECT * FROM users WHERE id = 123"
# → If empty, bug found!
```

**Example** (Service ↔ Metrics):
```bash
# Call API 10 times
for i in {1..10}; do curl /api/login; done

# Check Prometheus
curl localhost:9090/api/v1/query?query=auth_attempts_total
# → Should be exactly 10, not 20 (double counting)
```

### Strategy 2: State Machine Testing

For features with states (pending → processing → completed), test ALL transitions:

```
Valid transitions:
pending → processing ✓
processing → completed ✓
processing → failed ✓

Invalid transitions (should be prevented):
completed → processing ✗
failed → pending ✗
```

### Strategy 3: Negative Testing

Test what should NOT work:

```bash
# Should reject invalid JWT
curl -H "Authorization: Bearer invalid-token" /api/protected
# → Expect: 401 Unauthorized

# Should reject expired token
curl -H "Authorization: Bearer expired-token" /api/protected
# → Expect: 401 Unauthorized with specific error message

# Should reject missing required fields
curl -X POST /api/users -d '{}'
# → Expect: 400 Bad Request with validation errors
```

## When to Approve vs. Reject

### Approve ✅
- All functional tests pass
- All boundary cases handled
- No regressions
- Code matches specification
- Documentation updated

### Reject (Request Fix) ⚠️
- Critical bug found (crashes, data loss, security issue)
- Boundary case crashes
- Tests fail
- Missing error handling
- Performance regression >50%

### Approve with Notes 📝
- Minor issues that don't affect functionality
- Code style issues (not critical)
- Documentation could be better (but exists)
- Performance regression <20% with known cause

## Common Bug Patterns

### Pattern 1: Forgotten Error Handling
```go
// ❌ Bad
user, _ := userService.GetUser(id)  // Ignores error
return user.Name  // Crashes if user is nil

// ✅ Good
user, err := userService.GetUser(id)
if err != nil {
    return "", fmt.Errorf("get user: %w", err)
}
return user.Name
```

### Pattern 2: Race Conditions
```go
// ❌ Bad - not thread-safe
var counter int
func Increment() { counter++ }

// ✅ Good
var counter int64
func Increment() { atomic.AddInt64(&counter, 1) }
```

### Pattern 3: Resource Leaks
```go
// ❌ Bad - connection leak
func Query() {
    conn := db.Open()
    conn.Query("SELECT ...")
    // No conn.Close()!
}

// ✅ Good
func Query() {
    conn := db.Open()
    defer conn.Close()
    conn.Query("SELECT ...")
}
```

### Pattern 4: Silent Failures
```go
// ❌ Bad - error swallowed
if err := doSomething(); err != nil {
    log.Println("error:", err)  // Logged but execution continues
}

// ✅ Good - error propagated
if err := doSomething(); err != nil {
    return fmt.Errorf("do something: %w", err)
}
```

### Pattern 5: Hardcoded Secrets
```bash
# ❌ Bad
const API_KEY = "sk-1234567890abcdef"

# ✅ Good
apiKey := os.Getenv("API_KEY")
if apiKey == "" {
    return errors.New("API_KEY not set")
}
```

## QA Tools Checklist

Essential tools for effective QA:

- [ ] **Unit test runner** - `go test`, `pytest`, `npm test`
- [ ] **Coverage reporter** - `go test -cover`, `pytest-cov`
- [ ] **Linter** - `golangci-lint`, `ruff`, `eslint`
- [ ] **API testing** - `curl`, `httpie`, Postman
- [ ] **Load testing** - `ab`, `wrk`, `k6`
- [ ] **Database inspection** - `psql`, `mysql`, DB GUI
- [ ] **Log monitoring** - `tail -f logs/`, centralized logging
- [ ] **Metrics inspection** - Prometheus, Grafana

## Summary

**Good QA is proactive, not reactive.**

- Round 1: Does it work?
- Round 2: Where does it break?
- Round 3: Did fixes break anything else?

**Report issues clearly** with reproduction steps and suggested fixes.

**Most bugs hide at boundaries** - internal calls, edge cases, integration points.

**6 bugs in 3 rounds is NORMAL.** Catching them before production is SUCCESS.
