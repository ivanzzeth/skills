# Prometheus Metrics Best Practices

Real bugs found and fixed in web3-opb-auth. These patterns apply to any Prometheus integration.

## Metric Type Decision Tree

```
Do you need to track state that goes up AND down?
├─ YES → Use Gauge (connection pool, queue size, temperature)
└─ NO
   ├─ Do you need distribution/percentiles?
   │  ├─ YES → Use Histogram (latency, request size)
   │  └─ NO → Use Counter (requests, errors, events)
   └─ Need to count by categories?
      ├─ YES → Use CounterVec (labels for categorization)
      └─ NO → Use simple Counter
```

## Anti-Pattern 1: Double Counting

### The Bug

When function A calls function B, and BOTH have metrics instrumentation, you count the same event twice.

### Real Example

**BEFORE** (from web3-opb-auth):
```go
// jwt.go
func (s *JWTService) GenerateToken(userID string) (string, error) {
    token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
    signed, err := token.SignedString(s.privateKey)
    
    // ← Metric #1
    metrics.TokensIssuedTotal.WithLabelValues("jwt").Inc()
    return signed, err
}

func (s *JWTService) RefreshToken(oldToken string) (string, error) {
    // Verify old token, extract userID...
    
    // ← Calls GenerateToken() = Metric #1
    newToken, err := s.GenerateToken(userID)
    if err != nil {
        return "", err
    }
    
    // ← Metric #2
    metrics.TokensIssuedTotal.WithLabelValues("refresh").Inc()
    return newToken, nil
}
```

**Result**: One refresh token → 2 metric increments
- `tokens_issued_total{token_type="jwt"}` +1
- `tokens_issued_total{token_type="refresh"}` +1

**Impact**: Dashboard shows 2x actual token issuance rate. Capacity planning based on these metrics is wrong.

### The Fix: Internal Methods

Create uninstrumented internal methods for nested calls:

```go
// jwt.go
// ✅ Internal: No metrics (for reuse)
func (s *JWTService) generateTokenInternal(userID string) (string, error) {
    token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
    return token.SignedString(s.privateKey)
}

// ✅ Public: Records metrics
func (s *JWTService) GenerateToken(userID string) (string, error) {
    token, err := s.generateTokenInternal(userID)
    if err == nil {
        metrics.TokensIssuedTotal.WithLabelValues("jwt").Inc()
    }
    return token, err
}

// ✅ Public: Uses internal method, records own metrics
func (s *JWTService) RefreshToken(oldToken string) (string, error) {
    // Verify old token...
    
    // Use internal method → no double counting
    newToken, err := s.generateTokenInternal(userID)
    if err != nil {
        return "", err
    }
    
    metrics.TokensIssuedTotal.WithLabelValues("refresh").Inc()
    return newToken, nil
}
```

**Result**: One refresh token → 1 metric increment (correct)

### Detection Method

**Step 1**: Find all public functions with metrics:
```bash
grep -rn "metrics\." internal/service/
# Output: jwt.go:45: metrics.TokensIssuedTotal...
```

**Step 2**: Find internal calls to those functions:
```bash
grep -rn "GenerateToken\|VerifyToken" internal/service/
# If you see calls from other functions in same package → check for double counting
```

**Step 3**: Ask: "Does the caller also record metrics?"
- If YES → need internal method
- If NO → OK as-is

### When to Use Internal Methods

| Scenario | Need Internal Method? |
|----------|----------------------|
| Public API endpoint calls service method | ❌ No - different layers |
| Service method calls another service method | ✅ YES - same instrumentation layer |
| Service method calls repository method | ❌ No - different layers |
| Middleware wraps handler | ✅ YES if both record HTTP metrics |

## Anti-Pattern 2: Gauge That Only Goes Up

### The Bug

Using Gauge for something that should be a Counter, or forgetting to decrement.

### Real Example

**BEFORE**:
```go
var ActiveSessions = promauto.NewGauge(
    prometheus.GaugeOpts{
        Name: "web3_opb_auth_active_sessions",
        Help: "Current number of active sessions",
    },
)

// On login
func CreateSession(userID string) {
    // ... create session in database ...
    metrics.ActiveSessions.Inc()  // ← +1
}

// On logout - FORGOT TO DECREMENT
func DeleteSession(sessionID string) {
    // ... delete from database ...
    // ⚠️ Missing: metrics.ActiveSessions.Dec()
}

// Sessions also expire automatically after 24h
// ⚠️ No way to decrement when Redis evicts expired key
```

