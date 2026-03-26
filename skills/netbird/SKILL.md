---
name: netbird
description: >
  NetBird self-hosted WireGuard mesh VPN operations — server/client setup, peer management,
  reverse proxy configuration, Kubernetes operator integration, DNS management, ACL policies,
  and troubleshooting. This skill should be used when setting up or managing NetBird VPN
  infrastructure, connecting peers, exposing services via reverse proxy, integrating with
  K3s/K8s clusters, or troubleshooting VPN connectivity issues.
  Triggers include: "netbird", "wireguard", "mesh VPN", "VPN setup", "peer connection",
  "netbird reverse proxy", "netbird ACL", "netbird DNS", "netbird operator", "netbird status",
  "VPN tunnel", "wt0 interface", "setup key", "peer approval", "组网", "内网穿透",
  "VPN互联", "节点互联".
---

# netbird

Self-hosted WireGuard mesh VPN for connecting all devices into a private network. Covers server deployment, client setup, reverse proxy, Kubernetes integration, and security hardening.

## Architecture Overview

```
                     Internet
                        │
              ┌─────────┼─────────┐
              │         │         │
         ┌────▼───┐ ┌───▼────┐ ┌─▼──────────┐
         │Cloud A  │ │Cloud B │ │ Home Server │
         │(VPS)    │ │(VPS)   │ │ (behind NAT)│
         └────┬───┘ └───┬────┘ └─┬──────────┘
              │         │         │
              └─────────┼─────────┘
                   WireGuard Mesh
                   (100.64.0.0/10)
```

Key components:
- **Management Server**: Coordinates peer discovery, stores config, hosts dashboard
- **Signal Server**: Facilitates peer-to-peer connection negotiation
- **Relay Server**: Relays traffic when direct P2P is not possible (e.g., symmetric NAT)
- **Peers**: Each device running the NetBird client

## Server Installation (Self-hosted)

### Prerequisites

- A server with a public IP
- A domain with DNS A record pointing to the server (e.g., `nb.example.com`)
- Docker & Docker Compose installed

### Install

```bash
curl -fsSL https://github.com/netbirdio/netbird/releases/latest/download/getting-started.sh | bash
```

This script pulls Docker images, generates config, and starts all services (management + dashboard + signal + relay) with Traefik reverse proxy and automatic Let's Encrypt HTTPS.

### Post-install

```bash
# Verify all containers are running
docker compose ps

# Open dashboard in browser and complete setup wizard
# https://nb.example.com

# Generate a Setup Key: Dashboard → Access → Setup Keys → Add
```

## Client Installation

### Ubuntu / Debian

```bash
curl -fsSL https://pkgs.netbird.io/install.sh | sh
```

If behind a proxy:

```bash
curl -fsSL -x http://127.0.0.1:7897 https://pkgs.netbird.io/install.sh | \
  sudo https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 sh
```

### Connect

```bash
# Headless servers: always use --setup-key (no browser available)
sudo netbird up --setup-key <SETUP_KEY> --management-url https://nb.example.com

# Desktop: can use OAuth login
sudo netbird up --management-url https://nb.example.com
```

### Common Commands

```bash
sudo netbird status              # Connection status
sudo netbird status --detail     # Detailed peer info (IPs, latency, routes)
sudo netbird down                # Disconnect
sudo netbird up                  # Reconnect (no setup key needed after initial registration)
journalctl -u netbird -f         # View logs
ip addr show wt0                 # Check NetBird interface IP
```

## Reverse Proxy

NetBird includes a built-in reverse proxy for exposing internal services to the public internet with automatic TLS.

### Setup via Dashboard

Dashboard → **Reverse Proxy** → **Services** → **Add Service**:

1. Enter a **subdomain** (e.g., `grafana`)
2. Select base domain (e.g., `proxy.example.com`)
3. **Add Target**: select peer, protocol (HTTP/HTTPS), and port
4. **Authentication**: choose SSO / Password / PIN / Public
5. Click **Add Service**, wait for status to become **active**

