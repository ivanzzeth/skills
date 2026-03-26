---
name: test-strategy
description: >
  Language-agnostic layered testing strategy for microservices. Defines test pyramid
  (unit → integration → E2E → smoke), tooling per layer per language, and quality gates.
  Covers property-based testing, mutation testing, testcontainers, fault injection,
  post-deploy smoke tests on K8s, and synthetic monitoring.
  Supports: Go, Python, Rust, TypeScript/Node.js.
  Triggers: "test strategy", "testing pyramid", "test plan", "test coverage",
  "integration test", "e2e test", "smoke test", "mutation test", "分层测试",
  "测试策略", "how to test", "improve test coverage", "reduce production bugs".
---

# Test Strategy — Layered Testing for Microservices

Define, implement, and enforce a layered testing strategy that catches bugs at the
cheapest layer possible. Language-agnostic — adapt tooling to the project's stack.

## The Testing Pyramid

```
                    ╱╲
                   ╱  ╲          10% — E2E / Smoke
                  ╱────╲         Slow, fragile, but catches deployment bugs
                 ╱      ╲
                ╱────────╲       40% — Integration
               ╱          ╲     Real DB/Redis/HTTP, testcontainers, fault injection
              ╱────────────╲
             ╱              ╲    50% — Unit
            ╱────────────────╲   Fast, isolated, table-driven, property-based
           ╱                  ╲
          ╱  Static Analysis   ╲ Pre-commit: linters, type checkers, formatters
         ╱────────────────────╲
```

**Recommended ratio for microservices: 50/40/10**

Why not the classic 70/20/10? Spotify's Testing Honeycomb shows that for microservices,
integration tests have the highest ROI — services are small, so unit-testing trivial
handlers is waste. Focus integration tests on real DB/Redis/queue interactions.

## Quick Start

When user asks for a test strategy:

1. **Detect language** of the project (Go, Python, Rust, TypeScript, etc.)
2. **Read** `references/layers.md` for detailed per-layer guidance
3. **Assess** current coverage using the language's coverage tool
4. **Identify gaps** using the layer checklist below
5. **Implement** tests layer by layer, starting from the bottom

## Tooling by Language

| Layer | Go | Python | Rust | TypeScript |
|-------|-----|--------|------|------------|
| **Static** | golangci-lint, go vet | ruff, mypy, pyright | clippy, cargo check | eslint, tsc --noEmit |
| **Unit** | go test + testify | pytest | cargo test | jest / vitest |
| **Property** | pgregory.net/rapid | hypothesis | proptest | fast-check |
| **Integration** | testcontainers-go | testcontainers-python | testcontainers-rs | testcontainers-node |
| **Fault injection** | Toxiproxy | Toxiproxy | Toxiproxy | Toxiproxy |
| **Mutation** | gremlins | mutmut | cargo-mutants | stryker |
| **E2E** | K8s Job + curl | K8s Job + httpx | K8s Job + reqwest | playwright / K8s Job |
| **Coverage** | go tool cover | coverage.py / pytest-cov | cargo-tarpaulin | c8 / istanbul |

## Layer Checklist

### Layer 0: Static Analysis (pre-commit)

- [ ] Language linter configured and running in pre-commit hook
- [ ] Type checker passes (if applicable: mypy, tsc, clippy)
- [ ] Formatter enforced (gofmt, black, rustfmt, prettier)
- [ ] No suppressed/ignored errors without justification

### Layer 1: Unit Tests

- [ ] Table-driven / parametrized tests for business logic
- [ ] Edge cases: nil/None/null, zero, empty, max values, negative
- [ ] Error paths tested (every error branch exercised)
- [ ] Property-based tests for serialization, parsing, invariants
- [ ] Core packages: ≥ 95% line coverage

### Layer 2: Integration Tests

- [ ] Real database via testcontainers (not mocks)
- [ ] Real Redis/cache via testcontainers (not mocks)
- [ ] HTTP client/server integration with real handlers
- [ ] Fault injection via Toxiproxy (timeout, connection drop, latency)
- [ ] Transaction rollback / constraint violation scenarios

### Layer 3: E2E / Smoke / Acceptance Tests

**Automated:**
- [ ] Post-deploy K8s Job hits health + critical API endpoints
- [ ] Readiness probe checks real dependencies (DB ping, Redis ping)
- [ ] CronJob synthetic monitoring every 5 minutes
- [ ] Rollback trigger if smoke test fails

**WebUI acceptance (via Playwright MCP or `/webapp-testing`):**
- [ ] Critical user flows verified in browser (login, core actions, error states)
- [ ] Cross-browser check (Chrome, Firefox minimum)
- [ ] Mobile responsive check
- [ ] Screenshots captured for visual regression

**TUI acceptance (via `interactive-terminal` MCP):**
- [ ] CLI commands execute correctly with expected output
- [ ] Interactive prompts respond properly
- [ ] Error messages are clear and actionable
- [ ] Help text and usage examples work

### Layer 4: Mutation Testing (weekly CI)

- [ ] Mutation tool runs on critical business logic
- [ ] Mutation score ≥ 80% for payment/auth/core modules
- [ ] Survived mutants reviewed and tests added

## When to Use Each Layer

| Scenario | Layer |
|----------|-------|
| New business logic function | Unit (table-driven / parametrized) |
| New DB query / repository method | Integration (testcontainers) |
| Serialization / encoding / parsing | Unit (property-based) |
| Error handling under failure | Integration (Toxiproxy) |
| New API endpoint | Integration (real HTTP) |
| New deployment | Smoke (K8s Job) |
| Quarterly confidence check | Mutation |

## Cost of Bugs by Stage (IBM data)

| Found at | Cost multiplier |
|----------|----------------|
| Design | 1x |
| Development | 6x |
| Testing | 16x |
| **Production** | **100x** |

Shift left. Catch it as early as possible.

## Key Principles

1. **Never mock what you own** — use testcontainers for real DB/Redis
2. **Test behavior, not implementation** — test public interfaces, not internals
3. **One assertion concept per test** — focused, descriptive test names
4. **Flaky = broken** — flaky tests erode trust, fix or delete immediately
5. **Coverage is necessary but not sufficient** — mutation testing reveals weak tests

See `references/layers.md` for detailed implementation guides with code examples per language.
