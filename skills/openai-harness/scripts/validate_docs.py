#!/usr/bin/env python3
"""
Validate agent-first documentation structure and cross-links.

Checks:
1. Required files and directories exist
2. AGENTS.md is concise (~100 lines)
3. Cross-links are valid
4. Index files are up-to-date
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def validate_structure(repo_root: Path) -> List[str]:
    """Check required files and directories exist."""
    errors = []

    required_files = [
        "AGENTS.md",
        "ARCHITECTURE.md",
        "docs/DESIGN.md",
        "docs/QUALITY_SCORE.md",
        "docs/design-docs/index.md",
        "docs/design-docs/core-beliefs.md",
        "docs/product-specs/index.md",
        "docs/exec-plans/tech-debt-tracker.md",
    ]

    required_dirs = [
        "docs",
        "docs/design-docs",
        "docs/exec-plans",
        "docs/exec-plans/active",
        "docs/exec-plans/completed",
        "docs/generated",
        "docs/product-specs",
        "docs/references",
    ]

    for file_path in required_files:
        full_path = repo_root / file_path
        if not full_path.exists():
            errors.append(f"Missing required file: {file_path}")

    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        if not full_path.exists():
            errors.append(f"Missing required directory: {dir_path}")

    return errors


def validate_agents_md_size(repo_root: Path) -> List[str]:
    """Check that AGENTS.md is concise (target ~100 lines)."""
    errors = []
    agents_md = repo_root / "AGENTS.md"

    if not agents_md.exists():
        return errors  # Already caught by structure validation

    lines = agents_md.read_text().splitlines()
    # Exclude empty lines and comments
    content_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

    if len(lines) > 200:
        errors.append(
            f"AGENTS.md is too long ({len(lines)} lines). "
            f"Target is ~100 lines. Move detailed content to docs/"
        )
    elif len(lines) > 150:
        print(
            f"{Colors.YELLOW}⚠{Colors.NC} AGENTS.md is {len(lines)} lines. "
            f"Consider moving more content to docs/ (target ~100 lines)"
        )

    return errors


def extract_markdown_links(content: str) -> List[str]:
    """Extract markdown link paths from content."""
    # Match [text](path) and [text](path "title")
    link_pattern = r'\[([^\]]+)\]\(([^)]+?)(?:\s+"[^"]*")?\)'
    links = re.findall(link_pattern, content)
    # Return just the paths, filter out external URLs
    return [
        path for (_, path) in links
        if not path.startswith(('http://', 'https://', '#'))
    ]


def validate_cross_links(repo_root: Path) -> List[str]:
    """Check that all internal markdown links are valid."""
    errors = []

    markdown_files = list(repo_root.glob("**/*.md"))

    for md_file in markdown_files:
        try:
            content = md_file.read_text()
            links = extract_markdown_links(content)

            for link in links:
                # Resolve relative to the markdown file's directory
                if link.startswith('./'):
                    link = link[2:]
                elif link.startswith('../'):
                    # Handle relative paths
                    pass

                # Resolve the path
                target = (md_file.parent / link).resolve()

                if not target.exists():
                    rel_md = md_file.relative_to(repo_root)
                    errors.append(
                        f"Broken link in {rel_md}: {link} -> {target} not found"
                    )
        except Exception as e:
            rel_md = md_file.relative_to(repo_root)
            errors.append(f"Error processing {rel_md}: {e}")

    return errors


def validate_index_freshness(repo_root: Path) -> List[str]:
    """Check that index files reference all relevant documents."""
    warnings = []

    # Check design-docs/index.md references all design docs
    design_index = repo_root / "docs/design-docs/index.md"
    if design_index.exists():
        index_content = design_index.read_text()
        design_docs = list((repo_root / "docs/design-docs").glob("*.md"))
        design_docs = [d for d in design_docs if d.name != "index.md"]

        for doc in design_docs:
            if doc.name not in index_content:
                warnings.append(
                    f"docs/design-docs/{doc.name} not referenced in index.md"
                )

    # Check product-specs/index.md references all specs
    specs_index = repo_root / "docs/product-specs/index.md"
    if specs_index.exists():
        index_content = specs_index.read_text()
        specs = list((repo_root / "docs/product-specs").glob("*.md"))
        specs = [s for s in specs if s.name != "index.md"]

        for spec in specs:
            if spec.name not in index_content:
                warnings.append(
                    f"docs/product-specs/{spec.name} not referenced in index.md"
                )

    return warnings


def main():
    # Detect repository root (current directory by default)
    repo_root = Path.cwd()

    # Allow passing repo root as argument
    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])

    if not repo_root.exists():
        print(f"{Colors.RED}❌ Repository not found: {repo_root}{Colors.NC}")
        sys.exit(1)

    print(f"Validating documentation in: {repo_root}")
    print()

    all_errors = []
    warnings = []

    # Run validations
    errors = validate_structure(repo_root)
    all_errors.extend(errors)

    errors = validate_agents_md_size(repo_root)
    all_errors.extend(errors)

    errors = validate_cross_links(repo_root)
    all_errors.extend(errors)

    warns = validate_index_freshness(repo_root)
    warnings.extend(warns)

    # Report results
    if all_errors:
        print(f"{Colors.RED}❌ Validation failed with {len(all_errors)} error(s):{Colors.NC}")
        for error in all_errors:
            print(f"  - {error}")
        print()

    if warnings:
        print(f"{Colors.YELLOW}⚠ Found {len(warnings)} warning(s):{Colors.NC}")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if not all_errors and not warnings:
        print(f"{Colors.GREEN}✅ Documentation structure valid{Colors.NC}")
        sys.exit(0)
    elif not all_errors:
        print(f"{Colors.YELLOW}⚠ Validation passed with warnings{Colors.NC}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
