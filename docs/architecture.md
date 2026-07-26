---
title: Technical Architecture
description: Architecture of the GA4GH ServiceInfo service — a standalone Go service that serves standardized metadata via Kubernetes Ingress routing.
---

# Architecture

This document describes the technical architecture of the **GA4GH ServiceInfo service** — a lightweight, standalone Go service that standardizes service metadata across GA4GH genomics services.

---

## 1. The Problem

Every GA4GH service (DRS, TES, WES, TRS) is required to expose a `/service-info` endpoint. In practice, this metadata is **hardcoded inside application code** and almost never updated after deployment.

A real example from the GA4GH DRS Starter Kit (version `0.3.2`):

```json
{
  "version": "0.1.0",
  "createdAt": "2020-01-15T12:00:00",
  "updatedAt": "2020-01-15T12:00:00",
  "environment": "test"
}
```

The binary version is `0.3.2`, but the metadata says `0.1.0`. The timestamps are from 2020. The environment says `test` in a production cluster.

This happens because **updating this data requires a code change, a code review, a CI run, and a full container redeployment** — for a date field.

---

## 2. What the service Does

The service is a **standalone Go service** deployed as its own Pod in Kubernetes. It:

1. **Serves** `GET /service-info` with operator-managed metadata from a YAML ConfigMap.
2. **Validates** the metadata against the GA4GH ServiceInfo v1 specification on every load.
3. **Hot-reloads** when the ConfigMap is updated — zero restart, zero downtime.
4. **Exposes** `/healthz` and `/readyz` endpoints for Kubernetes probes.
5. **Never touches** the real GA4GH service — no proxying, no coupling, no blast radius.

The Kubernetes **Ingress controller** (which already exists in every production cluster) routes `/service-info` requests to the service and everything else directly to the real service.

---

## 3. High-Level Architecture

```
                           ┌────────────────────────────────┐
                           │       Kubernetes Ingress       │
                           │                                │
External Traffic           │  /service-info ────────────────┼──▶ service Pod (:8080)
─────────────────────────▶ │                                  │      Go binary, ~10MB
   :443 (HTTPS)            │  /* (everything else) ─────────┼──▶ GA4GH Service Pod
                           │                                  │      (DRS/TES/WES/TRS)
                           └────────────────────────────────┘

                           ┌────────────────────────────────┐
                           │  ConfigMap                     │
                           │  (mounted as volume)           │
                           │  Watched by fsnotify           │
                           └────────────────────────────────┘
```

### Key Properties

| Property | Value |
|---|---|
| **Language** | Go (single static binary) |
| **Container image** | `scratch` base, <20MB |
| **Memory footprint** | ~15–30MB RSS |
| **Startup time** | <100ms |
| **External dependencies** | None (Go stdlib `net/http`) |
| **Blast radius** | If service crashes, only `/service-info` returns 503. DRS/TES/WES continue working. |

---

## 4. Why Ingress Routing?

An earlier design routed **100% of all traffic** through the service as a reverse proxy, just to intercept the 1–5% of requests that hit `/service-info`. That approach had fundamental problems:

| Concern | Reverse Proxy | Ingress Routing (current) |
|---|---|---|
| Blast radius | service crash kills ALL traffic | Only `/service-info` is affected |
| Traffic overhead | Every request proxied through service | Only metadata requests hit service |
| Footprint | Heavy runtime + dependencies | ~10MB (Go static binary) |
| Integration effort | Restructure entire Pod | Add one Ingress rule |
| Coupling | service + service in same Pod | Completely independent Pods |

The Ingress routing pattern solves a small problem with a small solution.

---

## 5. Request Routing (Ingress)

The Kubernetes Ingress configuration routes requests based on path:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ga4gh-drs
spec:
  rules:
    - host: drs.myinstitute.org
      http:
        paths:
          # Service-info → service
          - path: /ga4gh/drs/v1/service-info
            pathType: Exact
            backend:
              service:
                name: serviceinfo-service
                port:
                  number: 8080

          # Everything else → DRS
          - path: /
            pathType: Prefix
            backend:
              service:
                name: drs
                port:
                  number: 8080
