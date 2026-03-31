---
name: remote-signer-cli
description: >
  Operate ivanzzeth/remote-signer from the shell: authenticate with Ed25519 API keys,
  manage EVM signers and signing rules, sign/broadcast/simulate transactions, handle
  approval workflows, and run health checks. Use when the user needs remote-signer CLI,
  policy-driven signing automation, agent-facing signing without a browser, or
  troubleshooting remote-signer from the terminal. Triggers: "remote-signer", "remote signer cli",
  "sign with remote-signer", "remote-signer-cli", "approval guard", "signing policy".
---

# Remote Signer CLI

[remote-signer](https://github.com/ivanzzeth/remote-signer) is a self-hosted, policy-driven signing service (EVM today; additional chains are planned). The primary operator-facing entrypoint is the **`remote-signer-cli`** binary (Cobra): EVM `sign`, `rule`, `signer`, `simulate`, `request`, `guard`, `broadcast`, plus `health`, `preset`, `keystore`, `validate`, `tui`, and `version`.

## Install

### All `cmd` mains (recommended for a full toolchain)

Install every `main` package under `cmd/`:

```bash
go install github.com/ivanzzeth/remote-signer/cmd/...@latest
```

Ensure `$(go env GOPATH)/bin` is on `PATH`.

**Naming vs `remote-signer-cli` helpers:** `go install` names binaries after the **last path segment** (for example `cmd/tui` → `tui`, `cmd/validate-rules` → `validate-rules`). The **`remote-signer-cli`** subcommands **`validate`** and **`tui`** do **not** call those names — they `exec` fixed names **`remote-signer-validate-rules`** and **`remote-signer-tui`** next to the CLI binary or on `PATH` (see upstream `cmd/remote-signer-cli/validate_cmd.go` and `tui_cmd.go`). To get matching names without manual symlinks, use **GitHub Releases**, or build from a clone the same way as upstream **`scripts/setup.sh`** (`go build -o …/remote-signer-tui ./cmd/tui`, etc.).

### Single entrypoint only

```bash
go install github.com/ivanzzeth/remote-signer/cmd/remote-signer-cli@latest
```

Use this when you only need the main Cobra CLI. You still need **`remote-signer-tui`** and **`remote-signer-validate-rules`** on `PATH` (or beside `remote-signer-cli`) if you rely on `remote-signer-cli tui` / `remote-signer-cli validate`.

### From a local clone

```bash
git clone https://github.com/ivanzzeth/remote-signer.git
cd remote-signer
go install ./cmd/...
# or match release names explicitly, e.g.:
# go build -o "$BIN/remote-signer-cli" ./cmd/remote-signer-cli
# go build -o "$BIN/remote-signer-tui" ./cmd/tui
# go build -o "$BIN/remote-signer-validate-rules" ./cmd/validate-rules
```

Optional: guided host setup (server + deps) — see the upstream [README](https://github.com/ivanzzeth/remote-signer/blob/main/README.md) and `scripts/setup.sh`.

### Install this Agent Skill (documentation bundle)

From the [ivanzzeth/skills](https://github.com/ivanzzeth/skills) monorepo:

```bash
npx skills add https://github.com/ivanzzeth/skills/tree/main/skills/remote-signer-cli
```

Or add the whole collection:

```bash
npx skills add ivanzzeth/skills
```

## `remote-signer-*` binary map

| Global name (what scripts / CLI `exec` expect) | Source package under `cmd/` | Role |
|-----------------------------------------------|-------------------------------|------|
| `remote-signer-cli` | `remote-signer-cli` | Main Cobra CLI (EVM API, presets, health, …); **`validate` / `tui` spawn children** |
| `remote-signer` | `remote-signer` | Signing service **server** |
| `remote-signer-tui` | `tui` | Terminal UI (also invoked by `remote-signer-cli tui`) |
| `remote-signer-validate-rules` | `validate-rules` | Offline rule validation (also invoked by `remote-signer-cli validate`) |
| `maltest` | `maltest` | Development / test utility |
| `verify-setup-polymarket` | `verify-setup-polymarket` | Polymarket setup verification |

`go install …/cmd/...@latest` installs the **directory** names (`tui`, `validate-rules`, …) unless you build with `-o` or rename to match the first column.

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
| `validate` | Spawns **`remote-signer-validate-rules`** with forwarded args |
| `tui` | Spawns **`remote-signer-tui`** with forwarded args |
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

## Smoke checks (after install)

```bash
remote-signer-cli version
remote-signer-cli health --url "$REMOTE_SIGNER_URL"
command -v remote-signer-tui remote-signer-validate-rules  # needed for `remote-signer-cli tui` / `validate`
```

## Relationship to other skills

- **web3-agent-browser** — browser automation with an EIP-1193 wallet backed by remote-signer; use that skill for dApp UX flows. Use **remote-signer-cli** for direct API/CLI automation, CI, or operator tasks.

## References

- Upstream repo: [github.com/ivanzzeth/remote-signer](https://github.com/ivanzzeth/remote-signer)
- Rule syntax and policies: repo `docs/` (e.g. rule syntax, security audits)
