#!/usr/bin/env python3
"""
Observability Validation Linter

Validates that services follow observability best practices:
- Expose /metrics endpoint for Prometheus
- Use structured logging (JSON format)
- Define health check endpoints
- Document metrics in code/docs

This is a STRUCTURAL validator (not implementation).
For implementation details, use monitoring-observability skill.

Usage:
    python validate_observability.py <project_root>
    python validate_observability.py <project_root> --check metrics
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Set
import json


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warning(self, msg: str):
        self.warnings.append(msg)

    def success(self, msg: str):
        self.passed.append(msg)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_summary(self):
        if self.passed:
            print(f"\n{Colors.GREEN}✅ Passed ({len(self.passed)}){Colors.NC}")
            for msg in self.passed:
                print(f"  {msg}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  Warnings ({len(self.warnings)}){Colors.NC}")
            for msg in self.warnings:
                print(f"  {msg}")

        if self.errors:
            print(f"\n{Colors.RED}❌ Errors ({len(self.errors)}){Colors.NC}")
            for msg in self.errors:
                print(f"  {msg}")


def check_metrics_endpoint(project_root: Path, result: ValidationResult):
    """
    Check if service exposes /metrics endpoint.

    Looks for:
    - HTTP route registration: /metrics
    - Prometheus library imports
    - Metrics handler setup
    """
    print(f"{Colors.BLUE}Checking metrics endpoint...{Colors.NC}")

    # Language-specific patterns
    patterns = {
        'go': [
            (r'/metrics', 'Route /metrics'),
            (r'prometheus\.', 'Prometheus import'),
            (r'promhttp\.Handler', 'Prometheus HTTP handler'),
        ],
        'python': [
            (r'/metrics', 'Route /metrics'),
            (r'from prometheus_client', 'Prometheus client import'),
            (r'generate_latest|MetricsHandler', 'Metrics handler'),
        ],
        'javascript': [
            (r'/metrics', 'Route /metrics'),
            (r'prom-client|prometheus', 'Prometheus client'),
            (r'register\.metrics', 'Metrics registration'),
        ],
    }

    found_lang = None
    found_patterns = set()

    # Search source files
    for ext, lang in [('.go', 'go'), ('.py', 'python'), ('.js', 'javascript'), ('.ts', 'javascript')]:
        for file_path in project_root.rglob(f'*{ext}'):
            # Skip vendor/node_modules
            if any(d in file_path.parts for d in ['vendor', 'node_modules', '.venv', 'venv']):
                continue

            try:
                content = file_path.read_text()
                for pattern, description in patterns.get(lang, []):
                    if re.search(pattern, content, re.IGNORECASE):
                        found_patterns.add(description)
                        found_lang = lang
            except Exception:
                pass

    if '/metrics' in str(found_patterns):
        result.success("Metrics endpoint /metrics found")
    else:
        result.warning("No /metrics endpoint found - consider exposing Prometheus metrics")

    if 'Prometheus' in str(found_patterns):
        result.success("Prometheus client library detected")


def check_structured_logging(project_root: Path, result: ValidationResult):
    """
    Check if service uses structured logging.

    Anti-patterns:
    - String formatting in logs: logger.info(f"User {id}")
    - Print statements: print("debug")

    Good patterns:
    - Structured fields: logger.info("user_action", extra={"user_id": id})
    - JSON logging configured
    """
    print(f"{Colors.BLUE}Checking structured logging...{Colors.NC}")

    unstructured_logs = []
    structured_logs = []

    # Check Python files
    for file_path in project_root.rglob('*.py'):
        if any(d in file_path.parts for d in ['venv', '.venv', '__pycache__']):
            continue

        try:
            content = file_path.read_text()
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                # Anti-pattern: f-string in logging
                if re.search(r'logger\.\w+\(f["\']', line):
                    unstructured_logs.append(f"{file_path}:{i}")

                # Anti-pattern: % formatting in logging
                if re.search(r'logger\.\w+\([^)]*%[^)]*\)', line):
                    unstructured_logs.append(f"{file_path}:{i}")

                # Good pattern: extra={} or structured logger
                if re.search(r'extra\s*=\s*\{', line) or 'structlog' in line:
                    structured_logs.append(f"{file_path}:{i}")

        except Exception:
            pass

    # Check Go files (simple heuristic)
    for file_path in project_root.rglob('*.go'):
        if 'vendor' in file_path.parts:
            continue

        try:
            content = file_path.read_text()
            # Check for structured logging libraries
            if re.search(r'(zap|zerolog|logrus)\.', content):
                structured_logs.append(str(file_path))

            # Anti-pattern: fmt.Printf for logging
            if re.search(r'fmt\.Printf\([^)]*log', content, re.IGNORECASE):
                unstructured_logs.append(str(file_path))

        except Exception:
            pass

    if structured_logs:
        result.success(f"Structured logging detected ({len(set(structured_logs))} files)")

    if unstructured_logs:
        result.warning(f"Unstructured logging found in {len(set(unstructured_logs))} locations")
        result.warning("  Use structured logging with extra fields, not string formatting")


def check_health_endpoints(project_root: Path, result: ValidationResult):
    """
    Check for health check endpoints.

    Expected:
    - /health or /health/liveness
    - /health/readiness (for K8s)
    """
    print(f"{Colors.BLUE}Checking health endpoints...{Colors.NC}")

    health_endpoints = []

    for ext in ['.go', '.py', '.js', '.ts']:
        for file_path in project_root.rglob(f'*{ext}'):
            if any(d in file_path.parts for d in ['vendor', 'node_modules', '.venv']):
                continue

            try:
                content = file_path.read_text()
                # Look for health endpoint routes
                if re.search(r'/health', content, re.IGNORECASE):
                    health_endpoints.append(str(file_path))
            except Exception:
                pass

    if health_endpoints:
        result.success(f"Health check endpoints found ({len(set(health_endpoints))} files)")

        # Check for both liveness and readiness
        all_content = []
        for file_path in set(health_endpoints):
            try:
                all_content.append(Path(file_path).read_text())
            except Exception:
                pass

        combined = '\n'.join(all_content)
        has_liveness = bool(re.search(r'/health/(liveness|live)', combined, re.IGNORECASE))
        has_readiness = bool(re.search(r'/health/(readiness|ready)', combined, re.IGNORECASE))

        if has_liveness:
            result.success("Liveness probe endpoint found")
        else:
            result.warning("Consider adding /health/liveness for K8s liveness probe")

        if has_readiness:
            result.success("Readiness probe endpoint found")
        else:
            result.warning("Consider adding /health/readiness for K8s readiness probe")
    else:
        result.warning("No health check endpoints found")
        result.warning("  Add /health/liveness and /health/readiness for K8s")


def check_infrastructure_docs(project_root: Path, result: ValidationResult):
    """
    Check if infrastructure documentation exists.

    Expected:
    - docs/infrastructure/INVENTORY.md (discovery file)
    - docs/infrastructure/{prometheus,grafana,loki}.md (setup docs)
    """
    print(f"{Colors.BLUE}Checking infrastructure documentation...{Colors.NC}")

    infra_dir = project_root / "docs" / "infrastructure"

    if not infra_dir.exists():
        result.warning("docs/infrastructure/ directory not found")
        result.warning("  Create with: mkdir -p docs/infrastructure")
        return

    inventory_file = infra_dir / "INVENTORY.md"
    if inventory_file.exists():
        result.success("Infrastructure inventory found (docs/infrastructure/INVENTORY.md)")

        # Check for key sections
        try:
            content = inventory_file.read_text()
            if 'Prometheus' in content or 'prometheus' in content:
                result.success("  Prometheus documented in inventory")
            if 'Grafana' in content or 'grafana' in content:
                result.success("  Grafana documented in inventory")
            if 'Loki' in content or 'loki' in content:
                result.success("  Loki documented in inventory")
        except Exception:
            pass
    else:
        result.warning("docs/infrastructure/INVENTORY.md not found")
        result.warning("  Create infrastructure discovery file for agents")


def check_grafana_dashboards(project_root: Path, result: ValidationResult):
    """
    Check for Grafana dashboard definitions.

    Expected locations:
    - deploy/grafana/*.json
    - monitoring/dashboards/*.json
    - .grafana/*.json
    """
    print(f"{Colors.BLUE}Checking Grafana dashboards...{Colors.NC}")

    dashboard_patterns = [
        "deploy/grafana/**/*.json",
        "monitoring/dashboards/**/*.json",
        ".grafana/**/*.json",
    ]

    dashboards = []
    for pattern in dashboard_patterns:
        for file_path in project_root.glob(pattern):
            dashboards.append(file_path)

    if not dashboards:
        result.warning("No Grafana dashboards found")
        result.warning("  Consider creating deploy/grafana/README.md with dashboard setup guide")
        return

    result.success(f"Found {len(dashboards)} Grafana dashboard(s)")

    # Validate dashboard structure
    for dashboard in dashboards:
        try:
            with open(dashboard) as f:
                data = json.load(f)

                # Check for required fields
                if "panels" not in data:
                    result.error(f"Dashboard {dashboard.name} missing 'panels' field")
                elif len(data.get("panels", [])) == 0:
                    result.warning(f"Dashboard {dashboard.name} has no panels")
                else:
                    result.success(f"  {dashboard.name}: {len(data['panels'])} panels")

                # Check for UID (required for provisioning)
                if "uid" not in data:
                    result.warning(f"Dashboard {dashboard.name} missing 'uid' field (needed for provisioning)")

        except json.JSONDecodeError as e:
            result.error(f"Dashboard {dashboard.name} has invalid JSON: {e}")
        except Exception as e:
            result.warning(f"Could not validate {dashboard.name}: {e}")


