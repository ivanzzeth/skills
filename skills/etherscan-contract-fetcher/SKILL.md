---
name: etherscan-contract-fetcher
description: >
  Fetch verified smart contract source code, ABI, and metadata from Etherscan API v2.
  Supports all EVM chains. Automatically detects EIP-1967 proxy contracts and fetches
  implementation source. This skill should be used when the user provides a contract
  address and wants to view, analyze, or audit its source code.
  Triggers include: "fetch contract", "get contract source", "download contract",
  "contract code", "contract address 0x", "etherscan source", "verified contract",
  "proxy implementation", "check contract on etherscan", "获取合约源码", "查合约".
---

# etherscan-contract-fetcher

Fetch verified smart contract source code from Etherscan API v2 for any EVM chain.

## Prerequisites

### Environment Variable

```bash
export ETHERSCAN_API_KEY=your_api_key
```

Get API key: https://etherscan.io/myapikey

One API key works for all chains via Etherscan API v2.

### Python Dependencies

The skill includes a bundled Python script. First-time setup:

```bash
pip install requests
```

## Usage

### Fetch Contract Source

```bash
# Default output: ~/.solidity-analyzer/contracts/{chainId}/{address}
python3 scripts/fetch_contract.py \
  --chain-id 1 \
  --address 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D

# Custom output directory
python3 scripts/fetch_contract.py \
  --chain-id 1 \
  --address 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D \
  --output-dir /path/to/custom/dir
```

**Parameters:**
- `--chain-id`, `-c`: Chain ID (see Supported Chains below)
- `--address`, `-a`: Contract address (0x...)
- `--output-dir`, `-o`: Custom output directory (default: `~/.solidity-analyzer/contracts/{chainId}/{address}`)

### Standard Directory Structure

All solidity analysis skills (etherscan-contract-fetcher, solidity-poc, solidity-audit) share a common workspace at `~/.solidity-analyzer/`:

```
~/.solidity-analyzer/
├── contracts/{chainId}/{address}/     # Fetched contract sources
│   ├── source/                        # Solidity source files
│   │   ├── Contract.sol
│   │   └── interfaces/
│   ├── abi.json                       # Contract ABI
│   ├── metadata.json                  # Compiler version, optimization, etc.
│   └── proxy_info.json               # If proxy detected
├── audits/{protocol}/                 # Audit reports and analysis (solidity-audit)
│   ├── 01-source-analysis.md
│   ├── ...
│   └── AUDIT-REPORT.md
└── poc/{protocol}/                    # POC tests (solidity-poc)
    ├── test/poc/
    └── foundry.toml
```

### Proxy Detection

The script automatically detects EIP-1967 proxy contracts by reading standard storage slots:

| Slot | Purpose |
|------|---------|
| `0x360894...` | Implementation address |
| `0xb53127...` | Admin address |
| `0xa3f0ad...` | Beacon address |

If a proxy is detected:
1. Proxy source is saved to `{output-dir}/`
2. Implementation source is automatically fetched to `{output-dir}/` as well
3. `proxy_info.json` documents the proxy relationship

### Scope Confirmation

After fetching, confirm audit scope with the user:

| Field | Action |
|-------|--------|
| In-scope contracts | List fetched contracts with SLOC and priority |
| Out-of-scope | Standard libraries, already-audited dependencies |
| Trust assumptions | External dependencies treated as trusted |

## Supported Chains

Etherscan API v2 supports all major EVM chains with a single API key:

| Chain | Chain ID |
|-------|----------|
| Ethereum | 1 |
| Optimism | 10 |
| BNB Chain | 56 |
| Polygon | 137 |
| Base | 8453 |
| Arbitrum | 42161 |
| Avalanche | 43114 |
| Fantom | 250 |
| Linea | 59144 |
| Scroll | 534352 |

For the full list, see: https://docs.etherscan.io/etherscan-v2

## Troubleshooting

### "ETHERSCAN_API_KEY not set"
```bash
export ETHERSCAN_API_KEY=your_key
```

### "Contract source code not verified"
The contract has not published its source on Etherscan. Options:
- Check if it's a proxy — the implementation may be verified
- Try a different block explorer (Sourcify, Blockscout)
- Decompile bytecode as last resort (limited usefulness)

### Rate limiting
Etherscan free tier: 5 calls/second. The script handles retries automatically.
