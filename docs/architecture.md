# Architecture

This document describes the full technical architecture of the **GA4GH ServiceInfo Sidecar** — a cloud-native reverse proxy that standardizes service metadata across GA4GH genomics services.

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

This happens because **updating this data requires a code change, a code review, a CI run, and a full container redeployment** — for a date field. This is the core problem the sidecar solves.

---

## 2. What the Sidecar Does

The sidecar is a **reverse proxy container** that runs alongside any GA4GH service inside the same Kubernetes Pod. It:

1. **Intercepts** `GET /ga4gh/{service}/v1/service-info` requests before they reach the real service.
2. **Fetches** the real service's own service-info response (optional, configurable).
3. **Deep-merges** the upstream response with the operator's YAML-based overrides.
4. **Validates** the merged response against the GA4GH ServiceInfo specification using Pydantic.
5. **Returns** a clean, correct, standards-compliant JSON response to the client.
6. **Forwards** all other requests (DRS objects, TES tasks, etc.) transparently to the real service.

---

## 3. High-Level Architecture

```
                              ┌────────────────────────────────────────────┐
                              │              Kubernetes Pod                │
                              │                                            │
                              │  ┌──────────────────┐  ┌───────────────┐  │
External Traffic              │  │                  │  │               │  │
──────────────────────────────┼─▶│  Sidecar         │  │  GA4GH        │  │
   :443 (via Ingress)         │  │  (FastAPI/Python) │  │  Service      │  │
                              │  │  :8080            │  │  (Java/Go)    │  │
                              │  │                  │  │  :8081        │  │
                              │  └──────┬───────────┘  └──────▲────────┘  │
                              │         │                      │           │
                              │         │ Proxy non-service-   │           │
                              │         │ info requests        │           │
                              │         └──────────────────────┘           │
                              │                                            │
                              │  ┌──────────────────────────────────────┐  │
                              │  │  ConfigMap (mounted as /app/configs) │  │
                              │  │  Watched by watchfiles (hot reload)  │  │
                              │  └──────────────────────────────────────┘  │
                              └────────────────────────────────────────────┘
```

### Port Assignment

| Port | Who uses it | Purpose |
|---|---|---|
| `:443` | Kubernetes Ingress | Public HTTPS facing the internet |
| `:8080` | Sidecar container | The only public-facing port inside the pod |
| `:8081` | GA4GH service container | Internal only — sidecar proxies to this |

---

## 4. Request Routing Logic

When a request arrives at port `8080`, the sidecar applies a simple routing decision:

```
Incoming Request
       │
       ▼
Is path == service_info_path?
  (e.g. /ga4gh/drs/v1/service-info)
       │
   ┌───┴───┐
   │  YES  │──▶ ServiceInfo Pipeline (see §5)
   │       │
   │  NO   │──▶ Transparent Reverse Proxy to :8081
   └───────┘    (passes headers, body, query params, HTTP method unchanged)
```

**Critical implementation detail**: Route registration order in FastAPI matters.

```python
# 1. Specific route registered FIRST
app.include_router(service_info_router)  # GET /service-info + configured path

# 2. Catch-all registered LAST
app.include_router(proxy_router)         # {path:path} — matches everything else
```

FastAPI's built-in routes (`/docs`, `/openapi.json`, `/redoc`) are always matched before any user-defined routes, so they are never proxied to the upstream service.

---

## 5. ServiceInfo Pipeline

When a request matches the configured service-info path, the full metadata assembly pipeline runs:

```
YAML Config + Env Vars
        │
        ▼
  load_config()              ← SidecarSettings (operational) + overrides (metadata)
        │
        ├── upstream_merge == True?
        │         │
        │         ▼
        │   fetch_upstream_service_info()    ← async HTTP GET to real service
        │         │
        │    Success? ──────────────────────────────────────────────┐
        │    Failure (timeout/refused/5xx)?                         │
        │         │                                                  │
        │         ▼                                                  ▼
        │   Fallback: use                               deep_merge(upstream, overrides)
        │   config-only                                 (operator YAML always wins)
        │
        ▼
  model_class.model_validate(merged)    ← Pydantic strict validation
        │
        ▼
  .model_dump(by_alias=True, exclude_none=True)   ← GA4GH-compliant camelCase JSON
        │
        ▼
   HTTP 200 Response
```

### Merge Precedence (Highest to Lowest)

| Priority | Source | Example |
|---|---|---|
| **1 (wins)** | Operator YAML / ConfigMap | `environment: "production"` |
| **2** | Upstream service response | `environment: "test"` |
| **3 (fallback)** | Sidecar defaults | hardcoded values in `SidecarSettings` |

### Deep Merge vs. Shallow Replace

The merge algorithm performs a **recursive deep merge**, not a shallow dict replace:

