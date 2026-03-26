---
name: woodpecker-ci
description: >
  Woodpecker CI operations for K3s cluster — pipeline management, triggering builds,
  checking status, viewing logs, adding new services, and troubleshooting. Covers the
  shared CI scripts (build.sh, deploy.sh, service conf), API access, and agent management.
  Triggers: "woodpecker", "CI/CD", "pipeline", "build status", "deploy status",
  "trigger build", "CI logs", "add to CI", "流水线", "构建", "部署状态".
---

# Woodpecker CI Operations

Manage CI/CD pipelines for services deployed on K3s.

## Architecture

```
GitHub (tag push) → Woodpecker Server (k3s) → Woodpecker Agent (Docker Compose on worker)
                                                       │
                                          ┌────────────┼────────────┐
                                          │            │            │
                                       test      build-push     deploy
                                     (go test)  (docker build  (kubectl
                                                + push to       set image)
                                                registry:30500)
```

- **Server**: K3s deployment `woodpecker-server`, gRPC NodePort 30900
- **Agent**: Docker Compose on k3s-worker-1 (`/opt/woodpecker-agent/docker-compose.yml`)
- **Trigger**: Git tag only (`when: - event: tag`)
- **UI**: https://ci.web3gate.xyz
- **API Token**: `$WOODPECKER_TOKEN` environment variable (local machine `~/.bashrc`)

## API Access

```bash
# List recent pipelines for a repo
curl -sf "https://ci.web3gate.xyz/api/repos/${REPO_ID}/pipelines?per_page=5" \
  -H "Authorization: Bearer $WOODPECKER_TOKEN"

# Get specific pipeline
curl -sf "https://ci.web3gate.xyz/api/repos/${REPO_ID}/pipelines/${PIPELINE_NUMBER}" \
  -H "Authorization: Bearer $WOODPECKER_TOKEN"

# Get pipeline logs (step_id from pipeline detail)
curl -sf "https://ci.web3gate.xyz/api/repos/${REPO_ID}/logs/${PIPELINE_NUMBER}/${STEP_ID}" \
  -H "Authorization: Bearer $WOODPECKER_TOKEN"

# List all repos
curl -sf "https://ci.web3gate.xyz/api/repos" \
  -H "Authorization: Bearer $WOODPECKER_TOKEN"
```

### Known Repo IDs

| Repo ID | Repository | Service |
|---------|-----------|---------|
| 1 | ivanzzeth/evm-gateway | EVM RPC Gateway |
| 4 | ivanzzeth/web3-opb-auth | Auth Service |

> Check API for current list: `curl -sf "https://ci.web3gate.xyz/api/repos" -H "Authorization: Bearer $WOODPECKER_TOKEN" | python3 -c "import sys,json; [print(f'{r[\"id\"]}: {r[\"full_name\"]}') for r in json.load(sys.stdin)]"`

## Triggering a Build

Builds are triggered by git tags:

```bash
# Tag and push (triggers CI pipeline)
git tag -a v1.0.0 -m "release description"
git push origin v1.0.0
```

Pipeline runs 3 steps sequentially: **test → build-push → deploy**

## Shared CI Scripts

Location: `linux-setup/ci/` (deployed to `/opt/ci/` on CI agent node)

```
linux-setup/ci/
├── build.sh              # docker build + push to localhost:30500
├── deploy.sh             # kubectl set image + rollout status
├── install.sh            # Install scripts to /opt/ci on worker node
└── services/
    ├── evm-gateway.conf          # Per-service config
    ├── ai-cli-proxy-api.conf
    └── web3-opb-auth.conf
```

### Service Config Format

```bash
# linux-setup/ci/services/<repo-name>.conf
IMAGE=<image-name>              # Docker image name
DEPLOY_NAME=<k8s-deployment>    # K8s deployment name (for kubectl set image)

# Test (optional overrides)
TEST_SETUP="apk add --no-cache gcc musl-dev"  # Pre-test setup
TEST_CMD="go test ./... -v -count=1"           # Test command
CGO_ENABLED=1                                   # CGO flag

# Build (optional)
DOCKER_BUILD_ARGS=""            # Extra docker build args
SRC_PATH="."                    # Source path (default: repo root)
```

### build.sh behavior
1. `docker build` from repo root (or `$SRC_PATH`)
2. Tags as `localhost:30500/$IMAGE:$TAG` and `localhost:30500/$IMAGE:latest`
3. Pushes both tags to cluster registry

