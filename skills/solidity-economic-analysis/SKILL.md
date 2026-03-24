---
name: solidity-economic-analysis
description: >
  Verify protocol invariants, analyze economic attack vectors (flash loan, MEV, sandwich attacks,
  oracle manipulation), and conduct OSINT research on historical exploits and security firm analyses.
  Steps 8 + 8.5 of the Solidity audit workflow. All outputs go to ~/.solidity-analyzer/audits/{protocol}/.
  Triggers: "economic analysis", "invariant", "flash loan attack", "MEV analysis", "sandwich attack",
  "oracle manipulation", "经济攻击", "不变量分析", "闪电贷"
---

# solidity-economic-analysis

Steps 8 and 8.5 of the Solidity audit workflow. Verify protocol invariants, analyze economic attack surfaces (flash loans, MEV, sandwich attacks, oracle manipulation), and conduct internet research (OSINT) on the protocol and similar projects. Integrate all findings into a single output document.

## Prerequisites

1. **Prior audit steps completed**: Steps 1-7 outputs must exist in `~/.solidity-analyzer/audits/{protocol}/`.
2. **Contract source fetched**: Source code at `~/.solidity-analyzer/contracts/{chainId}/{address}/source/`.
3. **Foundry installed**: Verify with `forge --version`. Required for invariant test examples.
4. **Internet access**: Required for OSINT research in Step 8.5.

## Output

Write all findings to a single file:

```
~/.solidity-analyzer/audits/{protocol}/08-invariant-economic.md
```

OSINT findings are integrated directly into this document, not written to a separate file.

---

## Step 8: Invariant & Economic Analysis

### 8.1 Protocol Invariant Analysis

Identify all protocol invariants. Start with these common DeFi invariant categories:

#### Common DeFi Invariants

| Category | Invariant | Formula |
|----------|-----------|---------|
| **Token** | Total supply equals sum of all balances | `totalSupply == sum(balances[i])` for all `i` |
| **AMM** | Constant product holds after every swap | `reserve0 * reserve1 >= k` (k only increases from fees) |
| **Lending** | Total borrowed never exceeds collateral-adjusted deposits | `totalBorrowed <= totalDeposited * collateralFactor` |
| **Vault** | Sum of user shares equals total shares | `sum(userShares[i]) == totalShares` for all `i` |
| **Staking** | Reward distribution is proportional to stake | `userReward[i] == totalRewards * (stake[i] / totalStake)` |
| **Bridge** | Locked on source equals minted on destination | `locked[srcChain] == minted[dstChain]` |

#### Invariant Verification Table

For each identified invariant, fill in this table:

| ID | Invariant | Formula | Verification Method | Status |
|----|-----------|---------|---------------------|--------|
| INV-01 | {description} | {mathematical formula} | {on-chain check / Foundry test / manual} | {HOLDS / BROKEN / CONDITIONAL} |
| INV-02 | {description} | {mathematical formula} | {verification method} | {status} |

#### Foundry Invariant Test Example

Write invariant tests for every identified invariant. Use this template as a starting point:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/Token.sol";

