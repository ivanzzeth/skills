---
name: solidity-contract-diff
description: >
  Compare two versions of a smart contract — before and after an upgrade, or between
  two addresses on the same or different chains. Uses etherscan-contract-fetcher to
  retrieve source code, then generates a structured diff report highlighting storage
  layout changes, function signature changes, and security-relevant modifications.
  This skill should be used when analyzing contract upgrades, comparing proxy
  implementations, or auditing changes between contract versions.
  Triggers include: "compare contracts", "contract diff", "upgrade diff",
  "what changed", "compare implementations", "diff 0x", "before and after",
  "合约对比", "合约差异", "升级对比", "版本对比", "compare versions".
---

# solidity-contract-diff

Compare two smart contract versions and produce a structured diff report. Part of the solidity audit toolkit.

## Gate Check (MANDATORY)

Before starting, verify both contract sources are available:

```bash
CHAIN_ID_A="{chainId_A}"
ADDRESS_A="{address_A}"
CHAIN_ID_B="{chainId_B}"
ADDRESS_B="{address_B}"

# Both sources must be fetched
ls ~/.solidity-analyzer/contracts/$CHAIN_ID_A/$ADDRESS_A/source/*.sol || echo "BLOCKED: Fetch contract A first (etherscan-contract-fetcher)"
ls ~/.solidity-analyzer/contracts/$CHAIN_ID_B/$ADDRESS_B/source/*.sol || echo "BLOCKED: Fetch contract B first (etherscan-contract-fetcher)"
```

If sources are missing, use **etherscan-contract-fetcher** to fetch them first.

## Workflow

### Step 1: Fetch Both Versions

```bash
# Fetch old implementation (contract A)
python3 scripts/fetch_contract.py -c {chainId_A} -a {address_A}

# Fetch new implementation (contract B)
python3 scripts/fetch_contract.py -c {chainId_B} -a {address_B}
```

For proxy upgrades on the same chain, both addresses share the same chain ID but have different implementation addresses.

### Step 2: Generate Diff

```bash
PROTOCOL="{protocol}"
DIR_A="$HOME/.solidity-analyzer/contracts/$CHAIN_ID_A/$ADDRESS_A/source"
DIR_B="$HOME/.solidity-analyzer/contracts/$CHAIN_ID_B/$ADDRESS_B/source"
DIFF_DIR="$HOME/.solidity-analyzer/audits/$PROTOCOL/diff_${ADDRESS_A}_${ADDRESS_B}"

mkdir -p "$DIFF_DIR"

# Full recursive diff
diff -ruN "$DIR_A" "$DIR_B" > "$DIFF_DIR/full.diff" || true

# Per-file diffs (easier to review)
for file_a in "$DIR_A"/*.sol; do
  filename=$(basename "$file_a")
  file_b="$DIR_B/$filename"
  if [ -f "$file_b" ]; then
    diff -u "$file_a" "$file_b" > "$DIFF_DIR/${filename}.diff" 2>/dev/null || true
  else
    echo "REMOVED: $filename" >> "$DIFF_DIR/removed_files.txt"
  fi
done

# Find new files in B not in A
for file_b in "$DIR_B"/*.sol; do
  filename=$(basename "$file_b")
  if [ ! -f "$DIR_A/$filename" ]; then
    echo "ADDED: $filename" >> "$DIFF_DIR/added_files.txt"
  fi
done
```

### Step 3: Compare Storage Layouts

```bash
cd "$DIR_A" && forge inspect ContractName storage-layout --pretty > "$DIFF_DIR/storage_A.txt" 2>/dev/null
cd "$DIR_B" && forge inspect ContractName storage-layout --pretty > "$DIFF_DIR/storage_B.txt" 2>/dev/null

# Diff storage layouts
diff -u "$DIFF_DIR/storage_A.txt" "$DIFF_DIR/storage_B.txt" > "$DIFF_DIR/storage.diff" || true
```

### Step 4: Compare Function Signatures

```bash
# Extract public/external function signatures from both versions
cd "$DIR_A" && forge inspect ContractName abi > "$DIFF_DIR/abi_A.json" 2>/dev/null
cd "$DIR_B" && forge inspect ContractName abi > "$DIFF_DIR/abi_B.json" 2>/dev/null

# Or use slither for function listing
cd "$DIR_A" && slither . --print function-summary 2>/dev/null > "$DIFF_DIR/functions_A.txt"
cd "$DIR_B" && slither . --print function-summary 2>/dev/null > "$DIFF_DIR/functions_B.txt"

diff -u "$DIFF_DIR/functions_A.txt" "$DIFF_DIR/functions_B.txt" > "$DIFF_DIR/functions.diff" || true
```