```

Users add **one Ingress rule**. That's the entire integration change.

---

## 6. Configuration Architecture

All metadata lives in a YAML file. In production, this file is mounted from a Kubernetes ConfigMap. For local development, a dummy config file is included in the repository.

The config file path is controlled by the `SERVICE_CONFIG_PATH` environment variable. If unset, it falls back to `./configs/dummy_service_info.yaml`.

### Example Configuration

```yaml
id: "org.ga4gh.myinstitute.drs"
name: "My Institute DRS"
type:
  group: "org.ga4gh"
  artifact: "drs"
  version: "1.4.0"
organization:
  name: "My Research Institute"
  url: "https://myinstitute.org"
version: "1.2.0"
environment: "production"
description: "DRS service for genomic data access."
```

No operational settings mixed in — the YAML is **pure metadata**. Deployment topology is handled by Kubernetes manifests.

### GA4GH Schema Validation

On every load (initial startup and hot-reload), the service validates that the following required fields are present and non-empty:

- `id`, `name`, `version`
- `type.group`, `type.artifact`, `type.version`
- `organization.name`, `organization.url`

If any required field is missing, the service **rejects the configuration** and retains the previously loaded valid config. It never crashes or serves invalid metadata.

---

## 7. Hot Reload Architecture

When a ConfigMap is updated, Kubernetes performs an **atomic symlink swap** on the mounted directory. The service detects this using `fsnotify` and reloads configuration atomically:

```
DevOps edits ConfigMap in Git
        │
        ▼
ArgoCD / Flux syncs to Kubernetes
        │
        ▼
Kubernetes updates ConfigMap → atomic symlink swap
        │
        ▼
fsnotify goroutine detects change
        │
        ▼
sync.RWMutex atomic config swap (old config kept on bad YAML)
        │
        ▼
Next request sees updated values — zero downtime
```

### Implementation Details

- **Directory watching**: `fsnotify` watches the *directory* containing the config file, not the file itself. This is required because Kubernetes ConfigMap updates work via symlink swaps — the file inode changes, so watching the file directly would miss the update.
- **Thread safety**: A `sync.RWMutex` protects the config pointer. HTTP handlers acquire a read lock (`RLock`), while the reload goroutine acquires a write lock (`Lock`) only during the brief pointer swap.
- **Failure safety**: If the new YAML is invalid (missing fields, bad syntax), the reload is rejected with a structured log error. The service continues serving the previous valid configuration.
- **Structured logging**: All reload events are logged via Go's `log/slog` package with JSON output, making them compatible with cloud-native observability stacks.

---

## 8. Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/service-info` | GET | GA4GH ServiceInfo JSON response |
| `/healthz` | GET | Kubernetes liveness probe — always returns `200 OK` |
| `/readyz` | GET | Kubernetes readiness probe — returns `200 OK` only after config is loaded |

---

## 9. Project Structure

```
ga4gh_service_info_sidecar_gsoc_2026/
├── cmd/
│   └── service/
│       └── main.go                  ← Entrypoint: HTTP server, slog, fsnotify
├── internal/
│   ├── config/
│   │   ├── config.go               ← ConfigWatcher, fsnotify, RWMutex, validation
│   │   └── config_test.go          ← Config loading and validation tests
│   ├── handler/
│   │   ├── service_info.go          ← GET /service-info handler
│   │   ├── health.go                ← GET /healthz, /readyz handlers
│   │   ├── service_info_test.go
│   │   └── health_test.go
│   └── model/
│       └── service_info.go          ← GA4GH ServiceInfo Go structs
├── configs/
│   └── dummy_service_info.yaml      ← Dummy config for local development
├── docs/                            ← MkDocs documentation
├── .github/workflows/               ← CI (Go vet, test, build)
├── go.mod
└── README.md
```

---

## 10. Phase Roadmap

| Phase | Feature | Status |
|---|---|---|
| **Phase 0** | Go module, HTTP server, GA4GH JSON response, unit tests | ✅ Done |
| **Phase 1** | YAML config loading, GA4GH schema validation, fsnotify hot reload, structured logging (`slog`) | ✅ Done |
| **Phase 2** | Dockerfile, K8s manifests, Ingress rule, Minikube testing | 📋 Planned |
| **Phase 3** | Helm chart, GitHub Actions CI/CD, quickstart guide | 📋 Planned |
