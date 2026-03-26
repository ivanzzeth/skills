# Vibe Coding Workflow Example

Complete example demonstrating the 6-step vibe coding workflow.

## User Request

> "Write a Go middleware for API rate limiting"

## Step 1: INTENT → Understand the Vibe

<summary>

**User wants:** A Go HTTP middleware that limits the rate of API requests to prevent abuse and ensure fair usage.

**Tech stack:** Go (standard library or specific framework?)

**Unclear points - need clarification:**
1. Which HTTP framework? (net/http, gin, echo, chi?)
2. Rate limit algorithm? (token bucket, sliding window, fixed window?)
3. Rate limit scope? (per IP, per user, per API key, global?)
4. Limit values? (requests per second/minute?)
5. Storage backend? (in-memory, Redis for distributed?)
6. Response on limit exceeded? (429 status, custom message, retry-after header?)

**Questions for user:**
- What HTTP framework are you using?
- Should this work across multiple instances (distributed)?
- What's your expected rate limit (e.g., 100 req/min per IP)?

</summary>

---

**User responds:** "Using standard net/http, in-memory is fine, 100 requests per minute per IP, return 429 with retry-after header"

---

## Step 2: PLAN FIRST → Architecture Sketch

<plan>

## Technical Approach
- Tech stack: Go 1.21+, standard `net/http`
- Algorithm: Token bucket (smooth rate limiting, allows bursts)
- Storage: In-memory with sync.Map for thread safety
- Scope: Per client IP address

## Module/Function Breakdown

```
ratelimit/
├── limiter.go      # Core rate limiter logic
│   ├── RateLimiter interface
│   ├── TokenBucket struct
│   └── Allow(key string) bool
├── middleware.go   # HTTP middleware wrapper
│   └── Middleware(next http.Handler) http.Handler
├── config.go       # Configuration
│   └── Config struct
└── limiter_test.go # Tests
```

## Key Abstractions
- **RateLimiter interface**: Allow swapping algorithms later
- **TokenBucket**: Core algorithm implementation
- **ClientKeyExtractor**: Function to extract client identifier (IP by default)

## Edge Cases & Risks
| Edge Case | Handling |
|-----------|----------|
| X-Forwarded-For header | Support for proxied requests |
| IPv6 addresses | Normalize IP format |
| Memory growth | Cleanup expired buckets periodically |
| Concurrent requests | sync.Map for thread safety |
| Clock skew | Use monotonic time |

## Dependencies
- External: None (stdlib only)
- Internal: None

</plan>

## Step 3: SPECS → CODE Generation

<code language="go">
// Package ratelimit provides HTTP rate limiting middleware.
package ratelimit

import (
	"net"
	"net/http"
	"strconv"
	"sync"
	"time"
)

// Config holds rate limiter configuration.
type Config struct {
	// RequestsPerMinute is the maximum requests allowed per minute per client.
	RequestsPerMinute int
	// BurstSize is the maximum burst size (defaults to RequestsPerMinute if 0).
	BurstSize int
	// CleanupInterval is how often to clean expired buckets (defaults to 1 minute).
	CleanupInterval time.Duration
}

// Validate checks if the configuration is valid.
func (c *Config) Validate() error {
	if c.RequestsPerMinute <= 0 {
		return &ConfigError{Field: "RequestsPerMinute", Message: "must be positive"}
	}
	return nil
}

// ConfigError represents a configuration validation error.
type ConfigError struct {
	Field   string
	Message string
}

func (e *ConfigError) Error() string {
	return "ratelimit: invalid config: " + e.Field + " " + e.Message
}

// RateLimiter defines the rate limiting interface.
type RateLimiter interface {
	// Allow checks if a request from the given key should be allowed.
	Allow(key string) bool
	// RetryAfter returns seconds until the next request is allowed.
	RetryAfter(key string) int
}

// tokenBucket implements token bucket rate limiting.
type tokenBucket struct {
	tokens     float64
	lastRefill time.Time
}

// Limiter implements RateLimiter using token bucket algorithm.
type Limiter struct {
	mu              sync.Mutex
	buckets         sync.Map // map[string]*tokenBucket
	rate            float64  // tokens per second
	burstSize       float64
	cleanupInterval time.Duration
	stopCleanup     chan struct{}
}

// NewLimiter creates a new rate limiter with the given configuration.
// Returns error if configuration is invalid.
func NewLimiter(cfg Config) (*Limiter, error) {
	if err := cfg.Validate(); err != nil {
		return nil, err
	}

	burstSize := cfg.BurstSize
	if burstSize == 0 {
		burstSize = cfg.RequestsPerMinute
	}

	cleanupInterval := cfg.CleanupInterval
	if cleanupInterval == 0 {
		cleanupInterval = time.Minute
	}

	l := &Limiter{
		rate:            float64(cfg.RequestsPerMinute) / 60.0, // per second
		burstSize:       float64(burstSize),
		cleanupInterval: cleanupInterval,
		stopCleanup:     make(chan struct{}),
	}

	go l.cleanupLoop()

	return l, nil
}

