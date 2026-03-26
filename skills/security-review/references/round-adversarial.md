# Round 4: ADVERSARIAL — Threat Modeling & Attack Simulation

## STRIDE Threat Model

For each external-facing endpoint, evaluate:

| Threat | Question | Mitigation |
|--------|----------|------------|
| **S**poofing | Can someone pretend to be another user/service? | Strong auth (JWT, mTLS), token validation |
| **T**ampering | Can data be modified in transit or at rest? | TLS, signed payloads, HMAC verification |
| **R**epudiation | Can a user deny performing an action? | Audit logging with timestamps and user IDs |
| **I**nformation Disclosure | Can sensitive data leak? | Minimal response data, no stack traces, encrypted storage |
| **D**enial of Service | Can the service be overwhelmed? | Rate limiting, resource limits, request size limits |
| **E**levation of Privilege | Can a user gain unauthorized access? | RBAC, principle of least privilege, input validation |

### Template

```markdown
## Threat Model: [Service Name] — [Endpoint]

### Assets
- User credentials
- Payment data
- API keys

### Trust Boundaries
- Public internet → API Gateway (TLS termination)
- API Gateway → Service (internal network)
- Service → Database (connection pool)

### Threats Identified
1. [STRIDE category] — [Description] — [Severity: C/H/M/L] — [Mitigation]
2. ...
```

## Attack Simulation Checklist

### Authentication Bypass
- [ ] Access protected endpoint without token → expect 401
- [ ] Access with expired token → expect 401
- [ ] Access with malformed token (truncated, wrong algorithm) → expect 401
- [ ] Access with token signed by wrong key → expect 401
- [ ] Access admin endpoint with regular user token → expect 403

### Injection
- [ ] SQL injection in query params: `?id=1; DROP TABLE users--`
- [ ] SQL injection in JSON body: `{"name": "'; DROP TABLE users--"}`
- [ ] Command injection (if any exec calls): `; cat /etc/passwd`
- [ ] Path traversal: `GET /files/../../../etc/passwd`
- [ ] Header injection: `X-Forwarded-For: 127.0.0.1`
- [ ] Log injection: `{"name": "user\n[ERROR] fake log entry"}`

### Resource Exhaustion
- [ ] Send 1MB JSON body → expect 413 or graceful rejection
- [ ] Send 10,000 concurrent requests → expect rate limiting (429)
- [ ] Send request with deeply nested JSON (100+ levels) → expect rejection
- [ ] Upload extremely large file → expect size limit
- [ ] Open many connections without sending data (slowloris) → expect timeout

### IDOR (Insecure Direct Object Reference)
- [ ] User A tries to read User B's resource by changing ID in URL
- [ ] User tries to modify resource belonging to another user
- [ ] User tries to delete resource belonging to another user
- [ ] Enumerate IDs: sequential IDs reveal data? (prefer UUIDs)

### Data Exposure
- [ ] Error responses do not contain stack traces
- [ ] Error responses do not reveal database structure
- [ ] API does not return more fields than needed (no `SELECT *` in responses)
- [ ] Sensitive fields masked in logs (passwords, tokens, PII)
- [ ] `robots.txt` and `sitemap.xml` do not expose internal URLs

### Race Conditions
- [ ] Double-submit: create same resource twice rapidly
- [ ] TOCTOU: check-then-act with concurrent modification
- [ ] Wallet/balance: withdraw twice simultaneously → negative balance?

## Reporting Template

```markdown
## Security Finding: [Title]

**Severity:** Critical / High / Medium / Low
**Round:** 4 — Adversarial
**Endpoint:** POST /api/v1/transfer
**Date:** 2026-03-26
**Status:** Open / Fixed / Accepted

### Description
[What was found and how to reproduce]

### Impact
[What could an attacker do with this vulnerability]

### Reproduction Steps
1. ...
2. ...
3. ...

### Recommended Fix
[Specific code/config change needed]

### Timeline
- Found: 2026-03-26
- Fix target: 2026-03-28
- Verified: [date]
```
