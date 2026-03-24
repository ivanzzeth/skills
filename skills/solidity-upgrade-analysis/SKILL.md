---
name: solidity-upgrade-analysis
description: Analyze upgrade risks for upgradeable contracts — storage collision detection, initializer security, proxy pattern validation (UUPS/Transparent/Beacon). Triggers: "upgrade analysis", "proxy upgrade", "storage collision", "initializer", "升级分析", "代理升级"
---

# solidity-upgrade-analysis

## When to Use

Use this skill only for upgradeable contracts that follow EIP-1967, UUPS, Transparent Proxy, or Beacon Proxy patterns. Do not apply to immutable contracts or non-proxy deployments.

## Checklist

### A. Storage Layout Compatibility

- [ ] New variables are appended only — never inserted between existing slots
- [ ] No type changes on existing variables (e.g., `uint256` to `uint128`)
- [ ] Gap variables (`__gap`) are maintained and decremented correctly
- [ ] Inherited contract order is unchanged
- [ ] No storage slot collisions between proxy and implementation

### B. Initialization Safety

- [ ] Initializer cannot be called twice (`initializer` modifier or equivalent guard)
- [ ] All state variables are properly initialized in `initialize()`
- [ ] No constructor logic that conflicts with proxy initialization
- [ ] `_disableInitializers()` is called in the constructor of the implementation
- [ ] Re-initialization uses `reinitializer(n)` with correct version number

### C. Access Control

- [ ] Upgrade permission is properly restricted (`onlyOwner`, `onlyRole`, or equivalent)
- [ ] Time-lock or multi-sig is required for upgrade execution
- [ ] Emergency pause mechanism exists and is tested
- [ ] `_authorizeUpgrade()` (UUPS) has proper access control
- [ ] Proxy admin cannot call implementation functions directly (Transparent Proxy)

### D. Logic Changes

- [ ] Function signatures remain compatible (no selector collisions)
- [ ] Return values are consistent with previous implementation
- [ ] Event emissions are unchanged or only additive
- [ ] No removed public/external functions that callers depend on
- [ ] Fallback/receive function behavior is preserved

## Commands

```bash
# Compare old and new storage layouts
forge inspect OldContract storage-layout --pretty
forge inspect NewContract storage-layout --pretty

# Check if implementation is initialized
cast call IMPL_ADDRESS "initialized()(bool)" --rpc-url $RPC_URL

# Read EIP-1967 implementation slot
cast storage PROXY_ADDRESS 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc --rpc-url $RPC_URL

# Read EIP-1967 admin slot
cast storage PROXY_ADDRESS 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103 --rpc-url $RPC_URL

# Diff storage layouts
diff <(forge inspect OldContract storage-layout --pretty) <(forge inspect NewContract storage-layout --pretty)
```

## Output Document

Write the analysis to `~/.solidity-analyzer/audits/{protocol}/07-upgrade-analysis.md` using the following template:

```markdown
# Upgrade Analysis: {Protocol}

**Date**: {YYYY-MM-DD}
**Auditor**: Claude
**Proxy Pattern**: {UUPS | Transparent | Beacon | Custom}
**Proxy Address**: `{address}`
**Old Implementation**: `{address}`
**New Implementation**: `{address}`

## Storage Compatibility

### Old Implementation Layout

| Slot | Variable | Type | Status |
|------|----------|------|--------|
| 0 | _initialized | uint8 | ✅ Unchanged |
| 1 | _owner | address | ✅ Unchanged |
| ... | ... | ... | ... |

### New Implementation Layout

| Slot | Variable | Type | Status |
|------|----------|------|--------|
| 0 | _initialized | uint8 | ✅ Unchanged |
| 1 | _owner | address | ✅ Unchanged |
| N | newVariable | uint256 | ✅ Appended |
| ... | ... | ... | ... |

### Storage Gap Analysis

- Old `__gap` size: {N} slots
- New `__gap` size: {M} slots
- Variables added: {K}
- Gap correctly decremented: {Yes/No}

## Initialization Analysis

- Initializer guard present: {Yes/No}
- `_disableInitializers()` in constructor: {Yes/No}
- Re-initialization version: {N/A or version number}
- Uninitialized state variables: {List or "None"}

## Breaking Changes

- [ ] Function signatures changed
- [ ] Events modified or removed
- [ ] Return values changed
- [ ] Public/external functions removed
- [ ] Fallback behavior altered

## Upgrade Risks

| Risk | Severity | Description |
|------|----------|-------------|
| {Risk name} | {Critical/High/Medium/Low} | {Description of the risk} |
| ... | ... | ... |

## Recommendations

1. {First recommendation}
2. {Second recommendation}
3. {Additional recommendations as needed}
```
