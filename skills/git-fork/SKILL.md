---
name: git-fork
description: >
  Fork repository management workflow for maintaining upstream synchronization,
  contributing back to upstream, and developing custom features on forked repos.
  This skill should be used when working with forked repositories, setting up
  upstream tracking, syncing upstream changes, contributing patches to upstream,
  or managing the relationship between a fork and its upstream source.
  Triggers include: "fork", "upstream", "sync upstream", "contribute upstream",
  "contrib", "fork init", "fork setup", "track upstream", "upstream merge",
  "upstream rebase", "submit PR to upstream", "cherry-pick from upstream".
---

# git-fork

Workflow for managing forked repositories — upstream tracking, synchronization, contribution, and custom development.

## Concepts

### Branch Structure

```
upstream/{platform}/{owner}/{repo}                # Mirror of upstream default branch
upstream/{platform}/{owner}/{repo}/{branch-name}  # Mirror of other upstream branches (e.g. release-v1.x)
main                                              # Production code — ONLY accepts merges from develop (and hotfix)
develop                                           # Integration branch — receives upstream sync, features, and contrib
feature/{name}                                    # Our own features (branch from develop, merge back to develop)
contrib/{name}                                    # Contributions to upstream (branch from upstream, PR to upstream)
sync/{date-or-version}                            # Temporary branch for merging upstream updates into develop
```

### Branch Roles

| Branch | Source | Target | Purpose |
|--------|--------|--------|---------|
| `upstream/{platform}/{owner}/{repo}` | upstream remote | origin (push) | Read-only mirror of upstream default branch. All collaborators can see it. |
| `upstream/{platform}/{owner}/{repo}/{branch}` | upstream remote | origin (push) | Read-only mirror of a specific upstream branch (e.g. `release/v1.x`). Created on demand. |
| `main` | develop | — | Production code. ONLY accepts merges from `develop` (and `hotfix/*`). Never merge directly. |
| `develop` | main (initial) | main (release) | Integration branch. Receives upstream sync, features, and contrib. |
| `feature/{name}` | develop | develop | Our own feature development. |
| `contrib/{name}` | upstream branch | upstream (PR) + develop | Code contributed to upstream. Also mergeable to develop when urgently needed. |
| `sync/{date-or-version}` | upstream branch | develop | Temporary branch to merge upstream updates into develop. Delete after merge. |

### Fork Detection

A repository is a fork project when local branches matching `upstream/*` exist:

```bash
git branch --list 'upstream/*'
```

## Workflows

### 1. Initialize a Fork

Set up upstream tracking for a newly forked or cloned repository. Also applies to existing repositories that need to adopt the git-fork workflow retroactively.

#### Pre-check

Before running fork init, detect the current state:

```bash
# Check if upstream/* branches already exist
git branch --list 'upstream/*'

# Check if upstream remote already exists
git remote | grep -q upstream

# Check if there are existing commits on main
git log --oneline -5
```

- If `upstream/*` branches exist → fork is already initialized, skip to other workflows.
- If no `upstream` remote exists but main has commits → **existing repository retrofit**. ASK the user for the upstream repository URL. Do not guess or infer it.
- If the repo is freshly forked/cloned → proceed with normal init.

#### Steps

```bash
# Step 1: Add upstream remote (if not already added)
#   For retrofit: ask the user for the URL first
git remote add upstream https://github.com/{owner}/{repo}.git

# Step 2: Fetch upstream
git fetch upstream

# Step 3: Detect upstream default branch
#   Check which branch the upstream HEAD points to
git remote show upstream | grep 'HEAD branch'
#   Common values: main, master, trunk, develop

# Step 4: Create local upstream mirror branch (pointing to upstream's current HEAD)
git branch upstream/{platform}/{owner}/{repo} upstream/{default-branch}

# Step 5: Push upstream branch to origin so collaborators can see it
git push origin upstream/{platform}/{owner}/{repo}

# Step 6: Create develop branch (if it does not exist)
#   Detect local main branch: check for main, master, trunk in order
#   Branch develop from whichever exists
git checkout main || git checkout master || git checkout trunk
git checkout -b develop
git push origin develop
```

**Retrofit note**: For existing repositories, the upstream mirror branch points to upstream's current HEAD — not the original fork point. Existing commits on main are treated as established customizations. No attempt to split or reorganize history. From this point forward, all new work follows the git-fork workflow.

**Platform values**: `github`, `gitlab`, `bitbucket`, or other hosting platform identifiers.

**Upstream default branch**: Do not assume `main`. Always detect via `git remote show upstream | grep 'HEAD branch'` before creating the mirror branch.