### deploy.sh behavior
1. `kubectl set image deployment/$DEPLOY_NAME $DEPLOY_NAME=registry.default.svc.cluster.local:5000/$IMAGE:$TAG`
2. `kubectl rollout status` with 120s timeout
3. **Assumes Deployment already exists** — first-time deploy needs manual `kubectl apply`

## Adding a New Service to CI

1. Create service conf: `linux-setup/ci/services/<repo-name>.conf`
2. Add `.woodpecker.yaml` to the repo (copy from existing service, adjust test step)
3. **First-time**: Manually `kubectl apply` the Deployment/Service/Ingress manifests
4. Push a tag to trigger first CI pipeline
5. Verify pipeline passes all 3 steps

### .woodpecker.yaml Template (Go service)

```yaml
when:
  - event: tag

steps:
  - name: test
    image: golang:1.24-alpine3.21
    environment:
      GOPROXY: https://goproxy.cn,direct
      GOPATH: /cache/go
      GOCACHE: /cache/gobuild
    commands:
      - . /ci/services/${CI_REPO_NAME}.conf
      - sh -c "${TEST_SETUP:-true}"
      - export CGO_ENABLED="${CGO_ENABLED:-0}"
      - sh -c "${TEST_CMD}"
    volumes:
      - /opt/ci:/ci:ro

  - name: build-push
    image: docker:cli
    environment:
      DOCKER_API_VERSION: "1.45"
    commands:
      - . /ci/services/${CI_REPO_NAME}.conf
      - . /ci/build.sh ${CI_COMMIT_TAG}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /opt/ci:/ci:ro

  - name: deploy
    image: alpine/k8s:1.32.3
    environment:
      KUBECONFIG_DATA:
        from_secret: kubeconfig
    commands:
      - . /ci/services/${CI_REPO_NAME}.conf
      - . /ci/deploy.sh ${CI_COMMIT_TAG}
    volumes:
      - /opt/ci:/ci:ro
```

### .woodpecker.yaml Template (Frontend / Node.js)

```yaml
when:
  - event: tag

steps:
  - name: build-check
    image: node:22-alpine
    commands:
      - npm ci
      - npm run build

  - name: build-push
    image: docker:cli
    environment:
      DOCKER_API_VERSION: "1.45"
    commands:
      - . /ci/services/${CI_REPO_NAME}.conf
      - . /ci/build.sh ${CI_COMMIT_TAG}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /opt/ci:/ci:ro

  - name: deploy
    image: alpine/k8s:1.32.3
    environment:
      KUBECONFIG_DATA:
        from_secret: kubeconfig
    commands:
      - . /ci/services/${CI_REPO_NAME}.conf
      - . /ci/deploy.sh ${CI_COMMIT_TAG}
    volumes:
      - /opt/ci:/ci:ro
```

## Agent Management

```bash
# Agent runs as Docker Compose on k3s-worker-1
# Location: /opt/woodpecker-agent/docker-compose.yml

# Restart agent
ssh k3s-worker-1 "cd /opt/woodpecker-agent && docker compose restart"

# View agent logs
ssh k3s-worker-1 "cd /opt/woodpecker-agent && docker compose logs --tail=50"

# Resource limits (configured in docker-compose.yml)
# - WOODPECKER_MAX_WORKFLOWS=1 (one pipeline at a time)
# - 1 CPU core (pinned to core 1, core 0 reserved for k3s)
# - 1GB memory per step
```

## Troubleshooting

### Pipeline not triggering
- Verify webhook is configured in GitHub repo settings → Woodpecker
- Check Woodpecker server logs: `kubectl logs -l app=woodpecker-server --tail=50`
- Verify tag was pushed: `git ls-remote --tags origin | grep <tag>`

### Build fails: Docker API version mismatch
- Set `DOCKER_API_VERSION: "1.45"` in build step environment

### Build fails: can't pull base image
- Docker daemon DNS may be overridden by NetBird
- Fix: `/etc/docker/daemon.json` → `{"dns": ["8.8.8.8", "1.1.1.1"]}` on worker node

### Deploy fails: .netrc permission denied
- Use `alpine/k8s` image (runs as root), not `bitnami/kubectl` (non-root)

### Deploy fails: image pull error
- Verify `/etc/rancher/k3s/registries.yaml` maps registry DNS to `http://localhost:30500`
- Restart k3s-agent after changing registries.yaml
