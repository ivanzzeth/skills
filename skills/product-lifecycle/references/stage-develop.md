# Stage 4: DEVELOP — Build & Test

## Goal

Implement the design with production quality, following TDD and project conventions.

## Workflow

### Step 1: Set up the project

If this is a new service:
- Create the repo/submodule under `projects/`
- Set up project module/package (Go module, Cargo.toml, pyproject.toml, package.json)
- Create initial directory structure
- Add Makefile / build scripts

### IRON RULE: Base Service First

When working on multi-service features (e.g. auth integration into evm-gateway):

1. **Base service** (auth, SDK): code → test → build → deploy to minikube → verify end-to-end
2. **ONLY THEN** start dependent service changes (evm-gateway, frontends)

Never do cross-service changes in parallel. If the base service isn't verified stable,
debugging dependent service integration is impossible.

This applies to: auth service, SDK libraries, shared infrastructure.

### Step 2: Implement vertical slices

Work through GitHub Issues in dependency order. For each issue:

1. **Read the issue** — understand the vertical slice scope
2. **Use language-specific skills:**
   - Go: `/golang-pro` for patterns, `/golang-testing` for tests
   - Solidity: `/develop-secure-contracts` for OZ patterns
   - Python/Rust/TypeScript: use appropriate language best-practice skill if installed
3. **Test per `/test-strategy`:**
   - Unit tests: table-driven + property-based (rapid) for business logic
   - Integration tests: testcontainers for real DB/Redis, Toxiproxy for fault injection
4. **Review before commit:** Invoke `/review-diff` to catch issues
5. **Commit:** Follow conventional commit format (project CLAUDE.md rules)

### Step 3: Code quality gates

After each PR / significant change:
- Run full test suite (redirect output to /tmp as per project rules)
- Check test coverage for core components (target: 95%)
- Ensure no `_ = xxx` error swallowing
- Ensure all inputs validated at entry points

### Step 4: Track progress

Optionally update `04-dev-log.md` with:
- Which issues are completed
- Any design changes discovered during implementation
- Blockers and how they were resolved

**Note:** If implementation reveals design flaws, go back to DESIGN stage:
```bash
bash scripts/lifecycle.sh jump <product> design
```

## Gate 4 Checklist

Before advancing to DELIVER, confirm:

- [ ] All GitHub Issues for MVP are closed (PRs merged)
- [ ] Tests pass (unit + integration)
- [ ] Core component coverage ≥ 95%
- [ ] No known critical bugs
- [ ] Code reviewed (via `/review-diff`)
- [ ] README / API docs updated
