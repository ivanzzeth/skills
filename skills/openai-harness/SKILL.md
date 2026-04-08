---
name: openai-harness
description: This skill should be used when setting up an agent-first repository structure following OpenAI harness engineering principles. Applies when the user wants to create AGENTS.md, establish progressive disclosure documentation hierarchy, enforce architectural boundaries, implement doc gardening, or transition from monolithic documentation to agent-optimized structure. Appropriate for greenfield projects or refactoring existing repositories to maximize agent productivity.
---

# OpenAI Harness

## Overview

Apply OpenAI's harness engineering principles to create agent-first repository structures. Enable AI agents to work effectively at scale through progressive disclosure documentation, mechanical enforcement, and feedback loops.

**Core philosophy**: Humans steer. Agents execute. Repository as single source of truth.

**Tech-stack agnostic**: Works with any language (Go, Python, JavaScript, Rust, Java, C++, etc.). Only requires bash, grep, git, python3.

## When to Use This Skill

Use when:
- Initializing a new agent-first repository
- Refactoring monolithic AGENTS.md to progressive disclosure
- Agents struggle to navigate or maintain architectural coherence
- Scaling agent-generated codebases (need mechanical enforcement)
- Setting up quality controls (doc gardening, golden principles)

## Core Capabilities

See **[references/capabilities.md](./references/capabilities.md)** for detailed explanations of each capability.

1. **Repository Structure Initialization** - Initialize full agent-first directory structure with templated files (`init_harness.sh`)
2. **Progressive Disclosure Documentation** - Structure docs in layers for efficient context usage ([principles](./references/openai-harness-principles.md), [examples](./references/example-agents-md.md))
3. **Architectural Enforcement** - Enforce strict boundaries with custom linters (`layer_dependencies_linter.{py,go,ts}`, `golden_principles_linter.py`)
4. **Token-Efficient Project Status** - Aggregate project status (97% token reduction: 7500 → 250) with `project_status.py`
5. **Documentation Gardening** - Automated doc quality checks with `doc_gardening.py` and `validate_docs.py`
6. **Code TODO Scanner** - Scan source for TODO/FIXME/BUG annotations across 9 languages (`code_todos.py`)
7. **Monolith Migration Assistant** - Refactor large AGENTS.md to progressive disclosure (`migrate_from_monolith.py`)
8. **Git Hooks Automation** - Language-agnostic Git hooks without npm/husky (`install_hooks.sh`)
9. **Observability Integration** - Validate Prometheus metrics, structured logging, health checks (`validate_observability.py`)
10. **CI/CD Integration** - Pre-configured workflows for GitHub Actions, GitLab CI, Woodpecker CI

## How to Use

### Quick Start
See **[references/quick-start.md](./references/quick-start.md)** for step-by-step guide (10 steps from installation to first deployment).

### Complete Example
See **[references/end-to-end-example.md](./references/end-to-end-example.md)** for real-world scenario (building JWT auth microservice with full observability in 55 minutes).

### Principles and Patterns
- **[references/openai-harness-principles.md](./references/openai-harness-principles.md)** - Full OpenAI harness engineering principles
- **[references/directory-structure.md](./references/directory-structure.md)** - Detailed structure specification
- **[references/best-practices.md](./references/best-practices.md)** - Wisdom learned from building agent-first repositories

### Examples and Anti-Patterns
- **[references/example-agents-md.md](./references/example-agents-md.md)** - Good AGENTS.md examples and what to avoid
- **[references/example-architecture-md.md](./references/example-architecture-md.md)** - Good ARCHITECTURE.md examples and what to avoid  
- **[references/common-pitfalls.md](./references/common-pitfalls.md)** - 12 real pitfalls with prevention/fixes

### Agent Team Collaboration & Quality Assurance
- **[references/agent-team-patterns.md](./references/agent-team-patterns.md)** - 4 agent collaboration patterns (Generator-Validator, Pipeline, Expert Pool, Hierarchical)
- **[references/qa-workflow.md](./references/qa-workflow.md)** - Systematic QA workflow with 3-round verification method
- **[references/metrics-best-practices.md](./references/metrics-best-practices.md)** - Prometheus metrics anti-patterns and fixes (double counting, stale gauges, high cardinality)

## Available Resources

### Scripts (`scripts/`)
- `init_harness.sh` - Initialize complete directory structure
- `validate_docs.py` - Validate documentation structure
- `doc_gardening.py` - Find stale/incomplete docs
- `code_todos.py` - Scan for TODO/FIXME/BUG in code
- `project_status.py` - Aggregate project status (97% token savings)
- `migrate_from_monolith.py` - Refactor large AGENTS.md
- `install_hooks.sh` - One-command Git hooks setup

### Git Hooks (`assets/git-hooks/`)
- `pre-commit` - Fast checks (1-5s): secrets, file size, TODOs, debug code
- `commit-msg` - Commit message validation (Conventional Commits)
- `pre-push` - Comprehensive checks (30s-2min): tests, security scan, doc validation

### Custom Linters (`assets/custom-linters/`)
- `layer_dependencies_linter.{py,go,ts}` - Language-specific layer validators
- `golden_principles_linter.py` - Context-aware rules linter (reads project docs)
- `validate_observability.py` - Observability integration validator

### CI/CD Templates (`assets/ci-examples/`)
- `github-actions-docs.yml` - GitHub Actions workflow
- `gitlab-ci-docs.yml` - GitLab CI configuration
- `woodpecker-docs.yml` - Woodpecker CI pipeline
- `README.md` - Integration guide

### References (`references/`)
- `openai-harness-principles.md` - Full OpenAI harness engineering principles
- `directory-structure.md` - Detailed directory structure spec
- `capabilities.md` - Detailed explanation of all 10 capabilities
- `quick-start.md` - Step-by-step guide from scratch
- `end-to-end-example.md` - Complete real-world scenario
- `example-agents-md.md` - AGENTS.md examples and anti-patterns
- `example-architecture-md.md` - ARCHITECTURE.md examples and anti-patterns
- `common-pitfalls.md` - 12 real pitfalls with prevention/fixes
- `best-practices.md` - Wisdom learned from building agent-first repositories
- `agent-team-patterns.md` - Agent collaboration patterns (Generator-Validator, Pipeline, Expert Pool)
- `qa-workflow.md` - QA 3-round verification with boundary testing techniques
- `metrics-best-practices.md` - Prometheus anti-patterns: double counting, stale gauges, high cardinality

## References

Based on:
- OpenAI "Harness engineering: leveraging Codex in an agent-first world" (Feb 11, 2026)
  - Original article: https://openai.com/index/harness-engineering/
- See `references/openai-harness-principles.md` for full article distillation
- See `references/directory-structure.md` for detailed structure specification
