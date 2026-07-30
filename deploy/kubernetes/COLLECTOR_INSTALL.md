# KubeOpt Collector -- Install Guide

## What it does

The KubeOpt collector is a lightweight read-only pod that runs inside your cluster.
It reads the Kubernetes API and metrics-server every 5 minutes and pushes a summary
to your KubeOpt instance. This replaces the Azure Run Command tunnel for hot-path
analysis -- no cloud credentials needed inside the cluster, no mutation permissions.

## Prerequisites

- `kubectl` configured for your target cluster
- KubeOpt instance running and accessible from inside the cluster
- A KubeOpt JWT token (from Settings > API Keys, or your login token)

## Install

```bash
# 1. Create namespace
kubectl create namespace kubeopt

# 2. Create the token secret
kubectl create secret generic kubeopt-collector-token \
  --from-literal=api_url=https://your-kubeopt-instance.com \
  --from-literal=token=<your-kubeopt-jwt> \
  -n kubeopt

# 3. Apply the manifest
kubectl apply -f kubeopt-collector.yaml

# 4. Verify it started
kubectl get pods -n kubeopt
kubectl logs deploy/kubeopt-collector -n kubeopt
```

Expected log output:
```
2026-07-28 10:00:00 INFO KubeOpt collector starting (cluster=node-1, interval=300s)
2026-07-28 10:00:05 INFO collecting cluster inventory...
2026-07-28 10:00:06 INFO report accepted: nodes=3 pods=47 metrics=True
```

## Local validation with Kind

```bash
# Create a local cluster
kind create cluster --name kubeopt-test

# Install metrics-server (optional -- collector works without it, usage fields will be null)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system \
  --type=json -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

# Point collector at local KubeOpt API
kubectl create namespace kubeopt
kubectl create secret generic kubeopt-collector-token \
  --from-literal=api_url=http://host.docker.internal:5010 \
  --from-literal=token=<your-local-token> \
  -n kubeopt

kubectl apply -f kubeopt-collector.yaml
kubectl logs deploy/kubeopt-collector -n kubeopt -f
```

## Local validation with Minikube

```bash
minikube start
minikube addons enable metrics-server

kubectl create namespace kubeopt
kubectl create secret generic kubeopt-collector-token \
  --from-literal=api_url=http://$(minikube ssh "ip route | grep default | awk '{print \$3}'"):5010 \
  --from-literal=token=<your-local-token> \
  -n kubeopt

kubectl apply -f kubeopt-collector.yaml
kubectl logs deploy/kubeopt-collector -n kubeopt -f
```

## Configuration

| Env var | Default | Description |
|---|---|---|
| `KUBEOPT_API_URL` | required | KubeOpt instance base URL |
| `KUBEOPT_TOKEN` | required | Bearer token for auth |
| `COLLECTOR_INTERVAL_SECONDS` | `300` | Seconds between collections |
| `METRICS_SERVER_URL` | auto | Override metrics-server endpoint |
| `CLUSTER_ID` | node hostname | Override cluster identifier |

## Uninstall

```bash
kubectl delete -f kubeopt-collector.yaml
kubectl delete secret kubeopt-collector-token -n kubeopt
kubectl delete namespace kubeopt
```

## Permissions granted (read-only)

- `nodes`, `pods`, `persistentvolumeclaims`, `services`, `namespaces` -- get, list
- `deployments`, `replicasets`, `statefulsets`, `daemonsets` -- get, list
- `horizontalpodautoscalers` -- get, list
- `metrics.k8s.io/nodes`, `metrics.k8s.io/pods` -- get, list

No write permissions. No exec. No secrets access.
