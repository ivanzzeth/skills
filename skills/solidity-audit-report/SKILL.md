---
name: solidity-audit-report
description: >
  Generate comprehensive Solidity audit reports with executive briefings. Includes audit
  report template, executive briefing, centralization risk score (A-F), severity
  classification, on-chain monitoring recommendations, and POC cross-references. This
  skill should be used when compiling audit findings into a final report, generating
  executive summaries, or creating monitoring recommendations.
  Triggers include: "audit report", "generate report", "executive briefing",
  "final report", "compile findings", "centralization score", "monitoring recommendations",
  "severity classification", "write report", "审计报告", "简报", "生成报告",
  "最终报告", "中心化评分", "监控建议".
---

# solidity-audit-report

Generate the final audit report and executive briefing for a Solidity protocol audit. This is Steps 10+11 of the solidity audit toolkit. All outputs go to `~/.solidity-analyzer/audits/{protocol}/`.

## When to use

Activate this skill when:
- All intermediate audit steps (1-9) are complete and their documents exist in `~/.solidity-analyzer/audits/{protocol}/`
- The user requests an audit report, executive briefing, or final deliverable
- The user says "audit report", "generate report", "executive briefing", "审计报告", "简报", or "生成报告"

## Severity Classification

| Severity | Criteria |
|----------|----------|
| **Critical** | Direct fund loss, no user interaction needed. Attacker can drain funds unilaterally. |
| **High** | Fund loss with specific conditions (e.g., requires oracle manipulation, specific state), or complete protocol DoS rendering the protocol unusable. |
| **Medium** | Conditional fund risk requiring multiple preconditions, governance attack vectors, significant value leak over time (e.g., fee miscalculation, rounding errors accumulating). |
| **Low** | Minor risk with negligible impact, best practice violation, gas optimization opportunity, or edge cases with extremely unlikely preconditions. |
| **Informational** | Code quality suggestions, naming improvements, documentation gaps. No direct risk to funds or availability. |

## Centralization Risk Score

| Grade | Criteria |
|-------|----------|
| **A** | Fully decentralized. No privileged roles. Contracts are immutable or governed entirely by on-chain governance with adequate delays. |
| **B** | Minimal privileges. All admin functions gated behind Timelock + MultiSig. Upgrade paths require governance approval with delay. |
| **C** | Some privileged roles exist. Partial Timelock coverage. Some admin functions callable without delay or with insufficient MultiSig thresholds. |
| **D** | Significant centralization. EOA admin accounts. No Timelock on critical functions. Single point of failure for key operations. |
| **F** | Single EOA controls all funds. No safeguards. Admin can rug-pull at will with no delay, no MultiSig, no governance. |

## Instructions

### Step 1: Verify prerequisites

Confirm all intermediate documents exist before generating the report:

```bash
PROTOCOL="{protocol}"
AUDIT_DIR="$HOME/.solidity-analyzer/audits/$PROTOCOL"

# Required intermediate documents
ls -la "$AUDIT_DIR"/01-INTERFACE-ARCH.md
ls -la "$AUDIT_DIR"/02-FUND-FLOW.md
ls -la "$AUDIT_DIR"/03-STATIC-ANALYSIS.md
ls -la "$AUDIT_DIR"/04-STORAGE-LAYOUT.md
ls -la "$AUDIT_DIR"/05-INVARIANTS-ECON.md
ls -la "$AUDIT_DIR"/06-POC-RESULTS.md
```

If any are missing, stop and inform the user which steps need to be completed first.

### Step 2: Generate AUDIT-REPORT.md

Write the file to `~/.solidity-analyzer/audits/{protocol}/AUDIT-REPORT.md` using this complete template:

