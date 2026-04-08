#!/usr/bin/env python3
"""
Project Status Overview

Aggregates key information from documentation to provide a quick overview:
- High-priority tech debt
- Security vulnerabilities
- Quality scores
- Active work
- Recent changes

This prevents agents from repeatedly reading multiple files to understand project state.
"""
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def parse_tech_debt(repo_root: Path) -> Dict[str, List[str]]:
    """Parse tech-debt-tracker.md and extract high-priority items."""
    debt_file = repo_root / "docs/exec-plans/tech-debt-tracker.md"
    if not debt_file.exists():
        return {}

    content = debt_file.read_text()
    debt = {"high": [], "medium": [], "low": []}

    current_priority = None
    item_pattern = re.compile(r'^####\s+(.+)$', re.MULTILINE)

    # Find sections
    high_section = content.find("## High Priority")
    medium_section = content.find("## Medium Priority")
    low_section = content.find("## Low Priority")
    resolved_section = content.find("## Resolved")

    if high_section != -1:
        end = medium_section if medium_section != -1 else resolved_section
        high_content = content[high_section:end] if end != -1 else content[high_section:]
        debt["high"] = [m.group(1) for m in item_pattern.finditer(high_content)]

    if medium_section != -1:
        end = low_section if low_section != -1 else resolved_section
        medium_content = content[medium_section:end] if end != -1 else content[medium_section:]
        debt["medium"] = [m.group(1) for m in item_pattern.finditer(medium_content)]

    if low_section != -1:
        end = resolved_section if resolved_section != -1 else len(content)
        low_content = content[low_section:end]
        debt["low"] = [m.group(1) for m in item_pattern.finditer(low_content)]

    return debt


def parse_security_audit(repo_root: Path) -> Dict[str, int]:
    """Parse security audit files and count vulnerabilities by severity."""
    docs_dir = repo_root / "docs"
    if not docs_dir.exists():
        return {}

    audit_files = list(docs_dir.glob("security-audit-*.md"))
    if not audit_files:
        return {}

    # Use most recent audit file
    latest_audit = max(audit_files, key=lambda f: f.stat().st_mtime)
    content = latest_audit.read_text()

    vulnerabilities = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    # Count NEEDS DECISION or unfixed vulnerabilities
    critical_section = content.find("## Critical")
    high_section = content.find("## High")
    medium_section = content.find("## Medium")
    low_section = content.find("## Low")

    def count_unfixed(section_start, section_end):
        if section_start == -1:
            return 0
        section = content[section_start:section_end] if section_end != -1 else content[section_start:]
        # Count items with "Status: NEEDS DECISION" or not marked FIXED
        items = re.findall(r'^###\s+#\d+', section, re.MULTILINE)
        unfixed = 0
        for item in items:
            item_start = section.find(item)
            next_item = section.find('\n###', item_start + 1)
            item_content = section[item_start:next_item] if next_item != -1 else section[item_start:]
            if "Status: NEEDS DECISION" in item_content or ("Status: FIXED" not in item_content and "Status:" in item_content):
                unfixed += 1
        return unfixed

    vulnerabilities["critical"] = count_unfixed(critical_section, high_section)
    vulnerabilities["high"] = count_unfixed(high_section, medium_section)
    vulnerabilities["medium"] = count_unfixed(medium_section, low_section)
    vulnerabilities["low"] = count_unfixed(low_section, -1)

    return vulnerabilities


def parse_quality_score(repo_root: Path) -> Tuple[str, Dict[str, str]]:
    """Parse QUALITY_SCORE.md and extract overall grade and domain grades."""
    quality_file = repo_root / "docs/QUALITY_SCORE.md"
    if not quality_file.exists():
        return ("Unknown", {})

    content = quality_file.read_text()

    # Extract overall health grade
    overall_match = re.search(r'## Overall Health:\s+\*\*([A-F][+-]?)\*\*', content)
    overall_grade = overall_match.group(1) if overall_match else "Unknown"

    # Extract domain grades
    domain_pattern = re.compile(r'###\s+(.+?)\s+-\s+Grade:\s+\*\*([A-F])\*\*', re.MULTILINE)
    domains = {m.group(1): m.group(2) for m in domain_pattern.finditer(content)}

    return (overall_grade, domains)


def list_active_plans(repo_root: Path) -> List[str]:
    """List active execution plans."""
    active_dir = repo_root / "docs/exec-plans/active"
    if not active_dir.exists():
        return []

    plans = []
    for plan_file in active_dir.glob("*.md"):
        # Extract title from first # heading
        content = plan_file.read_text()
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else plan_file.stem
        plans.append(f"{plan_file.name}: {title}")

    return plans