### Step 5: Write Diff Report

Output: `~/.solidity-analyzer/audits/{protocol}/diff-report.md`

```markdown
# Contract Diff Report: {Protocol Name}

## Overview

| | Contract A (Old) | Contract B (New) |
|--|-----------------|-----------------|
| Chain | {chain_name_A} (ID: {chainId_A}) | {chain_name_B} (ID: {chainId_B}) |
| Address | {address_A} | {address_B} |
| Contract Name | {name_A} | {name_B} |
| Compiler | {compiler_A} | {compiler_B} |

## File Changes Summary

| Category | Count | Files |
|----------|-------|-------|
| Modified | X | file1.sol, file2.sol |
| Added | X | newFile.sol |
| Removed | X | oldFile.sol |
| Unchanged | X | lib.sol |

## Storage Layout Changes

| Slot | Variable | Old Type | New Type | Status |
|------|----------|----------|----------|--------|
| 0 | _owner | address | address | Unchanged |
| 5 | _newVar | — | uint256 | **Added** |
| 3 | _removed | uint256 | — | **Removed** ⚠️ |

### Storage Safety Assessment
- [ ] No storage collisions (variables only appended, never inserted or reordered)
- [ ] No type changes on existing slots
- [ ] Gap variables adjusted correctly
- [ ] Proxy admin slot untouched

## Function Signature Changes

### Added Functions
| Function | Visibility | Modifiers |
|----------|-----------|-----------|
| `newFunction(uint256)` | external | onlyAdmin |

### Removed Functions
| Function | Visibility | Risk |
|----------|-----------|------|
| `oldFunction()` | public | ⚠️ Breaking change for integrators |

### Modified Functions
| Function | Change | Risk |
|----------|--------|------|
| `deposit(uint256)` | Added parameter validation | Low |
| `withdraw()` | Changed access control | **High** |

## Critical Changes (Security Review Required)

| # | File | Lines | Change Description | Risk |
|---|------|-------|-------------------|------|
| 1 | Vault.sol | L45-67 | Modified withdraw logic | **High** — review for reentrancy |
| 2 | Auth.sol | L12 | New admin role | **Medium** — access control change |
| 3 | Token.sol | L89 | Updated fee calculation | **Low** — verify math |

## Diff Snippets

### {filename}.sol

```diff
- old code line
+ new code line
```

**Analysis**: {What changed and why it matters}

## Recommendations

1. **{Recommendation 1}**: {description}
2. **{Recommendation 2}**: {description}
```

## Common Scenarios

### Proxy Upgrade (same chain)

```bash
# Old implementation detected via EIP-1967 slot
cast storage PROXY_ADDRESS 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc \
  --rpc-url https://evm.web3gate.xyz/evm/1 --block {old_block}

# New implementation (current)
cast storage PROXY_ADDRESS 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc \
  --rpc-url https://evm.web3gate.xyz/evm/1

# Fetch both, then diff
```

### Cross-chain Comparison

Compare the same protocol deployed on two chains (e.g., Ethereum vs Arbitrum):

```bash
python3 scripts/fetch_contract.py -c 1 -a {eth_address}
python3 scripts/fetch_contract.py -c 42161 -a {arb_address}
# Then diff as above
```

### Fork vs Original

Compare a forked protocol against the original to identify modifications:

```bash
python3 scripts/fetch_contract.py -c 1 -a {original_address}
python3 scripts/fetch_contract.py -c 1 -a {fork_address}
# Focus on: added admin functions, changed fee logic, modified access control
```

## Output Structure

```
~/.solidity-analyzer/audits/{protocol}/
├── diff_{addressA}_{addressB}/
│   ├── full.diff              # Complete recursive diff
│   ├── {filename}.sol.diff    # Per-file diffs
│   ├── storage_A.txt          # Old storage layout
│   ├── storage_B.txt          # New storage layout
│   ├── storage.diff           # Storage layout diff
│   ├── functions_A.txt        # Old function signatures
│   ├── functions_B.txt        # New function signatures
│   ├── functions.diff         # Function signature diff
│   ├── added_files.txt        # New files in B
│   └── removed_files.txt      # Files removed from A
└── diff-report.md             # Structured analysis report
```
