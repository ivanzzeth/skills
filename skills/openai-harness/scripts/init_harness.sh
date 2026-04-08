#!/usr/bin/env bash
# Initialize agent-first repository structure following OpenAI harness principles

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="${1:-}"
TARGET_DIR="${2:-.}"

usage() {
    cat <<EOF
Usage: $0 <project-name> [target-dir]

Initialize an agent-first repository structure with:
  - AGENTS.md (navigation map)
  - ARCHITECTURE.md (system structure)
  - docs/ hierarchy (design, specs, plans, references)
  - Linter scripts for validation

Arguments:
  project-name    Name of the project
  target-dir      Target directory (default: current directory)

Example:
  $0 my-awesome-project ./repos/my-project
EOF
    exit 1
}

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: Project name required${NC}"
    usage
fi

# Resolve target directory
TARGET_DIR=$(cd "$TARGET_DIR" 2>/dev/null && pwd || echo "$TARGET_DIR")

echo -e "${GREEN}Initializing harness structure for: $PROJECT_NAME${NC}"
echo -e "Target directory: $TARGET_DIR"
echo

# Create directory structure
create_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓${NC} Created: $dir"
    else
        echo -e "${YELLOW}→${NC} Exists: $dir"
    fi
}

create_file() {
    local file="$1"
    local content="$2"
    if [ ! -f "$file" ]; then
        echo "$content" > "$file"
        echo -e "${GREEN}✓${NC} Created: $file"
    else
        echo -e "${YELLOW}→${NC} Exists: $file"
    fi
}

# Create main structure
cd "$TARGET_DIR"

# Root documentation
create_dir "docs"
create_dir "docs/design-docs"
create_dir "docs/exec-plans"
create_dir "docs/exec-plans/active"
create_dir "docs/exec-plans/completed"
create_dir "docs/generated"
create_dir "docs/product-specs"
create_dir "docs/references"

# Scripts for validation
create_dir "scripts"
create_dir "scripts/lint"

# AGENTS.md template
AGENTS_MD_CONTENT="# $PROJECT_NAME

{2-3 sentence project overview}

## Documentation Navigation

This file serves as the entry point. Detailed documentation lives in:

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System structure and layer rules
- **[docs/DESIGN.md](./docs/DESIGN.md)** - Design philosophy
- **[docs/product-specs/](./docs/product-specs/)** - Feature requirements
- **[docs/design-docs/](./docs/design-docs/)** - Design decisions
- **[docs/exec-plans/active/](./docs/exec-plans/active/)** - Current work plans
- **[docs/QUALITY_SCORE.md](./docs/QUALITY_SCORE.md)** - Code quality tracking

## Critical Constraints

TODO: Add 3-5 most important rules

## Where to Add Information

| Type | Location |
|------|----------|
| System architecture | ARCHITECTURE.md |
| Design decision | docs/design-docs/{decision}.md |
| Product requirement | docs/product-specs/{feature}.md |
| Work plan | docs/exec-plans/active/{date}-{feature}.md |
| External docs | docs/references/{library}-llms.txt |

Rule: If it's >3 sentences, it belongs in docs/, not here."

create_file "AGENTS.md" "$AGENTS_MD_CONTENT"

# ARCHITECTURE.md template
ARCHITECTURE_MD_CONTENT="# System Architecture

## Overview

TODO: Describe the system

## Business Domains

TODO: List major domains

## Architectural Layers

