---
name: k3s-ops
description: >
  K3s hybrid cloud cluster operations — node management, service deployment, MetalLB/Traefik
  ingress, cert-manager TLS, private Docker registry, CI/CD with Woodpecker, resource limits,
  scheduling strategies, and troubleshooting. Designed for cross-cloud/cross-country clusters
  connected via WireGuard mesh VPN (NetBird). This skill should be used when deploying,
  managing, or troubleshooting K3s clusters, Kubernetes services, ingress, TLS certificates,
  CI/CD pipelines, or container registry operations.
  Triggers include: "k3s", "kubernetes", "kubectl", "helm", "deploy to k3s", "k3s cluster",
  "ingress", "traefik", "metallb", "cert-manager", "woodpecker", "CI/CD pipeline",
  "docker registry", "k8s deployment", "pod", "service expose", "TLS certificate",
  "部署", "集群", "K3s运维", "容器编排".
---

# k3s-ops

Hybrid cloud K3s cluster operations. Covers node setup, service deployment, ingress stack, CI/CD, resource management, and troubleshooting for cross-cloud clusters connected via WireGuard mesh VPN.

## Cluster Architecture

```
                    Internet
                       │
              ┌────────┼────────┐
              │        │        │
         ┌────▼───┐ ┌──▼─────┐ ┌▼──────────┐
         │Master  │ │Worker  │ │Local Dev   │
         │(VPS A) │ │(VPS B) │ │(Home, opt.)│
         └───┬────┘ └───┬────┘ └──┬─────────┘
             │          │         │
             └──────────┼─────────┘
                  WireGuard Mesh
                  (100.64.0.0/10)
```

Components:
- **K3s server** (single master with `--cluster-init` for etcd, expandable to HA)
- **K3s agents** (workers across cloud providers and local machines)
- **NetBird mesh VPN** for inter-node communication
- **MetalLB + Traefik + cert-manager** for public service exposure

## Node Setup

### Install K3s Server (Master)

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --cluster-init \
  --node-ip=<NETBIRD_IP> \
  --node-external-ip=<PUBLIC_IP> \
  --flannel-iface=wt0 \
  --tls-san=<NETBIRD_IP> \
  --disable=servicelb" sh -
```

Key flags:
- `--cluster-init`: Enable embedded etcd (HA-ready, can add masters later with zero downtime)
- `--node-ip=<NETBIRD_IP>`: Inter-node communication over VPN
- `--node-external-ip=<PUBLIC_IP>`: Advertised public IP for LoadBalancer services
- `--flannel-iface=wt0`: Route pod traffic over NetBird interface
- `--disable=servicelb`: Use MetalLB instead (ServiceLB cannot bind to public IP when node-ip is VPN IP)

### Install K3s Agent (Worker)

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="agent \
  --node-ip=<NETBIRD_IP> \
  --flannel-iface=wt0" \
  K3S_URL=https://<MASTER_NETBIRD_IP>:6443 \
  K3S_TOKEN=<TOKEN> sh -
```

Get token from master: `sudo cat /var/lib/rancher/k3s/server/node-token`

### Per-Node Checklist

For each new node:

1. Install NetBird agent + join mesh
2. Install Teleport agent + join cluster (for certificate-based SSH)
3. Create deployment user (`useradd -m -s /bin/bash deployer`)
4. Configure sudoers: `echo 'deployer ALL=(root) NOPASSWD: ALL' | tee /etc/sudoers.d/deployer`
5. Disable UFW: `sudo ufw disable` (conflicts with k3s iptables)
6. Install k3s (server or agent)
7. Configure `/etc/rancher/k3s/registries.yaml` for private registry
8. Set node labels

## Ingress Stack: MetalLB + Traefik + cert-manager

### Why This Stack

| Component | Reason |
|-----------|--------|
| **MetalLB** (L2 mode) | ServiceLB hostPort binds to `--node-ip` (VPN IP), cannot bind to public IP. MetalLB L2 properly advertises public IPs via ARP. |
| **Traefik** (k3s built-in) | Ingress controller with `hostNetwork: true` for zero-overhead routing. |
| **cert-manager** (DNS-01) | HTTP-01 fails in hybrid clusters (hairpin NAT, DNS issues, proxy leaks). DNS-01 works regardless of network topology. |

### Install MetalLB

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml
```

Configure IP pool:

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: public-pool
  namespace: metallb-system
spec:
  addresses:
  - <MASTER_PUBLIC_IP>/32
  - <WORKER_PUBLIC_IP>/32
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
  - public-pool
```

