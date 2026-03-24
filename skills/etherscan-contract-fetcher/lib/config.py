"""Configuration management for Etherscan Contract Fetcher."""
import json
import os
import sys
from pathlib import Path

# Paths
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
CHAINS_FILE = DATA_DIR / "chains.json"

# EVM Gateway template
EVM_GATEWAY_TEMPLATE = "https://evm.web3gate.xyz/evm/{chain_id}"

# Default output directory (current working directory)
DEFAULT_OUTPUT_BASE = "."

# Etherscan API
ETHERSCAN_API_URL = "https://api.etherscan.io/v2/api"

# EIP-1967 storage slots
EIP1967_IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
EIP1967_BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
EIP1967_ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"


def get_rpc_url(chain_id: int) -> str:
    """Get RPC URL for a specific chain using EVM Gateway."""
    return EVM_GATEWAY_TEMPLATE.format(chain_id=chain_id)


def get_etherscan_api_key() -> str:
    """
    Get Etherscan API key from environment variable.

    Returns:
        API key string

    Raises:
        SystemExit if ETHERSCAN_API_KEY not set
    """
    key = os.environ.get("ETHERSCAN_API_KEY")
    if not key:
        print("Error: ETHERSCAN_API_KEY environment variable not set", file=sys.stderr)
        print("  Please set it: export ETHERSCAN_API_KEY=your_api_key", file=sys.stderr)
        sys.exit(1)

    masked_key = key[:4] + "*" * (len(key) - 4)
    print(f"Using Etherscan API Key: {masked_key}")

    return key


def get_output_dir(user_provided: str | None = None) -> Path:
    """
    Get output directory.

    Args:
        user_provided: User-specified output directory

    Returns:
        Resolved output directory path
    """
    output_dir = Path(user_provided) if user_provided else Path(DEFAULT_OUTPUT_BASE)
    print(f"Output directory: {output_dir}")
    return output_dir


def get_chain_info(chain_id: int) -> dict | None:
    """
    Get chain information from cached chains.json.

    Args:
        chain_id: Chain ID to look up

    Returns:
        Chain info dict or None if not found
    """
    if not CHAINS_FILE.exists():
        return None

    try:
        with open(CHAINS_FILE) as f:
            chains = json.load(f)

        for chain in chains:
            if chain.get("chainId") == chain_id:
                return chain
        return None
    except (json.JSONDecodeError, IOError):
        return None


def get_chain_name(chain_id: int) -> str:
    """Get human-readable chain name."""
    info = get_chain_info(chain_id)
    if info:
        return info.get("name", f"Chain {chain_id}")
    return f"Chain {chain_id}"
