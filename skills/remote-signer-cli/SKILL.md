---
name: remote-signer-cli
description: >
  Operate ivanzzeth/remote-signer from the shell: authenticate with Ed25519 API keys,
  manage EVM signers and signing rules, sign/broadcast/simulate transactions, handle
  approval workflows, and run health checks. Use when the user needs remote-signer CLI,
  policy-driven signing automation, agent-facing signing without a browser, or
  troubleshooting remote-signer from the terminal. Triggers: "remote-signer", "remote signer cli",
  "sign with remote-signer", "rs-cli", "remote-signer-cli", "approval guard", "signing policy".
---

# Remote Signer CLI

[remote-signer](https://github.com/ivanzzeth/remote-signer) is a self-hosted, policy-driven signing service (EVM today; additional chains are planned). Agents and operators use the **`remote-signer-cli`** binary for the full API surface: EVM `sign`, `rule`, `signer`, `simulate`, `request`, `guard`, and `broadcast`, plus presets, keystores, validation, and TUI.

A newer Go module (**`rs-cli`**, package `internal/rscli`) is being expanded to mirror the Go SDK with a stable, modular command tree; until releases are unified, prefer **`remote-signer-cli`** for end-to-end operations.

## Install

### From the GitHub repository (recommended)

```bash
go install github.com/ivanzzeth/remote-signer/cmd/remote-signer-cli@latest
```

Ensure `$GOPATH/bin` or `$HOME/go/bin` is on `PATH`.

### From a local clone

```bash
git clone https://github.com/ivanzzeth/remote-signer.git
cd remote-signer
go install ./cmd/remote-signer-cli
```

Optional: guided host setup (server + deps) — see the upstream [README](https://github.com/ivanzzeth/remote-signer/blob/main/README.md) `scripts/setup.sh` flow.

### Install this Agent Skill (documentation bundle)

From the [ivanzzeth/skills](https://github.com/ivanzzeth/skills) monorepo:

```bash
npx skills add https://github.com/ivanzzeth/skills/tree/main/skills/remote-signer-cli
```

Or add the whole collection:

```bash
npx skills add ivanzzeth/skills
```

## Authentication (stable contract)

All authenticated subcommands share these **global flags** (see `remote-signer-cli --help`):

| Flag | Purpose |
|------|---------|
| `--url` | Remote signer base URL (default `https://localhost:8548`) |
| `--api-key-id` | API key id registered on the server |
| `--api-key-file` | PEM file with Ed25519 private key for request signing |
| `--api-key-keystore` | Encrypted keystore (alternative to `--api-key-file`) |
| `--api-key-password-env` | Env var name for keystore password (CI) |
| `--tls-ca`, `--tls-cert`, `--tls-key` | TLS / mTLS |
| `--tls-skip-verify` | Insecure dev only |
| `-o`, `--output` | `table` (default), `json`, `yaml` |

**Health** (`remote-signer-cli health`) does not require API authentication — only reachable `--url`.

## Command map

### Top-level (compatibility aliases)

For convenience, these mirror `evm` subcommands:

- `remote-signer-cli sign` → same as `remote-signer-cli evm sign`
- `remote-signer-cli rule` → same as `remote-signer-cli evm rule`

### `evm` (canonical)

```text
remote-signer-cli evm
  sign        Sign transactions, typed data, messages
  rule        List templates / work with rule config
  signer      Manage signers (list, create, unlock, lock, …)
  simulate    Simulate transactions; check simulation status
  request     Signing requests: list, get, approve, reject
  guard       Approval guard operations
  broadcast   Broadcast a signed tx to the chain
```

Use `remote-signer-cli evm <cmd> --help` for flags.

### Other top-level commands

| Command | Role |
|---------|------|
| `health` | `GET /health` — uptime check |
| `preset` | List presets / create rules from a preset |
| `keystore` | Encrypted Ed25519 keystores for API keys |
| `validate` | Delegates to `remote-signer-validate-rules` binary |
| `tui` | Launches `remote-signer-tui` |
| `version` | CLI version string |

## Minimal examples

**Health (no auth):**

```bash
remote-signer-cli health --url https://localhost:8548
```

**List signers (authenticated):**

```bash
remote-signer-cli --url https://localhost:8548 \
  --api-key-id admin \
  --api-key-file ./certs/client.key \
  evm signer list
```

**JSON output:**

```bash
remote-signer-cli -o json --url "$REMOTE_SIGNER_URL" \
  --api-key-id "$REMOTE_SIGNER_API_KEY_ID" \
  --api-key-file "$REMOTE_SIGNER_API_KEY_FILE" \
  evm signer list
```

Adjust paths to match your deployment (mTLS cert paths are often alongside the API key material).

## Relationship to other skills

- **web3-agent-browser** — browser automation with an EIP-1193 wallet backed by remote-signer; use that skill for dApp UX flows. Use **remote-signer-cli** for direct API/CLI automation, CI, or operator tasks.
- **`rs-cli` consolidation** — when the modular `rs-cli` binary reaches parity with `remote-signer-cli`, update install commands here; the **auth flag contract** should stay aligned with `pkg/client` and MCP tools.

## References

- Upstream repo: [github.com/ivanzzeth/remote-signer](https://github.com/ivanzzeth/remote-signer)
- Rule syntax and policies: repo `docs/` (e.g. rule syntax, security audits)
