#!/usr/bin/env python3
"""
Doc gardening: Find stale or obsolete documentation.

This is a template. Customize the checks for your specific project.
"""
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def find_stale_docs(repo_root: Path, days_threshold: int = 90) -> List[Tuple[Path, int]]:
    """
    Find documentation files that haven't been updated in N days.

    Returns list of (file_path, days_since_update) tuples.
    """
    stale_docs = []
    docs_dir = repo_root / "docs"

    if not docs_dir.exists():
        return stale_docs

    markdown_files = list(docs_dir.glob("**/*.md"))
    now = datetime.now()

    for md_file in markdown_files:
        # Skip index files and generated docs
        if md_file.name == "index.md" or "generated" in str(md_file):
            continue

        # Get last modification time
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
        days_old = (now - mtime).days

        if days_old > days_threshold:
            stale_docs.append((md_file, days_old))

    return stale_docs


def find_todo_markers(repo_root: Path) -> List[Tuple[Path, int, str]]:
    """
    Find TODO markers in documentation.

    Returns list of (file_path, line_number, content) tuples.
    """
    todos = []
    docs_dir = repo_root / "docs"

    if not docs_dir.exists():
        return todos

    markdown_files = list(docs_dir.glob("**/*.md"))
    todo_pattern = re.compile(r'TODO:?\s*(.+)', re.IGNORECASE)

    for md_file in markdown_files:
        try:
            lines = md_file.read_text().splitlines()
            for line_num, line in enumerate(lines, 1):
                match = todo_pattern.search(line)
                if match:
                    todos.append((md_file, line_num, line.strip()))
        except Exception as e:
            print(f"{Colors.RED}Error reading {md_file}: {e}{Colors.NC}")

    return todos


def find_empty_sections(repo_root: Path) -> List[Tuple[Path, str]]:
    """
    Find sections with no content (just header followed by another header or end).

    Returns list of (file_path, section_name) tuples.
    """
    empty_sections = []
    docs_dir = repo_root / "docs"

    if not docs_dir.exists():
        return empty_sections

    markdown_files = list(docs_dir.glob("**/*.md"))
    header_pattern = re.compile(r'^#{1,6}\s+(.+)$')

    for md_file in markdown_files:
        try:
            lines = md_file.read_text().splitlines()
            current_header = None
            has_content = False

            for line in lines:
                header_match = header_pattern.match(line)
                if header_match:
                    # Check if previous section was empty
                    if current_header and not has_content:
                        empty_sections.append((md_file, current_header))
                    # Start new section
                    current_header = header_match.group(1)
                    has_content = False
                elif line.strip():
                    # Non-empty line
                    has_content = True

            # Check last section
            if current_header and not has_content:
                empty_sections.append((md_file, current_header))

        except Exception as e:
            print(f"{Colors.RED}Error reading {md_file}: {e}{Colors.NC}")

    return empty_sections


def check_design_doc_verification(repo_root: Path) -> List[Path]:
    """
    Find design docs without verification status.

    Looks for design docs that don't have a "Verification" or "Status" section.
    """
    unverified = []
    design_docs_dir = repo_root / "docs/design-docs"

    if not design_docs_dir.exists():
        return unverified

    design_docs = list(design_docs_dir.glob("*.md"))
    design_docs = [d for d in design_docs if d.name not in ["index.md", "core-beliefs.md"]]

    for doc in design_docs:
        try:
            content = doc.read_text().lower()
            if "verification" not in content and "status" not in content:
                unverified.append(doc)
        except Exception as e:
            print(f"{Colors.RED}Error reading {doc}: {e}{Colors.NC}")

    return unverified


def main():
    repo_root = Path.cwd()

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])

    if not repo_root.exists():
        print(f"{Colors.RED}❌ Repository not found: {repo_root}{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.BLUE}🌱 Doc Gardening: {repo_root}{Colors.NC}")
    print()

    issues_found = False

    # Check for stale docs
    stale_docs = find_stale_docs(repo_root, days_threshold=90)
    if stale_docs:
        issues_found = True
        print(f"{Colors.YELLOW}📅 Stale documentation (>90 days old):{Colors.NC}")
        for doc, days in sorted(stale_docs, key=lambda x: x[1], reverse=True):
            rel_path = doc.relative_to(repo_root)
            print(f"  - {rel_path} ({days} days old)")
        print()

    # Check for TODOs
    todos = find_todo_markers(repo_root)
    if todos:
        issues_found = True
        print(f"{Colors.YELLOW}📝 TODO markers found:{Colors.NC}")
        for doc, line_num, content in todos[:10]:  # Limit to first 10
            rel_path = doc.relative_to(repo_root)
            print(f"  - {rel_path}:{line_num}")
            print(f"    {content}")
        if len(todos) > 10:
            print(f"  ... and {len(todos) - 10} more")
        print()

    # Check for empty sections
    empty_sections = find_empty_sections(repo_root)
    if empty_sections:
        issues_found = True
        print(f"{Colors.YELLOW}🔍 Empty sections:{Colors.NC}")
        for doc, section in empty_sections[:10]:  # Limit to first 10
            rel_path = doc.relative_to(repo_root)
            print(f"  - {rel_path}: '{section}'")
        if len(empty_sections) > 10:
            print(f"  ... and {len(empty_sections) - 10} more")
        print()

    # Check design doc verification
    unverified = check_design_doc_verification(repo_root)
    if unverified:
        issues_found = True
        print(f"{Colors.YELLOW}⚠ Design docs without verification status:{Colors.NC}")
        for doc in unverified:
            rel_path = doc.relative_to(repo_root)
            print(f"  - {rel_path}")
        print()

    if not issues_found:
        print(f"{Colors.GREEN}✅ No documentation issues found{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.BLUE}💡 Tip: Review and update documentation as needed{Colors.NC}")
        print(f"{Colors.BLUE}   Consider opening PRs to address these issues{Colors.NC}")
        sys.exit(0)  # Non-zero exit would break CI


if __name__ == "__main__":
    main()