contract InvariantTest is Test {
    Token token;
    address[] holders;

    function setUp() public {
        token = new Token("Test", "TST", 1_000_000e18);
        // Set up actors
        holders.push(address(0x1));
        holders.push(address(0x2));
        holders.push(address(0x3));
        // Seed balances
        token.transfer(holders[0], 100e18);
        token.transfer(holders[1], 200e18);
        // Target the token contract for fuzzing
        targetContract(address(token));
    }

    /// @notice totalSupply must always equal the sum of all holder balances
    function invariant_totalSupplyMatchesBalances() public view {
        uint256 sumBalances = 0;
        for (uint256 i = 0; i < holders.length; i++) {
            sumBalances += token.balanceOf(holders[i]);
        }
        // Include deployer balance
        sumBalances += token.balanceOf(address(this));
        assertEq(token.totalSupply(), sumBalances, "INV-01: totalSupply != sum(balances)");
    }

    /// @notice Admin address must never be address(0)
    function invariant_adminNeverZero() public view {
        assertTrue(token.admin() != address(0), "INV-02: admin is zero address");
    }
}
```

Run invariant tests:

```bash
forge test --match-contract InvariantTest -vvv 2>&1 | tee /tmp/invariant_test_result.txt
```

### 8.2 Economic Attack Analysis

#### 8.2a Flash Loan Attack Vectors

Identify all functions vulnerable to single-transaction manipulation via flash loans:

| Attack Type | Risk | Description | Mitigation |
|-------------|------|-------------|------------|
| **Price Manipulation** | Critical | Attacker borrows large amount, manipulates spot price in a pool, exploits price-dependent logic (e.g., collateral valuation), repays loan in same tx | Use TWAP oracles; add minimum liquidity checks; implement price deviation circuit breakers |
| **Governance Hijack** | High | Attacker flash-borrows governance tokens, votes on or executes a malicious proposal, returns tokens | Require token lock period before voting; snapshot-based voting power; time-delayed execution |
| **Liquidation Arbitrage** | High | Attacker manipulates price to make positions liquidatable, liquidates at a discount, restores price | Use time-weighted prices for liquidation triggers; add liquidation delay; require multi-block confirmation |
| **Reentrancy via Callback** | High | Flash loan callback re-enters protocol functions before state is updated | Follow CEI pattern; use reentrancy guards on all external-facing functions |

Check each protocol function:

- [ ] Does any function read a spot price that can be manipulated in the same block?
- [ ] Does any function allow large state changes without time delay?
- [ ] Are there callback functions that could re-enter the protocol?
- [ ] Can governance actions be executed in the same block as token acquisition?

#### 8.2b MEV Analysis

| Vector | Risk | Description |
|--------|------|-------------|
| **Frontrunning** | High | Attacker observes pending tx in mempool, submits same action with higher gas to execute first (e.g., sandwich a large swap, snipe a liquidation) |
| **Backrunning** | Medium | Attacker submits tx immediately after a target tx to capture arbitrage (e.g., after a large price move, after oracle update) |
| **Time-bandit** | Low | Miner/validator reorgs blocks to capture past MEV opportunities; primarily a theoretical risk on high-value transactions |

**MEV Mitigation Checklist:**

- [ ] **Commit-reveal scheme**: Sensitive operations (auctions, votes, large swaps) use a two-phase commit-reveal pattern
- [ ] **Private mempool / relay**: Users can submit transactions via Flashbots Protect, MEV Blocker, or similar private relays
- [ ] **Slippage protection**: All swap functions enforce user-specified `minAmountOut` / `maxAmountIn` parameters
- [ ] **Deadline checks**: All time-sensitive operations include a `deadline` parameter checked with `require(block.timestamp <= deadline)`
- [ ] **Batch auctions**: Protocol uses batch settlement to eliminate ordering advantages

#### 8.2c Sandwich Attack Analysis

```
Block N (single block):
┌─────────────────────────────────────────┐
│                                         │
│  Tx 1: Attacker buys token              │
│         (frontrun — pushes price up)    │
│                                         │
│  Tx 2: Victim swap executes             │
│         (buys at inflated price)        │
│                                         │
│  Tx 3: Attacker sells token             │
│         (backrun — profits from         │
│          price impact of Tx 2)          │
│                                         │
└─────────────────────────────────────────┘
Profit = Attacker sell proceeds - Attacker buy cost - gas fees
```

**Vulnerable Functions:**

| Function | Risk | Mitigation |
|----------|------|------------|
| `swap(tokenIn, tokenOut, amountIn)` without slippage param | Critical | Add `minAmountOut` parameter; revert if output below threshold |
| `addLiquidity()` without min amounts | High | Add `minTokenA` / `minTokenB` parameters to prevent value extraction |
| `removeLiquidity()` without min amounts | High | Add `minTokenA` / `minTokenB` parameters |
| `deposit()` that mints shares at spot rate | Medium | Use TWAP for share price; add deposit delay or commit-reveal |
| `liquidate()` with no access restriction | Medium | Use Dutch auction for liquidations; batch liquidations per block |

#### 8.2d Oracle Manipulation

| Oracle Type | Risk | Notes |
|-------------|------|-------|
| **Spot price** (e.g., `getReserves()`) | Critical | Trivially manipulable in a single transaction via flash loan. NEVER use as a price feed for value calculations. |
| **TWAP** (Uniswap v2/v3 oracle) | Medium | Resistant to single-block manipulation but vulnerable to multi-block attacks if observation window is short (< 30 min). Cost of attack scales with pool liquidity and window length. |
| **Chainlink** | Low | Decentralized oracle network with multiple data sources. Still check for staleness, deviation thresholds, and sequencer uptime (L2). |
| **Band / API3 / Pyth** | Medium | Varies by network; check update frequency, data source count, and push vs pull model. |
| **On-chain calculation** (e.g., `balanceOf / totalSupply`) | High | Manipulable via donation attacks (direct token transfers) or flash loans. |

**Oracle Security Checklist:**

- [ ] **TWAP, not spot**: Protocol uses time-weighted average price, not instantaneous spot price
- [ ] **Multiple sources**: Price feeds aggregate from 2+ independent oracle sources
- [ ] **Staleness check**: `require(block.timestamp - updatedAt < MAX_STALENESS)` on every oracle read
- [ ] **Deviation threshold**: Revert or pause if price deviates > X% from previous known good value
- [ ] **L2 sequencer check**: On L2 chains (Arbitrum, Optimism), check sequencer uptime before trusting oracle data
- [ ] **Minimum liquidity**: For on-chain TWAP, verify the underlying pool has sufficient liquidity to make manipulation uneconomical

### 8.3 Economic Assumptions

Document all economic assumptions the protocol relies on:

| Assumption | Valid? | Notes |
|------------|--------|-------|
| {e.g., "ETH price will not drop >50% in one block"} | {Yes/No/Conditional} | {evidence or reasoning} |
| {e.g., "Chainlink oracle updates within 1 heartbeat"} | {Yes/No/Conditional} | {check heartbeat config on-chain} |
| {e.g., "Pool liquidity is sufficient to prevent manipulation"} | {Yes/No/Conditional} | {current TVL, manipulation cost estimate} |
| {e.g., "Users will always set reasonable slippage"} | {No} | {users can be tricked or use default 100% slippage} |

---

## Step 8.5: Internet Research (OSINT)

Conduct targeted internet research to discover historical exploits, design context, and security analyses relevant to the protocol.

### Search Strategy

#### a. Historical Exploits

Search for prior hacks on this protocol and similar protocols (especially forks or same category).

**Search queries:**

```
"{protocol name}" hack exploit
"{protocol name}" vulnerability CVE
"{protocol name}" flash loan attack
"{protocol name} fork" hack
"{DeFi category}" exploit 2023 2024 2025
```

**Key Sources:**

| Source | URL | Coverage |
|--------|-----|----------|
| **Rekt News** | https://rekt.news | Postmortems of major DeFi exploits with detailed attack analysis |
| **DeFiLlama Hacks** | https://defillama.com/hacks | Comprehensive database of DeFi hacks with amounts, categories, chains |
| **SlowMist Hacked** | https://hacked.slowmist.io | Historical exploit database maintained by SlowMist security team |
| **BlockSec** | https://blocksec.com/blog | Technical attack analyses and real-time exploit detection writeups |

#### b. Official Documentation

Search for the protocol's own documentation, whitepapers, and design rationale.

**Search queries:**

```
"{protocol name}" docs documentation
"{protocol name}" whitepaper
"{protocol name}" architecture design
"{protocol name}" security model
```

**Look for:**

- Design decisions that affect security (e.g., why a particular oracle was chosen)
- Known limitations documented by the team
- Planned upgrades or migrations
- Economic model parameters (fees, incentives, slashing conditions)

#### c. Security Firm Analyses

Search for audits and security analyses published by reputable firms.

**Search queries:**

```
"{protocol name}" audit report
"{protocol name}" security review
"{protocol name}" bug bounty
site:code4rena.com "{protocol name}"
site:sherlock.xyz "{protocol name}"
```

**Trusted Security Firms:**

| Firm | Specialization | URL |
|------|----------------|-----|
| **Dedaub** | Static analysis, automated vulnerability detection | https://dedaub.com |
| **CertiK** | Formal verification, broad DeFi audit coverage | https://certik.com |
| **Trail of Bits** | Low-level systems security, custom tooling (Slither, Echidna) | https://trailofbits.com |
| **OpenZeppelin** | Standard library authors, upgrade safety, governance | https://openzeppelin.com |
| **Consensys Diligence** | Ethereum ecosystem security, MythX tooling | https://consensys.io/diligence |
| **Spearbit** | Distributed security review, senior-only reviewers | https://spearbit.com |
| **Cyfrin** | Foundry-native audits, competitive audit platform | https://cyfrin.io |
| **Hacken** | Exchange and bridge security, compliance-focused | https://hacken.io |
| **Quantstamp** | Automated and manual audits, DeFi insurance | https://quantstamp.com |
| **Sherlock** | Competitive audit marketplace, bug bounty integration | https://sherlock.xyz |

#### d. Community & Developer Discussions

Search for security-relevant discussions in community channels.

**Platforms:**

- **Twitter/X**: Search `"{protocol name}" vulnerability OR exploit OR hack OR bug`
- **Forums**: Protocol governance forums, Ethereum Magicians, Ethereum Research
- **Discord**: Protocol's official Discord (check #security or #dev channels)
- **Ethereum Research**: https://ethresear.ch — for novel attack vectors or economic model critiques
- **Code4rena / Sherlock**: Check if the protocol had a competitive audit contest; read all submitted findings

### OSINT Integration

Apply OSINT research at the appropriate audit steps:

| When to Search | What to Search | How to Integrate |
|----------------|----------------|------------------|
| Step 0 (Fork Detection) | Protocol forks, prior audits | Identify inherited vulnerabilities from parent protocol |
| Step 3 (Fund Flow) | Historical exploits on similar fund flow patterns | Flag functions matching known exploit patterns |
| Step 6 (Manual Review) | Specific vulnerability patterns found in code | Cross-reference with known CVEs and exploits |
| **Step 8 (This step)** | Economic attacks on same DeFi category | Validate invariants, attack vectors, and mitigations against real-world data |
| Step 9 (POC) | Exploit transaction traces and reproduction steps | Use as basis for POC test construction |

### OSINT Documentation Template

Include the following tables in `08-invariant-economic.md` under a dedicated OSINT section:

**Historical Exploits:**

| Date | Protocol | Attack Type | Amount Lost | Relevance to Current Audit |
|------|----------|-------------|-------------|---------------------------|
| {YYYY-MM-DD} | {name} | {flash loan / reentrancy / oracle / etc.} | {$X.XM} | {how this relates to the protocol under audit} |

**Official Design Rationale:**

| Design Decision | Source | Security Implication |
|-----------------|--------|----------------------|
| {e.g., "Uses Chainlink for price feed"} | {whitepaper section / docs page} | {reduces oracle manipulation risk but introduces staleness dependency} |

**Security Firm Analyses:**

| Firm | Report Date | Scope | Key Findings | Status |
|------|-------------|-------|--------------|--------|
| {firm name} | {YYYY-MM-DD} | {contracts audited} | {summary of critical/high findings} | {Fixed / Acknowledged / Unresolved} |

---

## Output Document Template

Write `~/.solidity-analyzer/audits/{protocol}/08-invariant-economic.md` using this structure:

```markdown
# Invariant & Economic Analysis — {protocol}

- **Date**: {YYYY-MM-DD}
- **Auditor**: {name}
- **Source**: `~/.solidity-analyzer/contracts/{chainId}/{address}/source/`

## 1. Protocol Invariants

{Invariant verification table}

### Invariant Test Results

{Foundry test output summary}

## 2. Flash Loan Attack Vectors

{Flash loan analysis table and checklist results}

## 3. MEV Analysis

{MEV vector table and mitigation checklist results}

## 4. Sandwich Attack Analysis

{Vulnerable functions table with mitigations}

## 5. Oracle Security

{Oracle type analysis and checklist results}

## 6. Economic Assumptions

{Assumptions table}

## 7. OSINT Findings

### 7.1 Historical Exploits

{Historical exploits table}

### 7.2 Official Design Rationale

{Design rationale table}

### 7.3 Security Firm Analyses

{Security firm analyses table}

### 7.4 Community Discussions

{Notable findings from forums, Twitter, Discord}

## 8. Summary of Economic Risks

| Risk | Severity | Description | Mitigation Status |
|------|----------|-------------|-------------------|
| {risk name} | {Critical/High/Medium/Low} | {description} | {Mitigated / Partial / Unmitigated} |
```
