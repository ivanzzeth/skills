#!/usr/bin/env node
/**
 * Layer Dependencies Linter (TypeScript Template)
 *
 * Validates that code follows layer dependency rules:
 *   Types → Config → Repo → Service → Runtime → UI
 *
 * Cross-cutting concerns must go through Providers.
 *
 * This is a TEMPLATE. Customize for your project:
 * 1. Update LAYER_RULES with your actual layer structure
 * 2. Update getLayer() to match your directory structure
 * 3. Update MODULE_PREFIX with your package name
 * 4. Add project-specific exceptions if needed
 *
 * Usage:
 *   ts-node layer_dependencies_linter.ts /path/to/project
 *   # or compile and run:
 *   tsc layer_dependencies_linter.ts && node layer_dependencies_linter.js /path/to/project
 */

import * as fs from 'fs';
import * as path from 'path';

// CUSTOMIZE THIS: Define your layer dependency rules
const LAYER_RULES: Record<string, Set<string>> = {
  types: new Set([]), // Bottom layer - depends on nothing
  config: new Set(['types']),
  repo: new Set(['types', 'config']),
  service: new Set(['types', 'config', 'repo', 'providers']),
  runtime: new Set(['types', 'config', 'repo', 'service', 'providers']),
  ui: new Set(['types', 'config', 'repo', 'service', 'runtime', 'providers']),
  providers: new Set(['types', 'config']), // Cross-cutting - limited dependencies
};

// CUSTOMIZE THIS: Your module prefix or package scope
const MODULE_PREFIX = '@yourorg/yourproject'; // Change this!

interface Violation {
  file: string;
  currentLayer: string;
  importedLayer: string;
  importPath: string;
}

/**
 * CUSTOMIZE THIS: Determine layer from file path
 */
function getLayer(filePath: string, projectRoot: string): string {
  const relPath = path.relative(projectRoot, filePath);
  const parts = relPath.split(path.sep);

  // CUSTOMIZE: Adjust these patterns for your directory structure
  for (const part of parts) {
    if (['types', 'models', 'interfaces'].includes(part)) return 'types';
    if (part === 'config') return 'config';
    if (['repo', 'dao', 'repositories'].includes(part)) return 'repo';
    if (['service', 'services'].includes(part)) return 'service';
    if (['runtime', 'app'].includes(part)) return 'runtime';
    if (['ui', 'components', 'views'].includes(part)) return 'ui';
    if (['providers', 'provider'].includes(part)) return 'providers';
  }

  // If not in any layer, treat as utility (allowed everywhere)
  return 'util';
}

/**
 * CUSTOMIZE THIS: Resolve import path to layer
 */
function resolveImportToLayer(importPath: string): string {
  // External imports (not from our module) are allowed
  if (!importPath.startsWith(MODULE_PREFIX) && !importPath.startsWith('.')) {
    return 'external';
  }

  // Relative imports - determine layer from path
  if (importPath.startsWith('.')) {
    // For relative imports, we'd need file context to resolve
    // For template simplicity, return util
    return 'util';
  }

  // Remove module prefix
  const relImport = importPath.replace(MODULE_PREFIX + '/', '');
  const parts = relImport.split('/');

  if (parts.length === 0) return 'util';

  // CUSTOMIZE: Map package structure to layers
  const firstPart = parts[0];
  switch (firstPart) {
    case 'types':
    case 'models':
    case 'interfaces':
      return 'types';
    case 'config':
      return 'config';
    case 'repo':
    case 'dao':
    case 'repositories':
      return 'repo';
    case 'service':
    case 'services':
      return 'service';
    case 'runtime':
    case 'app':
      return 'runtime';
    case 'ui':
    case 'components':
    case 'views':
      return 'ui';
    case 'providers':
    case 'provider':
      return 'providers';
    default:
      return 'util';
  }
}

/**
 * Extract import statements from TypeScript file
 */
function extractImports(filePath: string): string[] {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const imports: string[] = [];

    // Match: import ... from 'path'
    const importRegex = /import\s+(?:[\w\s{},*]+\s+from\s+)?['"]([^'"]+)['"]/g;
    let match: RegExpExecArray | null;

    while ((match = importRegex.exec(content)) !== null) {
      imports.push(match[1]);
    }

    return imports;
  } catch (error) {
    return [];
  }
}

/**
 * Validate a single file's imports against layer rules
 */
function validateFile(filePath: string, projectRoot: string): Violation[] {
  const violations: Violation[] = [];

  const currentLayer = getLayer(filePath, projectRoot);
  if (currentLayer === 'util') {
    // Utilities can import from anywhere
    return violations;
  }

  const imports = extractImports(filePath);
  const allowedLayers = LAYER_RULES[currentLayer] || new Set();

  for (const importPath of imports) {
    const importedLayer = resolveImportToLayer(importPath);

    if (importedLayer === 'external' || importedLayer === 'util') {
      // External and utility imports are always allowed
      continue;
    }

    if (!allowedLayers.has(importedLayer)) {
      const relPath = path.relative(projectRoot, filePath);
      violations.push({
        file: relPath,
        currentLayer,
        importedLayer,
        importPath,
      });
    }
  }

  return violations;
}

/**
 * Format violation for display
 */
function formatViolation(v: Violation): string {
  const allowed = Array.from(LAYER_RULES[v.currentLayer] || []).join(', ') || 'none';

  return `${v.file}: Layer '${v.currentLayer}' cannot import from '${v.importedLayer}'
  Import: ${v.importPath}
  Allowed layers for '${v.currentLayer}': ${allowed}
  Fix: Move import to allowed layer or use Provider interface`;
}

/**
 * Recursively find TypeScript files
 */
function findTypeScriptFiles(dir: string): string[] {
  const files: string[] = [];

  function walk(currentPath: string) {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);

      if (entry.isDirectory()) {
        // Skip node_modules, .git, etc.
        if (['node_modules', '.git', 'dist', 'build'].includes(entry.name)) {
          continue;
        }
        walk(fullPath);
      } else if (entry.isFile()) {
        // Only check .ts/.tsx files (skip tests)
        if (
          (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx')) &&
          !entry.name.endsWith('.test.ts') &&
          !entry.name.endsWith('.spec.ts')
        ) {
          files.push(fullPath);
        }
      }
    }
  }

  walk(dir);
  return files;
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.log('Usage: layer_dependencies_linter <project_root>');
    process.exit(1);
  }

  const projectRoot = path.resolve(args[0]);

  if (!fs.existsSync(projectRoot)) {
    console.log(`Error: ${projectRoot} not found`);
    process.exit(1);
  }

  console.log(`Validating layer dependencies in: ${projectRoot}\n`);

  // CUSTOMIZE: Adjust path for your source directory
  const srcDir = path.join(projectRoot, 'src');
  const tsFiles = findTypeScriptFiles(fs.existsSync(srcDir) ? srcDir : projectRoot);

  console.log(`Checking ${tsFiles.length} files...\n`);

  const allViolations: Violation[] = [];
  for (const tsFile of tsFiles) {
    const violations = validateFile(tsFile, projectRoot);
    allViolations.push(...violations);
  }

  if (allViolations.length > 0) {
    console.log(`❌ Found ${allViolations.length} layer dependency violation(s):\n`);
    for (const violation of allViolations) {
      console.log(formatViolation(violation));
      console.log();
    }
    process.exit(1);
  }

  console.log('✅ All layer dependencies are valid');
  process.exit(0);
}

main();
