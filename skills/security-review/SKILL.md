---
name: security-review
description: >
  Multi-round security audit for microservices before production deployment.
  Language-agnostic (Go, Python, Rust, TypeScript). Covers OWASP Top 10, input
  validation, auth/authz, secrets management, dependency scanning, container security,
  and K8s hardening. Each round focuses on a different attack surface. Services must
  pass all rounds before going live.
  Triggers: "security review", "security audit", "安全审计", "pre-production security",
  "owasp check", "vulnerability scan", "harden", "security checklist", "pen test prep".
---

# Security Review — Multi-Round Audit for Production Readiness

No service goes to production without passing security review. Each round focuses on
a different attack surface. Critical services require all 4 rounds; internal tools
may skip Round 4.

## Audit Rounds

```
Round 1: CODE        → Static analysis, OWASP Top 10, input validation
Round 2: DEPS        → Dependency vulnerabilities, supply chain
Round 3: INFRA       → Container, K8s, secrets, TLS
Round 4: ADVERSARIAL → Threat modeling, attack simulation
```

## Quick Start

```
/security-review <round> [service-name]    # Run a specific round
/security-review full [service-name]       # Run all 4 rounds
/security-review status [service-name]     # Check which rounds passed
```

When entering a round, read the corresponding `references/round-*.md` for detailed checklists.

## Round 1: CODE — Application Security

**Focus:** Find vulnerabilities in the code itself.

**Actions:**
1. Run language-appropriate security linter (see table below)
2. Manual review of OWASP Top 10 against codebase:

| Language | Security Linter | Command |
|----------|----------------|---------|
| Go | gosec + golangci-lint | `gosec ./...` / `golangci-lint run --enable gosec` |
| Python | bandit + safety | `bandit -r src/` / `safety check` |
| Rust | cargo-audit + clippy | `cargo audit` / `cargo clippy -- -D warnings` |
| TypeScript | eslint-plugin-security + npm audit | `npm audit` / `npx eslint --ext .ts` |

| # | Vulnerability | What to check |
|---|--------------|---------------|
| A01 | Broken Access Control | Auth checks on every endpoint, RBAC enforcement |
| A02 | Cryptographic Failures | TLS everywhere, no hardcoded secrets, proper hashing |
| A03 | Injection | SQL parameterized queries, no string concat, command injection |
| A04 | Insecure Design | Threat model exists, rate limiting, input validation |
| A05 | Security Misconfiguration | No debug mode in prod, minimal error disclosure |
| A06 | Vulnerable Components | (covered in Round 2) |
| A07 | Auth Failures | JWT validation, session management, brute-force protection |
| A08 | Data Integrity | CSRF protection, signed payloads, integrity checks |
| A09 | Logging Failures | Security events logged, no sensitive data in logs |
| A10 | SSRF | URL validation, no user-controlled internal requests |

**Gate:** All security linter findings resolved or explicitly accepted with justification. Every fix has a corresponding test.

See `references/round-code.md` for detailed checklist.

---

## Round 2: DEPS — Dependency & Supply Chain

**Focus:** Ensure no known vulnerabilities in dependencies.

**Actions:**
1. Run language-appropriate vulnerability scanner:
   - Go: `govulncheck ./...`
   - Python: `safety check` / `pip-audit`
   - Rust: `cargo audit`
   - TypeScript: `npm audit` / `npx snyk test`
2. Review lock file for unexpected changes (go.sum, poetry.lock, Cargo.lock, package-lock.json)
3. Check for typosquatting (similar package names)
4. Pin dependency versions (no floating)

**Gate:** Zero known critical/high CVEs. Medium CVEs documented with mitigation plan. CI pipeline includes vulnerability scanning.

See `references/round-deps.md` for detailed checklist.

---

## Round 3: INFRA — Container & K8s Hardening

**Focus:** Secure the deployment environment.

**Actions:**
1. **Dockerfile:**
   - Non-root user (`USER nonroot:nonroot`)
   - Minimal base image (distroless or alpine)
   - No secrets in image layers
   - `COPY --chmod` instead of `RUN chmod`

