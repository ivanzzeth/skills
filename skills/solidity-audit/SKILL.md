---
name: solidity-audit
description: >
  Smart contract security audit workflow orchestrator. Guides a 3-phase audit process
  (Understand → Verify → Report) with strict iron rules. Delegates to companion skills:
  etherscan-contract-fetcher for source retrieval, solidity-vulnerability-checklist for
  security checks, and solidity-poc for exploit verification. All outputs go to
  ~/.solidity-analyzer/. This skill should be used when conducting a full security audit
  of a smart contract or protocol.
  Triggers include: "audit contract", "security audit", "audit 0x", "full audit",
  "审计合约", "安全审计", "合约审计", "analyze security of".
---

# solidity-audit

Smart contract security audit workflow. Orchestrates a 3-phase process using companion skills.

## Companion Skills

This skill delegates specialized work to:

| Skill | Step | Purpose |
|-------|------|---------|
| **eip155-chains** | All | RPC endpoints via EVM Gateway |
| **etherscan-contract-fetcher** | 1 | Fetch verified source code + proxy detection |
| **solidity-interface-analysis** | 2 | Architecture diagrams, privileged addresses, call risks |
| **solidity-fund-flow-analysis** | 3 | Fund flow paths, risk matrix |
| **solidity-static-analysis** | 4 | Slither workflow, detector config, finding triage |
| **solidity-vulnerability-checklist** | 4, 6 | Top 5 vulnerability checks |
| **solidity-storage-analysis** | 5 | Storage layout, EIP-1967 slots, live state |
| **solidity-upgrade-analysis** | 7 | Storage collision, initializer, proxy patterns |
| **solidity-economic-analysis** | 8+8.5 | Invariants, flash loan/MEV/oracle attacks, OSINT |
| **solidity-poc** | 9 | Foundry fork-based POC development |
| **solidity-audit-report** | 10+11 | Final report + executive briefing |

## Workspace

All audit artifacts live in `~/.solidity-analyzer/`:

```
~/.solidity-analyzer/
├── contracts/{chainId}/{address}/   # Fetched sources (etherscan-contract-fetcher)
├── audits/{protocol}/               # Audit reports (this skill)
│   ├── 00-fork-analysis.md
│   ├── 01-source-analysis.md
│   ├── 02-interface-analysis.md
│   ├── 03-fund-flow-risk.md
│   ├── 04-static-analysis.md
│   ├── 05-storage-analysis.md
│   ├── 06-manual-review.md
│   ├── 07-upgrade-analysis.md       # If applicable
│   ├── 08-invariant-economic.md
│   ├── 09-poc-results.md
│   ├── AUDIT-REPORT.md              # Final report
│   └── AUDIT-BRIEF.md               # Executive briefing
└── poc/{protocol}/                   # POC tests (solidity-poc)
```

## Workflow: Understand → Verify → Report

### Phase 1: UNDERSTAND

**Step 0: Fork Detection**
Search if the protocol is a fork of an existing audited protocol. Check for prior audits.
→ Output: `audits/{protocol}/00-fork-analysis.md`

**Step 1: Fetch Source + Scope Confirmation**
Use **etherscan-contract-fetcher** to fetch contract source code. Confirm audit scope with user (in-scope contracts, trust assumptions).
→ Output: `audits/{protocol}/01-source-analysis.md`

**Step 2: Interface & Architecture Analysis**
- Contract architecture diagram (Mermaid)
- Privileged address analysis — verify ALL on-chain with `cast call`
- External call risk assessment
→ Output: `audits/{protocol}/02-interface-analysis.md`

**Step 3: Fund Flow Risk Analysis**
- Privileged account fund access paths
- User fund flow paths
- Risk matrix per function
→ Output: `audits/{protocol}/03-fund-flow-risk.md`

### Phase 2: VERIFY

**Step 4: Static Analysis (Slither)**
Run Slither with context from Steps 2-3. Use **solidity-vulnerability-checklist** detectors.
```bash
slither . --detect reentrancy-eth,reentrancy-no-eth,tx-origin,unprotected-upgrade,suicidal,arbitrary-send-eth,unchecked-lowlevel,unchecked-send,unchecked-transfer
```
→ Output: `audits/{protocol}/04-static-analysis.md`

