# Round 1: CODE — Application Security Checklist

## Automated Scans

Run the appropriate security linter for your language:

```bash
# Go
gosec ./...
golangci-lint run --enable gosec,sqlclosecheck,bodyclose,noctx

# Python
bandit -r src/
safety check

# Rust
cargo audit
cargo clippy -- -D warnings

# TypeScript
npm audit
npx eslint --ext .ts --plugin security src/
```

## Manual Review Checklist

### Input Validation
- [ ] All HTTP request parameters validated (type, length, range, format)
- [ ] JSON body validated against schema (no extra fields accepted)
- [ ] Path parameters sanitized (no path traversal: `../`)
- [ ] Query parameters typed (no raw string passed to DB)
- [ ] File uploads: type checked, size limited, stored outside webroot
- [ ] Content-Type header validated

### SQL / Database
- [ ] All queries use parameterized statements (no string concatenation)
- [ ] No raw SQL from user input
- [ ] Database user has minimal privileges (no DROP, no CREATE)
- [ ] sql.Rows always closed (sqlclosecheck linter)
- [ ] Transactions properly committed/rolled back

### Authentication
- [ ] JWT tokens validated: signature, expiration, issuer, audience
- [ ] No JWT secret in code (from env/vault only)
- [ ] Password hashing uses bcrypt/argon2 (not MD5/SHA)
- [ ] Brute-force protection: rate limiting on login
- [ ] Session tokens regenerated after authentication
- [ ] Logout invalidates token (if stateful sessions)

### Authorization
- [ ] Every endpoint checks permissions (not just authentication)
- [ ] No IDOR: user A cannot access user B's resources by changing ID
- [ ] Admin endpoints have separate authorization check
- [ ] RBAC/ABAC consistently enforced

### Error Handling
- [ ] Internal errors not exposed to clients (no stack traces in responses)
- [ ] Error messages don't reveal system internals
- [ ] Errors logged with context (but no sensitive data in logs)
- [ ] Panic recovery middleware in HTTP handlers

### Secrets
- [ ] No hardcoded credentials, API keys, or tokens in code
- [ ] No secrets in comments or TODOs
- [ ] `.env` files in `.gitignore`
- [ ] Git history clean of secrets (or secrets rotated if leaked)

### HTTP Headers
- [ ] CORS configured restrictively (not `*` in production)
- [ ] Security headers set: X-Content-Type-Options, X-Frame-Options, CSP
- [ ] No sensitive data in URL query parameters (use POST body)
- [ ] Rate limiting on all public endpoints

### Logging
- [ ] Authentication failures logged with IP and timestamp
- [ ] Authorization failures logged
- [ ] No passwords, tokens, or PII in logs
- [ ] Log injection prevented (user input not directly in log format strings)
