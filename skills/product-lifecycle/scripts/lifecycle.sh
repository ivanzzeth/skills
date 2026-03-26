#!/usr/bin/env bash
# Product Lifecycle state management script
# Usage:
#   lifecycle.sh init <product-name>      — Scaffold .product-lifecycle/<product>/
#   lifecycle.sh status <product-name>    — Show current stage
#   lifecycle.sh gate <product-name>      — Show gate checklist for current stage
#   lifecycle.sh advance <product-name>   — Move to next stage
#   lifecycle.sh jump <product-name> <stage>  — Jump to specific stage
#   lifecycle.sh import <product-name> <stage> — Import existing project at a specific stage
#   lifecycle.sh cycle <product-name>     — Complete current cycle, start new iteration
#   lifecycle.sh list                     — List all tracked products

set -euo pipefail

# Find repo root (where .product-lifecycle/ lives)
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BASE_DIR="${REPO_ROOT}/.product-lifecycle"

STAGES=("discover" "define" "design" "develop" "deliver" "grow")
STAGE_LABELS=("DISCOVER" "DEFINE" "DESIGN" "DEVELOP" "DELIVER" "GROW")
STAGE_DESCRIPTIONS=(
    "Market & User Research"
    "Product Definition"
    "Technical Architecture"
    "Build & Test"
    "Ship to Production"
    "Acquire & Retain Users"
)

usage() {
    echo "Usage: lifecycle.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  init <product>           Initialize a new product lifecycle (starts at DISCOVER)"
    echo "  import <product> <stage> Import existing project at a specific stage"
    echo "  status <product>         Show current stage and iteration"
    echo "  gate <product>           Show gate checklist for current stage"
    echo "  advance <product>        Move to next stage"
    echo "  jump <product> <stage>   Jump to a specific stage (discover|define|design|develop|deliver|grow)"
    echo "  cycle <product>          Complete iteration, archive and start new cycle from DISCOVER"
    echo "  list                     List all tracked products"
    exit 1
}

get_stage_index() {
    local stage="$1"
    for i in "${!STAGES[@]}"; do
        if [[ "${STAGES[$i]}" == "$stage" ]]; then
            echo "$i"
            return 0
        fi
    done
    echo "-1"
    return 1
}

get_current_stage() {
    local product="$1"
    local lifecycle_file="${BASE_DIR}/${product}/lifecycle.md"
    if [[ ! -f "$lifecycle_file" ]]; then
        echo "not-initialized"
        return 1
    fi
    grep -oP '(?<=current_stage: )\w+' "$lifecycle_file" 2>/dev/null || echo "unknown"
}

get_iteration() {
    local product="$1"
    local lifecycle_file="${BASE_DIR}/${product}/lifecycle.md"
    grep -oP '(?<=iteration: )\d+' "$lifecycle_file" 2>/dev/null || echo "1"
}

set_current_stage() {
    local product="$1"
    local new_stage="$2"
    local lifecycle_file="${BASE_DIR}/${product}/lifecycle.md"
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # Update current stage
    sed -i "s/^current_stage: .*/current_stage: ${new_stage}/" "$lifecycle_file"
    sed -i "s/^updated_at: .*/updated_at: ${timestamp}/" "$lifecycle_file"

    # Append to history
    local idx iteration
    idx=$(get_stage_index "$new_stage")
    iteration=$(get_iteration "$product")
    echo "- ${timestamp}: [Iter ${iteration}] Entered ${STAGE_LABELS[$idx]} — ${STAGE_DESCRIPTIONS[$idx]}" >> "$lifecycle_file"
}