### Configure Traefik with hostNetwork

```yaml
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: traefik
  namespace: kube-system
spec:
  valuesContent: |-
    hostNetwork: true
    dnsPolicy: ClusterFirstWithHostNet
    nodeSelector:
      kubernetes.io/hostname: <MASTER_NODE_NAME>
```

**Why hostNetwork**: Default pod network adds ~300ms overhead (iptables DNAT + flannel vxlan). With `hostNetwork: true`, same-region latency drops from ~730ms to ~24ms.

### Install cert-manager (DNS-01)

```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true
```

ClusterIssuer example (Route 53):

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: <YOUR_EMAIL>
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - dns01:
        route53:
          region: us-east-1
          hostedZoneID: <HOSTED_ZONE_ID>
          accessKeyID: <ACCESS_KEY_ID>
          secretAccessKeySecretRef:
            name: aws-route53-creds
            key: secret-access-key
```

**Never use HTTP-01** in hybrid clusters — use DNS-01 (Route 53, Cloudflare, etc.).

## Private Docker Registry

### Deploy in Cluster

```yaml
# registry:2 as ClusterIP + NodePort
apiVersion: v1
kind: Service
metadata:
  name: registry
spec:
  type: NodePort
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30500
  selector:
    app: registry
```

### Configure Nodes

On **every** k3s node, create `/etc/rancher/k3s/registries.yaml`:

```yaml
mirrors:
  "registry.default.svc.cluster.local:5000":
    endpoint:
      - "http://localhost:30500"
```

Then restart k3s/k3s-agent. Deployments reference images as `registry.default.svc.cluster.local:5000/<image>:<tag>`.

### Image Push (CI/CD)

```bash
docker build -t localhost:30500/my-app:v1.0 .
docker push localhost:30500/my-app:v1.0
```

## CI/CD with Woodpecker

### Architecture

- **Woodpecker Server**: In k3s (pinned to worker node)
- **Woodpecker Agent**: Docker Compose on the same worker (not in k3s — needs Docker socket access)

### Pipeline (triggered on git tag)

```yaml
# .woodpecker.yaml
steps:
  - name: test
    image: golang:1.24-alpine
    commands:
      - go test ./...

  - name: build-push
    image: docker:cli
    environment:
      DOCKER_BUILDKIT: "0"  # Legacy builder uses daemon proxy correctly
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    commands:
      - docker build -t localhost:30500/my-app:${CI_COMMIT_TAG} .
      - docker push localhost:30500/my-app:${CI_COMMIT_TAG}

  - name: deploy
    image: alpine/k8s:1.32.4  # Runs as root — avoids .netrc permission issues
    commands:
      - kubectl set image deployment/my-app my-app=registry.default.svc.cluster.local:5000/my-app:${CI_COMMIT_TAG}
      - kubectl rollout status deployment/my-app --timeout=120s
```

### Key Configuration Notes

- Use `docker:cli` not `plugins/docker` — avoids Docker API version mismatch
- Use `alpine/k8s` not `bitnami/kubectl` — non-root images cause `.netrc` permission denied
- Set `DOCKER_BUILDKIT=0` — BuildKit ignores daemon proxy for metadata fetch
- Set Docker daemon DNS: `/etc/docker/daemon.json` → `{"dns": ["8.8.8.8", "1.1.1.1"]}` (NetBird overrides host DNS)

### Agent Resource Limits

```yaml
# Docker Compose environment for Woodpecker agent
environment:
  WOODPECKER_MAX_WORKFLOWS: "1"           # One pipeline at a time
  WOODPECKER_BACKEND_DOCKER_LIMIT_MEM: "1073741824"    # 1GB per step
  WOODPECKER_BACKEND_DOCKER_LIMIT_CPU_QUOTA: "100000"  # 1 CPU core per step
  WOODPECKER_BACKEND_DOCKER_LIMIT_CPU_SET: "1"         # Pin to core 1 (core 0 for k3s)
```

## Resource Management

### Optimization Principles

1. **Requests ≈ actual usage** — avoid over-reservation that blocks scheduling
2. **Limits = 2-5x requests** — headroom for traffic spikes
3. **CI isolated by CPU pinning** — core 0 for k3s, core 1 for CI builds
4. **MAX_WORKFLOWS=1** — small nodes cannot handle concurrent builds
5. **Monitor before tuning** — deploy first, observe with `kubectl top`, then adjust

### Monitoring Commands

```bash
kubectl top nodes                              # Node-level usage
kubectl top pods --all-namespaces              # Pod-level usage
kubectl describe pod <pod> | grep -A5 "Requests\|Limits"  # Check configured limits
docker stats --no-stream                       # CI build container usage
```

## Scheduling Strategy

### Node Labels

```bash
# Location labels
kubectl label node <node> topology.kubernetes.io/zone=<zone>
# e.g., vultr-tokyo, oracle-cloud, local, cn

