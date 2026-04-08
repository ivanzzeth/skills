# Quick Start Guide

This guide walks through setting up an agent-first repository from absolute scratch.

## Step 1: Install the Skill

If not already installed, add all ivanzzeth skills:

```bash
npx skills add ivanzzeth/skills
```

Verify installation:
```bash
ls ~/.claude/skills/openai-harness
# Should show: SKILL.md, scripts/, assets/, references/
```

## Step 2: Initialize Your Project

Navigate to your project directory (or create a new one):

```bash
# For new project
mkdir my-service && cd my-service
git init

# For existing project
cd /path/to/existing/project
```

Run the harness initialization script:

```bash
~/.claude/skills/openai-harness/scripts/init_harness.sh my-service .
```

This creates the complete directory structure:
```
AGENTS.md              # Navigation map (~100 lines)
ARCHITECTURE.md        # System architecture
docs/
  ├── design-docs/
  │   ├── index.md
  │   └── core-beliefs.md
  ├── exec-plans/
  │   ├── active/
  │   ├── completed/
  │   └── tech-debt-tracker.md
  ├── product-specs/
  │   └── index.md
  ├── references/
  │   └── index.md
  ├── generated/
  │   └── README.md
  ├── infrastructure/
  │   └── INVENTORY.md
  ├── benchmarks/
  │   └── index.md
  ├── runbooks/
  │   └── index.md
  └── QUALITY_SCORE.md
scripts/
  └── lint/
      ├── validate_docs.py
      ├── doc_gardening.py
      ├── code_todos.py
      └── project_status.py
```

## Step 3: Customize Core Documentation

Edit the three foundational files:

**AGENTS.md** - Add your project overview (2-3 sentences) and critical constraints:
```markdown
# My Service

Authentication microservice for the XYZ platform.

**Critical constraints**:
- All auth tokens must expire in <24h
- Never store passwords in plaintext
- All endpoints require rate limiting
```

**ARCHITECTURE.md** - Define your business domains and layer rules:
```markdown
## Business Domains
- **auth** - Authentication and authorization
- **user** - User management
- **session** - Session tracking

## Layer Rules
Types → Config → Repo → Service → Runtime → API
```

**docs/design-docs/core-beliefs.md** - Add your golden principles:
```markdown
1. **Explicit Error Handling** - Never use `_ = xxx` to ignore errors
2. **Input Validation** - All user inputs validated at entry points
3. **DRY Principle** - Zero code duplication across domains
```

## Step 4: Install Git Hooks

Install the automated Git hooks for commit validation:

```bash
~/.claude/skills/openai-harness/scripts/install_hooks.sh
```

This installs three hooks:
- **pre-commit** - Checks secrets, file size, critical TODOs, debug code (1-5 seconds)
- **commit-msg** - Validates Conventional Commits format
- **pre-push** - Runs tests, security scan, doc validation (30s-2min)

## Step 5: Make Your First Commit

Test the hooks by making your first commit:

```bash
git add .
git commit -m "chore: initialize agent-first repository structure"
```

You should see output like:
```
✅ No secrets detected
✅ No large files (>5MB)
✅ AGENTS.md size OK (45 lines < 250 limit)
✅ No critical TODOs found
✅ No debug code found
✅ Commit message validated
```

## Step 6: Validate Documentation Structure

Run the documentation validator:

```bash
python scripts/lint/validate_docs.py
```

Expected output:
```
✅ AGENTS.md exists and is properly sized (45 lines)
✅ ARCHITECTURE.md exists
✅ docs/ structure is complete
✅ All required index files present
```

## Step 7: Check Project Status

Get a token-efficient overview of your project:

```bash
python scripts/lint/project_status.py
```

This aggregates:
- Quality scores by domain
- Tech debt tracking
- Security vulnerabilities
- TODO annotations

Saves 97% tokens (7500 → 250) compared to agents reading multiple files.

## Step 8: Add Your First Feature (with Observability)

Create a product spec for your first feature:

```bash
cat > docs/product-specs/user-login.md << 'EOF'
# User Login

## Requirements
- Email + password authentication
- JWT token generation
- Rate limiting (5 attempts/min)

## Success Criteria
- Login completes in <200ms (p95)
- All errors logged with structured fields
- Metrics exposed on /metrics endpoint
EOF
```

Implement with observability best practices:

```bash
# Add Prometheus metrics endpoint
# Add structured logging (JSON format)
# Add health check endpoints (/health/liveness, /health/readiness)

# Validate observability integration
python ~/.claude/skills/openai-harness/assets/custom-linters/validate_observability.py .
```

## Step 9: Track Tech Debt

As you develop, track technical debt in `docs/exec-plans/tech-debt-tracker.md`:

```markdown
## High Priority
- [ ] Add database connection pooling (performance impact)
- [ ] Fix race condition in token refresh (correctness issue)

## Medium Priority
- [ ] Add pagination to user list endpoint (scalability)

## Low Priority
- [ ] Refactor config loading (code quality)
```

## Step 10: Run Continuous Validation

Set up CI/CD integration (choose one):

```bash
# Copy GitHub Actions workflow
cp ~/.claude/skills/openai-harness/assets/ci-examples/github-actions-docs.yml \
   .github/workflows/docs-validation.yml

# Or GitLab CI
cp ~/.claude/skills/openai-harness/assets/ci-examples/gitlab-ci-docs.yml \
   .gitlab-ci.yml

# Or Woodpecker CI
cp ~/.claude/skills/openai-harness/assets/ci-examples/woodpecker-docs.yml \
   .woodpecker.yml
```

You're now running an agent-first repository with:
- ✅ Progressive disclosure documentation
- ✅ Automated Git hooks (secrets, TODOs, commit format)
- ✅ Documentation validation in CI
- ✅ Tech debt tracking
- ✅ Observability integration
- ✅ Token-efficient project status
