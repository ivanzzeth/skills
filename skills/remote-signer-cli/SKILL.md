---
name: remote-signer-cli
description: >
  Work with ivanzzeth/remote-signer: install binaries, use the slim remote-signer-cli for
  presets/rules/offline validation and TUI launch, and route signing/audit flows to the HTTP API,
  TUI, or Go/JS SDKs per upstream docs. Use when the user mentions remote-signer, remote-signer-cli,
  signing policy presets, validate-rules, remote-signer-tui, or local hook / testing behavior for
  the remote-signer repo. Triggers: "remote-signer", "remote signer", "remote-signer-cli",
  "remote-signer-tui", "validate-rules", "signing policy", "REMOTE_SIGNER_* pre-commit".
---

# Remote Signer CLI & toolchain

[remote-signer](https://github.com/ivanzzeth/remote-signer) is a self-hosted, policy-driven signing service (EVM today; additional chains are planned). **Money-moving and authenticated flows go through the running server** (HTTP API and/or `remote-signer-tui`). The checked-in **`remote-signer-cli`** on current `main` is intentionally **narrow**: local config/preset work, spawning **`remote-signer-validate-rules`**, and launching **`remote-signer-tui`**. It is **not** a full replacement for the EVM client surface; use **`docs/API.md`**, **`INTEGRATION.md`**, and the **TUI** for those capabilities.

## Install

### Constrained runners (`errno=11`, `resource temporarily unavailable`)

Some CI agents and heartbeats run with **very low process/thread limits**. Parallel `go` builds can fail with `fork/exec … resource temporarily unavailable` or `failed to create new OS thread errno=11`.

Mitigations (use one or more):

- Export **`GOMAXPROCS=1`** for `go install` / `go run` / `go test`.
- If a single `go install …/cmd/...` graph still fails, **install mains sequentially** (for example `cmd/remote-signer-cli`, then `cmd/tui`, then `cmd/validate-rules`) instead of one large parallel build.
- Prefer **GitHub Releases** binaries when you only need smoke checks, not a from-source build.

### All `cmd` mains (recommended for a full toolchain)

Install every `main` package under `cmd/`:

```bash
GOMAXPROCS=1 go install github.com/ivanzzeth/remote-signer/cmd/...@latest
```

Ensure `$(go env GOPATH)/bin` is on `PATH`.

**Same module root everywhere:** whether you use `go install github.com/ivanzzeth/remote-signer/cmd/...@latest` or clone and `go install ./cmd/...`, you are building from the **`github.com/ivanzzeth/remote-signer` module**. If upstream moves a `main` package, update both the `go install` path and your local `./cmd/...` invocations together so docs and scripts stay aligned.

**Naming vs `remote-signer-cli` helpers:** `go install` names binaries after the **last path segment** (for example `cmd/tui` → `tui`, `cmd/validate-rules` → `validate-rules`). The **`remote-signer-cli`** subcommands **`validate`** and **`tui`** `exec` fixed names **`remote-signer-validate-rules`** and **`remote-signer-tui`** next to the CLI binary or on `PATH` (see upstream `cmd/remote-signer-cli/validate_cmd.go` and `tui_cmd.go`). To get matching names without manual symlinks, use **GitHub Releases**, or build from a clone the same way as upstream **`scripts/setup.sh`** (see `BIN_DIR` / `REMOTE_SIGNER_BIN_DIR` there).

### Single entrypoint only

```bash
GOMAXPROCS=1 go install github.com/ivanzzeth/remote-signer/cmd/remote-signer-cli@latest
```

You still need **`remote-signer-tui`** and **`remote-signer-validate-rules`** on `PATH` (or beside `remote-signer-cli`) if you rely on `remote-signer-cli tui` / `remote-signer-cli validate`.

### From a local clone

```bash
git clone https://github.com/ivanzzeth/remote-signer.git
cd remote-signer
GOMAXPROCS=1 go install ./cmd/...
# or match release names explicitly, e.g.:
# go build -o "$BIN/remote-signer-cli" ./cmd/remote-signer-cli
# go build -o "$BIN/remote-signer-tui" ./cmd/tui
# go build -o "$BIN/remote-signer-validate-rules" ./cmd/validate-rules
```

Optional: guided host setup (server + deps) — upstream [README](https://github.com/ivanzzeth/remote-signer/blob/main/README.md) and `scripts/setup.sh`.

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
| `remote-signer-cli` | `remote-signer-cli` | **Slim** Cobra CLI: `rule`, `preset`, `validate`, `tui`, `version` (see below) |
| `remote-signer` | `remote-signer` | Signing service **server** |
| `remote-signer-tui` | `tui` | Terminal UI (also invoked by `remote-signer-cli tui`) |
| `remote-signer-validate-rules` | `validate-rules` | Offline rule validation (also invoked by `remote-signer-cli validate`) |
| `maltest` | `maltest` | Development / test utility |
| `verify-setup-polymarket` | `verify-setup-polymarket` | Polymarket setup verification |

`go install …/cmd/...@latest` installs the **directory** names (`tui`, `validate-rules`, …) unless you build with `-o` or rename to match the first column.

## `remote-signer-cli` command map (current `main`)

### `rule`

| Subcommand | Role |
|------------|------|
| `list-templates` | List templates from a local `--config` file (default `config.yaml`) |

### `preset`

| Subcommand | Role |
|------------|------|
| `list` | List preset files under `rules/presets/` (override with `--presets-dir`) |
| `create-from` | Render rule YAML from a preset; optional `--config` + `--write` to merge into config |
| `vars` | Print preset variables / hints for setup scripts (`--project-dir` for template resolution) |

### Pass-through / launcher commands

| Command | Role |
|---------|------|
| `validate` | Spawns **`remote-signer-validate-rules`** with forwarded args (e.g. `-config config.yaml`) |
| `tui` | Spawns **`remote-signer-tui`** with forwarded args (API URL, API key material, TLS flags — see [docs/TUI.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/TUI.md)) |
| `version` | Prints embedded CLI version string |

There is **no** `remote-signer-cli health` on current `main`; use **`curl`** against `/health` as documented in the upstream README.

## Where signing, simulation, broadcast, and audit live

| Need | Use |
|------|-----|
| Sign / simulate / requests / rules CRUD over HTTP | [docs/API.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/API.md) — authoritative REST contract (including audit listing / pagination as implemented in your revision) |
| Operator UI for signers, approvals, rules | `remote-signer-cli tui …` or run `remote-signer-tui` directly ([docs/TUI.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/TUI.md)) |
| Application integration | [INTEGRATION.md](https://github.com/ivanzzeth/remote-signer/blob/main/INTEGRATION.md) (Go / JS client surfaces) |

Some releases add extra operator docs (for example an SDK⇄CLI matrix). If your checkout includes **`docs/sdk-cli-matrix.md`**, treat it as the maintainer-maintained mapping between SDK calls and CLI or HTTP operations; otherwise rely on **`docs/API.md`** + **`INTEGRATION.md`**. Authoritative hook / E2E contract remains **[docs/TESTING.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/TESTING.md)** — keep install and smoke wording consistent with that file when they overlap.

## Minimal examples

**Config files and working directory**

- Commands below assume **`cd` into a clone of** [ivanzzeth/remote-signer](https://github.com/ivanzzeth/remote-signer) **at the repository root**, because bundled templates use **relative paths** (for example `rules/templates/*.yaml`, `e2e/fixtures/…`).
- **`config.example.yaml`** is the long-form reference; many keys use **`public_key_env`** — you must set those environment variables before `config.Load` succeeds. Do not treat it as a zero-setup copy/paste unless you have already wired env vars per [docs/CONFIGURATION.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/CONFIGURATION.md).
- **`api_keys` schema:** each key uses `admin: true` or `admin: false` for privilege level (plus `id`, `name`, `public_key` / `public_key_env`, `enabled`, optional rate limits). There is **no** `role` field in current upstream YAML — samples that use `role` will fail validation until converted to `admin`.
- **Explicit `--config`:** subcommands such as `rule list-templates` default to **`config.yaml` in the current working directory**. In scripts and docs, always pass **`--config`** with a concrete path (for example `--config config.e2e.yaml`) so a stray half-written `config.yaml` in another directory does not cause confusing load errors.
- For **offline CLI smoke** without wiring `public_key_env` secrets, prefer **standalone example rule files** (below) or **`config.e2e.yaml` only for read-only commands** like `rule list-templates`. Full **`validate -config …`** runs the same expansion as the server and can fail on a given checkout if the bundled config is mid-migration; use **`rules/treasury.example.yaml`** (and other `rules/*.example.yaml`) for deterministic validate smoke on a clean clone.

**List rule templates from a local config file:**

```bash
cd /path/to/remote-signer
remote-signer-cli rule list-templates --config config.e2e.yaml
```

**List presets bundled with the repo:**

```bash
cd /path/to/remote-signer
remote-signer-cli preset list
```

**Render YAML from a preset (stdout; run from repo root so preset `template_path` resolves):**

```bash
cd /path/to/remote-signer
remote-signer-cli preset create-from polymarket_safe_polygon.preset.js.yaml > /tmp/from-preset.yaml
```

Use **`--config some.yaml --write`** only when you intentionally merge into an existing config file (see `preset create-from --help`).

**Offline rule validation (wraps `remote-signer-validate-rules`; flags are forwarded verbatim):**

```bash
cd /path/to/remote-signer
GOMAXPROCS=1 remote-signer-cli validate rules/treasury.example.yaml
```

**Full config expansion (optional, stricter):**

```bash
cd /path/to/remote-signer
GOMAXPROCS=1 remote-signer-cli validate -config ./config.yaml
```

Use the path to **your** fully wired config (often copied from `config.example.yaml` after secrets and `public_key_env` / signer `key_env` targets are populated per [docs/CONFIGURATION.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/CONFIGURATION.md)). This runs the same template/instance expansion as the server. **`validate -config config.e2e.yaml`** is useful in upstream CI but may fail on a given `main` checkout while delegation graphs are in flux; for friction-free agent smoke, prefer **`rules/*.example.yaml`** and **`rule list-templates --config config.e2e.yaml`** instead of insisting on a green `-config config.e2e.yaml` validate.

**Launch TUI (forwards flags to `remote-signer-tui`):**

```bash
remote-signer-cli tui -api-key-id admin -api-key-file ./data/admin_private.pem -url http://localhost:8548
```

**Smoke path A — HTTP health (no TLS, no client certs)**

Use an **`http://`** base URL only when the listener is actually plain HTTP (TLS disabled in server config). From repo [README](https://github.com/ivanzzeth/remote-signer/blob/main/README.md):

```bash
curl -fsS "http://127.0.0.1:8548/health"
```

**Smoke path B — HTTPS + mTLS health (private CA; explicit trust + client cert)**

`curl -fsS` **against `https://` with a private CA** will fail TLS verification unless you pass CA + client certificate material (matches `scripts/gen-certs` / default Docker layout; paths relative to repo root).

**Prerequisite (clean clone):** `certs/*.crt` / `certs/*.key` are **not** checked in. Generate them first from a [remote-signer](https://github.com/ivanzzeth/remote-signer) clone at the repository root:

```bash
cd /path/to/remote-signer
./scripts/gen-certs.sh
test -f certs/ca.crt && test -f certs/client.crt && test -f certs/client.key
```

If your environment uses the deploy helper instead, the same intent is documented as `./scripts/deploy.sh gen-certs` in upstream [examples/README.md](https://github.com/ivanzzeth/remote-signer/blob/main/examples/README.md).

Then run the health probe (still no `-k` / `--insecure`):

```bash
curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key -fsS "https://127.0.0.1:8548/health"
```

Do **not** document **`curl -k` / `--insecure`** as the primary mTLS or private-CA workflow: it skips **server** certificate verification and does **not** supply **client** authentication. It is at most an emergency operator escape hatch, not a substitute for `--cacert` / `--cert` / `--key`.

If you set `REMOTE_SIGNER_URL`, it must use the **same scheme** as the running server (`http://` vs `https://`). Do not point `https://…` at a plain HTTP listener, or vice versa.

Never paste private keys, mnemonics, or raw API PEMs into agent prompts, issues, or skills — store them only in secret stores or local files excluded from git, following upstream **`docs/SECURITY.md`** / **`docs/CONFIGURATION.md`**. In Paperclip Web3 harness repos, align with that repo’s **`docs/SECRETS.md`** policy for execution processes.

## Local development: hooks and `REMOTE_SIGNER_*` overrides

After clone or when hook scripts change, install git hooks:

```bash
./scripts/install-hooks.sh
```

Pre-commit runs security scans and may run **E2E** when enabled. See **[docs/TESTING.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/TESTING.md)** for the full contract, including:

| Variable | Meaning |
|----------|---------|
| `REMOTE_SIGNER_PRE_COMMIT_E2E` | `auto` (default), `force`, or `skip` — controls whether the hook runs E2E for a given commit |
| `REMOTE_SIGNER_FORCE_PRE_COMMIT_E2E` | `1` forces E2E |
| `REMOTE_SIGNER_SKIP_PRE_COMMIT_E2E` | `1` skips E2E (escape hatch when the environment cannot run it — **prefer fixing the environment**) |

**Do not** treat `git commit --no-verify` as the default workflow; it bypasses the maintainer hooks entirely.

E2E uses **`E2E_API_PORT=18548`** by default in hooks to avoid colliding with a dev server on `8548`. Match the **`go test`** invocation in `docs/TESTING.md` when reproducing hook behavior.

## Smoke checks (after install)

```bash
remote-signer-cli version
command -v remote-signer-tui remote-signer-validate-rules  # needed for `remote-signer-cli tui` / `validate`
# Deterministic offline validate (from repo root; no secrets):
GOMAXPROCS=1 remote-signer-cli validate rules/treasury.example.yaml
# Smoke path A — plain HTTP listener (adjust host/port if needed):
curl -fsS "http://127.0.0.1:8548/health"
# Smoke path B — HTTPS + mTLS (explicit material; see "Smoke path B" above):
# ./scripts/gen-certs.sh && test -f certs/ca.crt && test -f certs/client.crt && test -f certs/client.key
# curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key -fsS "https://127.0.0.1:8548/health"
```

## Relationship to other skills

- **web3-agent-browser** — browser automation with an EIP-1193 wallet backed by remote-signer; use for dApp UX flows. Use **this skill** for repo-local CLI/preset/validate/TUI install paths and **docs/API.md** for direct HTTP automation.

## References

- Upstream repo: [github.com/ivanzzeth/remote-signer](https://github.com/ivanzzeth/remote-signer)
- [docs/API.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/API.md) — HTTP signing, rules, audit, auth
- [INTEGRATION.md](https://github.com/ivanzzeth/remote-signer/blob/main/INTEGRATION.md) — Go / JS SDK entrypoints
- [docs/TESTING.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/TESTING.md) — unit tests, E2E, hook env vars
- [docs/RULE_SYNTAX.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/RULE_SYNTAX.md) / [docs/RULES_TEMPLATES_AND_PRESETS.md](https://github.com/ivanzzeth/remote-signer/blob/main/docs/RULES_TEMPLATES_AND_PRESETS.md) — rule and preset semantics
- Optional per-release: `docs/sdk-cli-matrix.md` (SDK⇄CLI coverage) when present in your tree