# Capability labels
kubectl label node <node> node.kubernetes.io/instance-type=<type>
# e.g., high-perf, standard
```

### China Node Taint

```bash
kubectl taint nodes <cn-node> region=cn:NoSchedule
```

Pods must have matching toleration:

```yaml
tolerations:
  - key: "region"
    operator: "Equal"
    value: "cn"
    effect: "NoSchedule"
```

### Scheduling Best Practices

- **Latency-sensitive services**: Pin to same region as ingress node. Cross-region pod network adds 2-3s latency.
- **Traefik**: Pin to master with `hostNetwork: true`. Must be same region as backend pods.
- **Ingress + backend = same region**: Never route latency-sensitive traffic cross-region through flannel.
- **Compute-heavy workloads**: Schedule on high-perf nodes or run outside k3s via Docker.

## Troubleshooting

### DNS Resolution Fails in Pods

**Cause**: NetBird replaces `/etc/resolv.conf` with its own DNS.

**Fix**:
1. NetBird Dashboard → DNS → add `8.8.8.8:53` + `1.1.1.1:53` for all domains
2. CoreDNS Corefile: `forward . 8.8.8.8 1.1.1.1` (not `forward . /etc/resolv.conf`)

### CoreDNS CrashLoopBackOff

**Cause**: Custom ConfigMap `coredns-custom` with a top-level `. {}` block conflicts with the main Corefile.

**Fix**: Override files are imported INSIDE the existing `. {}` block — only add directives, not server blocks.

### ServiceLB Shows `<pending>` EXTERNAL-IP

**Cause**: ServiceLB hostPort binds to `--node-ip` (VPN IP), not public IP.

**Fix**: Use MetalLB L2 mode instead. MetalLB advertises public IPs via ARP on the physical interface.

### Proxy Environment Leaks into Pods

**Cause**: Host `http_proxy` inherited by k3s-agent, passed to pods. Proxy address (`127.0.0.1:7897`) doesn't exist inside containers.

**Fix**: Override per-deployment via Helm:
```bash
--set 'extraEnv[0].name=HTTP_PROXY' --set-string 'extraEnv[0].value=' \
--set 'extraEnv[1].name=HTTPS_PROXY' --set-string 'extraEnv[1].value=' \
--set 'extraEnv[2].name=NO_PROXY' --set-string 'extraEnv[2].value=*'
```

### cert-manager HTTP-01 Fails

**Cause**: Hairpin NAT + DNS issues + proxy leaks in hybrid clusters.

**Fix**: Use DNS-01 validation instead (Route 53, Cloudflare). DNS-01 does not require pods to access external HTTP endpoints.

### Image Pull Fails (registry.default.svc.cluster.local)

**Cause**: containerd resolves registry hostnames using host DNS, not CoreDNS. Cluster-internal DNS names don't resolve on the host.

**Fix**: Configure `/etc/rancher/k3s/registries.yaml` mapping the registry DNS to `http://localhost:<nodePort>`. Restart k3s after.

### BuildKit Ignores Daemon Proxy

**Cause**: Docker BuildKit uses its own network stack, ignores daemon proxy from systemd env.

**Fix**: Set `DOCKER_BUILDKIT=0` to use legacy builder which respects daemon proxy.

### UFW Blocks Traffic

**Cause**: UFW conflicts with k3s iptables rules.

**Fix**: `sudo ufw disable` on all k3s nodes. Use cloud provider firewalls or k8s network policies.

## Key Lessons

1. **NetBird + k3s = DNS config required** — always add public DNS upstream
2. **Never HTTP-01 in hybrid clusters** — always DNS-01
3. **MetalLB over ServiceLB** — when `--node-ip` is VPN IP
4. **Disable UFW on k3s nodes** — use cloud firewalls instead
5. **hostNetwork for Traefik** — eliminates ~300ms pod network overhead
6. **CPU pinning for CI** — protect online services from build load
7. **Proxy leaks affect everything** — override in each deployment
8. **DOCKER_BUILDKIT=0** — when proxy is needed for image pulls
9. **Root container images for CI deploy steps** — avoids permission issues
10. **Ingress + backend = same region** — cross-region flannel adds 2-3s
