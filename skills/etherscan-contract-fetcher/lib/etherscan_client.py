"""Etherscan API v2 client for fetching contract source code."""
import json
import re
import sys
from pathlib import Path

import requests

from .config import (
    ETHERSCAN_API_URL,
    EIP1967_ADMIN_SLOT,
    EIP1967_BEACON_SLOT,
    EIP1967_IMPLEMENTATION_SLOT,
    get_etherscan_api_key,
)


def is_valid_address(address: str) -> bool:
    """Validate Ethereum address format (0x + 40 hex chars)."""
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))


def get_storage_at(address: str, slot: str, chain_id: int, api_key: str) -> str | None:
    """Read storage slot value from contract using eth_getStorageAt."""
    params = {
        "chainid": chain_id,
        "module": "proxy",
        "action": "eth_getStorageAt",
        "address": address,
        "position": slot,
        "tag": "latest",
        "apikey": api_key
    }

    try:
        response = requests.get(ETHERSCAN_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("jsonrpc") == "2.0" and "result" in data:
            return data["result"]
        return None
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to read storage slot {slot}: {e}")
        return None


def extract_address_from_slot(slot_value: str) -> str | None:
    """Extract address from 32-byte storage slot value."""
    if not slot_value or slot_value == "0x" or slot_value == "0x0":
        return None
    # Storage slot is 32 bytes, address is last 20 bytes
    hex_value = slot_value[2:].zfill(64)
    address = "0x" + hex_value[-40:]
    # Check if it's a zero address
    if address == "0x" + "0" * 40:
        return None
    return address


def detect_eip1967_proxy(address: str, chain_id: int, api_key: str) -> dict:
    """
    Detect if contract is an EIP-1967 proxy and return implementation details.

    Returns dict with:
        - is_proxy: bool
        - implementation_address: str | None
        - beacon_address: str | None
        - admin_address: str | None
    """
    result = {
        "is_proxy": False,
        "implementation_address": None,
        "beacon_address": None,
        "admin_address": None
    }

    # Check implementation slot
    impl_slot = get_storage_at(address, EIP1967_IMPLEMENTATION_SLOT, chain_id, api_key)
    if impl_slot:
        impl_addr = extract_address_from_slot(impl_slot)
        if impl_addr:
            result["is_proxy"] = True
            result["implementation_address"] = impl_addr

    # Check beacon slot
    beacon_slot = get_storage_at(address, EIP1967_BEACON_SLOT, chain_id, api_key)
    if beacon_slot:
        beacon_addr = extract_address_from_slot(beacon_slot)
        if beacon_addr:
            result["is_proxy"] = True
            result["beacon_address"] = beacon_addr
            # Try to get implementation from beacon
            beacon_impl_slot = get_storage_at(beacon_addr, "0x0", chain_id, api_key)
            if beacon_impl_slot:
                beacon_impl = extract_address_from_slot(beacon_impl_slot)
                if beacon_impl:
                    result["implementation_address"] = beacon_impl

    # Check admin slot
    admin_slot = get_storage_at(address, EIP1967_ADMIN_SLOT, chain_id, api_key)
    if admin_slot:
        admin_addr = extract_address_from_slot(admin_slot)
        if admin_addr:
            result["admin_address"] = admin_addr

    return result


def fetch_contract_source(address: str, chain_id: int, api_key: str) -> dict:
    """
    Fetch contract source code from Etherscan API v2.

    Returns:
        API response result dict containing SourceCode, ABI, ContractName, etc.

    Raises:
        SystemExit on API error
    """
    params = {
        "chainid": chain_id,
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": api_key
    }

    try:
        response = requests.get(ETHERSCAN_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            print(f"❌ API Error: {data.get('message', 'Unknown error')}", file=sys.stderr)
            result = data.get("result", "")
            if result:
                print(f"   Details: {result}", file=sys.stderr)
            sys.exit(1)

        results = data.get("result", [])
        if not results:
            print("❌ No contract source found", file=sys.stderr)
            sys.exit(1)

        return results[0]

    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_contract_sources(source_code: str) -> dict[str, str]:
    """
    Parse contract source code, handling both single and multi-file contracts.

    Returns:
        Dict mapping file paths to their source code content
    """
    if not source_code:
        return {}

    # Multi-file contract (JSON format with double braces)
    if source_code.startswith("{{"):
        source_code = source_code[1:-1]  # Remove outer braces
        try:
            sources = json.loads(source_code)
            result = {}
            for file_path, file_data in sources.get("sources", {}).items():
                if isinstance(file_data, dict):
                    result[file_path] = file_data.get("content", "")
                else:
                    result[file_path] = file_data
            return result
        except json.JSONDecodeError:
            return {"Contract.sol": source_code}

    # Single brace JSON format
    if source_code.startswith("{"):
        try:
            sources = json.loads(source_code)
            result = {}
            for file_path, file_data in sources.get("sources", {}).items():
                if isinstance(file_data, dict):
                    result[file_path] = file_data.get("content", "")
                else:
                    result[file_path] = file_data
            return result
        except json.JSONDecodeError:
            return {"Contract.sol": source_code}

    # Plain single-file contract
    return {"Contract.sol": source_code}


def save_contract_sources(
    contract_data: dict,
    output_dir: Path,
    proxy_info: dict | None = None
) -> list[str]:
    """
    Save contract source code to files.

    Args:
        contract_data: API response result dict
        output_dir: Directory to save files
        proxy_info: Optional proxy detection info

    Returns:
        List of saved file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []

    contract_name = contract_data.get("ContractName", "Unknown")
    source_code = contract_data.get("SourceCode", "")

    # Print contract metadata
    print(f"   Contract Name: {contract_name}")
    print(f"   Compiler: {contract_data.get('CompilerVersion', 'Unknown')}")
    print(f"   Optimization: {'Yes' if contract_data.get('OptimizationUsed') == '1' else 'No'}")
    print(f"   Runs: {contract_data.get('Runs', 'N/A')}")
    print(f"   EVM Version: {contract_data.get('EVMVersion', 'Default')}")
    print(f"   License: {contract_data.get('LicenseType', 'Unknown')}")

    if not source_code:
        print("   ⚠️  Contract source code not verified")
        return saved_files

    # Save source files
    source_dir = output_dir / "source"
    sources = parse_contract_sources(source_code)

    for file_path, content in sources.items():
        filepath = source_dir / file_path.lstrip("/")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        saved_files.append(str(filepath))

    # Save ABI
    abi = contract_data.get("ABI", "")
    if abi and abi != "Contract source code not verified":
        abi_path = output_dir / "abi.json"
        try:
            abi_json = json.loads(abi)
            abi_path.write_text(json.dumps(abi_json, indent=2))
            saved_files.append(str(abi_path))
        except json.JSONDecodeError:
            pass

    # Save metadata
    metadata = {
        "contract_name": contract_name,
        "compiler_version": contract_data.get("CompilerVersion"),
        "optimization_used": contract_data.get("OptimizationUsed") == "1",
        "runs": contract_data.get("Runs"),
        "evm_version": contract_data.get("EVMVersion"),
        "license": contract_data.get("LicenseType"),
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    saved_files.append(str(metadata_path))

    # Save proxy info if provided
    if proxy_info and proxy_info.get("is_proxy"):
        proxy_path = output_dir / "proxy_info.json"
        proxy_path.write_text(json.dumps(proxy_info, indent=2))
        saved_files.append(str(proxy_path))

    return saved_files