```markdown
# {Protocol Name} 安全审计报告

## 项目信息

| 项目 | 详情 |
|------|------|
| 协议名称 | {Protocol Name} |
| 链 | {Chain (e.g., Ethereum Mainnet, Arbitrum)} |
| 审计日期 | {YYYY-MM-DD} |
| Solidity 版本 | {e.g., 0.8.20} |
| 审计范围 | {Commit hash or tag} |

### 合约地址

| 合约 | 地址 | 已验证 |
|------|------|--------|
| {ContractA} | `0x...` | ✅/❌ |
| {ContractB} | `0x...` | ✅/❌ |
| {ProxyAdmin} | `0x...` | ✅/❌ |

---

## 执行摘要

### 关键发现

1. {一句话概述最重要的发现}
2. {一句话概述第二重要的发现}
3. {一句话概述第三重要的发现}

### 风险概览

| 严重程度 | 数量 |
|----------|------|
| Critical | {n} |
| High | {n} |
| Medium | {n} |
| Low | {n} |
| Informational | {n} |
| **总计** | **{N}** |

---

## 中心化风险评估

### 总体评分: {A/B/C/D/F}

{一段话总结中心化风险的整体情况}

### 评估细分

| 维度 | 评分 | 说明 |
|------|------|------|
| 资金控制权 | {A-F} | {谁可以转移资金？需要几个签名？有无 Timelock？} |
| 升级权限 | {A-F} | {谁可以升级合约？代理模式？升级延迟？} |
| 暂停权限 | {A-F} | {谁可以暂停协议？有无暂停/恢复分离？} |
| 参数控制权 | {A-F} | {谁可以修改费率、阈值等关键参数？范围限制？} |
| 预言机依赖 | {A-F} | {使用哪些预言机？回退机制？操纵难度？} |
| Treasury 控制 | {A-F} | {协议金库管理方式？提款权限？} |

### 最坏情况分析

| 场景 | 影响 | 概率 |
|------|------|------|
| {Admin 私钥泄露} | {描述资金损失范围} | {低/中/高} |
| {升级为恶意实现} | {描述最大损失} | {低/中/高} |
| {预言机被操纵} | {描述套利或清算风险} | {低/中/高} |

### 信任假设

- {列出协议隐含的信任假设，如 "admin 不会恶意行事"}
- {如 "预言机价格偏差不会超过 X%"}
- {如 "MultiSig 签名者不会串谋"}

---

## 审计范围

### 已审计合约

| 文件 | 代码行数 | 复杂度 |
|------|----------|--------|
| `src/{Contract1}.sol` | {n} | {低/中/高} |
| `src/{Contract2}.sol` | {n} | {低/中/高} |
| `src/{Library1}.sol` | {n} | {低/中/高} |

### 不在范围内

- 第三方依赖 (OpenZeppelin, Chainlink, etc.)
- 前端及后端代码
- 链下基础设施 (keeper, relayer)
- {其他排除项}

---

## 第一章：接口与架构分析

> 详见 `01-INTERFACE-ARCH.md`

{概述架构分析的关键发现：合约继承关系、外部依赖、接口暴露面、访问控制模式}

---

## 第二章：资金流风险分析

> 详见 `02-FUND-FLOW.md`

{概述资金流分析结果：入金/出金路径、手续费计算、余额变更逻辑、重入风险}

---

## 第三章：静态分析结果

> 详见 `03-STATIC-ANALYSIS.md`

{概述 Slither/Mythril/Aderyn 等工具的发现摘要及人工确认结果}

---

## 第四章：存储布局分析

> 详见 `04-STORAGE-LAYOUT.md`

{概述存储冲突风险、代理升级兼容性、槽位布局关键发现}

---

## 第五章：不变量与经济攻击分析

> 详见 `05-INVARIANTS-ECON.md`

{概述核心不变量、经济攻击向量（闪电贷、三明治、预言机操纵）、博弈论分析}

---

## 第六章：POC 验证结果

> 详见 `06-POC-RESULTS.md`

{概述 POC 验证的发现：哪些漏洞已确认可利用、利用条件、实际损失估算}

---

## 发现详情

### Critical

#### [C-01] {发现标题}

| 属性 | 值 |
|------|------|
| 严重程度 | Critical |
| 影响范围 | {受影响的合约/函数} |
| 潜在损失 | {估算金额或 TVL 百分比} |
| 攻击复杂度 | {低/中/高} |
| POC | `poc/test/{TestName}.t.sol` |

**描述**

{详细描述漏洞的技术细节}

**攻击路径**

1. {攻击者执行步骤 1}
2. {攻击者执行步骤 2}
3. {结果：资金被盗/协议破坏}

**POC 结果**

```
参见 poc/test/{TestName}.t.sol
测试输出: {关键数值，如被盗金额}
```

**建议修复**

```solidity
// 修复前
{漏洞代码}