2. **K8s manifests:**
   - `securityContext.runAsNonRoot: true`
   - `securityContext.readOnlyRootFilesystem: true`
   - `securityContext.allowPrivilegeEscalation: false`
   - Resource limits set (prevent DoS via resource exhaustion)
   - NetworkPolicy restricts ingress/egress
   - Secrets from K8s Secrets or external vault (not env vars in manifests)

3. **TLS:**
   - All external endpoints TLS-terminated
   - cert-manager auto-renewal configured
   - Internal service-to-service: mTLS or trusted network

4. **Secrets management:**
   - No secrets in git (check git history too)
   - No secrets in container env vars visible via `kubectl describe`
   - Secrets rotatable without redeployment

**Gate:** `kubectl auth can-i --list` shows minimal permissions. No privilege escalation paths.

See `references/round-infra.md` for detailed checklist.

---

## Round 4: ADVERSARIAL — Threat Modeling & Attack Simulation

**Focus:** Think like an attacker.

**Actions:**
1. **STRIDE threat model** for each external-facing endpoint:
   - **S**poofing — can someone impersonate a user/service?
   - **T**ampering — can data be modified in transit?
   - **R**epudiation — can actions be denied without audit trail?
   - **I**nformation disclosure — can sensitive data leak?
   - **D**enial of service — can service be overwhelmed?
   - **E**levation of privilege — can a user gain admin access?

2. **Attack simulation** (manual, lightweight):
   - Try accessing endpoints without auth token
   - Try SQL injection on all user inputs
   - Try path traversal on file-serving endpoints
   - Try oversized payloads (1MB+ JSON body)
   - Try concurrent requests to race-condition-prone endpoints
   - Try expired/malformed JWT tokens

3. **Document** findings in `.product-lifecycle/{product}/security-audit.md`

**Gate:** All critical/high findings fixed with tests. Medium findings have mitigation timeline.

See `references/round-adversarial.md` for detailed checklist.

---

## Multi-Round Tracking

After each round, record the result:

```markdown
## Security Audit Status — {service-name}

| Round | Status | Date | Findings |
|-------|--------|------|----------|
| 1. CODE | PASS | 2026-03-26 | 0 critical, 2 minor (accepted) |
| 2. DEPS | PASS | 2026-03-26 | 0 CVEs |
| 3. INFRA | PASS | 2026-03-27 | Fixed: was running as root |
| 4. ADVERSARIAL | PASS | 2026-03-28 | Added rate limiting |
```

## When to Re-Audit

- **Major feature release** — full Round 1-4
- **Dependency update** — Round 2 only
- **Infrastructure change** — Round 3 only
- **New external endpoint** — Round 1 + Round 4
- **Quarterly** — Round 2 (dependency scan) at minimum

## Iron Rule: Every Fix Must Have a Test

**Security fixes without tests WILL regress.** After fixing any finding:

1. Write a test that **reproduces the vulnerability** (the test should fail before the fix)
2. Write a test that **verifies the fix works** (the test should pass after the fix)
3. Run full test suite to confirm no regressions

Examples of security tests per round:

| Round | Fix | Required Test |
|-------|-----|---------------|
| CODE | Added MaxBytesReader | Test: oversized body → 400 rejection |
| CODE | Added input validation | Test: malicious input → error, valid input → success |
| INFRA | Dockerfile non-root | (Verified by container startup, not unit test) |
| ADVERSARIAL | Added per-IP rate limit | Test: same IP over limit → blocked, different IPs → independent |
| ADVERSARIAL | Added CORS allow-list | Test: allowed origin → headers set, unknown origin → no headers |
| ADVERSARIAL | Added admin guard | Test: non-admin → 401, admin → passes |

**Gate amendment:** A round is NOT "PASS" until both the fix AND its tests are merged.

## Key Principles

1. **Defense in depth** — don't rely on a single layer
2. **Least privilege** — services get minimum required permissions
3. **Fail closed** — auth failure = deny, not allow
4. **Log security events** — auth failures, permission denials, input validation failures
5. **No security by obscurity** — assume attackers know your code
6. **No fix without test** — untested fixes are unverified fixes
