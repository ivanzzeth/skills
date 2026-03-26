# Round 2: DEPS — Dependency & Supply Chain Checklist

## Automated Scans

```bash
# Go
govulncheck ./...
go list -json -deps ./... | nancy sleuth
go list -u -m all  # check for outdated deps

# Python
pip-audit
safety check
pip list --outdated

# Rust
cargo audit
cargo outdated

# TypeScript
npm audit
npx snyk test
npm outdated
```

## Manual Review Checklist

### Known Vulnerabilities
- [ ] Language vulnerability scanner reports zero findings
  - Go: `govulncheck`, Python: `pip-audit`, Rust: `cargo audit`, TS: `npm audit`
- [ ] Medium CVEs documented with justification (mitigated, not reachable, etc.)

### Dependency Hygiene
- [ ] Lock file uses specific versions (no `latest`, no floating)
  - Go: `go.mod`+`go.sum`, Python: `poetry.lock`, Rust: `Cargo.lock`, TS: `package-lock.json`
- [ ] Lock file committed and reviewed for unexpected changes
- [ ] No vendored dependencies with local modifications (unless documented)
- [ ] Unused dependencies removed (`go mod tidy` / `pip-autoremove` / `cargo udeps` / `depcheck`)

### Supply Chain
- [ ] Dependencies from well-known, reputable sources
- [ ] No typosquatting packages (check similar names carefully)
- [ ] Private modules/packages configured properly for your registry

### Transitive Dependencies
- [ ] `go list -m all` reviewed for unexpected transitive deps
- [ ] No ancient, unmaintained libraries in the dependency tree
- [ ] Critical path dependencies have multiple maintainers (bus factor > 1)

### Update Strategy
- [ ] Dependency update schedule defined (monthly recommended)
- [ ] Security-critical deps (crypto, auth, TLS) updated within 48h of CVE
- [ ] Major version bumps reviewed for breaking changes before adopting
