---
name: solidity-static-analysis
description: >
  Run Slither static analysis on Solidity contracts, configure detectors, triage findings,
  and produce severity-ranked reports. This skill should be used when running automated
  security analysis on smart contracts, interpreting Slither output, or filtering false
  positives from static analysis results.
  Triggers include: "slither", "static analysis", "run slither", "slither detectors",
  "slither report", "automated analysis", "静态分析", "Slither分析", "自动化分析",
  "run security scan", "detector configuration".
---

# solidity-static-analysis

Step 4 of the Solidity audit workflow. Run Slither against fetched contract sources, triage findings by severity, and produce a structured report.

## Gate Check (MANDATORY)

Before starting, verify prior steps and tools are ready. **Do NOT proceed if any check fails.**

```bash
PROTOCOL="{protocol}"
CHAIN_ID="{chainId}"
ADDRESS="{address}"

# Tool check
slither --version || echo "BLOCKED: Install slither — pip install slither-analyzer"

# Steps 1-3 outputs must exist (static analysis uses architecture + fund flow context)
ls ~/.solidity-analyzer/contracts/$CHAIN_ID/$ADDRESS/source/*.sol || echo "BLOCKED: No source code fetched"
ls ~/.solidity-analyzer/audits/$PROTOCOL/02-interface-analysis.md || echo "BLOCKED: Step 2 not complete"
ls ~/.solidity-analyzer/audits/$PROTOCOL/03-fund-flow-risk.md || echo "BLOCKED: Step 3 not complete"
```

**Why Steps 2-3 matter**: Understanding architecture and fund flows is essential for triaging Slither findings. Without context, false positives cannot be identified.

Additional requirements:
- **Correct solc version**: Use `solc-select` to manage versions.
- **Output directory**: `~/.solidity-analyzer/audits/{protocol}/` must exist.

## Commands

Run all commands from the contract source directory:

```bash
cd ~/.solidity-analyzer/contracts/{chainId}/{address}/source
```

### Full analysis with JSON output

```bash
slither . --json ../slither-report.json 2>&1 | tee ../slither-output.txt
```

### High/Medium severity only

```bash
slither . --exclude-informational --exclude-low --exclude-optimization
```

### Specific detectors

```bash
slither . --detect reentrancy-eth,reentrancy-no-eth,arbitrary-send,controlled-delegatecall
```

### Exclude test/mock files

```bash
slither . --filter-paths "node_modules|test|mock"
```

## Key Slither Detectors

| Category | Detectors |
|----------|-----------|
| Reentrancy | `reentrancy-eth`, `reentrancy-no-eth`, `reentrancy-benign`, `reentrancy-events` |
| Access Control | `arbitrary-send`, `protected-vars`, `suicidal`, `unprotected-upgrade` |
| Logic | `incorrect-equality`, `tautology`, `boolean-cst`, `divide-before-multiply` |
| Low-level | `controlled-delegatecall`, `delegatecall-loop`, `unchecked-lowlevel` |
| State | `uninitialized-state`, `uninitialized-local`, `unused-state` |

## Output Document

Write the report to `~/.solidity-analyzer/audits/{protocol}/04-static-analysis.md` using this template:

```markdown
# Static Analysis Report — {protocol}

- **Tool**: Slither v{version}
- **Date**: {YYYY-MM-DD}
- **Source**: `~/.solidity-analyzer/contracts/{chainId}/{address}/source/`

## Summary

| Severity | Count |
|----------|-------|
| High     | {n}   |
| Medium   | {n}   |
| Low      | {n}   |
| Info     | {n}   |

## High Severity Findings

### H-{nn}: {Title}

| Field | Value |
|-------|-------|
| **Detector** | {detector-name} |
| **Location** | {file}:{line} |
| **Description** | {what Slither found} |
| **Impact** | {potential exploit or loss} |
| **Recommendation** | {concrete fix} |

## Medium Severity Findings

### M-{nn}: {Title}

| Field | Value |
|-------|-------|
| **Detector** | {detector-name} |
| **Location** | {file}:{line} |
| **Description** | {what Slither found} |
| **Impact** | {potential exploit or loss} |
| **Recommendation** | {concrete fix} |

## Low Severity Findings

### L-{nn}: {Title}

| Field | Value |
|-------|-------|
| **Detector** | {detector-name} |
| **Location** | {file}:{line} |
| **Description** | {what Slither found} |
| **Impact** | {potential exploit or loss} |
| **Recommendation** | {concrete fix} |

## False Positives

| Finding | Reason |
|---------|--------|
| {detector — location} | {why this is a false positive} |
```

## Triage Process

1. Parse `slither-report.json` for all findings.
2. Group findings by severity (High > Medium > Low > Informational).
3. For each finding, verify the detector output against the source code.
4. Mark confirmed false positives in the False Positives table with a clear justification.
5. For true positives, fill in Impact and Recommendation fields.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `slither: command not found` | Run `pip install slither-analyzer`. Ensure the pip bin directory is in `$PATH`. |
| Compilation errors | Check the required `solc` version with `solc-select versions`. Install the correct version with `solc-select install {version}` and activate with `solc-select use {version}`. Verify `remappings.txt` or `foundry.toml` remappings are correct. |
| Stack Too Deep errors | Use `--exclude` to skip problematic detectors (e.g., `--exclude reentrancy-eth`). Alternatively, increase the compiler optimizer runs or split analysis by contract. |
