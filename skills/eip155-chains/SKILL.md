---
name: eip155-chains
description: >
  EVM chain metadata and RPC endpoint management. Provides chain info lookup, healthy RPC
  discovery via the eip155-chains npm package, and EVM Gateway public/private JSON-RPC
  endpoints for 20+ chains. This skill should be used when the user needs RPC URLs,
  chain IDs, chain metadata, or wants to connect to an EVM chain.
  Triggers include: "RPC URL", "chain ID", "EVM chain", "JSON-RPC endpoint",
  "connect to Ethereum", "connect to Arbitrum", "which chain", "chain info",
  "RPC端点", "链ID", "节点地址", "EVM Gateway", "web3gate".
---

# eip155-chains

EVM chain metadata lookup and RPC endpoint management — via the `eip155-chains` npm package and EVM Gateway.

## EVM Gateway (Quick RPC)

EVM Gateway provides JSON-RPC endpoints for all major EVM chains with a single URL pattern.

### Public Endpoint (no API key)

```
https://evm.web3gate.xyz/evm/{chain_id}
```

### Private Endpoint (with API key)

```
https://evm.web3gate.xyz/evm/{chain_id}/api_key/{api_key}
```

### Examples

| Chain | Chain ID | Public RPC URL |
|-------|----------|----------------|
| Ethereum | 1 | `https://evm.web3gate.xyz/evm/1` |
| Optimism | 10 | `https://evm.web3gate.xyz/evm/10` |
| BNB Chain | 56 | `https://evm.web3gate.xyz/evm/56` |
| Polygon | 137 | `https://evm.web3gate.xyz/evm/137` |
| Base | 8453 | `https://evm.web3gate.xyz/evm/8453` |
| Arbitrum | 42161 | `https://evm.web3gate.xyz/evm/42161` |
| Avalanche | 43114 | `https://evm.web3gate.xyz/evm/43114` |
| Fantom | 250 | `https://evm.web3gate.xyz/evm/250` |
| Linea | 59144 | `https://evm.web3gate.xyz/evm/59144` |
| Scroll | 534352 | `https://evm.web3gate.xyz/evm/534352` |

### Quick Test

```bash
# Test Ethereum mainnet
curl -s -X POST https://evm.web3gate.xyz/evm/1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# With API key
curl -s -X POST https://evm.web3gate.xyz/evm/1/api_key/YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Using cast (Foundry)
cast block-number --rpc-url https://evm.web3gate.xyz/evm/1
```

When to use EVM Gateway vs other providers:
- **EVM Gateway**: Default choice. Simple URL pattern, no signup needed for public endpoint.
- **Alchemy/Infura**: When archive node access or advanced features (debug_*, trace_*) are required.

## eip155-chains npm Package

The `eip155-chains` package aggregates chain metadata and RPC endpoints from multiple sources (viem, chainid.network, 1rpc, flashbots) into a single API.

### Install

```bash
npm install eip155-chains
```

### Get Chain Info

```typescript
import { getChainById } from 'eip155-chains';

const options = {
  apiKey: {
    INFURA_API_KEY: 'your_infura_key',
    ALCHEMY_API_KEY: 'your_alchemy_key',
  },
  healthyCheckEnabled: true,  // Filter out dead RPCs
  filters: {
    features: ['privacy'],    // Optional: filter by features
  },
};

const chainInfo = await getChainById(1, options);
console.log('Chain name:', chainInfo.name);
console.log('RPCs:', chainInfo.rpc);
console.log('HTTPS RPCs:', chainInfo.classifiedRpc.https);
```

### Get RPCs Only

```typescript
import { getRpcsByChainId } from 'eip155-chains';

const rpcs = await getRpcsByChainId(1, [], true); // chainId, extraRpcs, healthyCheck
// Returns: Array<{ url: string, latency?: number, features?: string[] }>
```

### Create Ethers Provider

```typescript
import { getEthersProvider } from 'eip155-chains';

const [provider, stop] = await getEthersProvider(1, {
  healthyCheckEnabled: true,
  providerConfig: { type: 'fallback' }, // or 'race'
});

const blockNumber = await provider.getBlockNumber();
console.log('Block:', blockNumber);

// Release when done
await stop();
```

### RPC Features

RPCs can be filtered by features:

| Feature | Description |
|---------|-------------|
| `free to use` | No API key required |
| `privacy` | Does not log requests |
| `MEV protection` | Protects against frontrunning |
| `phishing protection` | Blocks known phishing contracts |
| `load balance` | Load-balanced endpoint |

```typescript
import { filterRpcListByFeatures } from 'eip155-chains';

const privacyRpcs = filterRpcListByFeatures(rpcs, ['privacy', 'MEV protection']);
```

### Register Custom RPC Service

Add EVM Gateway or any custom RPC source:

```typescript
import { registerRpcService, type RpcService } from 'eip155-chains';

const evmGateway: RpcService = {
  getRpcList: (chainId: number, apiKey?: string) => {
    const base = `https://evm.web3gate.xyz/evm/${chainId}`;
    const url = apiKey ? `${base}/api_key/${apiKey}` : base;
    return [{ url: url as `https://${string}` }];
  },
  getFeatures: () => ['free to use', 'load balance'],
};

registerRpcService(evmGateway);
```

### EIP-1193 Provider Adapter

For libraries that expect EIP-1193 interface:

```typescript
import { RacedEIP1193Provider, EthersJsonRpcProviderEIP1193Adapter } from 'eip155-chains';
import { JsonRpcProvider } from '@ethersproject/providers';

// Wrap ethers providers as EIP-1193
const providers = urls.map(url =>
  new EthersJsonRpcProviderEIP1193Adapter(new JsonRpcProvider(url))
);

// Race multiple providers (fastest response wins)
const racedProvider = new RacedEIP1193Provider(providers);
const blockNumber = await racedProvider.request({ method: 'eth_blockNumber' });
```

## Common Chain IDs

| Chain | ID | Native Token |
|-------|-----|-------------|
| Ethereum | 1 | ETH |
| Goerli (testnet) | 5 | ETH |
| Sepolia (testnet) | 11155111 | ETH |
| Optimism | 10 | ETH |
| BNB Chain | 56 | BNB |
| Polygon | 137 | MATIC |
| Fantom | 250 | FTM |
| Base | 8453 | ETH |
| Arbitrum One | 42161 | ETH |
| Avalanche C-Chain | 43114 | AVAX |
| Linea | 59144 | ETH |
| Scroll | 534352 | ETH |
| zkSync Era | 324 | ETH |
| Polygon zkEVM | 1101 | ETH |

Full list: https://chainid.network