### Authentication Options

| Method | Use Case |
|--------|----------|
| **SSO** | Browser-accessed services (dashboards, admin panels) |
| **Password** | Shared access with a common password |
| **PIN Code** | Numeric code for simple access |
| **Public** | Services with their own authentication (e.g., Infisical, JumpServer) |

### Best Practices

- **SSO for browser services**: Grafana, Prometheus, internal dashboards
- **Public for self-auth services**: Services that have their own login (JumpServer, Infisical)
- **Direct NetBird IP for programmatic access**: SDKs, CLIs, and APIs should use the internal NetBird IP directly — no reverse proxy overhead, no SSO interference, traffic already encrypted via WireGuard

### Limitation: Cannot Proxy Services on the Proxy Server Itself

Traffic goes through the WireGuard tunnel to reach the target peer. Localhost-to-localhost does not traverse the tunnel.

**Workaround**: Deploy the service on a different NetBird peer.

## Kubernetes Integration

### NetBird as K3s/K8s Network Layer

> **WARNING: Overlay on Overlay — unstable.** Using NetBird IP as `--node-ip` with Flannel means Flannel's overlay (VXLAN/WireGuard) runs on top of NetBird's WireGuard tunnel. This double encapsulation causes frequent disconnections, high latency (2-3s cross-node), and difficult-to-debug failures. **Not recommended for production.**

**Legacy approach** (NetBird overlay — unstable, not recommended):

```bash
# K3s server install — use NetBird IP as node IP
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --node-ip=<NETBIRD_IP> \
  --flannel-iface=wt0 \
  --tls-san=<NETBIRD_IP>" sh -
```

**Recommended approach** (public IP + flannel wireguard-native):

Use public IPs as `--node-ip` with Flannel WireGuard-Native for a single layer of WireGuard encryption. NetBird is retained for Teleport SSH access and non-k3s node connectivity, but k3s traffic goes directly over public IP.

```bash
# K3s server install — public IP direct
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --cluster-init \
  --node-ip=<PUBLIC_IP> \
  --node-external-ip=<PUBLIC_IP> \
  --flannel-backend=wireguard-native \
  --flannel-conf=/etc/rancher/k3s/flannel.json \
  --tls-san=<PUBLIC_IP> \
  --disable=servicelb" sh -
```

Custom flannel config (`/etc/rancher/k3s/flannel.json`) — port 51821 avoids conflict with NetBird's WireGuard on 51820:

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

See the `k3s-ops` skill for full setup details.

### NetBird Kubernetes Operator

Expose K8s Services to NetBird network via annotations:

```bash
# Install operator
helm repo add netbird https://netbirdio.github.io/kubernetes-operator
helm repo update

kubectl create namespace netbird-operator
kubectl create secret generic netbird-api-key-secret \
  -n netbird-operator \
  --from-literal=apiKey=<NETBIRD_API_KEY>

helm install netbird-operator netbird/netbird-operator \
  --namespace netbird-operator \
  --set netbirdAPI.endpoint=https://nb.example.com/api \
  --set netbirdAPI.keyFromSecret=netbird-api-key-secret
```

Expose a service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    netbird.io/expose: "true"
    netbird.io/groups: "public-access"
    netbird.io/resource-name: my-service-web
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

## DNS Management

### Problem: NetBird Overwrites resolv.conf

NetBird replaces `/etc/resolv.conf` with its own DNS server that only resolves `*.nb.example.com`. Original saved at `/etc/resolv.conf.original.netbird`.

### Fix: Add Public DNS Forwarding

In NetBird Dashboard → **DNS** → **Nameservers**:

1. Add a nameserver group with `8.8.8.8:53` and `1.1.1.1:53`
2. Set it to match **all domains** (not just NetBird domains)

