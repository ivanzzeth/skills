# Core Capabilities Detailed Guide

This document provides detailed explanations of each capability provided by the openai-harness skill.

## 1. Repository Structure Initialization

Initialize the full agent-first directory structure with properly templated files.

**Purpose**: Set up a complete harness structure from scratch, ensuring all required files and directories are in place with proper templates.

**Script**: `./scripts/init_harness.sh <project-name> <target-dir>`

**What it creates**:
- `AGENTS.md` - Navigation map (~100 lines, not encyclopedia)
- `ARCHITECTURE.md` - System structure and layer rules
- `docs/` hierarchy:
  - `design-docs/` with `index.md` and `core-beliefs.md`
  - `exec-plans/` with `active/`, `completed/`, and `tech-debt-tracker.md`
  - `product-specs/` with `index.md`
  - `references/` with `index.md`
  - `generated/` with `README.md`
  - `infrastructure/` with `INVENTORY.md`
  - `benchmarks/` with `index.md`
  - `runbooks/` with `index.md`
  - `QUALITY_SCORE.md`
- `scripts/lint/` with validation scripts

**When to use**: Starting a new project or doing major documentation refactoring.

**After initialization**:
1. Edit `AGENTS.md` - Add 2-3 sentence project overview and critical constraints
2. Edit `ARCHITECTURE.md` - Define business domains and layer rules
3. Edit `docs/design-docs/core-beliefs.md` - Add design philosophy and golden principles
4. Run validation: `./scripts/lint/validate_docs.py`

## 2. Progressive Disclosure Documentation

Structure documentation in layers for efficient context usage.

**Purpose**: Implement the three-level loading system where AGENTS.md is a navigation map, and detailed content lives in docs/.

**Principle**: AGENTS.md as table of contents, details in docs/

**Three-level loading**:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **AGENTS.md body** - When agent starts working (<100 lines)
3. **Detailed docs** - Loaded as needed by agent (unlimited)

**Where to put information**:

| Type | Location | Example |
|------|----------|---------|
| Project overview | AGENTS.md | "Authentication service for Web3Gate platform" |
| Critical constraints | AGENTS.md | "All auth tokens must expire in <24h" |
| System architecture | ARCHITECTURE.md | Domain boundaries, layer rules |
| Design decision | docs/design-docs/{decision}.md | "Why JWT over sessions" |
| Product requirement | docs/product-specs/{feature}.md | "OAuth2 integration spec" |
| Work plan | docs/exec-plans/active/{date}-{feature}.md | "Multi-factor auth implementation plan" |
| External library docs | docs/references/{library}-llms.txt | "Passport.js condensed docs" |
| Database schema | docs/generated/db-schema.md | Auto-generated from migrations |
| Quality tracking | docs/QUALITY_SCORE.md | Coverage and tech debt by domain |

**Template files available** in `assets/`:
- `AGENTS.md.template` - Navigation map template
- `ARCHITECTURE.md.template` - System architecture template
- `golden-principles.md.template` - Code quality rules template

## 3. Architectural Enforcement

Enforce strict architectural boundaries to prevent drift in agent-generated code.

**Purpose**: Use linters to mechanically enforce layer rules and dependency constraints, preventing architectural violations.

**Layer model** (from ARCHITECTURE.md template):
```
Types → Config → Repo → Service → Runtime → UI
         ↑
     Providers (cross-cutting concerns)
```

**Dependency rules**:
- Lower layers cannot import higher layers
- Each layer has clear responsibilities
- Cross-cutting concerns (logging, metrics) are separate

**Custom linters available**:
- `assets/custom-linters/layer_dependencies_linter.py` - Python layer validator
- `assets/custom-linters/layer_dependencies_linter.go` - Go layer validator
- `assets/custom-linters/layer_dependencies_linter.ts` - TypeScript layer validator
- `assets/custom-linters/golden_principles_linter.py` - Context-aware rules validation

**Usage**:
```bash
# Validate Python project
python assets/custom-linters/layer_dependencies_linter.py .

# Validate Go project
go run assets/custom-linters/layer_dependencies_linter.go .

# Validate TypeScript project
ts-node assets/custom-linters/layer_dependencies_linter.ts .

# Check golden principles compliance
python assets/custom-linters/golden_principles_linter.py . \
  --docs docs/design-docs/core-beliefs.md
```

**Built-in checks**:
- Error swallowing detection (`_ = xxx`)
- Empty catch blocks
- Hardcoded secrets patterns
- Console.log in production code
- Missing metrics instrumentation
- Unstructured logging

## 4. Token-Efficient Project Status

Aggregate project status in single overview, achieving 97% token reduction (7500 → 250 tokens).

**Purpose**: Prevent agents from repeatedly reading 15+ files to understand project status. One script aggregates everything.

**Script**: `./scripts/project_status.py`

