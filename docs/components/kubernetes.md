# Kubernetes-SOTA Practices

**Production-grade Kubernetes deployment patterns for the OpenSIN stack.** Repo: [OpenSIN-Code/kubernetes-sota-practices](https://github.com/OpenSIN-Code/kubernetes-sota-practices). Latest release: [`v0.1.0-alpha`](https://github.com/OpenSIN-Code/kubernetes-sota-practices/releases/tag/v0.1.0-alpha).

## What it does

Helm charts, Istio service mesh, k3s bootstrap, and Prometheus + Grafana monitoring for deploying Code-Swarm and Simone-MCP at scale — including on free Oracle Cloud A1.Flex tier.

## Contents

```
helm/
  code-swarm/     # production-ready chart for the agent fleet
  simone-mcp/     # AST tool layer chart with TLS + autoscale
istio/
  mtls.yaml       # mesh-wide mTLS
  gateway.yaml    # ingress gateway + virtual services
k3s/
  bootstrap.sh    # single-node bootstrap on OCI A1.Flex (24 GB)
  ha.sh           # 3-node HA configuration
monitoring/
  prometheus.yml  # scrape configs for the fleet
  grafana/        # pre-built dashboards
  alerts.yaml     # production alert rules
```

## Quick deploy

```bash
git clone https://github.com/OpenSIN-Code/kubernetes-sota-practices
cd kubernetes-sota-practices

# Bootstrap a free k3s cluster on OCI
bash k3s/bootstrap.sh

# Install Code-Swarm
helm install code-swarm ./helm/code-swarm \
  --namespace opensin --create-namespace \
  --set secretKey=$(openssl rand -base64 64)

# Install Simone-MCP
helm install simone-mcp ./helm/simone-mcp \
  --namespace opensin
```

## Highlights

- **HPA + PDB** for the agent fleet — scales 1 to 50 replicas based on queue depth
- **Istio mTLS** between every component
- **Pre-built Grafana dashboards** for agent latency, queue depth, error rates
- **Free-tier optimized** — fits in 24 GB OCI A1.Flex single-VM

## Status

- Helm charts: **shipped in v0.1.0-alpha**
- Istio + mTLS: **shipped**
- k3s bootstrap: **shipped**
- Prometheus + Grafana: **shipped**

## Known gaps for v0.2.0

- cert-manager + Let's Encrypt automation
- ArgoCD GitOps templates
- Multi-cluster federation patterns
- Backup/restore runbooks
