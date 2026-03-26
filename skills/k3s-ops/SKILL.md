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
kubectl get deployments -A
kubectl get svc -A
kubectl get ingress -A
kubectl get statefulsets -A
kubectl get cronjobs -A
docker ps --format "{{.Names}}\t{{.Image}}\t{{.Ports}}"  # for non-K8s services
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

## Key Lessons

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
