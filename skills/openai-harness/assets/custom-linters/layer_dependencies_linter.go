package main

/*
Layer Dependencies Linter (Go Template)

Validates that code follows layer dependency rules:
  Types → Config → Repo → Service → Runtime → UI

Cross-cutting concerns must go through Providers.

This is a TEMPLATE. Customize for your project:
1. Update layerRules with your actual layer structure
2. Update getLayer() to match your directory structure
3. Update modulePrefix with your Go module name
4. Add project-specific exceptions if needed

Usage:
  go run layer_dependencies_linter.go /path/to/project
*/

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
)

// CUSTOMIZE THIS: Define your layer dependency rules
var layerRules = map[string]map[string]bool{
	"types":     {},                                        // Bottom layer - depends on nothing
	"config":    {"types": true},
	"repo":      {"types": true, "config": true},
	"service":   {"types": true, "config": true, "repo": true, "providers": true},
	"runtime":   {"types": true, "config": true, "repo": true, "service": true, "providers": true},
	"ui":        {"types": true, "config": true, "repo": true, "service": true, "runtime": true, "providers": true},
	"providers": {"types": true, "config": true}, // Cross-cutting - limited dependencies
}

// CUSTOMIZE THIS: Your Go module prefix
const modulePrefix = "github.com/yourorg/yourproject" // Change this!

type violation struct {
	file          string
	currentLayer  string
	importedLayer string
	importPath    string
}

func (v violation) String() string {
	allowed := []string{}
	for layer := range layerRules[v.currentLayer] {
		allowed = append(allowed, layer)
	}
	allowedStr := strings.Join(allowed, ", ")
	if allowedStr == "" {
		allowedStr = "none"
	}

	return fmt.Sprintf(`%s: Layer '%s' cannot import from '%s'
  Import: %s
  Allowed layers for '%s': %s
  Fix: Move import to allowed layer or use Provider interface`,
		v.file, v.currentLayer, v.importedLayer, v.importPath,
		v.currentLayer, allowedStr)
}

// CUSTOMIZE THIS: Determine layer from file path
func getLayer(filePath, projectRoot string) string {
	relPath := strings.TrimPrefix(filePath, projectRoot+"/")
	parts := strings.Split(relPath, "/")

	// CUSTOMIZE: Adjust these patterns for your directory structure
	for _, part := range parts {
		switch part {
		case "types", "model", "models":
			return "types"
		case "config":
			return "config"
		case "repo", "dao", "repository":
			return "repo"
		case "service":
			return "service"
		case "runtime", "app", "cmd":
			return "runtime"
		case "ui", "handler", "controller":
			return "ui"
		case "providers", "provider":
			return "providers"
		}
	}

	// If not in any layer, treat as utility (allowed everywhere)
	return "util"
}

// CUSTOMIZE THIS: Resolve import path to layer
func resolveImportToLayer(importPath string) string {
	// External imports are allowed
	if !strings.HasPrefix(importPath, modulePrefix) {
		return "external"
	}

	// Remove module prefix
	relImport := strings.TrimPrefix(importPath, modulePrefix+"/")
	parts := strings.Split(relImport, "/")

	if len(parts) == 0 {
		return "util"
	}

	// CUSTOMIZE: Map package structure to layers
	firstPart := parts[0]
	switch firstPart {
	case "types", "model", "models":
		return "types"
	case "config":
		return "config"
	case "repo", "dao", "repository":
		return "repo"
	case "service":
		return "service"
	case "runtime", "app", "cmd":
		return "runtime"
	case "ui", "handler", "controller":
		return "ui"
	case "providers", "provider":
		return "providers"
	case "pkg", "internal":
		// Look at second part for internal packages
		if len(parts) > 1 {
			switch parts[1] {
			case "types", "model":
				return "types"
			case "config":
				return "config"
			case "repo", "dao":
				return "repo"
			case "service":
				return "service"
			case "providers", "provider":
				return "providers"
			}
		}
	}

	return "util"
}

func validateFile(filePath, projectRoot string) ([]violation, error) {
	var violations []violation

	currentLayer := getLayer(filePath, projectRoot)
	if currentLayer == "util" {
		// Utilities can import from anywhere
		return violations, nil
	}

	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, filePath, nil, parser.ImportsOnly)
	if err != nil {
		return nil, err
	}

	allowedLayers := layerRules[currentLayer]

	for _, imp := range node.Imports {
		importPath := strings.Trim(imp.Path.Value, `"`)
		importedLayer := resolveImportToLayer(importPath)

		if importedLayer == "external" || importedLayer == "util" {
			// External and utility imports are always allowed
			continue
		}

		if !allowedLayers[importedLayer] {
			relPath := strings.TrimPrefix(filePath, projectRoot+"/")
			violations = append(violations, violation{
				file:          relPath,
				currentLayer:  currentLayer,
				importedLayer: importedLayer,
				importPath:    importPath,
			})
		}
	}

	return violations, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: layer_dependencies_linter <project_root>")
		os.Exit(1)
	}

	projectRoot, err := filepath.Abs(os.Args[1])
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Validating layer dependencies in: %s\n\n", projectRoot)

	var allViolations []violation
	fileCount := 0

	// CUSTOMIZE: Adjust paths for your source directory
	err = filepath.Walk(projectRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip vendor, .git, etc.
		if info.IsDir() {
			name := info.Name()
			if name == "vendor" || name == ".git" || name == "node_modules" {
				return filepath.SkipDir
			}
			return nil
		}

		// Only check Go files (skip tests)
		if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
			return nil
		}

		fileCount++
		violations, err := validateFile(path, projectRoot)
		if err != nil {
			fmt.Printf("Warning: could not parse %s: %v\n", path, err)
			return nil
		}

		allViolations = append(allViolations, violations...)
		return nil
	})

	if err != nil {
		fmt.Printf("Error walking directory: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Checked %d files...\n\n", fileCount)

	if len(allViolations) > 0 {
		fmt.Printf("❌ Found %d layer dependency violation(s):\n\n", len(allViolations))
		for _, v := range allViolations {
			fmt.Println(v.String())
			fmt.Println()
		}
		os.Exit(1)
	}

	fmt.Println("✅ All layer dependencies are valid")
}
