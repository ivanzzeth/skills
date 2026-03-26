---
name: k3s-ops
description: >
  K3s hybrid cloud cluster operations AND local minikube dev environment — node management,
  service deployment, MetalLB/Traefik ingress, cert-manager TLS, private Docker registry,
  CI/CD with Woodpecker, resource limits, scheduling strategies, minikube local dev setup,
  and troubleshooting. Designed for cross-cloud/cross-country clusters connected via WireGuard
  mesh VPN (NetBird), with a parallel local minikube environment for development.
  This skill should be used when deploying, managing, or troubleshooting K3s clusters,
  minikube local environments, Kubernetes services, ingress, TLS certificates, CI/CD pipelines,
  or container registry operations.
  Triggers include: "k3s", "kubernetes", "kubectl", "helm", "deploy to k3s", "k3s cluster",
  "minikube", "local dev", "local environment", "本地环境", "ingress", "traefik", "metallb",
  "cert-manager", "woodpecker", "CI/CD pipeline", "docker registry", "k8s deployment", "pod",
  "service expose", "TLS certificate", "部署", "集群", "K3s运维", "容器编排".
---

# k3s-ops

Hybrid cloud K3s cluster operations + local minikube dev environment. Covers node setup, service deployment, ingress stack, CI/CD, resource management, and troubleshooting.

## IRON RULE: Environment Safety

Two independent Kubernetes environments exist. **Mixing them up can destroy production.**

| Environment | kubectl context | Cluster | Purpose |
|-------------|----------------|---------|---------|
| **Production** | `default` | K3s (Vultr Tokyo, 2 nodes) | Live services, real users |
| **Local Dev** | `minikube` | Minikube (single node, local) | Development, testing |

### Mandatory Rules

1. **ALWAYS use `--context` flag** — never rely on `current-context`
   ```bash
   kubectl --context minikube get pods     # local dev
   kubectl --context default get pods      # production
   ```