cmd_init() {
    local product="${1:?Product name required}"
    local product_dir="${BASE_DIR}/${product}"

    if [[ -d "$product_dir" ]]; then
        echo "ERROR: Product '${product}' already exists at ${product_dir}"
        echo "Use 'lifecycle.sh status ${product}' to check current state."
        exit 1
    fi

    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    mkdir -p "$product_dir"

    # Create lifecycle.md
    cat > "${product_dir}/lifecycle.md" << EOF
---
product: ${product}
current_stage: discover
iteration: 1
created_at: ${timestamp}
updated_at: ${timestamp}
---

# ${product} — Product Lifecycle

## Current Stage: DISCOVER — Market & User Research
## Iteration: 1

## Stage History

- ${timestamp}: [Iter 1] Initialized product lifecycle
- ${timestamp}: [Iter 1] Entered DISCOVER — Market & User Research
EOF

    # Create placeholder files for each stage
    cat > "${product_dir}/01-discovery.md" << EOF
# ${product} — Discovery

> Stage 1: Market & User Research
> Created: ${timestamp}

## Target Users

_TODO: Who are we building for?_

## Market Landscape

_TODO: What exists today? What are the gaps?_

## Competitors

_TODO: Direct and indirect competitors_

## Key Insights

_TODO: What did we learn?_
EOF

    cat > "${product_dir}/02-prd.md" << EOF
# ${product} — Product Requirements Document

> Stage 2: Product Definition
> Created: ${timestamp}

_This file will be populated during the DEFINE stage._
_Use /write-a-prd to generate the PRD._
EOF

    cat > "${product_dir}/03-design.md" << EOF
# ${product} — Technical Design

> Stage 3: Technical Architecture
> Created: ${timestamp}

_This file will be populated during the DESIGN stage._
_Use /architecture to generate the system design._

## Stateless Microservice Checklist

- [ ] No local file storage (use object storage / DB)
- [ ] No in-memory session state (use Redis / JWT)
- [ ] No sticky sessions required
- [ ] Horizontally scalable (multiple replicas safe)
- [ ] Graceful shutdown (handle SIGTERM)
- [ ] Health check endpoint (/healthz)
- [ ] Readiness check endpoint (/readyz)
- [ ] All config via environment variables
- [ ] 12-factor app compliant
EOF

    cat > "${product_dir}/04-dev-log.md" << EOF
# ${product} — Development Log

> Stage 4: Build & Test
> Created: ${timestamp}

_Track development progress here. Optional — PRs and commits are the source of truth._
EOF

    cat > "${product_dir}/05-deploy-checklist.md" << EOF
# ${product} — Deployment Checklist

> Stage 5: Ship to Production
> Created: ${timestamp}

## Pre-Deploy

- [ ] Dockerfile builds successfully
- [ ] Multi-stage build (minimal final image)
- [ ] K3s manifests created (Deployment + Service + Ingress)
- [ ] Resource limits set (CPU/memory)
- [ ] Replicas ≥ 2
- [ ] Health checks configured in K8s
- [ ] Secrets in K8s Secrets (not env vars in manifests)

## Deploy

- [ ] Image pushed to registry
- [ ] Deployed to K3s cluster
- [ ] Pods running and healthy
- [ ] Ingress accessible externally

## Post-Deploy

- [ ] Monitoring/alerting configured
- [ ] Logs visible in central logging
- [ ] Changelog generated
- [ ] Version tagged in git
EOF

    cat > "${product_dir}/06-growth-plan.md" << EOF
# ${product} — Growth Plan

> Stage 6: Acquire & Retain Users
> Created: ${timestamp}

_This file will be populated during the GROW stage._

## Channels

_TODO: Which channels to focus on?_

## Metrics

_TODO: North star metric? Leading indicators?_

## First 30 Days

_TODO: What's the launch plan?_
EOF

    echo "OK: Initialized '${product}' at ${product_dir}"
    echo "Current stage: DISCOVER"
    echo ""
    echo "Files created:"
    ls -1 "$product_dir"
}

cmd_import() {
    local product="${1:?Product name required}"
    local target="${2:?Target stage required (discover|define|design|develop|deliver|grow)}"

    local idx
    idx=$(get_stage_index "$target")
    if [[ "$idx" == "-1" ]]; then
        echo "ERROR: Unknown stage '${target}'. Valid stages: ${STAGES[*]}"
        exit 1
    fi

    # Run init (silently)
    local product_dir="${BASE_DIR}/${product}"
    if [[ -d "$product_dir" ]]; then
        echo "ERROR: Product '${product}' already exists. Use 'jump' to change stage."
        exit 1
    fi

    # Init silently, then override stage
    cmd_init "$product" > /dev/null

    local lifecycle_file="${product_dir}/lifecycle.md"
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # Set stage to target
    sed -i "s/^current_stage: .*/current_stage: ${target}/" "$lifecycle_file"
    sed -i "s/^updated_at: .*/updated_at: ${timestamp}/" "$lifecycle_file"

    # Mark earlier stages as imported
    for i in "${!STAGES[@]}"; do
        if [[ $i -lt $idx ]]; then
            echo "- ${timestamp}: [Iter 1] ${STAGE_LABELS[$i]} — imported (pre-existing)" >> "$lifecycle_file"
        fi
    done
    echo "- ${timestamp}: [Iter 1] Entered ${STAGE_LABELS[$idx]} — ${STAGE_DESCRIPTIONS[$idx]} (imported)" >> "$lifecycle_file"

    echo "OK: Imported '${product}' at stage ${STAGE_LABELS[$idx]} — ${STAGE_DESCRIPTIONS[$idx]}"
    echo "Earlier stages marked as pre-existing."
    echo ""
    echo "Next steps:"
    echo "  1. Fill in the stage docs with existing knowledge (.product-lifecycle/${product}/)"
    echo "  2. Run: lifecycle.sh gate ${product}  — to check current stage readiness"
}