**Naming example**: For a fork of `https://github.com/foundry-rs/foundry`:
- Remote: `upstream` → `https://github.com/foundry-rs/foundry.git`
- Local branch: `upstream/github/foundry-rs/foundry`

### 2. Sync Upstream Updates

Pull latest changes from upstream into the develop branch. Upstream updates always flow through develop, never directly into main.

```bash
# Step 1: Fetch latest from upstream
git fetch upstream

# Step 2: Update local upstream mirror branch
git checkout upstream/{platform}/{owner}/{repo}
git merge upstream/{default-branch} --ff-only
git push origin upstream/{platform}/{owner}/{repo}

# Step 3: Create sync branch from develop
git checkout develop
git checkout -b sync/$(date +%Y%m%d)
# Or use upstream version: sync/v1.2.0

# Step 4: Merge upstream changes
git merge upstream/{platform}/{owner}/{repo}

# Step 5: Resolve conflicts if any, then merge to develop
git checkout develop
git merge sync/$(date +%Y%m%d) --no-ff

# Step 6: Clean up
git branch -d sync/$(date +%Y%m%d)
git push origin develop
```

**Conflict resolution priority**: When upstream changes conflict with our customizations, preserve our customizations unless there is an explicit reason to adopt the upstream version.

### 3. Develop Our Own Features

For features specific to our fork, not intended for upstream.

```bash
# Branch from develop
git checkout develop
git checkout -b feature/{name}

# ... develop ...

# Merge back to develop
git checkout develop
git merge feature/{name} --no-ff
git branch -d feature/{name}
```

Follows standard Git Flow. Feature branches merge into `develop`. To release, see "Release: develop → main" below.

### 3.1. Contrib Code in Develop

Since the standard contrib workflow (Workflow 4) merges contrib into develop for self-testing, contrib code is available in develop immediately — no extra steps needed.

The contrib branch remains open for the upstream PR. When upstream eventually merges it, the next sync (Workflow 2) will bring in the same changes — git handles the deduplication automatically.

**Do NOT delete the contrib branch** until the upstream PR is merged or closed.

### 3.2. Release: develop → main

`main` is production code. It ONLY accepts merges from `develop` (and `hotfix/*` for emergencies).

```bash
# Merge develop into main for release
git checkout main
git merge develop --no-ff
git push origin main

# Tag the release (optional, follows git-flow-branch-creator convention)
git tag v{X.Y.Z}
git push origin v{X.Y.Z}
```

