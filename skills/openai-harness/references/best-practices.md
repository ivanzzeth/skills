# Best Practices for Agent-First Repositories

Wisdom learned from building and scaling agent-first repositories following OpenAI's harness engineering principles.

## Start Small

**Don't try to migrate everything at once.** 

When refactoring existing documentation or setting up a new project:
- Begin with critical constraints in AGENTS.md
- Add 2-3 most important architectural rules to ARCHITECTURE.md
- Create the docs/ structure but populate it progressively
- Move one section at a time from monolithic docs to progressive disclosure
- Let the structure grow organically as agents need more details

**Why**: Attempting to document everything upfront leads to:
- Documentation that's immediately stale
- Analysis paralysis
- Overwhelming agents with too much context
- Wasted effort on details that may change

**Example progression**:
1. Week 1: AGENTS.md with 3 critical constraints
2. Week 2: Add ARCHITECTURE.md with layer rules
3. Week 3: Move detailed design decisions to docs/design-docs/
4. Week 4: Add product specs as features are developed
5. Ongoing: Docs grow organically based on agent needs

## Be Ruthless with AGENTS.md Length

**If it's >3 sentences, it probably belongs in docs/.** Target ~100 lines.

AGENTS.md is a navigation map, not an encyclopedia:
- Each constraint should be 1-2 sentences max
- Each pointer to docs/ should be a single link
- No implementation details
- No code examples (those go in docs/references/)
- No historical context (that goes in docs/design-docs/)

**Test**: Can an agent skim AGENTS.md in 10 seconds and know:
- What this repository does
- Where to find detailed information
- What the critical constraints are

If the answer is no, AGENTS.md is too long or too vague.

**Bad example** (too detailed):
```markdown
## Authentication

We use JWT tokens for authentication. The token is generated using 
the RS256 algorithm with a 2048-bit key. Tokens expire after 24 hours 
and can be refreshed using the /refresh endpoint. The token payload 
includes user_id, email, and role. We validate tokens on every request 
using a middleware that checks the signature and expiration. If the 
token is expired, we return a 401 error...
```

**Good example** (navigation):
```markdown
## Authentication

JWT tokens expire in <24h (compliance requirement). See [docs/design-docs/authentication.md](./docs/design-docs/authentication.md) for token structure and validation.
```

## Cross-Link Aggressively

**Every concept mention should link to detailed docs. Agents follow links.**

Agents don't "know" where information lives—they navigate by following links:
- First mention of a term: link to its definition
- Architecture concepts: link to ARCHITECTURE.md
- Design decisions: link to docs/design-docs/
- Features: link to docs/product-specs/
- Operations: link to docs/runbooks/

**Think like a Wikipedia editor**: If you mention a concept that has documentation elsewhere, link to it.

**Example**:
```markdown
## API Design

All endpoints follow RESTful conventions. See [docs/design-docs/api-conventions.md](./docs/design-docs/api-conventions.md).

Rate limiting: 100 requests/minute per IP. Implementation details in [docs/design-docs/rate-limiting.md](./docs/design-docs/rate-limiting.md).

Authentication uses JWT tokens. See [docs/design-docs/authentication.md](./docs/design-docs/authentication.md).
```

**Anti-pattern** (no links):
```markdown
## API Design

All endpoints follow RESTful conventions. Rate limiting is 100 requests 
per minute per IP. Authentication uses JWT tokens.
```

The second version forces agents to search the entire repository to find these details.

## Validate Continuously

**Run validation in CI. Catch drift early.**

Documentation rot happens gradually, then suddenly:
- Week 1: One outdated link
- Week 2: Three stale sections
- Week 3: AGENTS.md grows to 300 lines
- Week 4: Agents can't find anything

**Prevent this with automated validation**:
```yaml
# .github/workflows/validate.yml
on: [push, pull_request]
jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate documentation structure
        run: python scripts/lint/validate_docs.py
      - name: Check AGENTS.md size
        run: |
          lines=$(wc -l < AGENTS.md)
          if [ $lines -gt 250 ]; then
            echo "AGENTS.md is $lines lines (limit: 250)"
            exit 1
          fi
      - name: Doc gardening
        run: python scripts/lint/doc_gardening.py

  scheduled-gardening:
    # Run weekly even if no commits
    schedule:
      - cron: '0 9 * * 1'  # Monday 9am
```

**What to validate**:
- AGENTS.md size limit (hard: 250 lines, soft: 100 lines)
- Required files exist (ARCHITECTURE.md, docs/design-docs/core-beliefs.md)
- No broken links
- No stale files (>90 days without update and no recent code references)
- Critical TODOs don't make it to main branch

## Encode Taste, Don't Document It

**If you're repeating the same review comment, make it a linter rule.**

Human review is expensive and inconsistent:
- Different reviewers have different standards
- Review comments get ignored
- Same mistakes happen repeatedly
- Agents don't learn from review comments

**Convert review patterns to linters**:

| Review comment (repeated) | Linter rule |
|---------------------------|-------------|
| "Don't swallow errors with `_ = xxx`" | Lint for `_ = ` pattern, fail CI |
| "Use structured logging, not f-strings" | Lint for `logger.info(f"...")` |
| "Service layer can't import Runtime layer" | Layer dependency linter |
| "All endpoints need rate limiting" | Check for rate limiter middleware |
| "No hardcoded secrets" | Secrets pattern detection |

**Example linter** (from golden_principles_linter.py):
```python
# Extract rule from docs/design-docs/core-beliefs.md:
# "Never use _ = xxx to ignore errors"

# Check all Go files:
if re.search(r'_\s*=\s*\w+\(', line):
    violations.append(
        f"{file_path}:{line_num}: Error swallowing detected"
    )
```

**Benefits**:
- Mechanical enforcement (no human inconsistency)
- Instant feedback (pre-commit hook)
- Self-documenting (linter error messages teach the rules)
- Scales infinitely (doesn't require more reviewers)

## Make It Executable

**Docs that show "how to run X" should just be scripts that run X.**

**Bad documentation**:
```markdown
# How to Deploy

1. Build the Docker image: `docker build -t myapp .`
2. Tag the image: `docker tag myapp registry.example.com/myapp:latest`
3. Push to registry: `docker push registry.example.com/myapp:latest`
4. Update K8s: `kubectl set image deployment/myapp myapp=registry.example.com/myapp:latest`
5. Wait for rollout: `kubectl rollout status deployment/myapp`
```

**Problem**: 
- Steps get stale when process changes
- Easy to miss a step
- Hard to automate
- Copy-paste errors

**Good documentation**:
```markdown
# How to Deploy

Run: `./scripts/deploy.sh production`

See [scripts/deploy.sh](../scripts/deploy.sh) for implementation.
```

```bash
#!/bin/bash
# scripts/deploy.sh
set -e

ENV=$1
IMAGE="registry.example.com/myapp:latest"

echo "Building Docker image..."
docker build -t myapp .

echo "Pushing to registry..."
docker tag myapp $IMAGE
docker push $IMAGE

echo "Deploying to $ENV..."
kubectl --context $ENV set image deployment/myapp myapp=$IMAGE
kubectl --context $ENV rollout status deployment/myapp

echo "✅ Deployed to $ENV"
```

**Benefits**:
- Always up-to-date (script is source of truth)
- Executable (agents can run it)
- Testable (CI can run it)
- No copy-paste errors

**Rule of thumb**: If your documentation has a numbered list of commands, it should be a script.

## Test With Agents

**Best validation is having an agent actually use the structure. Iterate based on what works.**

Your intuition about what agents need is often wrong. Agents:
- Skip entire sections you thought were important
- Get confused by "helpful" context
- Follow links you didn't expect
- Struggle with layouts you thought were clear

**Empirical testing**:
1. Give an agent a real task in your repository
2. Watch what it reads first
3. Note when it gets confused or searches repeatedly
4. Observe what it skips entirely
5. Record token usage

**Iterate based on findings**:
- Agent re-reads the same file 5 times? → Needs better navigation (add to AGENTS.md)
- Agent skips critical constraints? → Move to AGENTS.md (too buried)
- Agent reads 15 files to understand status? → Add project_status.py aggregation
- Agent can't find database schema? → Add to docs/generated/ with clear link
- Agent searches for "authentication" and misses docs? → Fix file naming

**Metrics to track**:
- Tokens used per task (target: <1000 for typical task)
- Number of file reads per task (target: <10)
- Task completion rate without human intervention
- Average time to find information

**Example improvement cycle**:
```
Observation: Agent reads AGENTS.md (200 tokens), then reads 
            ARCHITECTURE.md entirely (1500 tokens), then searches 
            for "layer rules" in 8 files (3000 tokens total)

Problem: Critical layer rules buried in middle of ARCHITECTURE.md

Fix: Add to AGENTS.md:
     "Layer rules: Service → Repo → Types. See ARCHITECTURE.md#layer-rules"
     
Result: Agent goes directly to relevant section (200 + 300 = 500 tokens)
        Token savings: 3700 → 500 (86% reduction)
```

**Testing checklist**:
- [ ] Agent can start a new feature from AGENTS.md alone
- [ ] Agent finds relevant docs within 3 file reads
- [ ] Agent understands critical constraints without asking
- [ ] Agent follows architectural rules without human review
- [ ] Agent's token usage is stable across multiple tasks

**When agents struggle repeatedly in the same area, your documentation structure has a bug.** Fix the structure, don't fix the prompt.

## Summary

These practices compound:
- **Start small** → Prevents documentation debt
- **Ruthless AGENTS.md** → Reduces token waste  
- **Aggressive cross-linking** → Improves discoverability
- **Continuous validation** → Catches drift early
- **Encode taste** → Scales quality without more humans
- **Make executable** → Keeps docs synchronized with reality
- **Test with agents** → Empirical validation of effectiveness

Each practice makes the others more effective. The repository becomes progressively easier for agents to navigate, which increases agent productivity, which justifies more investment in the structure, which further improves agent effectiveness.

This is the compounding loop of harness engineering.