cmd_status() {
    local product="${1:?Product name required}"
    local lifecycle_file="${BASE_DIR}/${product}/lifecycle.md"

    if [[ ! -f "$lifecycle_file" ]]; then
        echo "ERROR: Product '${product}' not found. Run 'lifecycle.sh init ${product}' first."
        exit 1
    fi

    local current_stage
    current_stage=$(get_current_stage "$product")
    local idx
    idx=$(get_stage_index "$current_stage")

    local iteration
    iteration=$(get_iteration "$product")

    echo "Product:   ${product}"
    echo "Iteration: ${iteration}"
    echo "Stage:     ${STAGE_LABELS[$idx]} — ${STAGE_DESCRIPTIONS[$idx]}"
    echo ""
    echo "Progress:"
    for i in "${!STAGES[@]}"; do
        if [[ $i -lt $idx ]]; then
            echo "  [x] ${STAGE_LABELS[$i]}"
        elif [[ $i -eq $idx ]]; then
            echo "  [>] ${STAGE_LABELS[$i]}  ← current"
        else
            echo "  [ ] ${STAGE_LABELS[$i]}"
        fi
    done
}

cmd_gate() {
    local product="${1:?Product name required}"
    local current_stage
    current_stage=$(get_current_stage "$product")
    local idx
    idx=$(get_stage_index "$current_stage")

    echo "Gate Check: ${STAGE_LABELS[$idx]} → ${STAGE_LABELS[$((idx+1))]:-DONE}"
    echo ""
    echo "Read references/stage-${current_stage}.md for the full gate checklist."
    echo "Confirm all items, then run: lifecycle.sh advance ${product}"
}

