# Stage 5: DELIVER — Ship to Production

## Goal

Containerize, deploy to K3s cluster, and verify production health.

## Prerequisites

**Before starting this stage, you MUST:**

1. **Read `.k3s-ops/cluster-inventory.md`** — know what's deployed, what monitoring exists, where data stores are
2. Read `/k3s-ops` skill — understand cluster architecture, ingress stack, scheduling
3. Read `/woodpecker-ci` skill — understand CI pipeline, shared scripts, how to trigger
4. Read `/netbird` skill — understand VPN mesh for cross-node connectivity
5. Check `$WOODPECKER_TOKEN` env var is set (needed for CI API access)
6. Run `kubectl get nodes` to verify cluster access
7. Run `kubectl get deployments` to check if service already exists in cluster

## Workflow

### Step 0: Security Audit (MANDATORY)

Invoke `/security-review full` before any deployment work.

4 rounds: CODE → DEPS → INFRA → ADVERSARIAL
- Round 1-3 must pass for all services
- Round 4 required for public-facing services
- Every fix must have a test

Record results in `.product-lifecycle/{product}/security-audit.md`.

### Step 1: Containerize

Review or create:
- Multi-stage Dockerfile (builder + minimal runtime)
- .dockerignore (exclude .env, .git, *.key, *.pem)
- Non-root user in final image
- HEALTHCHECK instruction

**If Dockerfile already exists:** Review against security checklist from Round 3, fix issues.

### Step 2: K8s Manifests

**First, check if service is already deployed:**

```bash
kubectl get deployment <service-name> -o yaml
kubectl get svc <service-name>
kubectl get ingress | grep <service-name>
```

**If already deployed:**
- Export current spec, compare with desired state
- Only modify what needs changing (don't blindly overwrite)
- Put updated manifests in `deploy/k8s/` for version control

**If first-time deployment:**
- Create `deploy/k8s/` with Deployment, Service, Ingress
- Match registry address from `/woodpecker-ci` skill (registry.default.svc.cluster.local:5000)
- Match container and deployment name with CI conf (`linux-setup/ci/services/<repo>.conf` → DEPLOY_NAME)
- Include: replicas ≥ 2, resource limits, health probes, securityContext, rolling update

### Step 3: Deploy

**CRITICAL: Local validation before production**

Before deploying to production K3s, validate locally first:

```bash
# Start local cluster (if not running)
minikube start

# Apply manifests locally
kubectl --context minikube apply -f deploy/k8s/

# Verify pods start correctly
kubectl --context minikube get pods -l app=<name>
kubectl --context minikube logs -l app=<name>

# Test health endpoint
kubectl --context minikube port-forward svc/<name> 8700:8700 &
curl -sf http://localhost:8700/health

# Clean up
minikube delete  # or leave running for future use
```

If it works locally, proceed to production. If it crashes locally, fix before touching production.

**CRITICAL: Correct deployment order**

The CI pipeline (Woodpecker) only does `kubectl set image` — it assumes the Deployment
already exists. There are three paths:

**Path A: First-time deployment**
1. Create K8s Secret for config: `kubectl create secret generic <name>-config --from-file=config.yaml`
2. Apply manifests: `kubectl apply -f deploy/k8s/`
3. Verify pods start: `kubectl get pods -l app=<name>`
4. Then push code + tag to let CI take over future updates

**Path B: Existing deployment, code update**
1. Push code to remote
2. Tag release: `git tag -a v1.x.x -m "description" && git push origin v1.x.x`
3. CI auto-triggers: test → build → deploy
4. Monitor: `kubectl rollout status deployment/<name> --timeout=120s`
5. Check pipeline status via Woodpecker API (see `/woodpecker-ci` skill)

**Path C: Spec change (e.g., add securityContext, change replicas)**
1. **Ensure current image is compatible with new spec** — if spec requires new code (e.g., new health endpoint), do Path B first
2. Apply spec: `kubectl apply -f deploy/k8s/deployment.yaml`
3. Verify rollout: `kubectl rollout status deployment/<name>`
4. If crash: `kubectl rollout undo deployment/<name>`

### Step 4: Post-deploy verification

- [ ] Pods running and healthy (all replicas)
- [ ] Ingress accessible externally
- [ ] TLS certificate valid
- [ ] API responds correctly (smoke test)
- [ ] No error spikes in logs (`kubectl logs -l app=<name> --tail=50`)

### Step 5: Monitoring & observability

Check `.k3s-ops/cluster-inventory.md` for existing monitoring stack (Prometheus, Grafana, etc.).

Invoke `/prometheus-monitoring` to configure:
- Prometheus scrape target for the new service (metrics endpoint)
- Alert rules (error rate, response time, pod restarts)

Invoke `/grafana-dashboard` to create:
- Service dashboard (request rate, latency, error rate, resource usage)

Also set up:
- CronJob synthetic monitor (health check every 5 min)
- Readiness probes that check real dependencies

### Step 6: Release

Invoke `/changelog-generator` to create release notes.
Git tag should already exist from Step 3.

### Step 7: Post-deploy smoke tests

Apply smoke test Job if available:
```bash
kubectl apply -f deploy/k8s/smoke-test-job.yaml
kubectl wait --for=condition=complete job/<name>-smoke-test --timeout=120s
```

If smoke fails: `kubectl rollout undo deployment/<name>`

## Gate 5 Checklist

Before advancing to GROW, confirm:

- [ ] **Security audit Round 1-3 passed** (Round 4 if public-facing)
- [ ] All security fixes have tests
- [ ] Service running on K3s with ≥ 2 replicas
- [ ] Ingress accessible with valid TLS
- [ ] Health checks passing
- [ ] Post-deploy smoke tests pass
- [ ] Monitoring configured
- [ ] Changelog and git tag created
- [ ] Rollback tested or documented (`kubectl rollout undo`)
