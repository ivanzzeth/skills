# OpenAI Harness References

Detailed documentation for the openai-harness skill. SKILL.md is the navigation map; this directory contains the comprehensive guides.

## Getting Started

- **[quick-start.md](./quick-start.md)** - Step-by-step guide to set up an agent-first repository from scratch (10 steps)
- **[end-to-end-example.md](./end-to-end-example.md)** - Complete real-world scenario: building a JWT auth microservice with full observability in 55 minutes
- **[capabilities.md](./capabilities.md)** - Detailed explanation of all 10 core capabilities with usage examples

## Core Concepts

- **[openai-harness-principles.md](./openai-harness-principles.md)** - Full distillation of OpenAI's harness engineering principles (repository as source of truth, progressive disclosure, mechanical enforcement, agent legibility)
- **[directory-structure.md](./directory-structure.md)** - Detailed specification of the agent-first directory structure (AGENTS.md, ARCHITECTURE.md, docs/ hierarchy, mechanical enforcement)
- **[best-practices.md](./best-practices.md)** - Wisdom learned from building agent-first repositories (start small, be ruthless with AGENTS.md length, cross-link aggressively, validate continuously, encode taste as linters, make docs executable, test with agents)

## Examples and Anti-Patterns

- **[example-agents-md.md](./example-agents-md.md)** - Good AGENTS.md examples (minimal, team-based, progressive disclosure) and anti-patterns (detailed implementation, duplication, too many constraints)
- **[example-architecture-md.md](./example-architecture-md.md)** - Good ARCHITECTURE.md examples (layered monolith, microservices, monorepo) and anti-patterns (no dependency rules, too much detail, missing "why")
- **[common-pitfalls.md](./common-pitfalls.md)** - 12 real pitfalls with prevention/fixes (documentation, architecture, agent workflow, security, quality, process pitfalls)

## Progressive Disclosure in Action

This references/ directory itself demonstrates progressive disclosure:
- **SKILL.md** (100 lines) - Navigation map with 1-line capability summaries
- **capabilities.md** (detailed) - Full explanation of what each capability does
- **quick-start.md** (practical) - Step-by-step instructions
- **end-to-end-example.md** (concrete) - Real-world complete scenario
- **best-practices.md** (wisdom) - Lessons learned from experience

Agents load SKILL.md first, then follow links to relevant detailed docs as needed.

## Usage Notes

All references are loaded **as needed** by agents. SKILL.md provides the overview and directs agents to the appropriate reference document.

For large reference files (>10k words), SKILL.md includes grep search patterns to help agents find relevant sections efficiently.