// Allow checks if a request from the given key should be allowed.
func (l *Limiter) Allow(key string) bool {
	if key == "" {
		panic("ratelimit: key must not be empty")
	}

	now := time.Now()

	bucket := l.getOrCreateBucket(key, now)

	l.mu.Lock()
	defer l.mu.Unlock()

	// Refill tokens based on time elapsed
	elapsed := now.Sub(bucket.lastRefill).Seconds()
	bucket.tokens += elapsed * l.rate
	if bucket.tokens > l.burstSize {
		bucket.tokens = l.burstSize
	}
	bucket.lastRefill = now

	// Check if we can consume a token
	if bucket.tokens >= 1 {
		bucket.tokens--
		return true
	}

	return false
}

// RetryAfter returns seconds until the next request is allowed.
func (l *Limiter) RetryAfter(key string) int {
	if key == "" {
		panic("ratelimit: key must not be empty")
	}

	val, ok := l.buckets.Load(key)
	if !ok {
		return 0
	}

	bucket := val.(*tokenBucket)

	l.mu.Lock()
	defer l.mu.Unlock()

	if bucket.tokens >= 1 {
		return 0
	}

	// Calculate time until next token
	tokensNeeded := 1 - bucket.tokens
	secondsUntilToken := tokensNeeded / l.rate

	return int(secondsUntilToken) + 1
}

func (l *Limiter) getOrCreateBucket(key string, now time.Time) *tokenBucket {
	val, ok := l.buckets.Load(key)
	if ok {
		return val.(*tokenBucket)
	}

	bucket := &tokenBucket{
		tokens:     l.burstSize,
		lastRefill: now,
	}

	actual, _ := l.buckets.LoadOrStore(key, bucket)
	return actual.(*tokenBucket)
}

func (l *Limiter) cleanupLoop() {
	ticker := time.NewTicker(l.cleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			l.cleanup()
		case <-l.stopCleanup:
			return
		}
	}
}

func (l *Limiter) cleanup() {
	now := time.Now()
	expireThreshold := 2 * time.Minute // Remove buckets idle for 2+ minutes

	l.buckets.Range(func(key, value any) bool {
		bucket := value.(*tokenBucket)
		l.mu.Lock()
		idle := now.Sub(bucket.lastRefill)
		l.mu.Unlock()

		if idle > expireThreshold {
			l.buckets.Delete(key)
		}
		return true
	})
}

// Close stops the cleanup goroutine.
func (l *Limiter) Close() {
	close(l.stopCleanup)
}