**Result**: 
- Gauge shows 1000 active sessions
- Actual active sessions (from database): 23
- Stale data → dashboard is useless

### The Fix: Use Counter When You Can't Track State

**Key insight**: If you can't reliably decrement, don't use Gauge. Use Counter + PromQL.

```go
// ✅ Use Counter for events
var TokensIssuedTotal = promauto.NewCounterVec(
    prometheus.CounterOpts{
        Name: "web3_opb_auth_tokens_issued_total",
        Help: "Total tokens issued by type",
    },
    []string{"token_type"}, // siwe, oauth2, refresh
)

// On login/refresh
func CreateSession(userID string, tokenType string) {
    // ... create session ...
    metrics.TokensIssuedTotal.WithLabelValues(tokenType).Inc()
}

// Query for rate in Grafana
// rate(web3_opb_auth_tokens_issued_total[5m])
// → Shows tokens/second (more useful than stale count)
```

**When to use Gauge vs Counter**:

| Use Gauge When | Use Counter When |
|---------------|-----------------|
| You control all increments AND decrements | You only see increments (events) |
| State is short-lived (<1min) | State is long-lived (hours/days) |
| You have cleanup hooks (defer, finally) | Cleanup is async/unreliable |
| Example: connection pool, in-flight requests | Example: total requests, logins, errors |

### Gauge Done Right

If you DO need a Gauge, ensure decrements happen:

```go
var InFlightRequests = promauto.NewGauge(
    prometheus.GaugeOpts{
        Name: "in_flight_requests",
        Help: "Current requests being processed",
    },
)

func HandleRequest(c *gin.Context) {
    metrics.InFlightRequests.Inc()
    defer metrics.InFlightRequests.Dec()  // ← ALWAYS paired with defer
    
    // Process request...
}
```

**Pattern**: Gauge.Inc() + defer Gauge.Dec() = always balanced

### Database Pool Metrics (Gauge Example)

```go
// Correct usage of Gauge for pool metrics
func collectDBMetrics(db *gorm.DB) {
    ticker := time.NewTicker(15 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        sqlDB, _ := db.DB()
        stats := sqlDB.Stats()
        
        // Gauge: reflects current state, periodically updated
        metrics.DBConnectionPoolSize.WithLabelValues("idle").Set(float64(stats.Idle))
        metrics.DBConnectionPoolSize.WithLabelValues("in_use").Set(float64(stats.InUse))
        metrics.DBConnectionPoolSize.WithLabelValues("max_open").Set(float64(stats.MaxOpenConnections))
    }
}
```

**Why this works**: Database driver tracks state for us. We just read and report.

## Anti-Pattern 3: High Cardinality Labels

### The Bug

Using unbounded values as label values → Prometheus OOM (out of memory).

### Real Example

**BEFORE**:
```go
func MetricsMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        c.Next()
        duration := time.Since(start).Seconds()
        
        // ⚠️ BUG: c.Request.URL.Path is UNBOUNDED
        endpoint := c.Request.URL.Path  // "/api/users/12345", "/api/users/67890", ...
        status := c.Writer.Status()
        
        metrics.HTTPRequestsTotal.WithLabelValues(endpoint, strconv.Itoa(status)).Inc()
    }
}
```

**Result**:
- User hits `/api/unknown-endpoint-abc123` → new label
- User hits `/api/unknown-endpoint-xyz789` → new label
- Attacker sends 10,000 random paths → 10,000 unique labels
- Prometheus stores time series for each unique label combination
- Memory explodes, Prometheus crashes

### The Fix: Bounded Labels

**Rule**: Label values must be from a FINITE, SMALL set.

```go
// ✅ Use route pattern, not actual path
func MetricsMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        c.Next()
        duration := time.Since(start).Seconds()
        
        // ✅ c.FullPath() returns route pattern
        endpoint := c.FullPath()  // "/api/users/:id" (same for all users)
        if endpoint == "" {
            endpoint = "unmatched"  // ← All 404s grouped into ONE label
        }
        
        status := c.Writer.Status()
        metrics.HTTPRequestsTotal.WithLabelValues(endpoint, strconv.Itoa(status)).Inc()
    }
}
```