**What it aggregates**:
- Quality scores by domain (from `QUALITY_SCORE.md`)
- Tech debt tracking (from `docs/exec-plans/tech-debt-tracker.md`)
- Security vulnerabilities (from security scan files)
- TODO annotations (from code scanner)
- Test coverage statistics
- Recent changes summary

**Output format**:
```
Project Status Overview

Quality Scores:
  auth: A (95% coverage, 0 tech debt)
  user: B (87% coverage, 3 medium priority items)
  session: C (72% coverage, 1 high priority item)

Tech Debt: 12 items (1 high, 6 medium, 5 low)
Security: 0 vulnerabilities
TODOs: 23 annotations (3 high priority)

Recent Changes:
  - Last commit: 2 hours ago
  - Files changed: 15
  - Tests passing: ✓
```

**Token savings**: Instead of reading 8-15 files (7500 tokens), agent reads one summary (250 tokens).

## 5. Documentation Gardening

Automated doc quality checks to detect staleness, incompleteness, and orphaned files.

**Purpose**: Keep documentation fresh and prevent documentation rot through automated detection.

**Scripts**:
- `./scripts/doc_gardening.py` - Find stale/incomplete docs
- `./scripts/validate_docs.py` - Validate documentation structure

**Checks performed**:

**Staleness detection**:
- Files not modified in 90+ days
- References to deprecated features
- Broken internal links
- TODOs in documentation

**Completeness checks**:
- Missing required sections (Purpose, Usage, Examples)
- Stub files with no content
- Empty index files

**Orphan detection**:
- Files not linked from any other document
- Design docs without implementation
- Specs without corresponding code

**Integration patterns**:
```yaml
# .github/workflows/doc-gardening.yml
name: Doc Gardening
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9am
jobs:
  garden:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Doc Gardening
        run: python scripts/doc_gardening.py
      - name: Create Issue if Problems Found
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Documentation issues detected',
              body: 'Doc gardening found issues. Review output.'
            })
```

## 6. Code TODO Scanner

Scan source code for TODO, FIXME, HACK, and other annotations to discover unfinished features and technical debt.

**Purpose**: Automated discovery of unfinished work, bugs, and tech debt directly from code annotations.

**Script**: `./scripts/code_todos.py . [--priority high|medium|low] [--format json]`

**Supported languages**: Python, Go, JavaScript, TypeScript, Rust, Java, C++, C#, Ruby (9 languages)

**Annotation priority levels**:

| Priority | Tags | Meaning | Action |
|----------|------|---------|--------|
| High | BUG, FIXME | Broken code, must fix before release | Block CI/deployment |
| Medium | TODO, XXX | Planned work, should address | Report in sprint planning |
| Low | HACK, NOTE, OPTIMIZE | Warnings/workarounds, consider refactoring | Track for future cleanup |

**Output formats**:
- **Text** (default): Human-readable summary with file:line references
- **JSON**: Machine-readable for CI integration

**Example output**:
```
Code Annotations Summary
Total: 23 annotations

High Priority (BUG, FIXME) - 3 items

  internal/service/auth.go (2 items)
    42: [FIXME] Race condition in token refresh
    67: [BUG] Nil pointer when OAuth provider offline

  pkg/cache/redis.go (1 items)
    105: [FIXME] Memory leak in connection pool

Medium Priority (TODO, XXX) - 15 items
Low Priority (HACK, NOTE) - 5 items

⚠️  3 high-priority items (BUG, FIXME) found
```

**CI Integration**:
```yaml
- name: Check for critical TODOs
  run: |
    python scripts/code_todos.py . --priority high
    # Exits with code 1 if any BUG/FIXME found
```

## 7. Monolith Migration Assistant

Refactor large AGENTS.md files to progressive disclosure structure.

**Purpose**: Automate the migration from monolithic documentation (500+ line AGENTS.md) to progressive disclosure structure.

**Script**: `./scripts/migrate_from_monolith.py <repo-root> [--execute]`

**How it works**:
1. **Analyze** existing AGENTS.md
2. **Identify** sections that should be separate files
3. **Suggest** target locations in docs/ hierarchy
4. **Preview** changes (dry-run mode)
5. **Execute** refactoring with backup

**Dry-run mode** (default):
- Shows what would be moved
- Suggests file locations
- No files modified

**Execute mode** (`--execute` flag):
- Creates backup: `AGENTS.md.backup.YYYYMMDD_HHMMSS`
- Creates target files in docs/
- Moves content to appropriate locations
- Updates AGENTS.md with links

**Example output**:
```
Analyzing AGENTS.md (547 lines)

Sections to migrate:
  1. "Authentication Flow" (67 lines)
     → docs/design-docs/authentication-flow.md

  2. "Database Schema" (89 lines)
     → docs/generated/db-schema.md

  3. "API Endpoints" (123 lines)
     → docs/product-specs/api-specification.md

New AGENTS.md will be: 98 lines

Run with --execute to apply changes
```

## 8. Git Hooks Automation

