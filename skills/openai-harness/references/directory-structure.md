# Agent-First Repository Directory Structure

## Standard Layout

```
repository-root/
├── AGENTS.md              # Map/table of contents (~100 lines)
├── ARCHITECTURE.md        # Domain layering and package structure
├── docs/
│   ├── design-docs/
│   │   ├── index.md       # Catalog of all design docs
│   │   ├── core-beliefs.md
│   │   └── {domain}-{feature}.md
│   ├── exec-plans/
│   │   ├── active/
│   │   │   └── {YYYY-MM-DD}-{feature}.md
│   │   ├── completed/
│   │   │   └── {YYYY-MM-DD}-{feature}.md
│   │   └── tech-debt-tracker.md
│   ├── generated/         # Auto-generated docs (schemas, etc.)
│   │   ├── db-schema.md
│   │   └── api-types.md
│   ├── product-specs/
│   │   ├── index.md       # Catalog of all product specs
│   │   └── {feature-name}.md
│   ├── references/        # External dependencies/libraries
│   │   ├── {library-name}-llms.txt
│   │   └── design-system-reference-llms.txt
│   ├── DESIGN.md          # High-level design philosophy
│   ├── FRONTEND.md        # Frontend conventions
│   ├── PLANS.md           # Planning conventions
│   ├── PRODUCT_SENSE.md   # Product principles
│   ├── QUALITY_SCORE.md   # Quality tracking by domain/layer
│   ├── RELIABILITY.md     # SLOs, monitoring, alerts
│   └── SECURITY.md        # Security requirements
├── src/                   # Application code
├── tests/                 # Test code
└── .github/
    └── workflows/         # CI/CD
```

## File Purposes

### AGENTS.md
- **Purpose**: Entry point and navigation map for agents
- **Length**: ~100 lines
- **Contains**:
  - Project overview (2-3 sentences)
  - Pointers to key documentation in docs/
  - Critical constraints (must be short!)
  - How to navigate the repository
- **Does NOT contain**:
  - Detailed instructions (goes in docs/)
  - Full architectural descriptions (goes in ARCHITECTURE.md)
  - Product requirements (goes in docs/product-specs/)

### ARCHITECTURE.md
- **Purpose**: Top-level map of system structure
- **Contains**:
  - Business domain breakdown
  - Package/module layering rules
  - Dependency direction constraints
  - Cross-cutting concern integration points (Providers)
- **Updated**: Whenever domain boundaries or layer rules change

### docs/design-docs/
- **Purpose**: Design decisions and verification status
- **index.md**: Catalog with verification status
- **core-beliefs.md**: Fundamental agent-first operating principles
- **Individual docs**: One per major design decision
- **Format**:
  ```markdown
  # {Feature} Design
  
  ## Context
  {Why this matters}
  
  ## Decision
  {What we decided}
  
  ## Alternatives Considered
  {What we ruled out and why}
  
  ## Consequences
  {Trade-offs, future implications}
  
  ## Verification
  - [ ] Implementation matches design
  - [ ] Tests cover key scenarios
  - [ ] Documentation updated
  ```

### docs/exec-plans/
- **Purpose**: Track complex work from start to finish
- **active/**: Currently in-progress plans
- **completed/**: Historical record of finished work
- **Format**:
  ```markdown
  # {Feature} Execution Plan
  
  ## Goal
  {What we're building and why}
  
  ## Progress
  - [x] Phase 1: {completed step}
  - [ ] Phase 2: {current step}
  - [ ] Phase 3: {future step}
  
  ## Decision Log
  ### {Date}: {Decision}
  {Context, rationale, alternatives}
  
  ## Blockers
  - {Issue} - Status: {blocked/unblocked}
  ```

### docs/generated/
- **Purpose**: Machine-generated documentation kept in sync with code
- **Examples**:
  - Database schemas (from migrations or introspection)
  - API type definitions (from OpenAPI/GraphQL schemas)
  - Dependency graphs
- **Rule**: Never edit manually - regenerate from source of truth

### docs/product-specs/
- **Purpose**: Feature requirements and acceptance criteria
- **index.md**: Catalog with implementation status
- **Format**:
  ```markdown
  # {Feature} Specification
  
  ## User Story
  As a {user type}, I want {goal} so that {benefit}
  
  ## Requirements
  ### Must Have
  - {requirement}
  
  ### Nice to Have
  - {requirement}
  
  ## Acceptance Criteria
  - [ ] {testable criterion}
  
  ## Out of Scope
  - {explicitly excluded}
  ```

### docs/references/
- **Purpose**: External library/framework documentation optimized for LLM context
- **Naming**: `{library-name}-llms.txt` or `{library-name}-reference.md`
- **Content**: Condensed documentation from external sources
- **Examples**:
  - `nixpacks-llms.txt` - Build system reference
  - `uv-llms.txt` - Python package manager
  - `design-system-reference-llms.txt` - UI component library

### docs/QUALITY_SCORE.md
- **Purpose**: Track code quality by domain and architectural layer
- **Format**:
  ```markdown
  # Quality Score
  
  Last updated: {date}
  
  ## By Domain
  | Domain | Test Coverage | Linter Pass | Documentation | Score |
  |--------|--------------|-------------|---------------|-------|
  | Auth   | 95%          | ✅          | ✅            | A     |
  | Billing| 80%          | ✅          | ⚠️            | B     |
  
  ## By Layer
  | Layer    | Compliance | Tech Debt | Score |
  |----------|-----------|-----------|-------|
  | Types    | 100%      | 0 issues  | A+    |
  | Service  | 90%       | 3 issues  | A     |
  
  ## Known Gaps
  - {domain/layer}: {specific issue} - Priority: {high/medium/low}
  ```

## Mechanical Enforcement

### Custom Linters
Location: `.github/linters/` or `scripts/lint/`

Examples:
- `validate_docs_structure.py` - Check docs/ structure matches spec
- `check_cross_links.py` - Verify all internal links work
- `verify_design_implementation.py` - Ensure code matches design docs

### CI Jobs
In `.github/workflows/docs-validation.yml`:
```yaml
- name: Validate Documentation
  run: |
    python scripts/lint/validate_docs_structure.py
    python scripts/lint/check_cross_links.py
    python scripts/lint/verify_freshness.py
```

### Doc Gardening Agent
Recurring cron job (daily/weekly) that:
1. Reads code to understand current behavior
2. Compares against docs/design-docs/, docs/product-specs/
3. Flags discrepancies
4. Opens PRs to fix stale documentation

## Migration from Existing Repository

If starting with existing monolithic AGENTS.md:

1. Create `docs/` structure
2. Move detailed content from AGENTS.md to appropriate docs/ subdirectories
3. Update AGENTS.md to be navigation map with pointers
4. Set up validation CI jobs
5. Run initial doc-gardening pass
6. Iterate based on agent performance

**Rule of thumb**: If information is >3 sentences, it probably belongs in docs/, not AGENTS.md.
