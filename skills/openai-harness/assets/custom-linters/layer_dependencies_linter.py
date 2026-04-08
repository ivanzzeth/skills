#!/usr/bin/env python3
"""
Layer Dependencies Linter (Python Template)

Validates that code follows layer dependency rules:
  Types → Config → Repo → Service → Runtime → UI

Cross-cutting concerns must go through Providers.

This is a TEMPLATE. Customize for your project:
1. Update LAYER_RULES with your actual layer structure
2. Update get_layer() to match your directory structure
3. Add project-specific exceptions if needed
"""
import sys
import re
from pathlib import Path
from typing import Dict, Set, List


# CUSTOMIZE THIS: Define your layer dependency rules
LAYER_RULES: Dict[str, Set[str]] = {
    "types": set(),  # Bottom layer - depends on nothing
    "config": {"types"},
    "repo": {"types", "config"},
    "service": {"types", "config", "repo", "providers"},
    "runtime": {"types", "config", "repo", "service", "providers"},
    "ui": {"types", "config", "repo", "service", "runtime", "providers"},
    "providers": {"types", "config"},  # Cross-cutting - limited dependencies
}


class LayerViolation(Exception):
    """
    Architectural layer dependency violation.

    Layers must follow dependency direction:
      Types → Config → Repo → Service → Runtime → UI
                ↑
            Providers

    Cross-cutting concerns (auth, telemetry, feature flags) must use Providers.

    Fix: Move the import to the correct layer, or refactor to use Provider interface.
    """
    pass


def get_layer(file_path: Path, project_root: Path) -> str:
    """
    Determine which layer a file belongs to based on directory structure.

    CUSTOMIZE THIS for your project structure.

    Example structures:
      src/types/user.py → "types"
      src/service/auth_service.py → "service"
      src/providers/auth_provider.py → "providers"
    """
    rel_path = file_path.relative_to(project_root)
    parts = rel_path.parts

    # CUSTOMIZE: Adjust these patterns for your directory structure
    if "types" in parts or "models" in parts:
        return "types"
    elif "config" in parts:
        return "config"
    elif "repo" in parts or "dao" in parts or "repository" in parts:
        return "repo"
    elif "service" in parts:
        return "service"
    elif "runtime" in parts or "app" in parts:
        return "runtime"
    elif "ui" in parts or "views" in parts or "components" in parts:
        return "ui"
    elif "providers" in parts or "provider" in parts:
        return "providers"

    # If not in any layer, treat as utility (allowed everywhere)
    return "util"


def extract_imports(file_path: Path) -> List[str]:
    """Extract import statements from a Python file."""
    try:
        content = file_path.read_text()
    except Exception:
        return []

    imports = []

    # Match: import foo.bar
    for match in re.finditer(r'^import\s+([\w.]+)', content, re.MULTILINE):
        imports.append(match.group(1))

    # Match: from foo.bar import baz
    for match in re.finditer(r'^from\s+([\w.]+)\s+import', content, re.MULTILINE):
        imports.append(match.group(1))

    return imports


def resolve_import_to_layer(import_path: str, project_root: Path) -> str:
    """
    Resolve an import path to a layer.

    CUSTOMIZE THIS for your project's package structure.

    Example:
      "myproject.service.auth" → resolve to src/service/auth.py → "service"
    """
    # CUSTOMIZE: Your project's base package name
    BASE_PACKAGE = "myproject"  # Change this!

    if not import_path.startswith(BASE_PACKAGE):
        # External import - allowed
        return "external"

    # Remove base package prefix
    rel_import = import_path[len(BASE_PACKAGE)+1:]
    parts = rel_import.split(".")

    # CUSTOMIZE: Map package structure to layers
    if parts[0] in ["types", "models"]:
        return "types"
    elif parts[0] == "config":
        return "config"
    elif parts[0] in ["repo", "dao", "repository"]:
        return "repo"
    elif parts[0] == "service":
        return "service"
    elif parts[0] in ["runtime", "app"]:
        return "runtime"
    elif parts[0] in ["ui", "views", "components"]:
        return "ui"
    elif parts[0] in ["providers", "provider"]:
        return "providers"

    return "util"


def validate_file(file_path: Path, project_root: Path) -> List[str]:
    """Validate a single file's imports against layer rules."""
    errors = []

    current_layer = get_layer(file_path, project_root)
    if current_layer == "util":
        # Utilities can import from anywhere
        return errors

    imports = extract_imports(file_path)
    allowed_layers = LAYER_RULES.get(current_layer, set())

    for import_path in imports:
        imported_layer = resolve_import_to_layer(import_path, project_root)

        if imported_layer == "external" or imported_layer == "util":
            # External and utility imports are always allowed
            continue

        if imported_layer not in allowed_layers:
            rel_path = file_path.relative_to(project_root)
            errors.append(
                f"{rel_path}: Layer '{current_layer}' cannot import from '{imported_layer}'\n"
                f"  Import: {import_path}\n"
                f"  Allowed layers for '{current_layer}': {', '.join(sorted(allowed_layers)) or 'none'}\n"
                f"  Fix: Move import to allowed layer or use Provider interface"
            )

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_dependencies_linter.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()

    if not project_root.exists():
        print(f"Error: {project_root} not found")
        sys.exit(1)

    print(f"Validating layer dependencies in: {project_root}")
    print()

    # CUSTOMIZE: Adjust glob pattern for your source directory
    python_files = list(project_root.glob("src/**/*.py"))
    python_files = [f for f in python_files if not f.name.startswith("test_")]

    print(f"Checking {len(python_files)} files...")

    all_errors = []
    for py_file in python_files:
        errors = validate_file(py_file, project_root)
        all_errors.extend(errors)

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} layer dependency violation(s):\n")
        for error in all_errors:
            print(error)
            print()
        sys.exit(1)
    else:
        print("✅ All layer dependencies are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