Language-agnostic Git hooks without npm/husky dependency.

**Purpose**: Install automated quality checks that run locally before commits and pushes, working with any language/framework.

**Script**: `./scripts/install_hooks.sh` (or `--uninstall`)

**Installed hooks**:

**pre-commit** (1-5 seconds):
- Secrets detection (passwords, API keys, private keys, tokens)
- File size check (warns on files >5MB)
- AGENTS.md size validation (soft limit 250 lines)
- Critical TODOs in staged files (BUG, FIXME)
- Debug code detection (console.log, print statements)
- Language-specific linters (if available): golangci-lint, ruff, eslint

**commit-msg**:
- Minimum length check (10 chars)
- No AI tool names (Claude, ChatGPT, Copilot, etc.)
- Conventional Commits format validation (optional warning)
- Subject line length (≤72 chars recommended)
- Formatting checks (no trailing whitespace, no period at end)
- Blank line between subject and body

**pre-push** (30s-2min):
- Run tests (auto-detect: `make test`, `go test`, `npm test`, `cargo test`)
- Block critical TODOs (BUG/FIXME)
- Documentation validation
- AGENTS.md hard limit (250 lines)
- Security scan on all pushed commits
- Commit message quality check on entire push
- Large commits warning (>100 files changed)

**Tech-stack agnostic design**:
- Pure bash, no npm/node required
- Auto-detects language and tools
- Graceful degradation if tools missing
- Works with Go, Python, Rust, Java, C++, etc.

## 9. Observability Integration

Validate Prometheus metrics, structured logging, health checks, and infrastructure documentation.

**Purpose**: Ensure services follow observability best practices for production deployment.

**Linter**: `assets/custom-linters/validate_observability.py <project-root> [--check metrics|logging|health|docs|dashboards|all]`

**Checks performed**:

**Metrics validation**:
- `/metrics` endpoint exposure
- Prometheus client library imports
- Metrics handler registration
- Language-specific patterns (Go: promhttp, Python: prometheus_client, JS: prom-client)

**Logging validation**:
- Structured logging (JSON format)
- No string formatting in logs (anti-pattern: `logger.info(f"...")`)
- Proper structured fields (anti-pattern: `logger.info("user_id: %s", id)`)
- Good patterns: `logger.info("action", extra={"user_id": id})`

**Health checks**:
- `/health` or `/health/liveness` endpoint
- `/health/readiness` endpoint (for Kubernetes)
- Proper probe implementation

**Infrastructure documentation**:
- `docs/infrastructure/INVENTORY.md` exists
- Documents Prometheus, Grafana, Loki endpoints
- Lists shared infrastructure resources

**Grafana dashboards** (NEW):
- Dashboard JSON files in `deploy/grafana/`, `monitoring/dashboards/`, or `.grafana/`
- Valid JSON structure with `panels` array
- UID field present (required for provisioning)
- Panel count validation (warns if dashboard has 0 panels)

**Example output**:
```
Observability Validation

✅ Passed (10)
  ✓ Metrics endpoint /metrics found
  ✓ Prometheus client library detected
  ✓ Structured logging detected (15 files)
  ✓ Health check endpoints found
  ✓ Liveness probe endpoint found
  ✓ Readiness probe endpoint found
  ✓ Infrastructure inventory found
  ✓ Found 1 Grafana dashboard(s)
    ✓ web3-opb-auth-dashboard.json: 12 panels

⚠️  Warnings (2)
  ⚠ Unstructured logging found in 3 locations
    Use structured logging with extra fields

✅ All observability checks passed
```

## 10. CI/CD Integration

Pre-configured workflows for popular CI/CD platforms.

**Purpose**: Quick setup of automated validation in CI/CD pipelines.

**Templates available**: `assets/ci-examples/`
- `github-actions-docs.yml` - GitHub Actions workflow
- `gitlab-ci-docs.yml` - GitLab CI configuration
- `woodpecker-docs.yml` - Woodpecker CI pipeline
- `README.md` - Integration guide and customization

**What they validate**:
- Documentation structure (`validate_docs.py`)
- Documentation freshness (`doc_gardening.py`)
- Critical TODOs (`code_todos.py --priority high`)
- AGENTS.md size limit (250 lines)
- Tests and coverage
- Security scans

**Scheduled runs**:
- Doc gardening: Weekly (Monday 9am)
- Creates GitHub issues on failure
- Auto-notifies team on Slack/email

**Installation**:
```bash
# GitHub Actions
cp assets/ci-examples/github-actions-docs.yml .github/workflows/docs-validation.yml

# GitLab CI
cp assets/ci-examples/gitlab-ci-docs.yml .gitlab-ci.yml

# Woodpecker CI
cp assets/ci-examples/woodpecker-docs.yml .woodpecker.yml
```

**Customization**: See `assets/ci-examples/README.md` for platform-specific configuration, secrets setup, and notification integration.