**Step 5: Storage Layout + Live State**
```bash
forge inspect ContractName storage-layout --pretty
cast storage {address} --rpc-url https://evm.web3gate.xyz/evm/{chainId}
```
→ Output: `audits/{protocol}/05-storage-analysis.md`

**Step 6: Manual Code Review**
Line-by-line review of critical functions. Run through **solidity-vulnerability-checklist** Top 5. Verify CEI pattern, check math, edge cases.
→ Output: `audits/{protocol}/06-manual-review.md`

**Step 7: Upgrade Risk Analysis** *(if proxy detected)*
Storage collision check, initializer security, implementation vs proxy layout comparison.
→ Output: `audits/{protocol}/07-upgrade-analysis.md`

**Step 8: Invariant & Economic Analysis**
Protocol invariants, flash loan vectors, MEV/sandwich analysis, oracle manipulation.
→ Output: `audits/{protocol}/08-invariant-economic.md`

**Step 8.5: Internet Research (OSINT)**
Search for historical exploits on similar protocols, official documentation, security firm analyses. Integrate findings into `08-invariant-economic.md`.

**Step 9: POC Development**
Use **solidity-poc** templates. Write Foundry fork tests for all confirmed vulnerabilities.
→ Output: `poc/{protocol}/test/poc/*.t.sol`, `audits/{protocol}/09-poc-results.md`

### Phase 3: REPORT

**Step 10: Final Audit Report**
Compile all findings. Include centralization risk score (A-F), finding severity classification, POC references.
→ Output: `audits/{protocol}/AUDIT-REPORT.md`

**Step 11: Executive Briefing**
Non-technical summary. Focus: fund safety, privilege risks, actionable recommendations.
→ Output: `audits/{protocol}/AUDIT-BRIEF.md`

## Iron Rules

1. **NO SKIPPING STEPS** — Complete ALL steps in order. If blocked, explain the specific blocker and ask user for permission to skip. "Time" is never a valid reason.

2. **NO UNVERIFIED CLAIMS** — Every privileged address, every state claim must be verified on-chain with `cast call` / `cast storage` / `cast code`. Forbidden: "needs verification", "unknown", "TBD", "?".

3. **POC IS MANDATORY** — Every finding (Critical/High/Medium) must have a Foundry fork POC. No POC = downgrade to Informational. Use **solidity-poc** templates.

4. **VERIFY BEFORE PROCEEDING** — After each step, self-check:
   ```bash
   # Check for unverified items
   grep -riE "need.*verif|TBD|TODO|unknown|\?\s*\|" ~/.solidity-analyzer/audits/{protocol}/
   # Check for unchecked boxes
   grep -rn "\- \[ \]" ~/.solidity-analyzer/audits/{protocol}/
   ```
   If either returns results, fix them before moving to the next step.

5. **CALCULATE ACTUAL SELECTORS** — All event Topic0 and function selectors must be real keccak256 hashes, not placeholders:
   ```bash
   cast keccak "Transfer(address,address,uint256)"
   ```

6. **NO NESTED .git** — When creating POC projects, always use `--no-git` or remove `.git` after clone:
   ```bash
   forge init poc --no-git
   ```

## Finding Severity Classification

| Severity | Criteria |
|----------|----------|
| **Critical** | Direct fund loss, no user interaction needed |
| **High** | Fund loss with specific conditions, or complete protocol DoS |
| **Medium** | Conditional fund risk, governance attack, or significant value leak |
| **Low** | Minor risk, best practice violation, gas optimization |
| **Informational** | Code quality, suggestions, no direct risk |

## Centralization Risk Score

| Grade | Description |
|-------|-------------|
| **A** | Fully decentralized, no privileged roles, immutable |
| **B** | Minimal privileges, Timelock + MultiSig on all admin functions |
| **C** | Some privileged roles, partial Timelock coverage |
| **D** | Significant centralization, EOA admin, no Timelock |
| **F** | Single EOA controls all funds, no safeguards |