```python
# Upstream DRS response:
upstream = {
    "organization": {"name": "Old Name", "url": "https://old.org"},
    "version": "0.3.2"
}

# Operator YAML:
override = {
    "organization": {"name": "My Institute"},  # Only overrides name, not url
    "version": "0.1.0"
}

# Result:
result = {
    "organization": {"name": "My Institute", "url": "https://old.org"},  # Merged!
    "version": "0.1.0"   # Override wins
}
```

Key rules:
- Dict keys are merged recursively.
- Scalar values in the override always win.
- Arrays are **replaced entirely** (not appended).
- `None` values in the override do **not** delete existing upstream keys.

---

## 6. Configuration Architecture

All configuration lives in a single YAML file (`configs/service_info.yaml`) that serves dual purpose:

```yaml
# ── Part 1: Operational Settings ────────────────────────────────────────────
# Controls sidecar behaviour — not returned to the client

upstream_url: "http://localhost:8081"        # Where to find the real service
service_type: "drs"                          # Which GA4GH service type
service_info_path: "/ga4gh/drs/v1/service-info"  # Path to intercept
upstream_merge: true                          # Enable merge mode

# ── Part 2: Operator Metadata Overrides ─────────────────────────────────────
# These are merged on top of the upstream response (and serve as fallback)

id: "org.ga4gh.myinstitute.drs"
name: "My Institute DRS"
version: "1.2.0"
organization:
  name: "My Research Institute"
  url: "https://myinstitute.org"
environment: "production"
```

### Environment Variable Overrides

Every operational setting can be overridden at runtime using `SIDECAR_*` environment variables — without touching the YAML file:

| Environment Variable | Config Key | Example |
|---|---|---|
| `SIDECAR_CONFIG_FILE` | — | `/etc/config/service_info.yaml` |
| `SIDECAR_UPSTREAM_URL` | `upstream_url` | `http://localhost:8081` |
| `SIDECAR_SERVICE_TYPE` | `service_type` | `drs` |
| `SIDECAR_SERVICE_INFO_PATH` | `service_info_path` | `/ga4gh/drs/v1/service-info` |
| `SIDECAR_UPSTREAM_MERGE` | `upstream_merge` | `true` |

