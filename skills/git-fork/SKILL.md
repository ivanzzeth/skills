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
upstream/{platform}/{owner}/{repo}   # Upstream read-only mirror (local branch, pushed to origin)
main                                 # Production code (with our customizations)
develop                              # Integration branch
feature/{name}                       # Our own features (branch from develop, merge back to develop)
contrib/{name}                       # Contributions to upstream (branch from upstream, PR to upstream)
sync/{date-or-version}               # Temporary branch for merging upstream updates into main
```

### Branch Roles

| Branch | Source | Target | Purpose |
|--------|--------|--------|---------|
| `upstream/{platform}/{owner}/{repo}` | upstream remote | origin (push) | Read-only mirror of upstream main/master. All collaborators can see it. |
| `main` | — | — | Our production code, including customizations on top of upstream. |
| `develop` | main | main | Integration branch for our own features. |
| `feature/{name}` | develop | develop | Our own feature development. |
| `contrib/{name}` | upstream branch | upstream (PR) | Code intended to be contributed back to upstream via PR. |
| `sync/{date-or-version}` | upstream branch | main | Temporary branch to merge upstream updates. Delete after merge. |

### Fork Detection

A repository is a fork project when local branches matching `upstream/*` exist:

```bash
git branch --list 'upstream/*'
```

## Workflows

### 1. Initialize a Fork

Set up upstream tracking for a newly forked or cloned repository.

```bash
# Step 1: Add upstream remote (if not already added)
git remote add upstream https://github.com/{owner}/{repo}.git

# Step 2: Fetch upstream
git fetch upstream

# Step 3: Create local upstream mirror branch
#   Determine upstream default branch (usually main or master)
git branch upstream/{platform}/{owner}/{repo} upstream/main

# Step 4: Push upstream branch to origin so collaborators can see it
git push origin upstream/{platform}/{owner}/{repo}
```

**Platform values**: `github`, `gitlab`, `bitbucket`, or other hosting platform identifiers.

**Naming example**: For a fork of `https://github.com/foundry-rs/foundry`:
- Remote: `upstream` → `https://github.com/foundry-rs/foundry.git`
- Local branch: `upstream/github/foundry-rs/foundry`

### 2. Sync Upstream Updates

Pull latest changes from upstream into our production branch.

```bash
# Step 1: Fetch latest from upstream
git fetch upstream

# Step 2: Update local upstream mirror branch
git checkout upstream/{platform}/{owner}/{repo}
git merge upstream/main --ff-only
git push origin upstream/{platform}/{owner}/{repo}

# Step 3: Create sync branch from main
git checkout main
git checkout -b sync/$(date +%Y%m%d)
# Or use upstream version: sync/v1.2.0

# Step 4: Merge upstream changes
git merge upstream/{platform}/{owner}/{repo}

# Step 5: Resolve conflicts if any, then merge to main
git checkout main
git merge sync/$(date +%Y%m%d) --no-ff

# Step 6: Clean up
git branch -d sync/$(date +%Y%m%d)
git push origin main
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

Follows standard Git Flow. Feature branches merge into `develop`, and `develop` merges into `main` for releases.

### 4. Contribute to Upstream

For code intended to be submitted as a PR to the upstream repository.

```bash
# Step 1: Branch from upstream mirror (NOT from main or develop)
git checkout upstream/{platform}/{owner}/{repo}
git checkout -b contrib/{name}

# Step 2: Develop the contribution
# ... make changes ...

# Step 3: Push contrib branch to origin
git push origin contrib/{name}

# Step 4: Create PR to upstream
#   - Base: upstream's main/master
#   - Head: our contrib/{name}
#   Use GitHub CLI or platform UI to create the PR.

# Step 5: After PR is merged upstream, clean up
git branch -d contrib/{name}
git push origin --delete contrib/{name}

# Step 6: Sync upstream to pick up the merged contribution
#   Follow "Sync Upstream Updates" workflow above.
```

**Important**: Always branch `contrib/*` from the upstream mirror branch, never from `main` or `develop`. This ensures the PR contains only the intended changes, without our customizations leaking into the upstream PR.

### 5. Cherry-pick from Upstream

To selectively pick specific commits from upstream without a full sync.

```bash
# Fetch latest
git fetch upstream

# Update upstream mirror
git checkout upstream/{platform}/{owner}/{repo}
git merge upstream/main --ff-only

# Cherry-pick onto develop or main
git checkout develop
git cherry-pick <commit-hash>
```

## Rules

1. **upstream branches are read-only mirrors** — Never commit directly to `upstream/*` branches. Only update them via `git merge upstream/{remote-branch} --ff-only`.
2. **contrib branches are clean** — Always branch from upstream mirror, never from main/develop. No fork-specific customizations should leak into contrib branches.
3. **sync branches are temporary** — Create for merging upstream updates, delete after merge to main is complete.
4. **Push upstream branches to origin** — This makes the upstream baseline visible to all collaborators without requiring them to configure the upstream remote.
5. **One upstream mirror per fork source** — Each upstream source gets exactly one `upstream/{platform}/{owner}/{repo}` branch.

## Compatibility

This skill is designed to work alongside:
- **git-flow-branch-creator** — Uses matching `feature/` prefix convention. Release and hotfix workflows are handled by git-flow-branch-creator, not this skill.
- **Other git/commit skills** — This skill only manages fork-specific branch workflows. Commit message format, PR templates, and changelog generation are delegated to other skills.