This makes NetBird DNS forward non-NetBird queries to public DNS.

### For K3s CoreDNS

Also update CoreDNS Corefile to not depend on `/etc/resolv.conf`:

```
forward . 8.8.8.8 1.1.1.1
```

Instead of the default `forward . /etc/resolv.conf`.

## Security Hardening

### SSH Access Restriction

Restrict SSH to NetBird subnet only:

```bash
# UFW firewall (recommended)
sudo ufw default deny incoming
sudo ufw allow from 100.64.0.0/10 to any port 22 proto tcp
sudo ufw enable
```

Apply to **ALL servers** — one missed server is one entry point.

### ACL Policies

Use NetBird Dashboard → **Access Control** to restrict which peers can reach which:

- Production servers: only admin peers can SSH
- Development services: accessible to all team peers
- Monitoring: accessible to monitoring peers only

### Peer Approval

Enable peer approval in Dashboard → **Settings** to require manual approval for new device registration.

### Network Segmentation

Use NetBird routes to limit which peers can access which subnets. Not all VPN peers need to reach all services.

### Auto-start on Boot

```bash
sudo systemctl enable netbird
```

## no_proxy Configuration (Critical)

If the machine has `http_proxy` / `https_proxy` set, NetBird internal traffic will be routed through the proxy and fail (502 Bad Gateway).

Add to `~/.bashrc` or `/etc/environment`:

```bash
export no_proxy=127.0.0.1,localhost,100.64.0.0/10,.nb.example.com
```

Key details:
- `100.64.0.0/10` — covers all NetBird peer IPs (100.64.x.x - 100.127.x.x)
- `.nb.example.com` — covers all NetBird FQDNs (use dot prefix, NOT `*` glob)
- `no_proxy` does NOT support glob patterns — `.domain.com` means "all subdomains of domain.com"

## Design Decisions

### NAS / Storage Devices: Do NOT Connect to NetBird

- **Security isolation**: NAS stores bulk data, keeping it off WireGuard reduces attack surface
- **No need for direct access**: NAS and the local server are on the same LAN; the local server accesses NAS over LAN, then serves data to NetBird peers
- **Architecture**: NAS → LAN → local server → NetBird → external peers

### Relay Server Placement

Place relay servers geographically between peers that cannot establish direct P2P connections (e.g., peers behind symmetric NAT or ISPs that block direct overseas TCP).

### Internal Access vs Reverse Proxy

| Access Pattern | Method | Auth |
|---------------|--------|------|
| Browser (public) | Reverse proxy (`*.proxy.example.com`) | SSO/Password/Public |
| SDK/CLI/API (programmatic) | Direct NetBird IP (`100.x.x.x`) | None (WireGuard encrypted) |
| Same LAN | LAN IP | None |

## Troubleshooting

### Peer Cannot Connect

```bash
sudo netbird status --detail    # Check connection state
ping <PEER_NETBIRD_IP>          # Test basic connectivity
sudo wg show wt0                # Check WireGuard handshake
journalctl -u netbird -f        # Check logs for errors
```

Common causes:
- Setup key expired → generate new one in Dashboard
- Firewall blocking UDP on port 51820 → open it
- Symmetric NAT on both sides → need a relay server

### DNS Resolution Fails Inside Containers/Pods

Check if NetBird overwrote resolv.conf:

```bash
cat /etc/resolv.conf
cat /etc/resolv.conf.original.netbird  # Original backup
```

Fix: Add public DNS forwarding in NetBird Dashboard (see DNS Management above).

### 502 Bad Gateway Through Reverse Proxy

- Check if `no_proxy` is configured correctly
- Check if the target service is running on the target peer
- Remember: cannot proxy services on the proxy server itself

### NetBird Interface Name

The interface name may vary:

```bash
ip link | grep -E "wt0|netbird"
```

Common names: `wt0`, `netbird0`. Verify before using in K3s flags.