// 修复后
{修复代码}
```

---

### High

#### [H-01] {发现标题}

| 属性 | 值 |
|------|------|
| 严重程度 | High |
| 影响范围 | {受影响的合约/函数} |
| 前提条件 | {触发条件} |
| POC | `poc/test/{TestName}.t.sol` |

**描述**

{详细描述}

**攻击路径**

1. {步骤}

**建议修复**

{修复方案}

---

### Medium

#### [M-01] {发现标题}

| 属性 | 值 |
|------|------|
| 严重程度 | Medium |
| 影响范围 | {受影响的合约/函数} |
| 前提条件 | {多个触发条件} |

**描述**

{详细描述}

**建议修复**

{修复方案}

---

### Low

#### [L-01] {发现标题}

| 属性 | 值 |
|------|------|
| 严重程度 | Low |
| 影响范围 | {受影响区域} |

**描述**

{详细描述}

**建议修复**

{修复方案}

---

### Informational

#### [I-01] {发现标题}

**描述**

{代码质量建议或最佳实践建议}

**建议**

{改进方案}

---

## 去中心化改进建议

| 优先级 | 当前状态 | 建议改进 | 预期效果 |
|--------|----------|----------|----------|
| 🔴 高 | {如：EOA 控制升级} | {如：迁移至 Timelock + 3/5 MultiSig} | {评分从 D 提升至 B} |
| 🔴 高 | {如：无暂停延迟} | {如：添加 48h Timelock} | {降低 rug-pull 风险} |
| 🟡 中 | {如：单一预言机源} | {如：集成 Chainlink + TWAP 双重验证} | {提高操纵成本} |
| 🟢 低 | {如：参数修改无事件} | {如：所有 setter 添加 Event 日志} | {提升链上透明度} |

---

## 链上监控建议

### 监控事项总览

| # | 监控事项 | 描述 | 重要性 | 监控方法 | 优先级 |
|---|----------|------|--------|----------|--------|
| 1 | 大额转账 | 单笔超过 TVL 1% 的转入/转出 | 高 | Event 监听 `Transfer(address,address,uint256)` | P0 |
| 2 | 管理员变更 | owner/admin 地址变更 | 高 | Event 监听 `OwnershipTransferred`, `AdminChanged` | P0 |
| 3 | 合约升级 | 实现合约地址变更 | 高 | Event 监听 `Upgraded(address)` | P0 |
| 4 | 暂停/恢复 | 协议暂停或恢复操作 | 高 | Event 监听 `Paused(address)`, `Unpaused(address)` | P0 |
| 5 | 参数修改 | 费率、阈值等关键参数变更 | 中 | Event 监听各参数 setter 的事件 | P1 |
| 6 | 异常交易模式 | 短时间内大量相似交易 | 中 | 交易频率分析 + mempool 监控 | P1 |
| 7 | 闪电贷活动 | 涉及协议的闪电贷交易 | 中 | 监听 `FlashLoan` 事件 + 单 tx 资金流分析 | P1 |
| 8 | 预言机价格偏差 | 预言机报价与市场价偏差超阈值 | 高 | 价格比对 (Chainlink vs DEX TWAP) | P0 |
| 9 | 治理提案 | 新提案创建或执行 | 中 | Event 监听 `ProposalCreated`, `ProposalExecuted` | P1 |
| 10 | 授权额度异常 | 无限授权或异常大额 approve | 低 | Event 监听 `Approval(address,address,uint256)` | P2 |
| 11 | 合约余额骤变 | 协议合约 ETH/token 余额短时间大幅变化 | 高 | 定时余额轮询 + 阈值告警 | P0 |
| 12 | 新合约部署 | Factory 合约部署新子合约 | 低 | Event 监听工厂合约的创建事件 | P2 |

### Topic0 计算

使用 `cast` 命令计算事件签名的 Topic0 值：

```bash
# Transfer(address,address,uint256)
cast keccak "Transfer(address,address,uint256)"
# 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef

# OwnershipTransferred(address,address)
cast keccak "OwnershipTransferred(address,address)"
# 0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0

# Upgraded(address)
cast keccak "Upgraded(address)"
# 0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b

# AdminChanged(address,address)
cast keccak "AdminChanged(address,address)"
# 0x7e644d79422f17c01e4894b5f4f588d331ebfa28653d42ae832dc59e38c9798f

# Paused(address)
cast keccak "Paused(address)"
# 0x62e78cea01bee320cd4e420270b5ea74000d11b0c9f74754ebdbfc544b05a258