**Never merge directly into main** from feature/*, contrib/*, sync/*, or upstream/* branches. All code flows through develop first.

### 4. Contribute to Upstream

For code intended to be submitted as a PR to the upstream repository.

#### Creating a contribution

```bash
# Step 1: Branch from upstream mirror (NOT from main or develop)
git checkout upstream/{platform}/{owner}/{repo}
git checkout -b contrib/{name}

# Step 2: Develop the contribution
# ... make changes ...

# Step 3: Push contrib branch to origin
git push origin contrib/{name}

# Step 4: Merge contrib into develop for self-testing
git checkout develop
git merge contrib/{name} --no-ff
git push origin develop

# Step 5: Test in develop
#   Run tests, verify functionality, confirm no regressions.
#   If issues are found, fix on contrib/{name} branch and re-merge to develop.

# Step 6: After self-testing passes, create PR to upstream
#   - Base: upstream's main/master
#   - Head: our contrib/{name}
gh pr create --repo {owner}/{repo} --base {default-branch} --head {our-user}:contrib/{name}
```

**Important**: Always branch `contrib/*` from the upstream mirror branch, never from `main` or `develop`. This ensures the PR contains only the intended changes, without our customizations leaking into the upstream PR.

**NEVER submit a PR to upstream before self-testing in develop.** Untested contributions waste upstream maintainers' time and damage our reputation as a contributor.

#### Maintaining open contributions

When `contrib/*` branches exist, they represent open PRs not yet merged by upstream. Before any other work, check their status:

```bash
# Step 1: List all open contrib branches
git branch --list 'contrib/*'

# Step 2: For each contrib branch, check upstream PR status
gh pr list --repo {owner}/{repo} --author {our-user} --state open
gh pr list --repo {owner}/{repo} --author {our-user} --state merged

# Step 3: If PR was merged upstream → clean up
git branch -d contrib/{name}
git push origin --delete contrib/{name}
#   Then follow "Sync Upstream Updates" to pick up the merged contribution.

# Step 4: If PR is still open → check if upstream has moved ahead
git fetch upstream
git log upstream/{default-branch} --oneline -5

# Step 5: If upstream has new commits → rebase contrib branch
git checkout contrib/{name}
git rebase upstream/{default-branch}
#   Resolve conflicts if any, then force push (contrib is our branch, safe to force push)
git push origin contrib/{name} --force-with-lease

# Step 5.1: Re-merge rebased contrib into develop (old merge is now stale)
git checkout develop
git merge contrib/{name} --no-ff
git push origin develop

# Step 6: Update upstream mirror branch as well
git checkout upstream/{platform}/{owner}/{repo}
git merge upstream/{default-branch} --ff-only
git push origin upstream/{platform}/{owner}/{repo}
```

**When to run this check**: Before starting any new work on a fork project, check if open `contrib/*` branches exist. If they do, run the maintenance steps above first. This prevents drift between contrib branches and upstream.

### 5. Cherry-pick from Upstream

To selectively pick specific commits from upstream without a full sync.

```bash
# Fetch latest
git fetch upstream

# Update upstream mirror
git checkout upstream/{platform}/{owner}/{repo}
git merge upstream/{default-branch} --ff-only

# Cherry-pick onto develop (never directly onto main)
git checkout develop
git cherry-pick <commit-hash>
git push origin develop
```

## MANDATORY Execution Order

When working on a fork project, operations MUST follow this strict order. Violating this order contaminates branches and makes upstream PRs impossible.

```
Phase 1: Fork Init
  └─ Add upstream remote, create upstream/* branch, push to origin
       ↓
Phase 2: Upstream Contributions (if any)
  └─ Create contrib/* from upstream branch → merge to develop for self-testing → PR to upstream
     ONLY upstream-compatible changes. NO fork-specific customizations.
       ↓
Phase 3: Fork Customizations
  └─ Create feature/* from develop → develop → main
     Package renames, branding, config changes, our own features — ALL go here.
```

**NEVER start Phase 3 before Phase 1 is complete.**
**NEVER mix Phase 2 and Phase 3 work in the same branch.**

Fork-specific customizations include but are not limited to:
- Package/module renaming (e.g., changing npm package name, Go module path)
- Version bumps unrelated to upstream
- Repository URL changes
- Custom branding, logos, or documentation specific to our fork
- Features not intended for upstream contribution

If any of these changes are made before the upstream branch exists and contrib branches are created, those changes will leak into future contrib branches and pollute upstream PRs.

## Rules

1. **main is protected** — `main` ONLY accepts merges from `develop` (via release) and `hotfix/*` (emergency). Never merge feature/*, contrib/*, sync/*, or upstream/* directly into main.
2. **develop is the integration hub** — All upstream syncs, features, and contrib code flow into develop first.
3. **upstream branches are read-only mirrors** — Never commit directly to `upstream/*` branches. Only update them via `git merge upstream/{remote-branch} --ff-only`.
4. **contrib branches are clean** — Always branch from upstream mirror, never from main/develop. No fork-specific customizations should leak into contrib branches.
5. **sync branches are temporary** — Create for merging upstream updates, delete after merge to develop is complete.
6. **Push upstream branches to origin** — This makes the upstream baseline visible to all collaborators without requiring them to configure the upstream remote.
7. **Multiple upstream branches allowed** — Default branch mirrors as `upstream/{platform}/{owner}/{repo}`. Additional branches (e.g. `release/v1.x`) mirror as `upstream/{platform}/{owner}/{repo}/{branch-name}`. Create additional mirrors only when needed for contrib or sync targeting a specific upstream branch.
8. **Verify upstream branch state** — Before any sync or contrib work, check that the upstream default branch has not been renamed (e.g. `master` → `main`). If renamed, re-point the local mirror branch:
   ```bash
   git remote show upstream | grep 'HEAD branch'
   # If default branch changed (e.g. master → main), re-point the mirror
   git fetch upstream
   git checkout upstream/{platform}/{owner}/{repo}
   git reset --hard upstream/{new-default-branch}
   git push origin upstream/{platform}/{owner}/{repo} --force-with-lease
   ```
9. **Phase order is non-negotiable** — Fork init → contrib → customization. No exceptions. No parallelization across phases.

## Compatibility

This skill is designed to work alongside:
- **git-flow-branch-creator** — Uses matching `feature/` prefix convention. Release and hotfix workflows are handled by git-flow-branch-creator, not this skill.
- **Other git/commit skills** — This skill only manages fork-specific branch workflows. Commit message format, PR templates, and changelog generation are delegated to other skills.