def get_agents_md_summary(repo_root: Path) -> str:
    """Extract quick summary from AGENTS.md if available."""
    agents_file = repo_root / "AGENTS.md"
    if not agents_file.exists():
        return "No AGENTS.md found"

    content = agents_file.read_text()
    lines = content.splitlines()

    # Get first heading and first few non-empty lines
    summary_lines = []
    for line in lines[:15]:
        if line.strip():
            summary_lines.append(line)
        if len(summary_lines) >= 5:
            break

    return "\n".join(summary_lines)


def main():
    repo_root = Path.cwd()

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])

    if not repo_root.exists():
        print(f"{Colors.RED}❌ Repository not found: {repo_root}{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}PROJECT STATUS OVERVIEW{Colors.NC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
    print()

    # Project summary from AGENTS.md
    print(f"{Colors.BOLD}{Colors.BLUE}📋 PROJECT{Colors.NC}")
    print(get_agents_md_summary(repo_root))
    print()

    # Quality score
    print(f"{Colors.BOLD}{Colors.BLUE}📊 QUALITY{Colors.NC}")
    overall_grade, domain_grades = parse_quality_score(repo_root)

    grade_color = Colors.GREEN if overall_grade.startswith('A') else Colors.YELLOW if overall_grade.startswith('B') else Colors.RED
    print(f"Overall Grade: {grade_color}{overall_grade}{Colors.NC}")

    if domain_grades:
        print("\nDomain Grades:")
        for domain, grade in sorted(domain_grades.items(), key=lambda x: x[1]):
            domain_color = Colors.GREEN if grade == 'A' else Colors.YELLOW if grade == 'B' else Colors.RED
            print(f"  {domain_color}{grade}{Colors.NC} - {domain}")
    print()

    # Security vulnerabilities
    print(f"{Colors.BOLD}{Colors.BLUE}🔒 SECURITY{Colors.NC}")
    vulns = parse_security_audit(repo_root)

    if vulns:
        total_vulns = sum(vulns.values())
        if total_vulns == 0:
            print(f"{Colors.GREEN}✅ No open vulnerabilities{Colors.NC}")
        else:
            print(f"Open Vulnerabilities: {total_vulns}")
            if vulns['critical'] > 0:
                print(f"  {Colors.RED}🔴 Critical: {vulns['critical']}{Colors.NC}")
            if vulns['high'] > 0:
                print(f"  {Colors.YELLOW}🟡 High: {vulns['high']}{Colors.NC}")
            if vulns['medium'] > 0:
                print(f"  Medium: {vulns['medium']}")
            if vulns['low'] > 0:
                print(f"  Low: {vulns['low']}")
    else:
        print("No security audit found")
    print()

    # Tech debt
    print(f"{Colors.BOLD}{Colors.BLUE}⚠️  TECH DEBT{Colors.NC}")
    debt = parse_tech_debt(repo_root)

    if debt:
        total_debt = len(debt.get('high', [])) + len(debt.get('medium', [])) + len(debt.get('low', []))
        if total_debt == 0:
            print(f"{Colors.GREEN}✅ No tracked tech debt{Colors.NC}")
        else:
            print(f"Total Items: {total_debt}")

            if debt.get('high'):
                print(f"\n{Colors.RED}High Priority ({len(debt['high'])}){Colors.NC}:")
                for item in debt['high'][:5]:  # Show first 5
                    print(f"  • {item}")
                if len(debt['high']) > 5:
                    print(f"  ... and {len(debt['high']) - 5} more")

            if debt.get('medium'):
                print(f"\n{Colors.YELLOW}Medium Priority ({len(debt['medium'])}){Colors.NC}:")
                for item in debt['medium'][:3]:  # Show first 3
                    print(f"  • {item}")
                if len(debt['medium']) > 3:
                    print(f"  ... and {len(debt['medium']) - 3} more")

            if debt.get('low'):
                print(f"\nLow Priority: {len(debt['low'])} items")
    else:
        print("No tech debt tracker found")
    print()

    # Active plans
    print(f"{Colors.BOLD}{Colors.BLUE}🚀 ACTIVE WORK{Colors.NC}")
    plans = list_active_plans(repo_root)

    if plans:
        print(f"Active Plans ({len(plans)}):")
        for plan in plans:
            print(f"  • {plan}")
    else:
        print("No active execution plans")
    print()

    # Quick reference
    print(f"{Colors.BOLD}{Colors.BLUE}📚 QUICK REFERENCE{Colors.NC}")
    print(f"  Architecture:     {repo_root}/ARCHITECTURE.md")
    print(f"  Core beliefs:     {repo_root}/docs/design-docs/core-beliefs.md")
    print(f"  Tech debt:        {repo_root}/docs/exec-plans/tech-debt-tracker.md")
    print(f"  Quality scores:   {repo_root}/docs/QUALITY_SCORE.md")
    print(f"  Security:         {repo_root}/docs/SECURITY.md")
    print()

    print(f"{Colors.BOLD}{'='*80}{Colors.NC}")


if __name__ == "__main__":
    main()