# Unpaused(address)
cast keccak "Unpaused(address)"
# 0x5db9ee0a495bf2e6ff9c91a7834c1ba4fdd244a5e8aa4e537bd38aeae4b073aa
```

### 推荐监控工具

| 工具 | 用途 | 适合场景 |
|------|------|----------|
| **Tenderly** | 交易模拟、实时告警、调试 | 开发+运维监控，支持自定义 webhook |
| **Forta** | 去中心化威胁检测网络 | 自定义检测 bot，社区共享威胁情报 |
| **OpenZeppelin Defender** | 自动化运维、告警、Relayer | 已有 OZ 生态的项目，Admin 管理 |
| **Dune Analytics** | 链上数据分析、仪表盘 | 历史数据分析，趋势监控 |
| **The Graph** | 去中心化索引协议 | 自定义 Subgraph 索引合约事件 |
| **Alchemy** | 节点服务 + Notify API | Webhook 通知，地址活动监控 |

### 警报通知配置

| 告警级别 | 触发条件 | 通知方式 | 响应时间 |
|----------|----------|----------|----------|
| 🔴 紧急 | Critical 事件 (大额转出、admin 变更、升级) | PagerDuty + Telegram + 电话 | < 5 分钟 |
| 🟡 警告 | High 事件 (参数修改、异常模式) | Telegram + Email | < 30 分钟 |
| 🟢 信息 | Low 事件 (授权变更、治理提案) | Email + Dashboard | < 24 小时 |

### 监控脚本示例

```javascript
const { ethers } = require("ethers");

const provider = new ethers.WebSocketProvider(process.env.WS_RPC_URL);

// --- 监控 Transfer 大额转账 ---
const TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const THRESHOLD = ethers.parseEther("100"); // 根据协议 TVL 调整

provider.on({
  address: "{CONTRACT_ADDRESS}",
  topics: [TRANSFER_TOPIC]
}, (log) => {
  const value = ethers.toBigInt(log.data);
  if (value > THRESHOLD) {
    const from = ethers.getAddress("0x" + log.topics[1].slice(26));
    const to = ethers.getAddress("0x" + log.topics[2].slice(26));
    console.log(`[ALERT] Large transfer: ${ethers.formatEther(value)} from ${from} to ${to}`);
    // sendTelegramAlert(...)
  }
});

// --- 监控 AdminChanged ---
const ADMIN_CHANGED_TOPIC = "0x7e644d79422f17c01e4894b5f4f588d331ebfa28653d42ae832dc59e38c9798f";

provider.on({
  address: "{PROXY_ADDRESS}",
  topics: [ADMIN_CHANGED_TOPIC]
}, (log) => {
  const prevAdmin = ethers.getAddress("0x" + log.topics[1].slice(26));
  const newAdmin = ethers.getAddress("0x" + log.topics[2].slice(26));
  console.log(`[CRITICAL] Admin changed from ${prevAdmin} to ${newAdmin}`);
  // sendPagerDutyAlert(...)
});

// --- 监控 Paused ---
const PAUSED_TOPIC = "0x62e78cea01bee320cd4e420270b5ea74000d11b0c9f74754ebdbfc544b05a258";

provider.on({
  address: "{CONTRACT_ADDRESS}",
  topics: [PAUSED_TOPIC]
}, (log) => {
  const account = ethers.getAddress("0x" + log.topics[1].slice(26));
  console.log(`[CRITICAL] Protocol PAUSED by ${account}`);
  // sendPagerDutyAlert(...)
});

console.log("Monitoring started...");
```

---

## 审计方法

本审计采用以下 10 步系统化方法：

1. **接口与架构分析** — 合约继承关系、外部依赖、访问控制模式梳理
2. **资金流追踪** — 所有入金/出金路径、手续费、余额变更逻辑分析
3. **静态分析** — 使用 Slither、Mythril、Aderyn 等工具自动扫描
4. **存储布局审查** — 代理模式存储兼容性、槽位冲突检查
5. **不变量与经济模型分析** — 核心不变量定义、经济攻击向量建模
6. **POC 编写与验证** — 对发现的漏洞编写 Foundry 测试验证
7. **人工代码审查** — 逐行审查关键路径代码
8. **交叉验证** — 工具结果与人工审查交叉确认
9. **风险评级与分类** — 按严重程度分级，附影响分析
10. **报告生成与建议** — 编写报告、去中心化改进建议、监控方案

---

## 附录

### A. 架构图

```
{插入协议架构 ASCII 图或引用 01-INTERFACE-ARCH.md 中的图表}
```

### B. 费用公式

```
{列出协议中所有费用计算公式}
例: fee = amount * feeRate / FEE_DENOMINATOR
```

### C. 参考文档

- 协议官方文档: {URL}
- 协议白皮书: {URL}
- 已有审计报告: {URL}
- OpenZeppelin 合约库: https://docs.openzeppelin.com/
- Solidity 文档: https://docs.soliditylang.org/

### D. 链上验证证据

```bash
# 验证合约 owner
cast call {CONTRACT} "owner()(address)" --rpc-url {RPC_URL}

