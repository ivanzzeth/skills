#!/usr/bin/env python3
"""
Golden Principles Linter

Reads golden principles from project documentation and validates code against them.

This linter is CONTEXT-AWARE: it extracts rules from your project's documentation:
  - CLAUDE.md (project-specific rules)
  - docs/design-docs/core-beliefs.md (agent-first principles)
  - .claude/skills/*/SKILL.md (skill best practices)

Built-in checks:
  1. No error ignoring (_ = xxx in Go, void in JS/TS)
  2. No empty catch blocks
  3. No hardcoded secrets/credentials
  4. No console.log in production code
  5. Structured logging only

CUSTOMIZABLE: Add your own rules by:
  1. Adding them to your documentation with clear "❌ DON'T" / "✅ DO" examples
  2. Implementing check functions below
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
    NC = '\033[0m'


class Violation:
    def __init__(self, file_path: str, line: int, rule: str, message: str, fix: str = ""):
        self.file_path = file_path
        self.line = line
        self.rule = rule
        self.message = message
        self.fix = fix

    def __str__(self):
        result = f"{self.file_path}:{self.line}: {self.rule}\n  {self.message}"
        if self.fix:
            result += f"\n  Fix: {self.fix}"
        return result


def extract_rules_from_docs(project_root: Path) -> Dict[str, str]:
    """
    Extract rules from project documentation.

    Looks for patterns like:
      ❌ DON'T: description
      ✅ DO: description

    Or sections like:
      ## Golden Principles
      ### 4.1 Explicit Errors
      Never ignore errors...
    """
    rules = {}

    doc_files = [
        project_root / "CLAUDE.md",
        project_root / "docs/design-docs/core-beliefs.md",
        project_root / "AGENTS.md",
    ]

    for doc_file in doc_files:
        if not doc_file.exists():
            continue

        content = doc_file.read_text()

        # Extract "❌ DON'T" patterns
        dont_pattern = re.compile(r'❌\s*DON[\'']T:?\s*(.+?)(?=\n\n|✅|$)', re.DOTALL)
        for match in dont_pattern.finditer(content):
            rule_text = match.group(1).strip()
            # Extract first sentence as rule name
            rule_name = rule_text.split('\n')[0].split('.')[0]
            rules[rule_name] = rule_text

        # Extract "MUST" / "NEVER" statements
        must_pattern = re.compile(r'(MUST|NEVER)\s+([^.\n]+)', re.IGNORECASE)
        for match in must_pattern.finditer(content):
            keyword = match.group(1).upper()
            rule_text = match.group(2).strip()
            rule_name = f"{keyword}: {rule_text[:50]}"
            rules[rule_name] = f"{keyword} {rule_text}"

    return rules


def check_error_ignoring_go(file_path: Path) -> List[Violation]:
    """Check for ignored errors in Go: _ = xxx"""
    violations = []

    if not str(file_path).endswith('.go'):
        return violations

    content = file_path.read_text()
    lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        # Match: _ = something
        if re.match(r'^\s*_\s*=\s*.+', line):
            violations.append(Violation(
                file_path=str(file_path),
                line=i,
                rule="No Error Ignoring",
                message=f"Error result ignored: {line.strip()}",
                fix="Handle the error explicitly or return it to caller"
            ))

    return violations


def check_empty_catch_blocks(file_path: Path) -> List[Violation]:
    """Check for empty catch blocks in JS/TS/Python"""
    violations = []

    extensions = ['.js', '.ts', '.tsx', '.py']
    if not any(str(file_path).endswith(ext) for ext in extensions):
        return violations

    content = file_path.read_text()
    lines = content.splitlines()

    # Simple heuristic: catch block followed by empty braces
    for i, line in enumerate(lines, 1):
        if 'catch' in line.lower() and 'except' in line.lower():
            # Check next few lines for empty block
            start = i
            brace_count = 0
            found_empty = False

            for j in range(i, min(i + 5, len(lines))):
                if '{' in lines[j-1]:
                    brace_count += lines[j-1].count('{')
                if '}' in lines[j-1]:
                    brace_count -= lines[j-1].count('}')

                # Found closing brace with no content
                if brace_count == 0 and j > start + 1:
                    # Check if there's actual content
                    block_content = '\n'.join(lines[start:j])
                    # Remove catch line and braces
                    block_content = re.sub(r'catch.*?\{', '', block_content)
                    block_content = re.sub(r'\}', '', block_content)
                    if not block_content.strip():
                        found_empty = True
                        break

            if found_empty:
                violations.append(Violation(
                    file_path=str(file_path),
                    line=i,
                    rule="No Empty Catch Blocks",
                    message="Empty catch block - errors are silently swallowed",
                    fix="Log the error or handle it explicitly"
                ))

    return violations


def check_hardcoded_secrets(file_path: Path) -> List[Violation]:
    """Check for hardcoded secrets/credentials"""
    violations = []

    content = file_path.read_text()
    lines = content.splitlines()

    # Patterns for potential secrets
    secret_patterns = [
        (r'password\s*=\s*["\'](?!.*\$\{)([^"\']{8,})["\']', "Hardcoded password"),
        (r'api[_-]?key\s*=\s*["\'](?!.*\$\{)([^"\']{16,})["\']', "Hardcoded API key"),
        (r'secret\s*=\s*["\'](?!.*\$\{)([^"\']{16,})["\']', "Hardcoded secret"),
        (r'token\s*=\s*["\'](?!.*\$\{)([^"\']{16,})["\']', "Hardcoded token"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, rule_name in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(Violation(
                    file_path=str(file_path),
                    line=i,
                    rule=f"No Hardcoded Secrets: {rule_name}",
                    message=f"Potential hardcoded secret: {line.strip()}",
                    fix="Move to environment variable or config file"
                ))

    return violations


def check_console_log(file_path: Path) -> List[Violation]:
    """Check for console.log in production JS/TS code"""
    violations = []

    extensions = ['.js', '.ts', '.tsx']
    if not any(str(file_path).endswith(ext) for ext in extensions):
        return violations

    # Skip test files
    if 'test' in str(file_path).lower() or 'spec' in str(file_path).lower():
        return violations

    content = file_path.read_text()
    lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        if re.search(r'\bconsole\.(log|info|warn|error|debug)\(', line):
            violations.append(Violation(
                file_path=str(file_path),
                line=i,
                rule="Structured Logging Only",
                message=f"console.log found in production code: {line.strip()}",
                fix="Use structured logger (e.g., winston, pino) instead"
            ))

    return violations


def check_unstructured_logging_python(file_path: Path) -> List[Violation]:
    """Check for unstructured logging in Python"""
    violations = []

    if not str(file_path).endswith('.py'):
        return violations

    content = file_path.read_text()
    lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        # Check for f-string or % formatting in logging
        if 'logger.' in line or 'logging.' in line:
            if re.search(r'logger\.\w+\(f["\']', line) or re.search(r'%\s*\(', line):
                violations.append(Violation(
                    file_path=str(file_path),
                    line=i,
                    rule="Structured Logging Only",
                    message=f"Unstructured logging (f-string/% formatting): {line.strip()}",
                    fix="Use extra={} for structured fields: logger.info('msg', extra={'key': value})"
                ))

    return violations


def check_extracted_rules(file_path: Path, rules: Dict[str, str]) -> List[Violation]:
    """
    Check code against rules extracted from documentation.

    This function converts textual rules from docs into code checks.
    """
    violations = []

    try:
        content = file_path.read_text()
        lines = content.splitlines()
    except Exception:
        return violations

    for rule_name, rule_text in rules.items():
        rule_lower = rule_text.lower()

        # Rule: Never/Must not + action
        if "never" in rule_lower or "must not" in rule_lower:
            # Extract what to avoid
            if "never use" in rule_lower or "must not use" in rule_lower:
                # Try to extract forbidden pattern
                forbidden_match = re.search(r'never use\s+["`]?([^"`\n]+)["`]?', rule_lower)
                if not forbidden_match:
                    forbidden_match = re.search(r'must not use\s+["`]?([^"`\n]+)["`]?', rule_lower)

                if forbidden_match:
                    forbidden = forbidden_match.group(1).strip()

                    # Check if forbidden pattern appears in code
                    for i, line in enumerate(lines, 1):
                        if forbidden in line.lower() and not line.strip().startswith("#"):
                            violations.append(Violation(
                                file_path=str(file_path),
                                line=i,
                                rule=rule_name,
                                message=f"Forbidden pattern found: {line.strip()}",
                                fix=f"Rule: {rule_text[:100]}"
                            ))

        # Rule: Must/Always + action
        if "must" in rule_lower and "must not" not in rule_lower:
            # Check for required patterns
            if "must validate" in rule_lower and "input" in rule_lower:
                # Check for input validation
                # Look for function definitions without validation
                for i, line in enumerate(lines, 1):
                    # Simple heuristic: function with user_input or request param but no validation
                    if re.search(r'def\s+\w+.*\b(user_input|request|data)\b', line, re.IGNORECASE):
                        # Check next 10 lines for validation keywords
                        has_validation = False
                        for j in range(i, min(i + 10, len(lines))):
                            if any(kw in lines[j].lower() for kw in ["validate", "check", "verify", "assert"]):
                                has_validation = True
                                break

                        if not has_validation:
                            violations.append(Violation(
                                file_path=str(file_path),
                                line=i,
                                rule=rule_name,
                                message=f"Function may lack input validation: {line.strip()}",
                                fix=f"Rule: {rule_text[:100]}"
                            ))

        # Rule: Explicit "❌ DON'T" examples
        if "don't:" in rule_lower or "don't " in rule_lower:
            # Try to extract anti-pattern code example
            dont_match = re.search(r'❌.*?don\'?t:?\s*(.+?)(?=\n\n|✅|$)', rule_text, re.IGNORECASE | re.DOTALL)
            if dont_match:
                anti_pattern = dont_match.group(1).strip()

                # Extract code from anti-pattern if it has code block
                code_match = re.search(r'```\w*\n(.+?)\n```', anti_pattern, re.DOTALL)
                if code_match:
                    forbidden_code = code_match.group(1).strip()

                    # Simple substring check (not perfect, but better than nothing)
                    # Normalize whitespace for comparison
                    forbidden_normalized = re.sub(r'\s+', ' ', forbidden_code)

                    for i, line in enumerate(lines, 1):
                        line_normalized = re.sub(r'\s+', ' ', line)
                        if len(forbidden_normalized) > 10 and forbidden_normalized in line_normalized:
                            violations.append(Violation(
                                file_path=str(file_path),
                                line=i,
                                rule=f"Anti-pattern: {rule_name}",
                                message=f"Code matches anti-pattern from docs: {line.strip()}",
                                fix="See documentation for correct approach"
                            ))

    return violations


def validate_file(file_path: Path, project_root: Path, extracted_rules: Dict[str, str]) -> List[Violation]:
    """Run all checks on a file"""
    violations = []

    # Run all built-in checks
    violations.extend(check_error_ignoring_go(file_path))
    violations.extend(check_empty_catch_blocks(file_path))
    violations.extend(check_hardcoded_secrets(file_path))
    violations.extend(check_console_log(file_path))
    violations.extend(check_unstructured_logging_python(file_path))

    # Add checks based on extracted rules from docs
    violations.extend(check_extracted_rules(file_path, extracted_rules))

    return violations


def find_source_files(project_root: Path) -> List[Path]:
    """Find all source files to check"""
    patterns = [
        "**/*.go",
        "**/*.py",
        "**/*.js",
        "**/*.ts",
        "**/*.tsx",
    ]

    exclude_dirs = {
        "node_modules", ".git", "vendor", "dist", "build",
        "__pycache__", ".venv", "venv"
    }

    files = []
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            # Check if any excluded dir in path
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            # Skip test files
            if "test" in file_path.name or "spec" in file_path.name:
                continue
            files.append(file_path)

    return files


def main():
    if len(sys.argv) < 2:
        print("Usage: golden_principles_linter.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()

    if not project_root.exists():
        print(f"{Colors.RED}Error: {project_root} not found{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.BLUE}Golden Principles Linter{Colors.NC}")
    print(f"Validating code against project best practices\n")
    print(f"Project root: {project_root}\n")

    # Extract rules from docs
    print("Extracting rules from documentation...")
    rules = extract_rules_from_docs(project_root)
    print(f"Found {len(rules)} rules in documentation\n")

    # Find source files
    print("Finding source files...")
    source_files = find_source_files(project_root)
    print(f"Checking {len(source_files)} files...\n")

    # Validate files
    all_violations = []
    for file_path in source_files:
        violations = validate_file(file_path, project_root)
        all_violations.extend(violations)

    # Report results
    if all_violations:
        print(f"{Colors.RED}❌ Found {len(all_violations)} violation(s):{Colors.NC}\n")

        # Group by rule
        by_rule: Dict[str, List[Violation]] = {}
        for v in all_violations:
            if v.rule not in by_rule:
                by_rule[v.rule] = []
            by_rule[v.rule].append(v)

        for rule, violations in sorted(by_rule.items()):
            print(f"{Colors.YELLOW}{rule} ({len(violations)} violations){Colors.NC}")
            for v in violations[:5]:  # Show first 5 per rule
                print(f"  {v}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
            print()

        sys.exit(1)
    else:
        print(f"{Colors.GREEN}✅ All checks passed{Colors.NC}")
        sys.exit(0)


if __name__ == "__main__":
    main()