**Result**:
- `/api/users/12345` → label `"/api/users/:id"`
- `/api/users/67890` → label `"/api/users/:id"` (same)
- `/api/unknown-anything` → label `"unmatched"` (all 404s)
- Total unique labels: ~20 (number of routes + "unmatched")

### Cardinality Limits

| Label Type | Max Cardinality | Example |
|-----------|----------------|---------|
| Endpoint | <50 | Route patterns ("/api/users/:id") |
| Status code | <20 | 200, 201, 400, 401, 404, 500... |
| Method | <10 | GET, POST, PUT, DELETE... |
| Auth type | <5 | siwe, oauth2, jwt |
| User ID | ❌ NEVER | Unbounded |
| IP address | ❌ NEVER | Unbounded |
| Session ID | ❌ NEVER | Unbounded |

**Rule of thumb**: If label value comes from user input, probably unbounded → DON'T use it.

### Exception: Pre-Aggregated Metrics

If you MUST track per-user metrics, aggregate them in application code:

```go
// ❌ DON'T: Create time series per user
metrics.UserRequests.WithLabelValues(userID).Inc()

// ✅ DO: Store in database, aggregate periodically
func RecordUserRequest(userID string) {
    // Store in database
    db.Exec("UPDATE user_stats SET request_count = request_count + 1 WHERE user_id = ?", userID)
    
    // Aggregate metric (total across ALL users)
    metrics.TotalRequests.Inc()
}

// Separate job: Export top 10 users to Prometheus
func ExportTopUsers() {
    rows := db.Query("SELECT user_id, request_count FROM user_stats ORDER BY request_count DESC LIMIT 10")
    for rows.Next() {
        // Only 10 time series created
        metrics.TopUserRequests.WithLabelValues(userID).Set(count)
    }
}
```

## Anti-Pattern 4: Recording Metrics for Internal Verification

### The Bug

Recording metrics for operations that are internal checks, not user actions.

### Real Example

**BEFORE**:
```go
// bind.go - binds Ethereum address to existing user
func (s *BindAuthService) BindEthAddress(userID, message, signature string) error {
    // Verify SIWE signature
    result, err := s.siweVerifier.Verify(ctx, &model.SiweMessage{...})
    
    // Verify user owns the JWT
    jwtResult, err := s.jwtService.VerifyToken(jwtToken)  // ← Records metrics!
    
    // ⚠️ This is INTERNAL verification, not a user action
    // Should NOT count as "JWT verification event"
}
```

**VerifyToken**:
```go
func (s *JWTService) VerifyToken(token string) (*VerifyResult, error) {
    // Verify JWT...
    
    metrics.JWTVerifications.Inc()  // ← Counted here
    return result, nil
}
```

**Result**: 
- User action: "Bind Ethereum address"
- Metrics recorded: +1 bind, +1 JWT verification
- Dashboard shows inflated "JWT verifications" (includes internal checks)

### The Fix: Internal Methods Without Metrics

```go
// jwt.go
// ✅ Internal: No metrics
func (s *JWTService) VerifyTokenInternal(token string) (*VerifyResult, error) {
    // Verify JWT logic...
    return result, nil
}

// ✅ Public: Records metrics (for user-facing endpoints)
func (s *JWTService) VerifyToken(token string) (*VerifyResult, error) {
    result, err := s.VerifyTokenInternal(token)
    if err == nil {
        metrics.JWTVerifications.Inc()
    }
    return result, err
}

// bind.go
func (s *BindAuthService) BindEthAddress(...) error {
    // Use internal method → no metrics inflation
    jwtResult, err := s.jwtService.VerifyTokenInternal(jwtToken)
    
    // Only record the actual user action
    metrics.BindAttempts.Inc()
}
```

**Rule**: Metrics should reflect USER actions, not internal implementation details.

## Anti-Pattern 5: Missing Metrics for New Code Paths

### The Bug

Adding new feature but forgetting to instrument it.

### Real Example