# 验证 Timelock 延迟
cast call {TIMELOCK} "getMinDelay()(uint256)" --rpc-url {RPC_URL}

# 验证代理实现地址
cast storage {PROXY} 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc --rpc-url {RPC_URL}

# 验证 MultiSig 阈值
cast call {MULTISIG} "getThreshold()(uint256)" --rpc-url {RPC_URL}

# 验证暂停状态
cast call {CONTRACT} "paused()(bool)" --rpc-url {RPC_URL}
```

---

## 免责声明

本审计报告基于审计时提供的源代码和信息。审计不保证代码零漏洞。本报告不构成投资建议。审计范围仅限于上述列出的合约，不包括第三方依赖、链下组件、或审计期间之后的代码变更。安全是一个持续的过程，建议协议方建立持续的安全监控和漏洞赏金计划。
```

### Step 3: Generate AUDIT-BRIEF.md

Write the file to `~/.solidity-analyzer/audits/{protocol}/AUDIT-BRIEF.md` using this complete template:

```markdown
# {Protocol Name} 审计执行简报

## 项目信息

| 项目 | 详情 |
|------|------|
| 协议名称 | {Protocol Name} |
| 链 | {Chain} |
| 审计日期 | {YYYY-MM-DD} |
| 审计范围 | {Commit hash or tag} |
| 发现总数 | {N} (Critical: {n}, High: {n}, Medium: {n}, Low: {n}, Info: {n}) |

---

## 总体安全评级: {A/B/C/D/F}

| 评级 | 含义 |
|------|------|
| **A** | 安全性极高。无 Critical/High 发现，代码质量优秀，去中心化程度高。 |
| **B** | 安全性良好。无 Critical 发现，少量 High/Medium 可通过简单修复解决。 |
| **C** | 安全性一般。存在需要关注的风险点，建议修复后再上线或进行二次审计。 |
| **D** | 安全性较差。存在 Critical 或多个 High 级别问题，不建议在当前状态下上线。 |
| **F** | 安全性极差。存在可被直接利用的严重漏洞，必须全面修复后重新审计。 |

**本协议评级: {A/B/C/D/F}**

{一段话说明评级理由}

---

## 资金安全分析

### 安全点 ✅

- ✅ {如：使用 ReentrancyGuard 防止重入攻击}
- ✅ {如：关键函数有 onlyOwner 访问控制}
- ✅ {如：使用 SafeERC20 处理代币转账}
- ✅ {如：价格预言机有偏差检查}
- ✅ {如：提款有延迟机制}

### 风险点 ⚠️

- ⚠️ {如：admin 可以无延迟修改费率至 100%}
- ⚠️ {如：升级无 Timelock，admin 可立即替换实现}
- ⚠️ {如：紧急提款函数可绕过所有检查}
- ⚠️ {如：单一预言机源，无回退机制}

---

## 特权账号权限详情

### EOA 账号（单点故障风险）

> EOA 账号由单个私钥控制，私钥泄露即意味着该账号所有权限被接管。

#### {Role1, e.g., Owner} — `0x...`

| 权限 | 函数 | 影响 |
|------|------|------|
| {权限1} | `{functionName}()` | {如：可转移所有协议资金} |
| {权限2} | `{functionName}()` | {如：可暂停所有合约} |
| {权限3} | `{functionName}()` | {如：可修改费率参数} |
| {权限4} | `{functionName}()` | {如：可升级合约实现} |

**风险**: {总结该角色的最大风险，如 "私钥泄露可导致全部 TVL 损失"}

#### {Role2, e.g., FeeManager} — `0x...`

| 权限 | 函数 | 影响 |
|------|------|------|
| {权限1} | `{functionName}()` | {如：可设置费率 0-100%} |
| {权限2} | `{functionName}()` | {如：可指定费用接收地址} |

**风险**: {总结该角色的最大风险}

### MultiSig 账号（相对安全）

#### {MultiSig Name} — `0x...` ({M}/{N} MultiSig)

| 权限 | 函数 | 影响 |
|------|------|------|
| {权限1} | `{functionName}()` | {如：Treasury 资金管理} |
| {权限2} | `{functionName}()` | {如：协议参数调整} |

**安全性评估**: {如 "3/5 MultiSig，需 3 个签名者串谋才能恶意操作，风险较低"}

### Oracle 账号

#### {Oracle Name} — `0x...`

| 权限 | 函数 | 影响 |
|------|------|------|
| 价格喂送 | `{updatePrice}()` | {如：影响所有借贷清算阈值} |
| {权限2} | `{functionName}()` | {如：可设置价格有效期} |

**风险**: {如 "预言机被操纵可导致错误清算，影响所有借贷头寸"}

---

## 建议措施

### 高优先级（上线前必须完成）

| # | 现状 | 建议 | 原因 |
|---|------|------|------|
| 1 | {如：Owner 为 EOA} | {如：迁移至 3/5 MultiSig + 48h Timelock} | {如：消除单点故障风险，给用户退出时间} |
| 2 | {如：无升级延迟} | {如：添加 Timelock，最低 48h 延迟} | {如：防止恶意升级，给用户撤离窗口} |
| 3 | {如：{Critical 发现}} | {如：修复方案} | {如：直接资金损失风险} |

### 中优先级（上线后 30 天内完成）

| # | 现状 | 建议 | 原因 |
|---|------|------|------|
| 1 | {如：单一预言机} | {如：集成备用预言机} | {如：提高价格可靠性} |
| 2 | {如：无链上监控} | {如：部署 Forta bot + Tenderly 告警} | {如：实时发现异常操作} |

### 低优先级（持续改进）

| # | 现状 | 建议 | 原因 |
|---|------|------|------|
| 1 | {如：无漏洞赏金计划} | {如：设立 Immunefi 赏金计划} | {如：激励白帽发现漏洞} |
| 2 | {如：文档不完整} | {如：补充 NatSpec 注释} | {如：提高代码可维护性} |

---

## 快速参考

### 关键地址

| 角色 | 地址 | 类型 | 风险等级 |
|------|------|------|----------|
| Owner | `0x...` | EOA / MultiSig | 🔴 高 / 🟢 低 |
| Admin | `0x...` | EOA / MultiSig | 🔴 高 / 🟢 低 |
| Treasury | `0x...` | MultiSig | 🟡 中 |
| Oracle | `0x...` | Chainlink / EOA | 🟡 中 |
| Proxy Admin | `0x...` | EOA / Timelock | 🔴 高 / 🟢 低 |

### 信任假设

1. {如：Owner MultiSig 的签名者不会串谋恶意操作}
2. {如：Chainlink 预言机价格偏差不会超过 5%}
3. {如：紧急暂停功能仅在真正紧急情况下使用}
4. {如：协议方不会利用升级权限部署恶意实现}

---

## 免责声明

本简报为审计报告的精简版本，供管理层和非技术决策者参考。完整技术细节请参阅 `AUDIT-REPORT.md`。本文件不构成投资建议，不保证代码零漏洞。安全是一个持续的过程。
```

