# Common Pitfalls and How to Avoid Them

Based on real mistakes from agent-first projects.

## Documentation Pitfalls

### Pitfall 1: Monolithic AGENTS.md That Never Gets Refactored

**Symptom**: AGENTS.md grows to 500+ lines, team keeps adding to it

**Why it happens**:
- Easy to append to existing file
- Refactoring feels like non-urgent work
- No automatic size checking

**Consequences**:
- Agents waste context on irrelevant info
- Doc rots - sections contradict each other
- New info buried in noise

**Prevention**:
```yaml
# Add to CI (.github/workflows/docs.yml)
- name: Check AGENTS.md size
  run: |
    LINES=$(wc -l < AGENTS.md)
    if [ $LINES -gt 200 ]; then
      echo "::error::AGENTS.md is $LINES lines (max: 200)"
      exit 1
    fi
```

**Fix**:
1. Run `migrate_from_monolith.py AGENTS.md`
2. Move 80% of content to docs/
3. Update AGENTS.md to be navigation map
4. Add CI check to prevent regression

---

### Pitfall 2: Documentation Lives in Google Docs / Slack

**Symptom**: "Check the design doc I shared last week" → link to Google Doc

**Why it happens**:
- Google Docs feels easier for collaboration
- Markdown seems technical
- No enforcement

**Consequences**:
- **Agents can't see it** - literally invisible to agent context
- Version control lost
- Search doesn't work
- Access control issues (doc sharing)

**Prevention**:
```markdown
# In CLAUDE.md or AGENTS.md

## Iron Rule: Repository is Source of Truth

ALL knowledge must be in the repository:
- Design decisions → docs/design-docs/
- Product specs → docs/product-specs/
- Meeting notes → docs/meetings/ (converted from Google Docs)

Agents can't see:
- ❌ Google Docs
- ❌ Slack threads
- ❌ Tribal knowledge

If it's not in git, it doesn't exist for agents.
```

**Fix**:
1. Convert existing Google Docs to Markdown
2. Move to docs/ with proper structure
3. Update links in AGENTS.md
4. Delete or archive Google Docs (with redirect to repo)

---

### Pitfall 3: Stale Documentation No One Notices

**Symptom**: Code changed 6 months ago, docs still describe old behavior

**Why it happens**:
- No automated freshness checks
- Docs not part of code review
- No ownership

**Consequences**:
- Agents follow outdated instructions
- Bugs introduced following "correct" docs
- Trust in documentation erodes

**Prevention**:
```yaml
# Add scheduled doc gardening (.github/workflows/scheduled.yml)
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday

jobs:
  doc-gardening:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/doc_gardening.py
      - name: Create issue if stale docs found
        if: failure()
        run: |
          gh issue create \
            --title "Stale documentation detected" \
            --body "See workflow logs"
```

**Fix**:
1. Add "Last updated: YYYY-MM-DD" to all docs
2. Run `doc_gardening.py` weekly
3. Assign ownership (CODEOWNERS for docs/)
4. Include docs in PR review checklist

---

## Architecture Pitfalls

### Pitfall 4: No Layer Enforcement = Gradual Chaos

**Symptom**: "Service layer imports from UI" — discovered 6 months later

**Why it happens**:
- ARCHITECTURE.md defines rules but nothing enforces them
- Agents (and humans) take shortcuts
- No automated checks

**Consequences**:
- Circular dependencies
- Hard to test (UI imports Service imports UI)
- Impossible to split into microservices later

**Prevention**:
```go
// tests/architecture/layers_test.go
func TestLayerBoundaries(t *testing.T) {
    violations := checkLayerDependencies()
    if len(violations) > 0 {
        t.Fatalf("Found %d layer violations:\n%s", 
            len(violations), violations)
    }
}
```

**Fix**:
1. Use custom linter templates from `assets/custom-linters/`
2. Add to CI as mandatory check
3. Fix existing violations (may need refactoring)
4. Document exceptions explicitly

