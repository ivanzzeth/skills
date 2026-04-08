# CI/CD Integration Examples

These configuration files demonstrate how to integrate OpenAI Harness documentation validation and maintenance into your CI/CD pipeline.

## Available Examples

### 1. GitHub Actions (`github-actions-docs.yml`)

**Setup**:
```bash
mkdir -p .github/workflows
cp assets/ci-examples/github-actions-docs.yml .github/workflows/docs-validation.yml
```

**Features**:
- ✅ Validates documentation structure on every PR
- ✅ Checks AGENTS.md size (warns if >200 lines)
- ✅ Weekly scheduled doc gardening
- ✅ Creates GitHub issues when problems found

**Schedule**: Configure the `cron` section for doc gardening (default: Monday 9:00 UTC)

---

### 2. GitLab CI (`gitlab-ci-docs.yml`)

**Setup**:
```bash
# Add to existing .gitlab-ci.yml or create new file
cat assets/ci-examples/gitlab-ci-docs.yml >> .gitlab-ci.yml
```

**Features**:
- ✅ Validates docs on MR and branch changes
- ✅ Generates artifact reports
- ✅ Optional quality score check
- ✅ Scheduled doc gardening (configure in GitLab UI)

**Configure Schedule**:
1. Go to GitLab project → CI/CD → Schedules
2. Click "New schedule"
3. Description: "Weekly doc gardening"
4. Interval Pattern: `0 9 * * 1` (Monday 9:00 UTC)
5. Target Branch: `main`

---

### 3. Woodpecker CI (`woodpecker-docs.yml`)

**Setup**:
```bash
mkdir -p .woodpecker
cp assets/ci-examples/woodpecker-docs.yml .woodpecker/docs.yml
```

**Features**:
- ✅ Validates docs on push/PR
- ✅ Multi-pipeline setup (validation + scheduled gardening)
- ✅ Project status overview on PRs
- ✅ Cron-based doc gardening

**Configure Cron**:
1. Go to Woodpecker UI → Repository Settings
2. Add cron job named "doc-gardening"
3. Schedule: `0 9 * * 1` (Monday 9:00 UTC)
4. Branch: `main`

---

## Required Scripts

All CI configurations assume these scripts exist in your repository:

```
scripts/
├── lint/
│   ├── validate_docs.py      # Documentation structure validation
│   └── doc_gardening.py       # Find stale/incomplete docs
└── status.py                  # Project status overview (optional)
```

**Install these scripts**:
```bash
# Copy from openai-harness skill
cp /path/to/openai-harness/scripts/validate_docs.py scripts/lint/
cp /path/to/openai-harness/scripts/doc_gardening.py scripts/lint/
cp /path/to/openai-harness/scripts/project_status.py scripts/status.py
chmod +x scripts/lint/*.py scripts/status.py
```

---

## Customization

### Adjust AGENTS.md Size Threshold

Default warning: >200 lines

**Change threshold**:
```yaml
# In any CI config, modify the check:
if [ $AGENTS_LINES -gt 150 ]; then  # Change 200 to 150
```

### Change Doc Gardening Schedule

Default: Every Monday at 9:00 UTC

**Common alternatives**:
- Daily: `0 9 * * *`
- Twice weekly: `0 9 * * 1,4` (Monday, Thursday)
- Monthly: `0 9 1 * *` (1st of month)

### Add Slack/Discord Notifications

**Example for GitHub Actions**:
```yaml
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Documentation validation failed: ${{ github.event.pull_request.html_url }}"
      }
```

---

## Integration with Existing CI

### Merge with Existing Workflows

**If you already have CI pipelines**, merge the documentation jobs:

**GitHub Actions**:
```yaml
# Add to existing .github/workflows/ci.yml
jobs:
  # ... existing jobs ...
  
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python scripts/lint/validate_docs.py
```

**GitLab CI**:
```yaml
# Add to existing .gitlab-ci.yml
validate-docs:
  stage: test  # Use your existing stage
  image: python:3.11-slim
  script:
    - python scripts/lint/validate_docs.py
```

**Woodpecker CI**:
```yaml
# Add to existing .woodpecker.yml
steps:
  # ... existing steps ...
  
  validate-docs:
    image: python:3.11-slim
    commands:
      - python scripts/lint/validate_docs.py
```

---

## Troubleshooting

### "Script not found" errors

**Symptom**: `python: can't open file 'scripts/lint/validate_docs.py'`

**Solution**: Ensure scripts are copied to your repository and committed.

### Permission denied

**Symptom**: `Permission denied: ./scripts/lint/validate_docs.py`

**Solution**: 
```bash
chmod +x scripts/lint/*.py scripts/status.py
git add scripts/
git commit -m "Make scripts executable"
```

### False positives in doc gardening

**Symptom**: Empty sections flagged as issues (e.g., "Critical (3)" is empty)

**Solution**: These are structural headers. Update `doc_gardening.py` to ignore sections that are intentionally empty containers.

---

## Best Practices

1. **Start with validation only** - Add doc gardening after you're comfortable with structure validation
2. **Run locally first** - Test scripts with `make validate-docs` before CI
3. **Fix issues incrementally** - Don't try to fix all doc problems at once
4. **Schedule gardening wisely** - Weekly is usually sufficient, daily can be noisy
5. **Use fail-fast for PRs** - Block merges if validation fails
6. **Use soft-fail for gardening** - Don't block CI if gardening finds minor issues

---

## Example Makefile Targets

Add these to your project's Makefile for local testing:

```makefile
.PHONY: validate-docs doc-gardening

# Validate documentation structure
validate-docs:
	@python scripts/lint/validate_docs.py

# Run doc gardening
doc-gardening:
	@python scripts/lint/doc_gardening.py

# Full doc check
check-docs: validate-docs doc-gardening
	@echo "✅ Documentation checks complete"
```

Then test locally:
```bash
make validate-docs
make doc-gardening
```
