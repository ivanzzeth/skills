#!/usr/bin/env python3
"""
Code TODO Scanner

Scans source code for TODO, FIXME, HACK, XXX, BUG, NOTE annotations.
Helps discover unfinished features and technical debt in code.

Usage:
    python code_todos.py <project_root>
    python code_todos.py <project_root> --format json
    python code_todos.py <project_root> --priority high

Supported annotations:
    BUG, FIXME    - High priority (bugs/broken code)
    TODO, XXX     - Medium priority (planned work)
    HACK, NOTE    - Low priority (warnings/explanations)
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import json


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'


class Annotation:
    PRIORITY = {
        'BUG': 1,
        'FIXME': 1,
        'TODO': 2,
        'XXX': 2,
        'HACK': 3,
        'NOTE': 3,
        'OPTIMIZE': 2,
    }

    COLORS = {
        1: Colors.RED,      # High priority
        2: Colors.YELLOW,   # Medium priority
        3: Colors.CYAN,     # Low priority
    }

    def __init__(self, file_path: Path, line_num: int, tag: str, message: str, code_context: str = ""):
        self.file_path = file_path
        self.line_num = line_num
        self.tag = tag.upper()
        self.message = message.strip()
        self.code_context = code_context
        self.priority = self.PRIORITY.get(self.tag, 2)

    def to_dict(self):
        return {
            'file': str(self.file_path),
            'line': self.line_num,
            'tag': self.tag,
            'priority': self.priority,
            'message': self.message,
            'context': self.code_context,
        }

    def __str__(self):
        color = self.COLORS.get(self.priority, Colors.NC)
        return f"{color}{self.file_path}:{self.line_num} [{self.tag}]{Colors.NC} {self.message}"


def find_annotations(project_root: Path) -> List[Annotation]:
    """
    Scan source code for annotations.

    Supports:
    - Single-line comments: // TODO, # TODO
    - Multi-line comments: /* TODO */
    - Inline comments: func() // TODO
    """
    annotations = []

    # Source file patterns
    patterns = {
        "**/*.go",
        "**/*.py",
        "**/*.js",
        "**/*.ts",
        "**/*.tsx",
        "**/*.jsx",
        "**/*.rs",
        "**/*.java",
        "**/*.cpp",
        "**/*.c",
        "**/*.h",
        "**/*.sh",
    }

    exclude_dirs = {
        "node_modules", ".git", "vendor", "dist", "build",
        "__pycache__", ".venv", "venv", "target", ".next",
        "coverage", ".pytest_cache", ".mypy_cache"
    }

    # Annotation pattern: matches TODO: message, TODO(user): message, TODO - message
    # Captures: (TAG) optional(user) separator message
    annotation_regex = re.compile(
        r'\b(TODO|FIXME|HACK|XXX|BUG|NOTE|OPTIMIZE)(?:\(([^)]+)\))?[:\s-]+(.+)',
        re.IGNORECASE
    )

    files = []
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            files.append(file_path)

    for file_path in files:
        try:
            lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()

            for line_num, line in enumerate(lines, 1):
                match = annotation_regex.search(line)
                if match:
                    tag = match.group(1).upper()
                    user = match.group(2) or ""
                    message = match.group(3).strip()

                    # Include user in message if present
                    if user:
                        message = f"({user}) {message}"

                    # Get code context (the line without comment)
                    code_context = line.split('//', 1)[0].split('#', 1)[0].strip()

                    annotation = Annotation(
                        file_path=file_path.relative_to(project_root),
                        line_num=line_num,
                        tag=tag,
                        message=message,
                        code_context=code_context
                    )
                    annotations.append(annotation)

        except Exception as e:
            print(f"{Colors.RED}Error reading {file_path}: {e}{Colors.NC}", file=sys.stderr)

    return annotations


def print_report(annotations: List[Annotation], priority_filter: str = None):
    """
    Print human-readable report.

    Groups annotations by:
    1. Priority (high/medium/low)
    2. File
    """
    if not annotations:
        print(f"{Colors.GREEN}✅ No code annotations found{Colors.NC}")
        return

    # Filter by priority if requested
    if priority_filter:
        priority_map = {'high': 1, 'medium': 2, 'low': 3}
        target_priority = priority_map.get(priority_filter.lower())
        if target_priority:
            annotations = [a for a in annotations if a.priority == target_priority]

    if not annotations:
        print(f"{Colors.GREEN}✅ No {priority_filter} priority annotations found{Colors.NC}")
        return

    # Group by priority
    by_priority = defaultdict(list)
    for annotation in annotations:
        by_priority[annotation.priority].append(annotation)

    # Print summary
    print(f"{Colors.BOLD}Code Annotations Summary{Colors.NC}")
    print(f"Total: {len(annotations)} annotations\n")

    priority_names = {1: 'High Priority (BUG, FIXME)', 2: 'Medium Priority (TODO, XXX)', 3: 'Low Priority (HACK, NOTE)'}

    for priority in sorted(by_priority.keys()):
        items = by_priority[priority]
        color = Annotation.COLORS[priority]
        print(f"{color}{Colors.BOLD}{priority_names[priority]} - {len(items)} items{Colors.NC}\n")

        # Group by file
        by_file = defaultdict(list)
        for item in items:
            by_file[item.file_path].append(item)

        for file_path in sorted(by_file.keys()):
            file_items = by_file[file_path]
            print(f"  {Colors.BOLD}{file_path}{Colors.NC} ({len(file_items)} items)")

            for item in sorted(file_items, key=lambda x: x.line_num):
                print(f"    {item.line_num:4d}: [{item.tag}] {item.message}")

            print()

    # Priority breakdown
    print(f"\n{Colors.BOLD}Priority Breakdown:{Colors.NC}")
    for priority in sorted(by_priority.keys()):
        count = len(by_priority[priority])
        color = Annotation.COLORS[priority]
        priority_name = priority_names[priority].split(' - ')[0]
        print(f"  {color}●{Colors.NC} {priority_name}: {count}")


def print_json(annotations: List[Annotation]):
    """Print JSON output for programmatic consumption."""
    output = {
        'total': len(annotations),
        'by_priority': {},
        'annotations': [a.to_dict() for a in annotations]
    }

    # Count by priority
    for annotation in annotations:
        priority_name = {1: 'high', 2: 'medium', 3: 'low'}[annotation.priority]
        if priority_name not in output['by_priority']:
            output['by_priority'][priority_name] = 0
        output['by_priority'][priority_name] += 1

    print(json.dumps(output, indent=2))


def main():
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Usage: {sys.argv[0]} <project_root> [--format json] [--priority high|medium|low]{Colors.NC}")
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    output_format = 'text'
    priority_filter = None

    # Parse arguments
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == '--format' and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
        elif arg == '--priority' and i + 1 < len(sys.argv):
            priority_filter = sys.argv[i + 1]

    if not project_root.exists():
        print(f"{Colors.RED}Error: {project_root} not found{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.BLUE}Scanning code annotations in: {project_root}{Colors.NC}\n")

    annotations = find_annotations(project_root)

    if output_format == 'json':
        print_json(annotations)
    else:
        print_report(annotations, priority_filter)

    # Exit code based on high-priority items
    high_priority_count = sum(1 for a in annotations if a.priority == 1)
    if high_priority_count > 0:
        print(f"\n{Colors.YELLOW}⚠️  {high_priority_count} high-priority items (BUG, FIXME) found{Colors.NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