---

### Pitfall 5: "Golden Principles" That Aren't Enforced

**Symptom**: CLAUDE.md says "Never use `_ = xxx` to ignore errors" but code is full of it

**Why it happens**:
- Rules written in prose
- No automated checking
- Agents/humans miss during review

**Consequences**:
- Principles become aspirational, not actual
- Inconsistent codebase
- Bugs from ignored errors

**Prevention**:
```python
# Add golden_principles_linter.py to CI
- name: Check Golden Principles
  run: python scripts/golden_principles_linter.py .
```

**Fix**:
1. Use `golden_principles_linter.py` template
2. Customize for your language (Go, TypeScript, Python)
3. Add checks for each principle
4. Run in CI (fail on violations)

---

## Agent Workflow Pitfalls

### Pitfall 6: Agents Don't Know What Changed Recently

**Symptom**: Agent reads 6-month-old design doc, implements outdated approach

**Why it happens**:
- No "last updated" timestamps
- No change log
- Agents start from AGENTS.md → might miss recent updates

**Consequences**:
- Implement deprecated patterns
- Redo recently completed work
- Confusion about current state

**Prevention**:
```markdown
# In all docs/design-docs/*.md

---
last_updated: 2026-04-08
status: Active | Deprecated | Superseded by X
---

# Design Doc Title

[Require this frontmatter in all design docs]
```

**Fix**:
1. Add frontmatter to all design docs
2. Update `doc_gardening.py` to check freshness
3. Mark deprecated docs clearly
4. Add "Recent Changes" section to AGENTS.md (last 7 days)

---

### Pitfall 7: No Quick Status Overview → Wasted Context

**Symptom**: Agent reads 5 different files to understand "what's broken right now"

**Why it happens**:
- Information scattered across multiple docs
- No aggregation
- Each file read costs tokens

**Consequences**:
- 7,500 tokens wasted on redundant reads
- Slow agent startup
- Context limit hit faster

**Prevention**:
```bash
# Add make target
make status:
	@python scripts/project_status.py
```

**Fix**:
1. Use `project_status.py` from openai-harness skill
2. Add to Makefile
3. Document in AGENTS.md: "Run `make status` first"
4. CI can run it for each PR (shows status in logs)

---

## Security Pitfalls

### Pitfall 8: Secrets in Documentation Examples

**Symptom**: `config.example.yaml` contains real API key (accidentally committed)

**Why it happens**:
- Copy-paste from real config
- Forgot to redact
- No automated secret scanning

**Consequences**:
- **Real security breach** (keys leaked to git history)
- Revoke and rotate all secrets
- Trust issues

**Prevention**:
```yaml
# Add to CI
- name: Scan for secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
```

**Or use pre-commit hook**:
```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached | grep -E '(API_KEY|SECRET|PASSWORD).*=.*[a-zA-Z0-9]{20,}'; then
  echo "ERROR: Potential secret detected"
  exit 1
fi
```

**Fix**:
1. Add secret scanning to CI
2. Use placeholder values in examples: `API_KEY=your-api-key-here`
3. If leaked: Rotate immediately, don't just delete from git (still in history)

---

### Pitfall 9: Agent Generates Insecure Code, No Review Catches It

**Symptom**: Agent implements SQL query with string concatenation (SQL injection vuln)

**Why it happens**:
- No security linter
- Human review misses it
- Agent follows "works" over "secure"

**Consequences**:
- **Production vulnerabilities**
- Expensive security audits
- Customer trust issues

**Prevention**:
```yaml
# Add security linter to CI
- name: Security scan
  run: |
    # For Go
    go install github.com/securego/gosec/v2/cmd/gosec@latest
    gosec ./...
    
    # For JS/TS
    npm audit
    
    # For Python
    pip install bandit
    bandit -r .
```

**Fix**:
1. Add language-specific security linter
2. Make it mandatory in CI
3. Document secure patterns in docs/SECURITY.md
4. Add security-auditor agent to review critical code

