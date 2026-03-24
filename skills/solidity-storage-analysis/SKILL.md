---
name: solidity-storage-analysis
description: Analyze Solidity contract storage using Foundry storage layout inspection, EIP-1967 proxy slot verification, live on-chain state snapshots via cast storage, and storage collision detection. Triggers: "storage layout", "storage analysis", "cast storage", "proxy slots", "存储布局", "链上状态"
---

# solidity-storage-analysis

Perform storage layout analysis and live on-chain state verification for Solidity contracts. This is Step 5 of a solidity audit workflow.

All outputs go to `~/.solidity-analyzer/audits/{protocol}/`.

## When to use

Activate this skill when the user requests storage layout inspection, proxy slot verification, on-chain state snapshots, or storage collision analysis for Solidity contracts.

## RPC Configuration

Use the following RPC endpoint pattern for all on-chain queries:

```
https://evm.web3gate.xyz/evm/{chainId}
```

Common chain IDs: 1 (Ethereum), 56 (BSC), 137 (Polygon), 42161 (Arbitrum), 10 (Optimism).

## Commands

```bash
# Read on-chain storage at a specific slot
cast storage ADDRESS SLOT --rpc-url https://evm.web3gate.xyz/evm/{chainId}

# EIP-1967 Implementation slot
cast storage ADDRESS 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc --rpc-url https://evm.web3gate.xyz/evm/1

# Generate storage layout from source
forge inspect ContractName storage-layout --pretty

# Read live contract state
cast call ADDRESS "owner()" --rpc-url $RPC_URL
cast call ADDRESS "paused()" --rpc-url $RPC_URL
cast call ADDRESS "totalSupply()" --rpc-url $RPC_URL
```

## EIP-1967 Proxy Slots

Check these standard proxy slots on any upgradeable contract:

| Slot | Purpose |
|------|---------|
| `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` | Implementation |
| `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50` | Beacon |
| `0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103` | Admin |

Read all three slots for every proxy contract. A non-zero value indicates the slot is active. Decode the returned bytes32 as an address (strip leading zeros).

## Instructions

1. **Prepare the output directory.** Create `~/.solidity-analyzer/audits/{protocol}/` if it does not exist.

2. **Generate the storage layout.** Run `forge inspect ContractName storage-layout --pretty` for every in-scope contract. Record each slot's name, type, offset, and size.

3. **Check EIP-1967 proxy slots.** For each contract address, read the Implementation, Beacon, and Admin slots using `cast storage`. If the Implementation slot returns a non-zero value, the contract is a proxy -- record the implementation address and repeat the storage layout analysis on the implementation contract.

4. **Snapshot live state.** Use `cast call` to read critical state variables (owner, paused, totalSupply, and any protocol-specific getters). Record the block height and query time.

5. **Detect storage collisions.** Compare the storage layouts of proxy and implementation contracts. Flag any slot overlaps between inherited contracts or between proxy admin storage and implementation storage.

6. **Write the output document.** Generate `~/.solidity-analyzer/audits/{protocol}/05-storage-analysis.md` using the template below.

7. **Summarize findings.** Report any storage collisions, unexpected proxy configurations, or live state anomalies to the user.

## Output Document Template

Write `audits/{protocol}/05-storage-analysis.md` with the following structure:

```markdown
# Storage Analysis: {Protocol}

**Date**: {YYYY-MM-DD}
**Auditor**: Claude Code
**Chain**: {chain name} (ID: {chainId})

## Contract Storage Layout

### {ContractName} (`{address}`)

| Slot | Name | Type | Offset | Size |
|------|------|------|--------|------|
| 0    | _initialized | uint8 | 0 | 1 |
| 0    | _initializing | bool | 1 | 1 |
| ...  | ... | ... | ... | ... |

## Live Contract State Snapshot

**Query Time**: {ISO 8601 timestamp}
**Block Height**: {block number}

### {ContractName} (`{address}`)

| Variable | Type | On-chain Value | Analysis |
|----------|------|----------------|----------|
| owner | address | 0x... | Matches expected multisig |
| paused | bool | false | Protocol is active |
| totalSupply | uint256 | ... | Consistent with documented supply |

**Cast commands used:**
\```bash
cast call {address} "owner()" --rpc-url https://evm.web3gate.xyz/evm/{chainId}
cast call {address} "paused()" --rpc-url https://evm.web3gate.xyz/evm/{chainId}
cast call {address} "totalSupply()" --rpc-url https://evm.web3gate.xyz/evm/{chainId}
\```

## Critical Storage Slots

List any slots that hold privileged roles, pause flags, or monetary values. Flag slots that lack access control or that multiple contracts share.

| Contract | Slot | Variable | Risk Level | Notes |
|----------|------|----------|------------|-------|
| ... | ... | ... | ... | ... |

## Proxy Storage (if applicable)

### {ProxyContractName} (`{proxy address}`)

| Slot | EIP-1967 Role | Value | Decoded Address |
|------|---------------|-------|-----------------|
| 0x360894...bbc | Implementation | 0x000...{addr} | {implementation address} |
| 0xa3f0ad...d50 | Beacon | 0x000...000 | (not set) |
| 0xb53127...103 | Admin | 0x000...{addr} | {admin address} |

## Storage Safety Assessment

- [ ] **No storage collisions**: Proxy and implementation layouts do not overlap on any slot.
- [ ] **Gap variables present**: Upgradeable base contracts reserve `__gap` slots for future storage.
- [ ] **Immutables handled correctly**: Immutable variables are stored in bytecode, not in storage slots.
- [ ] **Live state matches architecture**: On-chain values (owner, paused, supply) are consistent with the protocol's documented architecture and expected configuration.
```