**BEFORE**:
```go
// siwe_auth.go - SIWE login records metrics
func (s *SiweAuthService) Login(message, signature string) error {
    result, err := s.siweVerifier.Verify(...)
    if err != nil {
        metrics.RecordAuthAttempt("siwe", "failure")
        return err
    }
    metrics.RecordAuthAttempt("siwe", "success")
    return nil
}

// main.go - NEW: OIDC login via SIWE
authenticateFn := func(message, signature string) (string, error) {
    result, err := siweVerifier.Verify(...)
    if err != nil {
        return "", err  // ⚠️ Missing metrics!
    }
    userID, err := userService.FindOrCreateUserByAddress(result.Address)
    return strconv.FormatUint(userID, 10), err  // ⚠️ Missing metrics!
}
```

**Result**: 
- SIWE login metrics: recorded ✓
- OIDC login metrics: missing ✗
- Dashboard shows only partial picture

### The Fix: Checklist for New Features

When adding new code path:

1. ✅ Does it serve requests? → Add HTTP metrics
2. ✅ Does it authenticate users? → Add auth attempt metrics
3. ✅ Does it issue tokens? → Add token issuance metrics
4. ✅ Does it access database? → Check DB pool metrics exist
5. ✅ Does it call external API? → Add external call metrics

**Fixed**:
```go
authenticateFn := func(message, signature string) (string, error) {
    result, err := siweVerifier.Verify(...)
    if err != nil {
        metrics.RecordAuthAttempt("siwe_oidc", "failure")  // ✅ Added
        return "", err
    }
    userID, err := userService.FindOrCreateUserByAddress(result.Address)
    if err != nil {
        metrics.RecordAuthAttempt("siwe_oidc", "failure")  // ✅ Added
        return "", err
    }
    metrics.RecordAuthAttempt("siwe_oidc", "success")  // ✅ Added
    return strconv.FormatUint(userID, 10), nil
}
```

### Detection Method

**Code review checklist**:
```bash
# Find all auth methods
grep -rn "func.*Login\|func.*Auth" internal/service/

# For each method, check if metrics.RecordAuthAttempt() exists
grep -A 10 "func.*Login" internal/service/siwe_auth.go | grep "metrics.RecordAuthAttempt"

# If missing → bug found
```

## Metrics Naming Conventions

Follow Prometheus best practices:

```
{namespace}_{subsystem}_{name}_{unit}_total

web3_opb_auth_requests_total              ✅ Counter
web3_opb_auth_request_duration_seconds    ✅ Histogram
web3_opb_auth_db_connections              ✅ Gauge
web3_opb_auth_tokens_issued_total         ✅ Counter

total_requests                            ❌ Missing namespace
requestCount                              ❌ CamelCase (use snake_case)
duration                                  ❌ Missing unit
active_sessions_count                     ❌ Don't suffix with "_count" for Gauge
```

## Testing Metrics

Write unit tests for metric recording:

```go
// metrics_test.go
func TestRecordHTTPRequest(t *testing.T) {
    // Reset metrics before test
    HTTPRequestsTotal.Reset()
    
    // Record request
    RecordHTTPRequest("GET", "/api/users", 200, 0.5)
    
    // Verify metric increased
    metric := testutil.ToFloat64(
        HTTPRequestsTotal.WithLabelValues("GET", "/api/users", "200"),
    )
    assert.Equal(t, 1.0, metric)
}

func TestDoubleCountingPrevented(t *testing.T) {
    TokensIssuedTotal.Reset()
    
    // Call RefreshToken (which internally generates token)
    jwtService.RefreshToken(oldToken)
    
    // Should only increment "refresh", not "jwt"
    jwtCount := testutil.ToFloat64(TokensIssuedTotal.WithLabelValues("jwt"))
    refreshCount := testutil.ToFloat64(TokensIssuedTotal.WithLabelValues("refresh"))
    
    assert.Equal(t, 0.0, jwtCount, "Should not count jwt")
    assert.Equal(t, 1.0, refreshCount, "Should count refresh")
}
```

## Summary

| Anti-Pattern | Fix | Detection |
|--------------|-----|-----------|
| Double counting | Internal methods without metrics | Grep for nested calls + metrics |
| Gauge only going up | Use Counter if can't track decrements | Check for Inc() without Dec() |
| High cardinality | Use bounded label values | Check if label from user input |
| Internal verification metrics | Separate internal methods | Check if metrics in validation code |
| Missing metrics | Checklist for new features | Code review + test coverage |

**Golden rule**: Metrics should reflect user behavior, not implementation details.
