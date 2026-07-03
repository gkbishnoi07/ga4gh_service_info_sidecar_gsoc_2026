---
title: Technical Architecture
description: Architecture of the GA4GH ServiceInfo Sidecar — a standalone Go service that serves standardized metadata via Kubernetes Ingress routing.
---

# Architecture

This document describes the technical architecture of the **GA4GH ServiceInfo Sidecar** — a lightweight, standalone Go service that standardizes service metadata across GA4GH genomics services.

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

## 2. What the Sidecar Does

The sidecar is a **standalone Go service** deployed as its own Pod in Kubernetes. It:

1. **Serves** `GET /service-info` with operator-managed metadata from a YAML ConfigMap.
2. **Validates** the metadata against the GA4GH ServiceInfo v1 specification.
3. **Hot-reloads** when the ConfigMap is updated — zero restart, zero downtime.
4. **Exposes** `/healthz` and `/readyz` endpoints for Kubernetes probes.
5. **Never touches** the real GA4GH service — no proxying, no coupling, no blast radius.

The Kubernetes **Ingress controller** (which already exists in every production cluster) routes `/service-info` requests to the sidecar and everything else directly to the real service.

---

## 3. High-Level Architecture

```
                           ┌─────────────────────┐
                           │   Kubernetes Ingress │
                           │                       │
External Traffic           │  /service-info ──────┼──▶ Sidecar Pod (:8080)
─────────────────────────▶ │                       │    (Go binary, ~10MB)
   :443 (HTTPS)            │  /* (everything else)┼──▶ GA4GH Service Pod
                           │                       │    (DRS/TES/WES/TRS)
                           └─────────────────────┘

                           ┌─────────────────────┐
                           │  ConfigMap           │
                           │  (mounted as volume) │
                           │  Watched by fsnotify │
                           └─────────────────────┘
```

### Key Properties

| Property | Value |
|---|---|
| **Language** | Go (single static binary) |
| **Container image** | `scratch` base, <20MB |
| **Memory footprint** | ~15–30MB RSS |
| **Startup time** | <100ms |
| **External dependencies** | None (Go stdlib `net/http`) |
| **Blast radius** | If sidecar crashes, only `/service-info` returns 503. DRS/TES/WES continue working. |

---

## 4. Why Not a Reverse Proxy?

An earlier design routed **100% of all traffic** through the sidecar as a reverse proxy, just to intercept the 1–5% of requests that hit `/service-info`. That approach had fundamental problems:

| Concern | Reverse Proxy | Ingress Routing (current) |
|---|---|---|
| Blast radius | Sidecar crash kills ALL traffic | Only `/service-info` is affected |
| Traffic overhead | Every request proxied through Python | Only metadata requests hit sidecar |
| Footprint | ~100MB (Python + pip + venv) | ~10MB (Go static binary) |
| Integration effort | Restructure entire Pod | Add one Ingress rule |
| Coupling | Sidecar + DRS in same Pod | Completely independent Pods |

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
          # Service-info → Sidecar
          - path: /ga4gh/drs/v1/service-info
            pathType: Exact
            backend:
              service:
                name: serviceinfo-sidecar
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

## 6. Configuration

All metadata lives in a YAML file mounted from a Kubernetes ConfigMap:

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

---

## 7. Hot Reload *(Phase 2)*

When a ConfigMap is updated, Kubernetes performs an **atomic symlink swap** on the mounted directory. The sidecar detects this using `fsnotify` and reloads configuration atomically:

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

---

## 8. Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/service-info` | GET | GA4GH ServiceInfo JSON response |
| `/healthz` | GET | Kubernetes liveness probe |
| `/readyz` | GET | Kubernetes readiness probe |

---

## 9. Project Structure

```
ga4gh_service_info_sidecar_gsoc_2026/
├── cmd/
│   └── sidecar/
│       └── main.go                  ← Entrypoint: HTTP server on :8080
├── internal/
│   ├── config/
│   │   └── config.go               ← Config loading (YAML + env vars)
│   ├── handler/
│   │   ├── service_info.go          ← GET /service-info handler
│   │   ├── health.go                ← GET /healthz, /readyz handlers
│   │   ├── service_info_test.go
│   │   └── health_test.go
│   └── model/
│       └── service_info.go          ← GA4GH ServiceInfo Go structs
├── configs/
│   └── service_info.yaml            ← Example config (metadata only)
├── docs/                            ← MkDocs documentation
├── .github/workflows/               ← CI (Go vet, test, build)
├── go.mod
└── README.md
```

---

## 10. Phase Roadmap

| Phase | Feature | Status |
|---|---|---|
| **Phase 0** | Repo setup — Go module, basic HTTP server, hardcoded JSON | ✅ Done |
| **Phase 1** | YAML config loading, GA4GH schema validation, unit tests | 📋 Planned |
| **Phase 2** | fsnotify hot reload, RWMutex atomic swap, structured logging | 📋 Planned |
| **Phase 3** | Dockerfile, K8s manifests, Ingress rule, Minikube testing | 📋 Planned |
| **Phase 4** | Helm chart, GitHub Actions CI/CD, docs, quickstart guide | 📋 Planned |
