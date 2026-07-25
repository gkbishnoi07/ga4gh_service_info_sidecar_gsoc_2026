# GA4GH ServiceInfo SERVICE

A lightweight, cloud-native standalone Go microservice for standardizing and serving GA4GH `/service-info` metadata across implementations such as DRS, TES, WES, and TRS.

A standalone microservice maintained under the [Global Alliance for Genomics and Health (GA4GH)](https://www.ga4gh.org/).

---

## How It Works

The SERVICE runs as a **standalone Pod** alongside your genomics API (e.g. DRS/TES) in the same Kubernetes cluster. Your Ingress controller routes `/service-info` requests directly to the SERVICE, while routing all other API traffic to your main service. 

Metadata is managed via a Kubernetes `ConfigMap` mounted as a file. The SERVICE uses Go's `fsnotify` library to listen for changes to the ConfigMap directory and **hot-reloads** the configuration dynamically in memory without restarting the container.

---

## Features

- **Standard Compliance:** Validates the configuration against the official GA4GH ServiceInfo JSON schema.
- **Dynamic Hot-Reloading:** Refreshes metadata in real time when the mounted ConfigMap is updated (uses thread-safe `sync.RWMutex`).
- **Kubernetes Health Probes:** Exposes `/healthz` (liveness) and `/readyz` (readiness). The `/readyz` probe fails with `503 Service Unavailable` if the file watcher experiences a fatal system error (e.g., inotify descriptor exhaustion).
- **Graceful Shutdown:** Implements `context.Context` signals to intercept `SIGTERM` and shutdown the HTTP listener and background file watcher cleanly without dropping active requests.
- **CORS Support:** Exposes full Cross-Origin Resource Sharing (CORS) headers and handles preflight `OPTIONS` requests automatically, allowing web applications to easily query metadata.
- **Observability:** Exposes Prometheus metrics via `/metrics` (instruments request counts and latency histograms).

---

## Getting Started

### Local Development

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026.git
   cd ga4gh_service_info_sidecar_gsoc_2026
   ```

2. **Run Local Server:**
   ```bash
   go run ./cmd/server
   ```
   *The server will start on port `8080` using a local dummy config path fallback.*

3. **Query Endpoints:**
   ```bash
   # ServiceInfo metadata
   curl -i http://localhost:8080/service-info

   # Prometheus Metrics
   curl -i http://localhost:8080/metrics

   # Kubernetes health probes
   curl -i http://localhost:8080/healthz
   curl -i http://localhost:8080/readyz
   ```

4. **Run Unit Tests:**
   ```bash
   go test ./... -v
   ```

---

## Observability & Metrics

The `/metrics` endpoint exposes standard Go/Process metrics along with custom SERVICE HTTP metrics:

- `ga4gh_SERVICE_http_requests_total{path, method, status}`: Total number of requests processed.
- `ga4gh_SERVICE_http_request_duration_seconds{path, method}`: Histogram of request latencies.

Example Prometheus config scrape job snippet:
```yaml
scrape_configs:
  - job_name: 'ga4gh-service-info-SERVICE'
    static_configs:
      - targets: ['ga4gh-SERVICE.default.svc.cluster.local:8080']
```

---

## Kubernetes Deployment (Minikube E2E Testing)

We provide Kubernetes manifests under `deploy/` to easily deploy the SERVICE.

### 1. Point local terminal to Minikube Docker registry
If testing in Minikube, configure your shell to build inside the Minikube virtual environment:
```bash
# PowerShell
minikube docker-env | Invoke-Expression

# Bash/Zsh
eval $(minikube docker-env)
```

### 2. Build the Docker Image
Build the scratch-based image inside Minikube's Docker daemon:
```bash
docker build -t ga4gh-service-info-SERVICE:latest .
```

### 3. Apply the Manifests
```bash
kubectl apply -f deploy/
```

### 4. Verify deployment state
```bash
# Check pod is running and healthy
kubectl get pods -l app=ga4gh-SERVICE

# Expose port locally to verify endpoints
kubectl port-forward svc/ga4gh-SERVICE 8080:8080
```
Query `http://localhost:8080/service-info` or `http://localhost:8080/metrics` to verify.

### 5. Verify Hot-Reloading in-cluster
1. Edit the running configmap:
   ```bash
   kubectl edit configmap service-info-config
   ```
2. Change the `name` field value (e.g. from `"GA4GH Service Info SERVICE"` to `"My Local Genomics Service"`).
3. Request `/service-info` again. Inside a few seconds, the SERVICE picks up the symlink swap and serves the updated field without any container restarts or restarts:
   ```bash
   curl http://localhost:8080/service-info
   ```

### Ingress Integration
Review `deploy/ingress.yaml` for instructions on how to integrate the SERVICE path rule into your existing genomics service's Ingress.



---

## Related Specifications

- [GA4GH ServiceInfo Specification](https://github.com/ga4gh-discovery/ga4gh-service-info)
- [GA4GH DRS Specification](https://github.com/ga4gh/data-repository-service-schemas)
- [GA4GH TES Specification](https://github.com/ga4gh/task-execution-schemas)

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).