#!/bin/bash
# Install Git hooks for agent-first projects
#
# Usage:
#   ./scripts/install_hooks.sh              # Install all hooks
#   ./scripts/install_hooks.sh --uninstall  # Remove all hooks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Determine project root (where .git directory is)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Find the openai-harness skill directory
# Try multiple possible locations
SKILL_HOOKS=""
for LOCATION in \
    "$HOME/.claude/skills/openai-harness/assets/git-hooks" \
    "./assets/git-hooks" \
    "../openai-harness/assets/git-hooks"; do
    if [ -d "$LOCATION" ]; then
        SKILL_HOOKS="$LOCATION"
        break
    fi
done

if [ -z "$SKILL_HOOKS" ]; then
    echo -e "${RED}❌ Cannot find openai-harness git-hooks directory${NC}"
    echo -e "${YELLOW}Tried locations:${NC}"
    echo "  - $HOME/.claude/skills/openai-harness/assets/git-hooks"
    echo "  - ./assets/git-hooks"
    echo "  - ../openai-harness/assets/git-hooks"
    exit 1
fi

echo -e "${BOLD}${BLUE}Git Hooks Installation${NC}"
echo -e "Project: $PROJECT_ROOT"
echo -e "Hooks source: $SKILL_HOOKS"
echo ""

# Uninstall mode
if [ "$1" = "--uninstall" ]; then
    echo -e "${YELLOW}Uninstalling Git hooks...${NC}"

    for HOOK in pre-commit commit-msg pre-push; do
        HOOK_PATH="$HOOKS_DIR/$HOOK"
        if [ -f "$HOOK_PATH" ]; then
            # Check if it's our hook (contains "agent-first projects")
            if grep -q "agent-first projects" "$HOOK_PATH"; then
                rm "$HOOK_PATH"
                echo -e "${GREEN}✓${NC} Removed $HOOK"
            else
                echo -e "${YELLOW}⊘${NC} Skipped $HOOK (not installed by this script)"
            fi
        fi
    done

    echo -e "${GREEN}✅ Git hooks uninstalled${NC}"
    exit 0
fi

# Install mode
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${RED}❌ Not a git repository${NC}"
    exit 1
fi

echo -e "${BLUE}Installing Git hooks...${NC}"
echo ""

INSTALLED=0
SKIPPED=0

for HOOK in pre-commit commit-msg pre-push; do
    SOURCE="$SKILL_HOOKS/$HOOK"
    DEST="$HOOKS_DIR/$HOOK"

    if [ ! -f "$SOURCE" ]; then
        echo -e "${RED}✗${NC} Missing source: $HOOK"
        continue
    fi

    # Check if hook already exists
    if [ -f "$DEST" ]; then
        # If it's our hook, update it
        if grep -q "agent-first projects" "$DEST"; then
            echo -e "${YELLOW}↻${NC} Updating $HOOK"
            cp "$SOURCE" "$DEST"
            chmod +x "$DEST"
            INSTALLED=$((INSTALLED + 1))
        else
            echo -e "${YELLOW}⊘${NC} Skipped $HOOK (custom hook exists)"
            echo -e "   Backup exists at: $DEST.backup"
            cp "$DEST" "$DEST.backup"
            SKIPPED=$((SKIPPED + 1))
        fi
    else
        echo -e "${GREEN}✓${NC} Installed $HOOK"
        cp "$SOURCE" "$DEST"
        chmod +x "$DEST"
        INSTALLED=$((INSTALLED + 1))
    fi
done

echo ""
echo -e "${BOLD}Summary:${NC}"
echo -e "  Installed: $INSTALLED"
echo -e "  Skipped: $SKIPPED"
echo ""

if [ $INSTALLED -gt 0 ]; then
    echo -e "${GREEN}✅ Git hooks installed successfully${NC}"
    echo ""
    echo -e "${BOLD}Hooks active:${NC}"
    [ -f "$HOOKS_DIR/pre-commit" ] && echo -e "  ${GREEN}●${NC} pre-commit   - Checks secrets, TODOs, file size, docs"
    [ -f "$HOOKS_DIR/commit-msg" ] && echo -e "  ${GREEN}●${NC} commit-msg   - Validates commit message format"
    [ -f "$HOOKS_DIR/pre-push" ] && echo -e "  ${GREEN}●${NC} pre-push     - Runs tests, security scan, doc validation"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Make a test commit to see pre-commit checks in action"
    echo -e "  2. Try pushing to see pre-push validation"
    echo -e "  3. Customize hooks in .git/hooks/ if needed"
    echo ""
    echo -e "${YELLOW}To uninstall:${NC} ./scripts/install_hooks.sh --uninstall"
else
    echo -e "${YELLOW}⚠️  No hooks were installed${NC}"
fi

# Check if required scripts exist
echo -e "${BLUE}Checking required scripts...${NC}"
MISSING_SCRIPTS=""

if [ ! -f "$PROJECT_ROOT/scripts/lint/validate_docs.py" ]; then
    MISSING_SCRIPTS="${MISSING_SCRIPTS}\n  - scripts/lint/validate_docs.py"
fi
if [ ! -f "$PROJECT_ROOT/scripts/lint/code_todos.py" ]; then
    MISSING_SCRIPTS="${MISSING_SCRIPTS}\n  - scripts/lint/code_todos.py"
fi

if [ -n "$MISSING_SCRIPTS" ]; then
    echo -e "${YELLOW}⚠️  Some optional scripts are missing:${NC}"
    echo -e "$MISSING_SCRIPTS"
    echo ""
    echo -e "${YELLOW}Copy from openai-harness skill:${NC}"
    echo -e "  mkdir -p scripts/lint"
    echo -e "  cp $SKILL_HOOKS/../../../scripts/validate_docs.py scripts/lint/"
    echo -e "  cp $SKILL_HOOKS/../../../scripts/code_todos.py scripts/lint/"
    echo -e "  chmod +x scripts/lint/*.py"
else
    echo -e "${GREEN}✓${NC} All required scripts present"
fi

echo ""