2. **Before ANY kubectl/helm command**: confirm which environment you're targeting
3. **NEVER apply production manifests directly to minikube** — they have incompatible:
   - `nodeSelector` (production: `vultr-tokyo`, minikube: none)
   - Image references (production: `registry.default.svc.cluster.local:5000/`, minikube: local images)
   - Ingress class (production: `traefik`, minikube: `nginx`)
   - TLS (production: cert-manager Let's Encrypt, minikube: none/self-signed)
4. **Each service has separate manifests**: `deploy/k8s/` = production, `deploy/minikube/` = local dev
5. **When user says "deploy" without specifying environment**: ASK which one

### Quick Context Check

```bash
# See all contexts and which is current
kubectl config get-contexts
# Expected output:
#   CURRENT   NAME       CLUSTER    AUTHINFO   NAMESPACE
#   *         default    default    default              ← production k3s
#             minikube   minikube   minikube   default   ← local dev
```

## IMPORTANT: Read Cluster Inventory First

Before ANY cluster operation, read the project-level cluster inventory:

```
.k3s-ops/cluster-inventory.md
```

This file lists all deployed services, data stores, monitoring stack, CI/CD components,
and their access details. **Don't guess what's in the cluster — read the inventory.**

The inventory is project-specific (not in this skill). If it doesn't exist, scan the
cluster first and create it:

```bash
# Production
kubectl --context default get deployments -A
kubectl --context default get svc -A
kubectl --context default get ingress -A

# Local dev
kubectl --context minikube get deployments -A
kubectl --context minikube get svc -A
kubectl --context minikube get ingress -A
```

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
              Flannel WireGuard-Native
              (public IP direct, port 51821)
```

Components:
- **K3s server** (single master with `--cluster-init` for etcd, expandable to HA)
- **K3s agents** (workers across cloud providers and local machines)
- **Flannel WireGuard-Native** for encrypted pod network over public IPs (ChaCha20-Poly1305)
- **NetBird mesh VPN** retained for Teleport SSH access and non-k3s node connectivity
- **MetalLB + Traefik + cert-manager** for public service exposure

## Node Setup

### Install K3s Server (Master)

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --cluster-init \
  --node-ip=<PUBLIC_IP> \
  --node-external-ip=<PUBLIC_IP> \
  --flannel-backend=wireguard-native \
  --flannel-conf=/etc/rancher/k3s/flannel.json \
  --tls-san=<PUBLIC_IP> \
  --disable=servicelb" sh -
```

Key flags:
- `--cluster-init`: Enable embedded etcd (HA-ready, can add masters later with zero downtime)
- `--node-ip=<PUBLIC_IP>`: Use public IP for inter-node communication (not VPN IP — avoids overlay instability)
- `--node-external-ip=<PUBLIC_IP>`: Advertised public IP for LoadBalancer services
- `--flannel-backend=wireguard-native`: Encrypted pod network via WireGuard (ChaCha20-Poly1305)
- `--flannel-conf=/etc/rancher/k3s/flannel.json`: Custom config for WireGuard port (see below)
- `--disable=servicelb`: Use MetalLB instead for flexible multi-node IP management

### Flannel WireGuard Config

Create `/etc/rancher/k3s/flannel.json` on **every node** (server and agent):

```json
{
  "Network": "10.42.0.0/16",
  "EnableIPv4": true,
  "EnableIPv6": false,
  "Backend": {
    "Type": "wireguard",
    "PersistentKeepalive": 25,
    "ListenPort": 51821
  }
}
```

> **Port 51821** avoids conflict with NetBird WireGuard (default 51820). The `--flannel-wireguard-port` flag does NOT exist — use `--flannel-conf` instead.

### Install K3s Agent (Worker)

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="agent \
  --node-ip=<PUBLIC_IP> \
  --node-external-ip=<PUBLIC_IP> \
  --flannel-conf=/etc/rancher/k3s/flannel.json" \
  K3S_URL=https://<MASTER_PUBLIC_IP>:6443 \
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
| **MetalLB** (L2 mode) | Supports multiple IP pools and fine-grained IP allocation across nodes. MetalLB L2 properly advertises public IPs via ARP. |
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

**Why hostNetwork**: Default pod network adds overhead (iptables DNAT). With `hostNetwork: true`, Traefik listens directly on all host interfaces. Same-region cross-node latency with flannel wireguard-native is ~0.6ms.

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

> **Full details:** See `/woodpecker-ci` skill for pipeline management, API access,
> shared CI scripts, templates, and troubleshooting.

Summary:
- **Server**: K3s deployment `woodpecker-server`, gRPC NodePort 30900
- **Agent**: Docker Compose on k3s-worker-1, pinned to CPU core 1 (core 0 for k3s)
- **Trigger**: Git tag → test → build-push → deploy (3-step pipeline)
- **API Token**: `$WOODPECKER_TOKEN` env var (local machine `~/.bashrc`)
- **UI**: https://ci.web3gate.xyz
- **Shared scripts**: `linux-setup/ci/` (build.sh, deploy.sh, services/*.conf)

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

- **Latency-sensitive services**: Pin to same region as ingress node. Same-region flannel wireguard-native latency ~0.6ms. Cross-region can add seconds.
- **Traefik**: Pin to master with `hostNetwork: true`. Must be same region as backend pods.
- **Ingress + backend = same region**: Never route latency-sensitive traffic cross-region.
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

**Cause**: ServiceLB is disabled (`--disable=servicelb`). MetalLB handles LoadBalancer IPs.

**Fix**: Ensure MetalLB is installed with correct IPAddressPool. If not using MetalLB, remove `--disable=servicelb`.

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

## Minikube Local Dev Environment

### Overview

Minikube provides a single-node local Kubernetes cluster for development and testing. It mirrors the production k3s environment but with simplified infrastructure (no MetalLB, no cert-manager, no Woodpecker CI).

### Prerequisites

```bash
# Verify minikube is running
minikube status

# If not running:
minikube start --cpus=4 --memory=8192 --driver=docker
```

### Minikube Addons

```bash
# Enable nginx ingress (replaces production Traefik)
minikube addons enable ingress

# Enable registry (optional, alternative to `minikube image load`)
minikube addons enable registry

# Enable metrics-server (for kubectl top)
minikube addons enable metrics-server
```

### Infrastructure Setup (PostgreSQL + Redis)

```bash
# Add Helm repos (same as production)
helm --kube-context minikube repo add bitnami https://charts.bitnami.com/bitnami
helm --kube-context minikube repo update

# PostgreSQL
helm --kube-context minikube install postgres bitnami/postgresql \
  --set auth.postgresPassword=devpassword \
  --set primary.persistence.size=1Gi

# Redis
helm --kube-context minikube install redis bitnami/redis \
  --set auth.password=devpassword \
  --set master.persistence.size=1Gi \
  --set replica.replicaCount=0
```

### Image Build Workflow

Production uses Woodpecker CI. Local dev builds images directly:

```bash
# Option 1: Build inside minikube's Docker daemon (fastest, no push)
eval $(minikube docker-env)
cd /path/to/service
docker build -t <service>:dev -f Dockerfile .
eval $(minikube docker-env -u)

# Option 2: Build on host, load into minikube
docker build -t <service>:dev -f Dockerfile .
minikube image load <service>:dev
```

**Important**: Deployments must use `imagePullPolicy: Never` or `IfNotPresent` for local images.

### Manifest Differences (Production vs Minikube)

When creating minikube manifests from production ones, apply these changes:

| Field | Production | Minikube |
|-------|-----------|---------|
| `nodeSelector` | `topology.kubernetes.io/zone: vultr-tokyo` | **Remove entirely** |
| `replicas` | 2 | 1 |
| `image` | `registry.default.svc.cluster.local:5000/<name>:<tag>` | `<name>:dev` |
| `imagePullPolicy` | `IfNotPresent` | `Never` (for local images) |
| `resources.requests` | Tuned for production | Lower or remove |
| `resources.limits` | Tuned for production | Lower or remove |
| Ingress `ingressClassName` | `traefik` | `nginx` |
| Ingress TLS | cert-manager + Let's Encrypt | Remove or self-signed |
| Ingress host | `*.web3gate.xyz` | `*.local.web3gate.xyz` |
| Config secrets | Kubernetes Secret (production values) | Kubernetes Secret (dev values) |

### Local Domain Setup

Add to `/etc/hosts` (use `minikube ip` for the IP):

```bash
echo "$(minikube ip) auth.local.web3gate.xyz account.local.web3gate.xyz evm.local.web3gate.xyz app.local.web3gate.xyz" | sudo tee -a /etc/hosts
```

### Accessing Services

```bash
# Port-forward (simplest, no ingress needed)
kubectl --context minikube port-forward svc/web3-opb-auth 8700:8700
kubectl --context minikube port-forward svc/web3-opb-auth-frontend 8080:8080

# Via minikube service (opens browser)
minikube service web3-opb-auth --url

# Via ingress (requires ingress addon + /etc/hosts)
curl http://auth.local.web3gate.xyz/health
```

### Config Secret for Local Dev

Create a dev config secret (never reuse production secrets):

```bash
# Create config.yaml for local dev (from config.example.yaml, with dev values)
kubectl --context minikube create secret generic web3-opb-auth-config \
  --from-file=config.yaml=config.dev.yaml
```

### Common Minikube Commands

```bash
# Check cluster status
minikube status

# View dashboard
minikube dashboard

# SSH into minikube node
minikube ssh

# Get minikube IP (for /etc/hosts)
minikube ip

# View logs
kubectl --context minikube logs deployment/<name> -f

# Restart from scratch
minikube delete && minikube start --cpus=4 --memory=8192
```

### Minikube vs Production Comparison

```
Production (k3s):
  Internet → DNS → MetalLB → Traefik (hostNetwork) → Service → Pod
  TLS: cert-manager (Let's Encrypt DNS-01)
  Registry: in-cluster registry:5000 (NodePort 30500)
  CI/CD: Woodpecker (git tag → build → push → deploy)

Local Dev (minikube):
  localhost → /etc/hosts → minikube IP → nginx-ingress → Service → Pod
  TLS: none (HTTP) or self-signed
  Registry: minikube image load (no registry needed)
  CI/CD: manual (docker build → minikube image load → kubectl apply)
```

## Key Lessons (Production K3s)

1. **Use public IP as --node-ip** when nodes have stable public IPs — avoids overlay network instability
2. **Flannel wireguard-native port conflicts with NetBird** — use `--flannel-conf` with `"ListenPort": 51821` (NOT `--flannel-wireguard-port`, that flag doesn't exist)
3. **Changing --node-ip requires etcd member update** — update peer URL via `etcdctl member update` first
4. **Changing flannel backend requires cleaning old interfaces** — `ip link delete flannel.1` and clear routes before restart
5. **Never HTTP-01 in hybrid clusters** — always DNS-01
6. **MetalLB for flexible IP management** — supports multi-node IP pools
7. **Disable UFW on k3s nodes** — use cloud firewalls instead
8. **hostNetwork for Traefik** — eliminates iptables DNAT overhead
9. **CPU pinning for CI** — protect online services from build load
10. **Proxy leaks affect everything** — override in each deployment
11. **DOCKER_BUILDKIT=0** — when proxy is needed for image pulls
12. **Root container images for CI deploy steps** — avoids permission issues
13. **Ingress + backend = same region** — cross-region adds seconds of latency
14. **NetBird + k3s = DNS config required** — always add public DNS upstream in NetBird dashboard
