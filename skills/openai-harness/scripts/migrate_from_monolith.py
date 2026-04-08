#!/usr/bin/env python3
"""
Migrate from monolithic AGENTS.md to progressive disclosure structure.

Analyzes existing AGENTS.md and suggests where content should be moved.
Can optionally execute the migration automatically.
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'


class Section:
    def __init__(self, level: int, title: str, content: str, line_start: int):
        self.level = level
        self.title = title
        self.content = content
        self.line_start = line_start
        self.suggested_location = None
        self.reason = None


def parse_markdown_sections(content: str) -> List[Section]:
    """Parse markdown file into sections based on headings."""
    lines = content.splitlines()
    sections = []
    current_section = None

    for i, line in enumerate(lines):
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if heading_match:
            # Save previous section
            if current_section:
                sections.append(current_section)

            # Start new section
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            current_section = Section(level, title, "", i + 1)
        elif current_section:
            current_section.content += line + "\n"

    # Don't forget last section
    if current_section:
        sections.append(current_section)

    return sections


def analyze_section(section: Section) -> Tuple[str, str]:
    """
    Analyze a section and suggest where it should be moved.

    Returns: (suggested_location, reason)
    """
    title_lower = section.title.lower()
    content_lower = section.content.lower()

    # Keep in AGENTS.md (navigation/overview)
    if section.level == 1:
        return ("AGENTS.md", "Top-level title - keep in AGENTS.md")

    if any(keyword in title_lower for keyword in ["overview", "quick start", "navigation", "references"]):
        return ("AGENTS.md", "Navigation/overview section")

    if len(section.content.strip()) < 200:  # Very short section
        return ("AGENTS.md", "Brief section - can stay in AGENTS.md")

    # Architecture
    if any(keyword in title_lower for keyword in ["architecture", "system design", "layers", "domains", "modules"]):
        return ("ARCHITECTURE.md", "Architectural content")

    if "depends on" in content_lower or "layer" in content_lower:
        return ("ARCHITECTURE.md", "Describes dependencies/layers")

    # Design decisions
    if any(keyword in title_lower for keyword in ["decision", "why we", "trade-off", "alternatives"]):
        return ("docs/design-docs/{slug}.md", "Design decision - create dedicated doc")

    if "we chose" in content_lower or "decided to" in content_lower:
        return ("docs/design-docs/{slug}.md", "Contains design rationale")

    # Product specs
    if any(keyword in title_lower for keyword in ["feature", "requirements", "user story", "acceptance criteria"]):
        return ("docs/product-specs/{slug}.md", "Product requirement")

    # Security
    if any(keyword in title_lower for keyword in ["security", "auth", "vulnerability", "threat"]):
        return ("docs/SECURITY.md", "Security-related content")

    # Reliability
    if any(keyword in title_lower for keyword in ["reliability", "slo", "monitoring", "alerting", "incident"]):
        return ("docs/RELIABILITY.md", "Reliability/operations content")

    # Golden principles / coding standards
    if any(keyword in title_lower for keyword in ["principles", "standards", "conventions", "best practices", "rules"]):
        return ("docs/design-docs/core-beliefs.md", "Coding principles/standards")

    if "must" in content_lower and "never" in content_lower:
        return ("docs/design-docs/core-beliefs.md", "Contains mandatory rules")

    # External references
    if "http://" in content_lower or "https://" in content_lower:
        if content_lower.count("http") > 3:
            return ("docs/references/{topic}-llms.txt", "Multiple external links - reference material")

    # Default: if section is long, move to docs/DESIGN.md
    if len(section.content.strip()) > 500:
        return ("docs/DESIGN.md", "Long detailed section - move to DESIGN.md")

    return ("AGENTS.md", "Keep in AGENTS.md (unclear where else)")


def generate_slug(title: str) -> str:
    """Generate filename-safe slug from title."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')
    return slug


