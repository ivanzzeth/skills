# Round 3: INFRA — Container & K8s Hardening Checklist

## Container Security

### Dockerfile
- [ ] Base image is minimal (distroless or alpine, not ubuntu/debian full)
- [ ] Base image tag pinned to digest (`@sha256:...`) or specific version
- [ ] Multi-stage build: build stage ≠ runtime stage
- [ ] Final image runs as non-root user
- [ ] No secrets in any build layer (no `COPY .env`, no `ARG SECRET=...`)
- [ ] No unnecessary tools in final image (no curl, no shell if possible)
- [ ] `.dockerignore` excludes `.env`, `.git`, `*.key`, `*.pem`

### Image Scanning

```bash
# Scan image for vulnerabilities
# Option 1: Trivy (free, comprehensive)
trivy image my-service:latest

# Option 2: Grype (anchore)
grype my-service:latest
```

- [ ] Zero critical/high vulnerabilities in image scan
- [ ] Image scan integrated in CI pipeline

## K8s Hardening

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 65534           # nobody
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

- [ ] `runAsNonRoot: true` set
- [ ] `readOnlyRootFilesystem: true` (**must add emptyDir mounts for /tmp and any writable paths** — Go runtime, casbin, SQLite all need writable /tmp)
- [ ] `allowPrivilegeEscalation: false`
- [ ] All capabilities dropped
- [ ] No `privileged: true` containers
- [ ] No `hostNetwork`, `hostPID`, `hostIPC`

### Resource Limits
- [ ] CPU and memory limits set on all containers
- [ ] Limits prevent single pod from exhausting node resources
- [ ] Requests set appropriately for scheduling

### Network Policy
- [ ] Default deny ingress policy exists
- [ ] Each service has explicit ingress rules (only from needed sources)
- [ ] Egress restricted to known endpoints (DB, Redis, external APIs)

### RBAC
- [ ] Service accounts use minimal permissions
- [ ] No `cluster-admin` role bindings for application pods
- [ ] Secrets access restricted to pods that need them

## Secrets Management

- [ ] Secrets stored in K8s Secrets (base64, not plaintext in manifests)
- [ ] Secret manifests NOT committed to git
- [ ] Consider external secrets operator (Vault, AWS SM) for sensitive services
- [ ] Secrets rotatable without pod restart (watch for file-mounted secrets)
- [ ] `kubectl describe pod` does not reveal secret values
- [ ] `HISTFILE` unset in debug sessions (prevent secrets in shell history)

## TLS

- [ ] All external endpoints TLS-terminated (via Ingress + cert-manager)
- [ ] Certificates auto-renewed (cert-manager with Let's Encrypt)
- [ ] No self-signed certs in production
- [ ] TLS version ≥ 1.2 enforced
- [ ] HSTS headers set on public endpoints

## Audit

```bash
# Check what the service account can do
kubectl auth can-i --list --as=system:serviceaccount:default:my-service

# Check for overly permissive roles
kubectl get clusterrolebindings -o json | jq '.items[] | select(.subjects[]?.name == "my-service")'
```
