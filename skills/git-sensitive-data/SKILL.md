---
name: git-sensitive-data
description: >
  Prevents sensitive data from being committed to git repositories. Covers .gitignore
  maintenance, pre-commit sensitive file detection, secret scanning, and bidirectional
  .gitignore verification. This skill should be used proactively before ANY git add or
  git commit operation, and when working with .gitignore files, environment variables,
  credentials, API keys, or secret management.
  Triggers include: "gitignore", ".gitignore", "sensitive file", "secret", "credential",
  "API key", "keystore", ".env", "config.yaml", "private key", ".pem", ".key",
  "ignore file", "check secrets", "scan secrets", "leak prevention".
  Also trigger proactively when about to run: git add, git commit, or modify .gitignore.
---

# git-sensitive-data

Prevent sensitive data from leaking into git repositories through .gitignore management, pre-commit checks, and secret scanning.

## Pre-Commit Check (MANDATORY)

Before every `git add` or `git commit`, verify the following:

### 1. Sensitive files are excluded

Check that none of these file types are staged:

| Category | Patterns | Risk |
|----------|----------|------|
| Environment | `.env`, `.env.*` (except `.env.example`) | API keys, DB passwords, service URLs |
| Config with secrets | `config.yaml`, `config.local.yaml`, `config.production.yaml` | Connection strings, tokens |
| Cryptographic keys | `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.jks` | Private keys, certificates |
| Credentials | `credentials.json`, `service-account.json`, `keystore.json` | Cloud/service credentials |
| Wallet/Blockchain | `keystore/`, `*.keystore`, `mnemonic.txt`, `seed.txt` | Private keys, seed phrases |
| SSH | `id_rsa`, `id_ed25519`, `*.pub` (private keys) | SSH access |
| Token files | `.token`, `.auth`, `token.json` | OAuth/API tokens |

```bash
# Quick check: are any sensitive files staged?
git diff --cached --name-only | grep -iE '\.(env|key|pem|p12|pfx|jks)$|credentials|keystore|secret|token\.json|service-account'
```

### 2. Scan staged content for secrets

Beyond filenames, check the actual content of staged changes for embedded secrets:

```bash
# Check staged diff for common secret patterns
git diff --cached -U0 | grep -iE '(password|secret|api_key|apikey|token|private_key|access_key|secret_key)\s*[:=]'
```

Patterns to flag:
- `password = "..."` or `password: ...`
- `API_KEY`, `SECRET_KEY`, `ACCESS_KEY` assignments
- `Bearer ...` tokens
- Base64-encoded key material (long alphanumeric strings > 40 chars)
- `-----BEGIN (RSA |EC |)PRIVATE KEY-----`

If any matches are found, **STOP and alert the user**. Do not proceed with the commit.

### 3. Binary files check

Never commit compiled binaries. They bloat the repository and cannot be meaningfully diffed.

```bash
# Check for binary files in staging
git diff --cached --numstat | grep '^-' | awk '{print $3}'
```

## .gitignore Template

Every repository should have a `.gitignore` that covers at minimum:

```gitignore
# Environment & Secrets
.env
.env.*
!.env.example
config.yaml
config.local.yaml
config.production.yaml
*.key
*.pem
*.p12
*.pfx
*.jks
credentials.json
service-account.json
keystore/
mnemonic.txt
seed.txt

# Binaries
*.exe
*.dll
*.so
*.dylib
/bin/
/build/
/dist/

# IDE & OS
.idea/
.vscode/
*.swp
.DS_Store
Thumbs.db
```

Adapt to the project's tech stack. For example:
- **Node.js**: add `node_modules/`, `.npm`
- **Go**: add vendor directory if not checked in
- **Rust**: add `target/`
- **Python**: add `__pycache__/`, `*.pyc`, `.venv/`

## .gitignore Verification (Bidirectional)

Check .gitignore in BOTH directions — this catches both leaks and over-ignoring:

### Direction 1: Sensitive files ARE ignored (security)

```bash
# Verify sensitive patterns are ignored
echo ".env" | git check-ignore --stdin
echo "config.yaml" | git check-ignore --stdin
echo "credentials.json" | git check-ignore --stdin

# List all ignored files to spot-check
git ls-files --ignored --exclude-standard
```

### Direction 2: Legitimate code is NOT ignored (completeness)

```bash
# Check if any important files are being ignored
git status --ignored

# Investigate a specific file
git check-ignore -v path/to/file
# Output: .gitignore:15:*.generated.go    path/to/file.generated.go

# Add exception for false positives
# In .gitignore: !path/to/important.generated.go
```

### Common .gitignore mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Overly broad patterns (`*.go`, `src/`) | Excludes source code | Use specific paths |
| Missing negation for examples | `.env.example` ignored by `.env.*` | Add `!.env.example` |
| Ignoring entire directories with needed files | Missing nested config | Use negation patterns |
| Using `*` without path prefix | Ignores everything | Scope to specific directories |
| Adding rules without verification | Silent file exclusion | Always run `git status --ignored` after changes |

## Remediation: Secret Already Committed

If a secret was already committed, removing it from the file is NOT enough — it remains in git history.

```bash
# Step 1: Rotate the secret immediately
#   Change the password/key/token in the actual service

# Step 2: Remove from history (requires git filter-repo)
#   MUST backup the repo first
cp -r /path/to/repo /path/to/backup/repo-backup-$(date +%Y%m%d)
git filter-repo --path path/to/secret-file --invert-paths

# Step 3: Force push (coordinate with team)
git push origin --force --all

# Step 4: Add to .gitignore to prevent recurrence
echo "path/to/secret-file" >> .gitignore
```

**The secret is considered compromised** the moment it was pushed. Always rotate first, then clean history.

## Anti-Patterns

1. **DO NOT** commit `.env`, `config.yaml` with secrets, or any credential files
2. **DO NOT** use overly broad .gitignore patterns that exclude legitimate code
3. **DO NOT** add .gitignore rules without verifying no needed files are excluded
4. **DO NOT** assume removing a file from the working tree removes it from history
5. **DO NOT** store secrets in code comments or variable names as "temporary" placeholders
6. **DO NOT** commit mock secrets that look real (e.g., `sk_live_...`) — use obviously fake values