def main():
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Usage: {sys.argv[0]} <path/to/AGENTS.md> [--execute]{Colors.NC}")
        print()
        print("  --execute: Actually perform the migration (default: dry-run)")
        sys.exit(1)

    agents_md_path = Path(sys.argv[1])
    execute = "--execute" in sys.argv

    if not agents_md_path.exists():
        print(f"{Colors.RED}❌ File not found: {agents_md_path}{Colors.NC}")
        sys.exit(1)

    repo_root = agents_md_path.parent

    print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}AGENTS.MD MIGRATION ANALYZER{Colors.NC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
    print()

    # Read and parse AGENTS.md
    content = agents_md_path.read_text()
    sections = parse_markdown_sections(content)

    print(f"📄 Analyzing: {agents_md_path}")
    print(f"📊 Found {len(sections)} sections")
    print()

    # Analyze each section
    migration_plan = {}
    for section in sections:
        location, reason = analyze_section(section)
        section.suggested_location = location
        section.reason = reason

        if location not in migration_plan:
            migration_plan[location] = []
        migration_plan[location].append(section)

    # Print migration plan
    print(f"{Colors.BOLD}{Colors.BLUE}MIGRATION PLAN{Colors.NC}")
    print()

    # Sort by location
    keep_in_agents = migration_plan.get("AGENTS.md", [])
    move_to_other = {k: v for k, v in migration_plan.items() if k != "AGENTS.md"}

    if keep_in_agents:
        print(f"{Colors.GREEN}✅ KEEP IN AGENTS.MD ({len(keep_in_agents)} sections){Colors.NC}")
        for section in keep_in_agents:
            print(f"  • {section.title} ({len(section.content)} chars)")
            print(f"    Reason: {section.reason}")
        print()

    if move_to_other:
        print(f"{Colors.YELLOW}📦 TO BE MOVED ({sum(len(v) for v in move_to_other.values())} sections){Colors.NC}")
        print()

        for location in sorted(move_to_other.keys()):
            sections_list = move_to_other[location]
            print(f"  {Colors.BOLD}{location}{Colors.NC} ({len(sections_list)} sections):")
            for section in sections_list:
                slug = generate_slug(section.title)
                actual_location = location.replace("{slug}", slug)
                print(f"    • {section.title}")
                print(f"      → {actual_location}")
                print(f"      Reason: {section.reason}")
            print()

    # Calculate reduction
    total_chars = len(content)
    keep_chars = sum(len(s.content) for s in keep_in_agents)
    move_chars = total_chars - keep_chars

    print(f"{Colors.BOLD}SUMMARY{Colors.NC}")
    print(f"  Original size: {total_chars} chars")
    print(f"  Keep in AGENTS.md: {keep_chars} chars ({keep_chars*100//total_chars}%)")
    print(f"  Move to docs/: {move_chars} chars ({move_chars*100//total_chars}%)")
    print()

    # Target check
    if keep_chars > 3000:
        print(f"{Colors.YELLOW}⚠️  AGENTS.md will still be {keep_chars} chars (target: ~2000){Colors.NC}")
        print(f"   Consider moving more content to docs/")
    else:
        print(f"{Colors.GREEN}✅ AGENTS.md will be {keep_chars} chars (within target){Colors.NC}")
    print()

    if execute:
        print(f"{Colors.BOLD}{Colors.RED}🚀 EXECUTING MIGRATION{Colors.NC}")
        print(f"{Colors.YELLOW}This will modify files. Commit your work first!{Colors.NC}")
        print()

        # Check if working directory is clean
        import subprocess
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=repo_root
            )
            if result.returncode == 0 and result.stdout.strip():
                print(f"{Colors.YELLOW}⚠️  Warning: You have uncommitted changes.{Colors.NC}")
                response = input("Continue anyway? [y/N]: ")
                if response.lower() != 'y':
                    print("Migration cancelled.")
                    sys.exit(0)
        except Exception:
            print(f"{Colors.YELLOW}⚠️  Warning: Could not check git status.{Colors.NC}")

        # Backup original AGENTS.md
        import shutil
        from datetime import datetime
        backup_name = f"AGENTS.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = repo_root / backup_name
        shutil.copy2(agents_md_path, backup_path)
        print(f"✅ Backup created: {backup_name}")
        print()

        # Execute migration
        files_created = []
        files_updated = []

        # 1. Create target files and move content
        for location in sorted(move_to_other.keys()):
            sections_list = move_to_other[location]

            for section in sections_list:
                # Determine actual file path
                if "{slug}" in location:
                    slug = generate_slug(section.title)
                    actual_location = location.replace("{slug}", slug)
                else:
                    actual_location = location

                target_path = repo_root / actual_location

                # Create directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Prepare content
                section_content = f"# {section.title}\n\n{section.content.strip()}\n"

                # Append or create file
                if target_path.exists():
                    # Append to existing file
                    existing_content = target_path.read_text()
                    if section.title not in existing_content:
                        target_path.write_text(existing_content + "\n\n" + section_content)
                        files_updated.append(actual_location)
                        print(f"📝 Updated: {actual_location}")
                else:
                    # Create new file
                    target_path.write_text(section_content)
                    files_created.append(actual_location)
                    print(f"✅ Created: {actual_location}")

        print()

        # 2. Update AGENTS.md - keep only sections that should stay
        new_agents_content = f"# {sections[0].title}\n\n"  # Keep title

        for section in keep_in_agents:
            if section.level == 1:
                continue  # Skip title (already added)
            heading = "#" * section.level + " " + section.title
            new_agents_content += f"{heading}\n\n{section.content.strip()}\n\n"

        # 3. Add navigation links for moved sections
        new_agents_content += "\n## Detailed Documentation\n\n"
        new_agents_content += "The following topics have been moved to detailed documentation:\n\n"

        for location in sorted(move_to_other.keys()):
            if "{slug}" in location:
                for section in move_to_other[location]:
                    slug = generate_slug(section.title)
                    actual_location = location.replace("{slug}", slug)
                    new_agents_content += f"- **[{section.title}](./{actual_location})** - {section.reason}\n"
            else:
                section_titles = [s.title for s in move_to_other[location]]
                new_agents_content += f"- **[{location}](./{location})** - {', '.join(section_titles[:3])}\n"

        # Write new AGENTS.md
        agents_md_path.write_text(new_agents_content)
        print(f"📝 Updated: AGENTS.md")
        print()

        # Summary
        print(f"{Colors.GREEN}✅ Migration completed!{Colors.NC}")
        print()
        print(f"Files created: {len(files_created)}")
        for f in files_created:
            print(f"  + {f}")
        print()
        if files_updated:
            print(f"Files updated: {len(files_updated)}")
            for f in files_updated:
                print(f"  ~ {f}")
            print()
        print(f"Backup: {backup_name}")
        print()
        print(f"Next steps:")
        print(f"  1. Review changes: git diff")
        print(f"  2. Validate: python scripts/lint/validate_docs.py")
        print(f"  3. Commit if satisfied: git add . && git commit -m 'Refactor AGENTS.md to progressive disclosure'")
        print(f"  4. Or restore backup: cp {backup_name} AGENTS.md")
        print()
    else:
        print(f"{Colors.BLUE}💡 This is a dry-run. Add --execute to perform migration.{Colors.NC}")
        print()
        print(f"Next steps:")
        print(f"  1. Review the migration plan above")
        print(f"  2. Manually create target files and move content")
        print(f"  3. OR run with --execute (when implemented)")
        print()


if __name__ == "__main__":
    main()
