# GA4GH ServiceInfo Sidecar

A lightweight, standalone Go service for standardizing and extending GA4GH ServiceInfo metadata across implementations such as DRS, TES, WES, and TRS.

Built as part of **Google Summer of Code 2026** under [GA4GH](https://www.ga4gh.org/).

---

## How It Works

The sidecar runs as its own Kubernetes Pod. The cluster's Ingress controller routes `/service-info` requests to the sidecar, while all other traffic (DRS objects, TES tasks, etc.) goes directly to the real service — untouched.

Metadata is managed via a YAML ConfigMap with hot-reload support. Update a field in Git, ArgoCD syncs it, and the sidecar picks it up in seconds — no restart, no redeployment.

---

## Prerequisites

- [Go 1.22+](https://go.dev/dl/)
- Git

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026.git
cd ga4gh_service_info_sidecar_gsoc_2026
```

### Build & Run

```bash
go run ./cmd/sidecar
```

The server starts on `:8080`. Test it with:

```bash
# ServiceInfo metadata
curl http://localhost:8080/service-info

# Kubernetes probes
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz
```

### Run Tests

```bash
go test ./... -v -race
```

---

## Project Roadmap

| Phase | Feature | Status |
|---|---|---|
| **Phase 0** | Go module, basic HTTP server, hardcoded JSON | ✅ Done |
| **Phase 1** | YAML config loading, GA4GH schema validation | 📋 Planned |
| **Phase 2** | fsnotify hot reload, structured logging | 📋 Planned |
| **Phase 3** | Dockerfile, K8s manifests, Ingress, Minikube | 📋 Planned |
| **Phase 4** | Helm chart, CI/CD, docs, quickstart | 📋 Planned |

---

## Related Specifications

- [GA4GH ServiceInfo v1](https://github.com/ga4gh-discovery/ga4gh-service-info)
- [GA4GH Starter Kit DRS](https://github.com/ga4gh/ga4gh-starter-kit-drs)
- [GA4GH TES](https://github.com/ga4gh/task-execution-schemas)

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).