cmd_advance() {
    local product="${1:?Product name required}"
    local current_stage
    current_stage=$(get_current_stage "$product")
    local idx
    idx=$(get_stage_index "$current_stage")

    if [[ $idx -ge $(( ${#STAGES[@]} - 1 )) ]]; then
        echo "Product '${product}' is at the final stage (GROW)."
        echo "To start a new iteration (new feature cycle), run:"
        echo "  lifecycle.sh cycle ${product}"
        exit 0
    fi

    local next_stage="${STAGES[$((idx+1))]}"
    local next_idx=$((idx+1))

    set_current_stage "$product" "$next_stage"

    echo "OK: ${product} advanced to ${STAGE_LABELS[$next_idx]} — ${STAGE_DESCRIPTIONS[$next_idx]}"
}

cmd_jump() {
    local product="${1:?Product name required}"
    local target="${2:?Target stage required (discover|define|design|develop|deliver|grow)}"

    local idx
    idx=$(get_stage_index "$target")
    if [[ "$idx" == "-1" ]]; then
        echo "ERROR: Unknown stage '${target}'. Valid stages: ${STAGES[*]}"
        exit 1
    fi

    set_current_stage "$product" "$target"
    echo "OK: ${product} jumped to ${STAGE_LABELS[$idx]} — ${STAGE_DESCRIPTIONS[$idx]}"
}

cmd_cycle() {
    local product="${1:?Product name required}"
    local lifecycle_file="${BASE_DIR}/${product}/lifecycle.md"
    local product_dir="${BASE_DIR}/${product}"

    if [[ ! -f "$lifecycle_file" ]]; then
        echo "ERROR: Product '${product}' not found."
        exit 1
    fi

    local old_iteration timestamp new_iteration
    old_iteration=$(get_iteration "$product")
    new_iteration=$((old_iteration + 1))
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # Archive current iteration's stage files
    local archive_dir="${product_dir}/iterations/iter-${old_iteration}"
    mkdir -p "$archive_dir"
    for f in 01-discovery.md 02-prd.md 03-design.md 04-dev-log.md 05-deploy-checklist.md 06-growth-plan.md; do
        if [[ -f "${product_dir}/${f}" ]]; then
            cp "${product_dir}/${f}" "${archive_dir}/${f}"
        fi
    done

    # Reset stage files for new iteration (keep structure, clear content)
    cat > "${product_dir}/01-discovery.md" << EOF
# ${product} — Discovery (Iteration ${new_iteration})

> Stage 1: Market & User Research
> Created: ${timestamp}
> Previous iterations archived in iterations/

## Target Users

_TODO_

## Market Landscape

_TODO_

## Competitors

_TODO_

## Key Insights

_TODO_
EOF

    cat > "${product_dir}/02-prd.md" << EOF
# ${product} — PRD (Iteration ${new_iteration})

> Stage 2: Product Definition
> Created: ${timestamp}

_Use /write-a-prd to generate._
EOF

    cat > "${product_dir}/03-design.md" << EOF
# ${product} — Technical Design (Iteration ${new_iteration})

> Stage 3: Technical Architecture
> Created: ${timestamp}

_Use /architecture to generate._
EOF

    cat > "${product_dir}/04-dev-log.md" << EOF
# ${product} — Dev Log (Iteration ${new_iteration})

> Stage 4: Build & Test
> Created: ${timestamp}
EOF

    cat > "${product_dir}/05-deploy-checklist.md" << EOF
# ${product} — Deploy Checklist (Iteration ${new_iteration})

> Stage 5: Ship to Production
> Created: ${timestamp}

_Reuse and update the deploy checklist from previous iteration if applicable._
EOF

    cat > "${product_dir}/06-growth-plan.md" << EOF
# ${product} — Growth Plan (Iteration ${new_iteration})

> Stage 6: Acquire & Retain Users
> Created: ${timestamp}

_Build on the growth plan from previous iteration._
EOF

    # Update lifecycle.md
    sed -i "s/^current_stage: .*/current_stage: discover/" "$lifecycle_file"
    sed -i "s/^iteration: .*/iteration: ${new_iteration}/" "$lifecycle_file"
    sed -i "s/^updated_at: .*/updated_at: ${timestamp}/" "$lifecycle_file"
    echo "- ${timestamp}: [Iter ${new_iteration}] New cycle started — archived iteration ${old_iteration}" >> "$lifecycle_file"
    echo "- ${timestamp}: [Iter ${new_iteration}] Entered DISCOVER — Market & User Research" >> "$lifecycle_file"

    echo "OK: ${product} started iteration ${new_iteration}"
    echo "Archived iteration ${old_iteration} to: ${archive_dir}"
    echo "Current stage: DISCOVER"
}

cmd_list() {
    if [[ ! -d "$BASE_DIR" ]]; then
        echo "No products tracked yet. Run 'lifecycle.sh init <product-name>' to start."
        exit 0
    fi

    echo "Tracked Products:"
    echo ""
    for dir in "${BASE_DIR}"/*/; do
        if [[ -f "${dir}lifecycle.md" ]]; then
            local product
            product=$(basename "$dir")
            local stage
            stage=$(get_current_stage "$product")
            local idx
            idx=$(get_stage_index "$stage")
            local iteration
            iteration=$(get_iteration "$product")
            echo "  ${product} [iter ${iteration}]: ${STAGE_LABELS[$idx]} — ${STAGE_DESCRIPTIONS[$idx]}"
        fi
    done
}

# Main dispatch
case "${1:-}" in
    init)    cmd_init "${2:-}" ;;
    import)  cmd_import "${2:-}" "${3:-}" ;;
    status)  cmd_status "${2:-}" ;;
    gate)    cmd_gate "${2:-}" ;;
    advance) cmd_advance "${2:-}" ;;
    jump)    cmd_jump "${2:-}" "${3:-}" ;;
    cycle)   cmd_cycle "${2:-}" ;;
    list)    cmd_list ;;
    *)       usage ;;
esac
