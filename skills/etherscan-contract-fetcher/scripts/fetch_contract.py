#!/usr/bin/env python3
"""
Fetch verified smart contract source code from Etherscan API v2.
Supports all EVM chains. Automatically detects EIP-1967 proxy contracts.
"""
import argparse
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import get_etherscan_api_key, get_output_dir, get_chain_name
from lib.etherscan_client import (
    is_valid_address,
    detect_eip1967_proxy,
    fetch_contract_source,
    save_contract_sources,
)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch smart contract source code from Etherscan API v2"
    )
    parser.add_argument(
        "--chain-id", "-c",
        type=int,
        required=True,
        help="Blockchain chain ID (e.g., 1 for Ethereum, 42161 for Arbitrum)"
    )
    parser.add_argument(
        "--address", "-a",
        type=str,
        required=True,
        help="Contract address (0x-prefixed)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Base output directory (default: projects/eth/solidity)"
    )
    parser.add_argument(
        "--no-proxy-detection",
        action="store_true",
        help="Disable automatic EIP-1967 proxy detection"
    )
    parser.add_argument(
        "--proxy-only",
        action="store_true",
        help="Only download the proxy contract, skip implementation"
    )

    args = parser.parse_args()

    # Validate address
    address = args.address.strip().lower()
    if not is_valid_address(address):
        print(f"❌ Invalid address format: {address}", file=sys.stderr)
        print("   Address must be 0x-prefixed followed by 40 hex characters", file=sys.stderr)
        sys.exit(1)

    # Get API key (validates and displays masked key)
    api_key = get_etherscan_api_key()

    # Get output directory
    # Default: ~/.solidity-analyzer/contracts/{chainId}/{address}
    if args.output_dir is None:
        output_dir = get_output_dir(None) / "contracts" / str(args.chain_id) / address
    else:
        output_dir = get_output_dir(args.output_dir)

    chain_name = get_chain_name(args.chain_id)

    print("")
    print("=" * 60)
    print(f"📥 Fetching contract: {address}")
    print(f"   Chain: {chain_name} (ID: {args.chain_id})")
    print(f"   Output: {output_dir}")
    print("=" * 60)

    # Detect EIP-1967 proxy
    proxy_info = None
    implementation_address = None

    if not args.no_proxy_detection:
        print("")
        print("🔍 Checking for EIP-1967 proxy pattern...")
        proxy_info = detect_eip1967_proxy(address, args.chain_id, api_key)

        if proxy_info["is_proxy"]:
            print("   ✅ EIP-1967 PROXY DETECTED!")
            if proxy_info["implementation_address"]:
                print(f"      Implementation: {proxy_info['implementation_address']}")
                implementation_address = proxy_info["implementation_address"]
            if proxy_info["beacon_address"]:
                print(f"      Beacon: {proxy_info['beacon_address']}")
            if proxy_info["admin_address"]:
                print(f"      Admin: {proxy_info['admin_address']}")
        else:
            print("   Not a proxy contract (or not using EIP-1967 standard)")

    # Fetch and save proxy/main contract
    print("")
    print("📄 Fetching contract source...")
    contract_data = fetch_contract_source(address, args.chain_id, api_key)
    saved_files = save_contract_sources(contract_data, output_dir, proxy_info)

    # Fetch implementation if proxy detected
    if implementation_address and not args.proxy_only:
        print("")
        print("=" * 60)
        print(f"📥 Fetching implementation contract: {implementation_address}")
        print("=" * 60)

        impl_output_dir = output_dir.parent / implementation_address
        print("")
        print("📄 Fetching implementation source...")
        impl_data = fetch_contract_source(implementation_address, args.chain_id, api_key)
        impl_saved = save_contract_sources(impl_data, impl_output_dir)
        saved_files.extend(impl_saved)

        # Create reference file in proxy directory
        impl_ref_path = output_dir / "IMPLEMENTATION_ADDRESS.txt"
        impl_ref_path.write_text(implementation_address)

    # Summary
    print("")
    print("=" * 60)
    print(f"✅ Done! {len(saved_files)} files saved")
    print(f"   📁 {output_dir}")
    if implementation_address and not args.proxy_only:
        print(f"   📁 {output_dir.parent / implementation_address}")
        print("")
        print("💡 For analysis, focus on the IMPLEMENTATION contract.")
    print("=" * 60)


if __name__ == "__main__":
    main()