Enforced dependency direction:
\`\`\`
Types → Config → Repo → Service → Runtime → UI
         ↑
     Providers
\`\`\`

See docs/DESIGN.md for details.

## Enforcement

- Custom linters in scripts/lint/
- Structural tests in tests/architecture/"

create_file "ARCHITECTURE.md" "$ARCHITECTURE_MD_CONTENT"

# docs/ files
DESIGN_MD_CONTENT="# Design Philosophy

## Core Principles

1. **Agent Legibility First** - Optimize for agent comprehension
2. **Enforce Boundaries** - Strict architectural layers
3. **Progressive Disclosure** - Start simple, dive deep as needed
4. **Mechanical Enforcement** - Linters > documentation

## Layer Rules

See [ARCHITECTURE.md](../ARCHITECTURE.md) for details.

## Golden Principles

See [exec-plans/tech-debt-tracker.md](./exec-plans/tech-debt-tracker.md) for current focus areas."

create_file "docs/DESIGN.md" "$DESIGN_MD_CONTENT"

QUALITY_SCORE_CONTENT="# Quality Score

Last updated: $(date +%Y-%m-%d)

## By Domain

| Domain | Test Coverage | Linter Pass | Documentation | Score |
|--------|--------------|-------------|---------------|-------|
| TODO   | TODO         | TODO        | TODO          | TODO  |

## By Layer

| Layer    | Compliance | Tech Debt | Score |
|----------|-----------|-----------|-------|
| Types    | TODO      | TODO      | TODO  |
| Service  | TODO      | TODO      | TODO  |

## Known Gaps

- TODO: Add quality gaps"

create_file "docs/QUALITY_SCORE.md" "$QUALITY_SCORE_CONTENT"

RELIABILITY_MD_CONTENT="# Reliability

## SLOs

TODO: Define service level objectives

## Monitoring

TODO: Define metrics and alerts

## Incident Response

TODO: Define runbooks"

create_file "docs/RELIABILITY.md" "$RELIABILITY_MD_CONTENT"

SECURITY_MD_CONTENT="# Security

## Authentication

TODO: Define auth model

## Authorization

TODO: Define authz model

## Data Protection

TODO: Define encryption, secrets management

## Security Testing

TODO: Define security test requirements"

create_file "docs/SECURITY.md" "$SECURITY_MD_CONTENT"

# Design docs index
DESIGN_INDEX_CONTENT="# Design Documentation Index

| Design | Status | Last Updated |
|--------|--------|--------------|
| TODO   | TODO   | TODO         |

## Verification Status

- ✅ Implemented and verified
- 🚧 In progress
- ❌ Not yet implemented"

create_file "docs/design-docs/index.md" "$DESIGN_INDEX_CONTENT"

CORE_BELIEFS_CONTENT="# Core Beliefs

Agent-first operating principles for this project:

1. **Repository is source of truth** - No important knowledge in Slack, docs, or heads
2. **Progressive disclosure** - AGENTS.md = map, docs/ = details
3. **Mechanical enforcement** - Linters + CI, not just documentation
4. **Golden principles** - Encode taste once, enforce continuously
5. **Agent legibility** - Make UI, logs, metrics accessible to agents

See [../DESIGN.md](../DESIGN.md) for implementation."

create_file "docs/design-docs/core-beliefs.md" "$CORE_BELIEFS_CONTENT"

# Exec plans
TECH_DEBT_CONTENT="# Technical Debt Tracker

## High Priority

- TODO: Add high-priority tech debt

## Medium Priority

- TODO: Add medium-priority tech debt

## Low Priority

- TODO: Add low-priority tech debt

## Resolved

- TODO: Track resolved debt (with dates)"

create_file "docs/exec-plans/tech-debt-tracker.md" "$TECH_DEBT_CONTENT"

# Product specs index
PRODUCT_INDEX_CONTENT="# Product Specifications Index

| Feature | Status | Owner | Last Updated |
|---------|--------|-------|--------------|
| TODO    | TODO   | TODO  | TODO         |

## Status Legend

- 📝 Spec in progress
- ✅ Spec approved
- 🚧 In development
- ✅ Shipped"

create_file "docs/product-specs/index.md" "$PRODUCT_INDEX_CONTENT"

# Basic validation script
VALIDATE_DOCS_SCRIPT='#!/usr/bin/env python3
"""Validate documentation structure and cross-links."""
import sys
from pathlib import Path

def validate_structure():
    """Check required files and directories exist."""
    required = [
        "AGENTS.md",
        "ARCHITECTURE.md",
        "docs/DESIGN.md",
        "docs/QUALITY_SCORE.md",
        "docs/design-docs/index.md",
        "docs/product-specs/index.md",
        "docs/exec-plans/tech-debt-tracker.md",
    ]

    errors = []
    for path in required:
        if not Path(path).exists():
            errors.append(f"Missing required file: {path}")

    return errors

if __name__ == "__main__":
    errors = validate_structure()
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Documentation structure valid")
'

create_file "scripts/lint/validate_docs_structure.py" "$VALIDATE_DOCS_SCRIPT"
chmod +x "scripts/lint/validate_docs_structure.py"

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Harness structure initialized!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Next steps:"
echo "  1. Edit AGENTS.md - Add project overview and constraints"
echo "  2. Edit ARCHITECTURE.md - Define domains and layers"
echo "  3. Edit docs/DESIGN.md - Add design principles"
echo "  4. Run validation: scripts/lint/validate_docs_structure.py"
echo
echo "See OpenAI harness principles for guidance."