### Step 4: Self-check before finalizing

Run these commands to verify report completeness:

```bash
PROTOCOL="{protocol}"
AUDIT_DIR="$HOME/.solidity-analyzer/audits/$PROTOCOL"

# Verify all findings have POC references
echo "=== Findings count ==="
grep -E "^#### \[" "$AUDIT_DIR/AUDIT-REPORT.md" | wc -l

echo "=== POC references count ==="
grep -E "poc/test/|\.t\.sol" "$AUDIT_DIR/AUDIT-REPORT.md" | wc -l

# Check for placeholder Topic0 values (should return nothing)
echo "=== Placeholder check (should be empty) ==="
grep -E "0x\.\.\.|empty|Topic0.*\?" "$AUDIT_DIR/AUDIT-REPORT.md"

# Verify all 6 chapters are present
echo "=== Chapter references ==="
grep -c "详见.*\.md" "$AUDIT_DIR/AUDIT-REPORT.md"

# Verify both files exist
echo "=== Output files ==="
ls -la "$AUDIT_DIR/AUDIT-REPORT.md" "$AUDIT_DIR/AUDIT-BRIEF.md"
```

If the POC references count is less than the Critical + High findings count, go back and add missing POC references. If placeholder values are found, replace them with actual computed values.

### Step 5: Summary output

After generating both files, print a summary:

```
Audit deliverables generated:
  - {AUDIT_DIR}/AUDIT-REPORT.md  (Full audit report)
  - {AUDIT_DIR}/AUDIT-BRIEF.md   (Executive briefing)

Findings: {N} total (C:{n} H:{n} M:{n} L:{n} I:{n})
Centralization Risk Score: {A-F}
Overall Security Rating: {A-F}
```
