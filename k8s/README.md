# VeloBid K8s Migration Guide

This directory contains Kubernetes manifests to run the VeloBid + Hermes stack on k3s with Longhorn storage.

## Prerequisites

- k3s installed: `curl -sfL https://get.k3s.io | sh -`
- Longhorn installed:
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.7.0/deploy/longhorn.yaml
  ```
- Both container images built and pushed to a registry (or loaded into k3s):
  ```bash
  # Option A: Load images directly into k3s
  docker save velobid:latest -o /tmp/velobid.tar
  docker save velobid-hermes:latest -o /tmp/hermes.tar
  sudo k3s ctr images import /tmp/velobid.tar
  sudo k3s ctr images import /tmp/hermes.tar

  # Option B: Push to registry and reference in deployment
  docker tag velobid:latest registry.example.com/velobid:latest
  docker push registry.example.com/velobid:latest
  ```

- `kubectl` configured (k3s sets this up automatically)

## Deploy

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets (REQUIRED: edit secrets.yaml with your credentials first)
#    Generate credential pool JSON from ~/.hermes/auth.json:
#      python3 -c "import json; print(json.dumps({'version':1,'credential_pool':{'opencode-go':[...]}}))" | base64 -w0
#    Then update the HERMES_CREDENTIALS_JSON value in secrets.yaml
kubectl apply -f k8s/secrets.yaml

# 3. Create config
kubectl apply -f k8s/config.yaml

# 4. Create storage
kubectl apply -f k8s/storage.yaml

# 5. Deploy VeloBid
kubectl apply -f k8s/velobid.yaml

# 6. Deploy Hermes
kubectl apply -f k8s/hermes.yaml

# 7. (Optional) Ingress
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n velobid -w
```

## Data Migration from Docker

### 1. Migrate Hermes profiles

```bash
# Backup profiles from Docker volume
docker run --rm -v hermes_data:/source -v $(pwd)/backup:/backup alpine \
  cp -a /source/profiles /backup/

# Copy into Longhorn PVC (once velobid namespace exists)
kubectl create deployment temp --image=alpine -n velobid -- sleep 3600
kubectl cp backup/profiles temp:/mnt/profiles -n velobid
kubectl delete deployment temp -n velobid
```

### 2. Migrate shared data (blueprints, bids, configs)

```bash
# Backup shared data
docker run --rm -v shared_data:/source -v $(pwd)/backup:/backup alpine \
  cp -a /source /backup/shared

# Copy to PVC (similar profile migration approach)
```

### 3. Switch DNS

Update Tailscale funnel or DNS to point to the new K8s ingress IP:
```bash
kubectl get ingress -n velobid
# Use the assigned IP as the Tailscale node
```

## Comparison: Docker Compose → K8s

| Aspect | Docker Compose | K8s |
|--------|---------------|-----|
| **VeloBid** | Single container | Deployment (replicas: 1, HPA ready) |
| **Hermes** | Single container | StatefulSet (needs stable identity) |
| **Storage** | Docker volumes | Longhorn PVCs |
| **Config** | Env file + file mounts | ConfigMap + Secrets |
| **Health** | Docker healthcheck | liveness + readiness probes |
| **Network** | docker-compose DNS | ClusterIP services |
| **Ingress** | Tailscale funnel | Tailscale operator / nginx |
| **Secrets** | .env file | SealedSecrets / External Secrets |
| **Resource mgmt** | deploy.resources | requests + limits |

## Scaling

Once on K8s:

```bash
# Scale VeloBid horizontally (stateless)
kubectl scale deployment velobid -n velobid --replicas=3

# Set up HPA
kubectl autoscale deployment velobid -n velobid --cpu-percent=70 --min=1 --max=5

# For Hermes: add per-bidder replicas if needed
# Hermes is stateful (profiles on PVC) — use StatefulSet with per-pod PVC
```

## Notes

- **Hermes is stateful** — profiles, sessions, memory live on PVC. Scale carefully.
- **Shared-data PVC** must be ReadWriteMany (Longhorn supports this).
- **Docker socket** is NOT mounted in K8s. The profile manager instead uses a direct API endpoint inside the Hermes container (not yet built).
