#!/usr/bin/env bash
# Check that required skills are installed for a given stage.
# Usage: check-deps.sh [stage]
#   If no stage given, checks all stages.
#   Exits 0 if all deps met, 1 if any missing.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Skill directories to search (in priority order)
SKILL_DIRS=(
    "${REPO_ROOT}/.claude/skills"
    "${REPO_ROOT}/.agents/skills"
)

# Stage → required skills mapping
declare -A STAGE_DEPS
STAGE_DEPS[discover]="competitive-intelligence-analyst marketing-psychology"
STAGE_DEPS[define]="product-marketing-context marketing-ideas write-a-prd"
STAGE_DEPS[design]="architecture api-design prd-to-plan prd-to-issues"
STAGE_DEPS[develop]="review-diff refactor test-strategy"
STAGE_DEPS[deliver]="security-review woodpecker-ci docker-expert multi-stage-dockerfile kubernetes-specialist monitoring-observability changelog-generator"
STAGE_DEPS[grow]="seo-audit copywriting email-sequence landing-page-design lead-research-assistant startup-financial-modeling"

# Known install sources for skills that might be missing
declare -A INSTALL_SOURCES
INSTALL_SOURCES[competitive-intelligence-analyst]="shipshitdev/library@competitive-intelligence-analyst"
INSTALL_SOURCES[marketing-psychology]="coreyhaines31/marketingskills@marketing-psychology"
INSTALL_SOURCES[product-marketing-context]="coreyhaines31/marketingskills@product-marketing-context"
INSTALL_SOURCES[marketing-ideas]="coreyhaines31/marketingskills@marketing-ideas"
INSTALL_SOURCES[write-a-prd]="mattpocock/skills@write-a-prd"
INSTALL_SOURCES[architecture]="ivanzzeth/skills@architecture"
INSTALL_SOURCES[api-design]="affaan-m/everything-claude-code@api-design"
INSTALL_SOURCES[prd-to-plan]="mattpocock/skills@prd-to-plan"
INSTALL_SOURCES[prd-to-issues]="mattpocock/skills@prd-to-issues"
INSTALL_SOURCES[golang-pro]="jeffallan/claude-skills@golang-pro"
INSTALL_SOURCES[golang-testing]="affaan-m/everything-claude-code@golang-testing"
INSTALL_SOURCES[review-diff]="ivanzzeth/skills@review-diff"
INSTALL_SOURCES[refactor]="ivanzzeth/skills@refactor"
INSTALL_SOURCES[test-strategy]="ivanzzeth/skills@test-strategy"
INSTALL_SOURCES[security-review]="ivanzzeth/skills@security-review"
INSTALL_SOURCES[woodpecker-ci]="ivanzzeth/skills@woodpecker-ci"
INSTALL_SOURCES[docker-expert]="sickn33/antigravity-awesome-skills@docker-expert"
INSTALL_SOURCES[multi-stage-dockerfile]="github/awesome-copilot@multi-stage-dockerfile"
INSTALL_SOURCES[kubernetes-specialist]="jeffallan/claude-skills@kubernetes-specialist"
INSTALL_SOURCES[monitoring-observability]="ahmedasmar/devops-claude-skills@monitoring-observability"
INSTALL_SOURCES[changelog-generator]="composiohq/awesome-claude-skills@changelog-generator"
INSTALL_SOURCES[seo-audit]="coreyhaines31/marketingskills@seo-audit"
INSTALL_SOURCES[copywriting]="coreyhaines31/marketingskills@copywriting"
INSTALL_SOURCES[email-sequence]="coreyhaines31/marketingskills@email-sequence"
INSTALL_SOURCES[landing-page-design]="inferen-sh/skills@landing-page-design"
INSTALL_SOURCES[lead-research-assistant]="composiohq/awesome-claude-skills@lead-research-assistant"
INSTALL_SOURCES[startup-financial-modeling]="wshobson/agents@startup-financial-modeling"

skill_exists() {
    local skill_name="$1"
    for dir in "${SKILL_DIRS[@]}"; do
        if [[ -d "${dir}/${skill_name}" ]]; then
            return 0
        fi
    done
    return 1
}

check_stage() {
    local stage="$1"
    local deps="${STAGE_DEPS[$stage]:-}"
    if [[ -z "$deps" ]]; then
        echo "ERROR: Unknown stage '${stage}'"
        echo "Valid stages: discover define design develop deliver grow"
        return 1
    fi

    local missing=()
    local found=()
    for skill in $deps; do
        if skill_exists "$skill"; then
            found+=("$skill")
        else
            missing+=("$skill")
        fi
    done

    local stage_upper
    stage_upper=$(echo "$stage" | tr '[:lower:]' '[:upper:]')

    if [[ ${#missing[@]} -eq 0 ]]; then
        echo "OK: ${stage_upper} — all ${#found[@]} skills installed"
        return 0
    else
        echo "MISSING: ${stage_upper} — ${#missing[@]} skill(s) not found:"
        for skill in "${missing[@]}"; do
            local source="${INSTALL_SOURCES[$skill]:-unknown}"
            if [[ "$source" == \#* ]]; then
                echo "  - ${skill}  (${source})"
            else
                echo "  - ${skill}"
                echo "    Install: npx skills add ${source} -y"
            fi
        done
        return 1
    fi
}

# Main
target_stage="${1:-all}"
exit_code=0

if [[ "$target_stage" == "all" ]]; then
    for stage in discover define design develop deliver grow; do
        check_stage "$stage" || exit_code=1
        echo ""
    done
else
    check_stage "$target_stage" || exit_code=1
fi

exit $exit_code