This is the standard [12-Factor App](https://12factor.net/config) configuration pattern, essential for Kubernetes deployments where values are injected via Pod spec environment variables.

---

## 7. Hot Reload Architecture *(Phase 2 — Coming Soon)*

In Kubernetes, configuration is stored in a **ConfigMap** mounted as a directory volume. When the ConfigMap is updated (via GitOps or `kubectl`), Kubernetes performs an **atomic symlink swap** on the mounted directory.

The sidecar detects this swap using the `watchfiles` Python library and reloads configuration in memory without restarting the container.

```
DevOps Engineer edits ConfigMap in Git
          │
          ▼
ArgoCD / Flux syncs to Kubernetes
          │
          ▼
Kubernetes updates ConfigMap → atomic symlink swap on /app/configs/
          │
          ▼
watchfiles detects filesystem change
          │
          ▼
Thread-safe in-memory state swapped via RLock
          │
          ▼
Next request sees updated configuration — zero downtime, zero restart
```

!!! warning "Critical Kubernetes Mount Rule"
    The ConfigMap **must** be mounted as a **directory**, not with `subPath`.
    Using `subPath` prevents Kubernetes from performing the symlink swap,
    which means `watchfiles` will never detect the change.

    ```yaml
    # ✅ Correct
    volumeMounts:
      - name: config
        mountPath: /app/configs

    # ❌ Wrong — breaks hot reload
    volumeMounts:
      - name: config
        mountPath: /app/configs/service_info.yaml
        subPath: service_info.yaml
    ```

---

## 8. Operating Modes

The sidecar supports two operating modes, configurable via `upstream_merge`:

### Mode A — Enrichment Mode (`upstream_merge: true`)

```
Client ──▶ Sidecar ──▶ Upstream (fetch service-info)
                  │
                  ▼
         Merge: upstream + YAML overrides
                  │
                  ▼
         Return merged response
```

**Best for**: Production deployments where the real service is running and the operator wants to correct or enrich its metadata.

### Mode B — Standalone Mode (`upstream_merge: false`)

```
Client ──▶ Sidecar
                  │
                  ▼
         Serve YAML directly (no upstream call)
```

**Best for**: CI/CD pipelines, integration tests, or deployments where the upstream service does not expose a `/service-info` endpoint.

---

## 9. Codebase Structure

```
ga4gh-service-info-sidecar/
│
├── sidecar/                        ← Application package
│   ├── main.py                     ← FastAPI app factory, route registration order
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── service_info.py     ← GET /service-info (MVP fallback route)
│   │       └── proxy.py            ← Intercepts configured path + catch-all proxy
│   │
│   ├── config/
│   │   ├── settings.py             ← YAML loader, env var overrides, SidecarSettings
│   │   ├── merge.py                ← Pure deep_merge() function
│   │   └── watcher.py              ← [Phase 2] watchfiles hot-reload daemon
│   │
│   ├── core/
│   │   ├── provider.py             ← Orchestrates the full metadata pipeline
│   │   └── upstream.py             ← Async HTTP fetch from upstream service
│   │
│   └── models/
│       ├── service_info.py         ← Pydantic models: Service, Organization, ServiceType
│       └── registry.py             ← SERVICE_REGISTRY: maps service_type → Pydantic model
│
├── configs/
│   └── service_info.yaml           ← Local dev config (becomes a Kubernetes ConfigMap)
│
├── tests/
│   ├── test_merge.py               ← 16 unit tests for deep_merge()
│   ├── test_service_info.py        ← 58 unit and integration tests for models + API
│   ├── test_upstream.py            ← 6 async tests for upstream fetching
│   ├── test_proxy.py               ← 9 tests for proxy routing logic
│   └── test_integration.py         ← 6 full-stack tests: config → upstream → response
│
├── Dockerfile                      ← Container image for the sidecar
├── docker-compose.yml              ← Local dev: sidecar + DRS Starter Kit
└── mkdocs.yml                      ← MkDocs config for this documentation
```

---

## 10. Kubernetes Deployment Architecture

In production, the sidecar runs as a **sidecar container** inside the same Kubernetes Pod as the GA4GH service it wraps.

```yaml
# pod.yaml (simplified)
spec:
  containers:
    # ── The real DRS service (internal only) ──
    - name: drs
      image: ga4gh/ga4gh-starter-kit-drs:0.3.2
      ports:
        - containerPort: 4500    # Only reachable inside the pod

    # ── The sidecar (public-facing) ──
    - name: sidecar
      image: ghcr.io/ga4gh/ga4gh-serviceinfo-sidecar:latest
      ports:
        - containerPort: 8080    # This is the only port exposed via Kubernetes Service
      env:
        - name: SIDECAR_UPSTREAM_URL
          value: "http://localhost:4500"  # Containers in same Pod share localhost
        - name: SIDECAR_SERVICE_TYPE
          value: "drs"
      volumeMounts:
        - name: sidecar-config
          mountPath: /app/configs   # Directory mount (not subPath) for hot-reload

  volumes:
    - name: sidecar-config
      configMap:
        name: drs-sidecar-config    # This ConfigMap is the operator's control knob
```

### Key Kubernetes Properties

- **Shared network namespace**: All containers in a Pod share `localhost`. The sidecar reaches DRS at `http://localhost:4500` without any service discovery overhead.
- **No direct access to DRS**: The Kubernetes Service only exposes port `8080` (the sidecar). Nobody can bypass the sidecar and hit DRS directly.
- **GitOps workflow**: The ConfigMap is stored in Git. When an operator updates it, ArgoCD/Flux syncs it to the cluster, triggering the hot-reload cycle automatically.

---

## 11. Data Flow: End-to-End Example

Below is a complete walkthrough of a request for `/ga4gh/drs/v1/service-info` in production:

```
1. Researcher queries:
   GET https://drs.myinstitute.org/ga4gh/drs/v1/service-info

2. Kubernetes Ingress routes to Sidecar Pod on :8080

3. Sidecar FastAPI receives request:
   → Path matches configured service_info_path
   → ServiceInfo Pipeline triggered

4. load_config() reads /app/configs/service_info.yaml
   → Extracts operational settings (upstream_url, upstream_merge=True)
   → Extracts operator overrides (id, name, version, organization, environment)

5. fetch_upstream_service_info() calls:
   GET http://localhost:4500/ga4gh/drs/v1/service-info
   → Returns DRS's own metadata (version="0.1.0", environment="test", ...)

6. deep_merge(upstream_data, operator_overrides):
   → Operator's id, name, version, environment win
   → Upstream's contactUrl, documentationUrl, createdAt are preserved

7. Service.model_validate(merged):
   → Pydantic validates all required fields are present and correctly typed
   → Strips any unrecognised fields

8. .model_dump(by_alias=True, exclude_none=True):
   → Produces camelCase keys (contactUrl not contact_url)
   → Omits None optional fields

9. HTTP 200 JSON response returned to researcher
```

---

## 12. Future Phases

| Phase | Feature | Status |
|---|---|---|
| **Phase 0** | MVP — static YAML → service-info endpoint | ✅ Done |
| **Phase 1** | Reverse proxy + upstream merge + DRS integration | ✅ Done |
| **Phase 2** | Hot reload via `watchfiles` + thread-safe state | 🔄 In Progress |
| **Phase 3** | Kubernetes ConfigMap + Pod spec + minikube testing | 📋 Planned |
| **Phase 4** | Helm chart + GitHub Actions CI + README | 📋 Planned |
| **Future** | Attestation (aTLS, Intel SGX / AWS Nitro Enclaves) | 🔭 Research |