// Middleware creates an HTTP middleware that rate limits requests.
func Middleware(limiter RateLimiter) func(http.Handler) http.Handler {
	if limiter == nil {
		panic("ratelimit: limiter must not be nil")
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			clientIP := extractClientIP(r)

			if !limiter.Allow(clientIP) {
				retryAfter := limiter.RetryAfter(clientIP)
				w.Header().Set("Retry-After", strconv.Itoa(retryAfter))
				w.Header().Set("X-RateLimit-Remaining", "0")
				http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// extractClientIP extracts the client IP from the request.
// Supports X-Forwarded-For and X-Real-IP headers for proxied requests.
func extractClientIP(r *http.Request) string {
	// Check X-Forwarded-For first (may contain multiple IPs)
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// Take the first IP (original client)
		if idx := len(xff); idx > 0 {
			for i, c := range xff {
				if c == ',' {
					return xff[:i]
				}
			}
			return xff
		}
	}

	// Check X-Real-IP
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}

	// Fall back to RemoteAddr
	ip, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return ip
}
</code>

## Step 4: SELF-REVIEW → Improve Before Delivery

<review>

## DRY Check
- [x] No duplicated logic - bucket access centralized in getOrCreateBucket
- [x] IP extraction logic in single function

## Validation Check
- [x] Config.Validate() checks all required fields
- [x] NewLimiter returns error on invalid config
- [x] Empty key causes panic (exposes bug immediately)
- [x] Nil limiter in Middleware causes panic

## Robustness Check
- [x] Thread-safe with sync.Map + mutex
- [x] Handles proxied requests (X-Forwarded-For, X-Real-IP)
- [x] Cleanup goroutine prevents memory leak
- [x] Close() method for graceful shutdown

## Naming & Clarity
- [x] Clear interface: RateLimiter with Allow/RetryAfter
- [x] Descriptive config fields with comments
- [x] Standard Go naming conventions

## Improvements Applied
1. Added ConfigError type for structured errors
2. Added Retry-After header for 429 responses
3. Added X-RateLimit-Remaining header
4. Added Close() for cleanup goroutine lifecycle
5. Added burst size configuration option

</review>

## Step 5: TEST → Verify Correctness

<tests>

## Unit Test Cases

### Test 1: Happy path - requests under limit
```go
func TestLimiter_Allow_UnderLimit(t *testing.T) {
    cfg := Config{RequestsPerMinute: 60} // 1 per second
    limiter, err := NewLimiter(cfg)
    if err != nil {
        t.Fatal(err)
    }
    defer limiter.Close()

    // First request should be allowed
    if !limiter.Allow("192.168.1.1") {
        t.Error("expected first request to be allowed")
    }
}
```
Input: Single request from IP
Expected: Allow() returns true

### Test 2: Edge case - rate limit exceeded
```go
func TestLimiter_Allow_ExceedsLimit(t *testing.T) {
    cfg := Config{RequestsPerMinute: 1, BurstSize: 1}
    limiter, err := NewLimiter(cfg)
    if err != nil {
        t.Fatal(err)
    }
    defer limiter.Close()

    limiter.Allow("192.168.1.1") // consume the only token

    if limiter.Allow("192.168.1.1") {
        t.Error("expected second request to be denied")
    }
}
```
Input: Two rapid requests, limit is 1
Expected: Second request denied

### Test 3: Edge case - different clients isolated
```go
func TestLimiter_Allow_IsolatedClients(t *testing.T) {
    cfg := Config{RequestsPerMinute: 1, BurstSize: 1}
    limiter, err := NewLimiter(cfg)
    if err != nil {
        t.Fatal(err)
    }
    defer limiter.Close()

    limiter.Allow("192.168.1.1") // consume client1's token

    // Different client should have their own bucket
    if !limiter.Allow("192.168.1.2") {
        t.Error("different client should not be affected")
    }
}
```
Input: Requests from two different IPs
Expected: Each has independent limit

### Test 4: Error case - invalid config
```go
func TestNewLimiter_InvalidConfig(t *testing.T) {
    cfg := Config{RequestsPerMinute: 0}
    _, err := NewLimiter(cfg)
    if err == nil {
        t.Error("expected error for invalid config")
    }
}
```
Input: RequestsPerMinute = 0
Expected: Returns ConfigError

### Test 5: Retry-After header calculation
```go
func TestLimiter_RetryAfter(t *testing.T) {
    cfg := Config{RequestsPerMinute: 60, BurstSize: 1}
    limiter, err := NewLimiter(cfg)
    if err != nil {
        t.Fatal(err)
    }
    defer limiter.Close()

    limiter.Allow("192.168.1.1") // consume token

    retryAfter := limiter.RetryAfter("192.168.1.1")
    if retryAfter < 1 {
        t.Errorf("expected retry-after >= 1, got %d", retryAfter)
    }
}
```
Input: Request after limit exceeded
Expected: RetryAfter returns positive seconds

## Integration Test - Middleware

```go
func TestMiddleware_RateLimited(t *testing.T) {
    cfg := Config{RequestsPerMinute: 1, BurstSize: 1}
    limiter, _ := NewLimiter(cfg)
    defer limiter.Close()

    handler := Middleware(limiter)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    }))

    // First request - allowed
    req1 := httptest.NewRequest("GET", "/", nil)
    req1.RemoteAddr = "192.168.1.1:12345"
    rec1 := httptest.NewRecorder()
    handler.ServeHTTP(rec1, req1)
    if rec1.Code != http.StatusOK {
        t.Errorf("first request: expected 200, got %d", rec1.Code)
    }

    // Second request - denied
    req2 := httptest.NewRequest("GET", "/", nil)
    req2.RemoteAddr = "192.168.1.1:12345"
    rec2 := httptest.NewRecorder()
    handler.ServeHTTP(rec2, req2)
    if rec2.Code != http.StatusTooManyRequests {
        t.Errorf("second request: expected 429, got %d", rec2.Code)
    }
    if rec2.Header().Get("Retry-After") == "" {
        t.Error("expected Retry-After header")
    }
}
```

## How to Run
```bash
go test -v ./ratelimit/...
go test -race ./ratelimit/...  # Check for race conditions
go test -cover ./ratelimit/... # Check coverage
```

</tests>

## Step 6: ITERATE → Continuous Improvement

<next>

## Current Status
- [x] Core token bucket rate limiter implemented
- [x] HTTP middleware with proper headers
- [x] Thread-safe with cleanup mechanism
- [x] Self-reviewed and improved
- [x] Test cases provided (5 unit + 1 integration)

## Suggested Enhancements
1. **Distributed support** - Add Redis backend for multi-instance deployments
2. **Custom key extractor** - Allow rate limiting by user ID, API key, etc.
3. **Multiple limits** - Support different limits for different endpoints
4. **Metrics** - Add Prometheus metrics for monitoring
5. **Sliding window** - Alternative algorithm option

## Questions for You
- Is this implementation what you expected?
- Should I add Redis support for distributed deployments?
- Do you need different rate limits for different endpoints?
- Any edge cases I missed?
- Ready to integrate or need changes?

</next>