---

## Quality Pitfalls

### Pitfall 10: Test Coverage Gradually Declines

**Symptom**: Started at 90% coverage, now 65%

**Why it happens**:
- New code added without tests
- No coverage gates in CI
- "Will add tests later" (never happens)

**Consequences**:
- Regressions slip through
- Fear of refactoring (might break things)
- Tech debt accumulates

**Prevention**:
```yaml
# Add to CI
- name: Coverage gate
  run: |
    go test -coverprofile=coverage.out ./...
    COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
    if (( $(echo "$COVERAGE < 85" | bc -l) )); then
      echo "Coverage $COVERAGE% is below 85%"
      exit 1
    fi
```

**Fix**:
1. Add coverage gates to CI (fail if <85%)
2. Track per-domain coverage in docs/QUALITY_SCORE.md
3. Critical code (auth) requires 95%+
4. Make test writing part of Definition of Done

---

## Process Pitfalls

### Pitfall 11: "Agent-First" Means "No Human Review"

**Symptom**: Agents merge their own PRs, humans never look

**Why it happens**:
- Misunderstanding "agent-first"
- Automation fatigue
- Trust in agents

**Consequences**:
- Architectural drift (agents don't see big picture)
- Accumulated bad patterns
- Security issues

**Prevention**:
```markdown
# In AGENTS.md

## Human Review Required For:

- Architecture changes (new layers, boundaries)
- Security-critical code (auth, authz, crypto)
- Breaking API changes
- Database schema migrations
- Infrastructure changes (k8s, CI/CD)

Agents can auto-merge:
- Bug fixes (with tests)
- Documentation updates
- Dependency updates (if tests pass)
- Code formatting
```

**Fix**:
1. Define what needs human review
2. Configure GitHub branch protection
3. Use CODEOWNERS for critical paths
4. Agents request review, don't auto-merge critical code

---

### Pitfall 12: No Feedback Loop → Same Mistakes Repeated

**Symptom**: Agent makes same error 3 times, each time human corrects manually

**Why it happens**:
- Feedback not captured in docs
- No learning from mistakes
- Issue tracker doesn't update docs

**Consequences**:
- Waste time on repeated corrections
- Frustration
- Agents don't improve

**Prevention**:
```markdown
# Workflow when fixing agent mistake:

1. Fix the code (PR)
2. **Update docs** to prevent recurrence:
   - If architectural: Update ARCHITECTURE.md
   - If golden principle: Add to docs/design-docs/core-beliefs.md
   - If process: Update AGENTS.md workflow
3. Add linter/test if possible
4. Commit docs + linter in same PR as fix
```

**Fix**:
1. Treat "agent made a mistake" as "docs were unclear"
2. Always update docs when correcting
3. Add tests/linters to enforce
4. Review docs quarterly for accumulation

---

## Checklist: Avoiding Common Pitfalls

**Documentation**:
- [ ] AGENTS.md <200 lines
- [ ] CI checks docs size
- [ ] All docs in repo (not Google Docs)
- [ ] Automated doc gardening weekly
- [ ] Last-updated timestamps on design docs

**Architecture**:
- [ ] Layer dependencies enforced (custom linter)
- [ ] Golden principles have automated checks
- [ ] Architectural tests in CI

**Agent Workflow**:
- [ ] Quick status script (`make status`)
- [ ] Recent changes visible
- [ ] Clear human review requirements

**Security**:
- [ ] Secret scanning in CI
- [ ] Security linter for language
- [ ] Examples use placeholders, not real secrets

**Quality**:
- [ ] Coverage gates (fail if <85%)
- [ ] Per-domain coverage tracked
- [ ] Critical code requires 95%+

**Process**:
- [ ] Human review for architecture/security
- [ ] Feedback loop: fix → update docs
- [ ] Quarterly docs review

Use this checklist monthly to catch drift early.