def main():
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Usage: {sys.argv[0]} <project_root> [--check <aspect>]{Colors.NC}")
        print("\nAspects: metrics, logging, health, docs, dashboards, all (default)")
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()

    if not project_root.exists():
        print(f"{Colors.RED}Error: {project_root} not found{Colors.NC}")
        sys.exit(1)

    # Parse check filter
    check_filter = 'all'
    if '--check' in sys.argv:
        idx = sys.argv.index('--check')
        if idx + 1 < len(sys.argv):
            check_filter = sys.argv[idx + 1]

    print(f"{Colors.BLUE}Observability Validation{Colors.NC}")
    print(f"Project: {project_root}")
    print(f"Check: {check_filter}\n")

    result = ValidationResult()

    # Run checks
    if check_filter in ['all', 'metrics']:
        check_metrics_endpoint(project_root, result)

    if check_filter in ['all', 'logging']:
        check_structured_logging(project_root, result)

    if check_filter in ['all', 'health']:
        check_health_endpoints(project_root, result)

    if check_filter in ['all', 'docs']:
        check_infrastructure_docs(project_root, result)

    if check_filter in ['all', 'dashboards']:
        check_grafana_dashboards(project_root, result)

    # Print results
    result.print_summary()

    # Exit code
    if result.has_errors():
        print(f"\n{Colors.RED}Validation failed{Colors.NC}")
        sys.exit(1)
    elif result.warnings:
        print(f"\n{Colors.YELLOW}Validation passed with warnings{Colors.NC}")
        sys.exit(0)
    else:
        print(f"\n{Colors.GREEN}✅ All observability checks passed{Colors.NC}")
        sys.exit(0)


if __name__ == "__main__":
    main()
