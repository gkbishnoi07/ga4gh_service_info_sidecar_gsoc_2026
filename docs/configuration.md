# Configuration Reference

The service is configured using a single YAML configuration file. In production Kubernetes environments, this YAML file is typically mounted into the container filesystem via a `ConfigMap`.

---

## Configuration Schema

All metadata fields conform to the [GA4GH ServiceInfo v1 Specification](https://github.com/ga4gh-discovery/ga4gh-service-info).

### Field Reference Table

| YAML Field | JSON Field | Type | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `id` | String | **Yes** | A unique identifier for the service instance (e.g. `org.ga4gh.example.drs`). |
| `name` | `name` | String | **Yes** | Human-readable name of the service (e.g. `Main Clinical DRS`). |
| `type.group` | `type.group` | String | **Yes** | Namespace representing the organization or standard (typically `org.ga4gh`). |
| `type.artifact` | `type.artifact` | String | **Yes** | The GA4GH service type (e.g., `drs`, `wes`, `tes`, `trs`). |
| `type.version` | `type.version` | String | **Yes** | The version of the service type specification implemented (e.g. `1.2.0`). |
| `organization.name` | `organization.name` | String | **Yes** | Name of the organization responsible for the service. |
| `organization.url` | `organization.url` | String | **Yes** | URL to the organization homepage (must be a valid URL starting with `http://` or `https://`). |
| `version` | `version` | String | **Yes** | Version of the service implementation itself. |
| `description` | `description` | String | No | A short, human-readable description of this service. |
| `environment` | `environment` | String | No | The environment tier in which the service runs (e.g., `production`, `staging`, `dev`). |
| `contactUrl` | `contactUrl` | String | No | A contact link or email URL (e.g., `mailto:support@example.org`). |
| `documentationUrl` | `documentationUrl` | String | No | Link to developer or user documentation for this service instance. |
| `createdAt` | `createdAt` | String | No | ISO 8601 creation timestamp of the service instance (e.g., `2026-08-20T12:00:00Z`). |
| `updatedAt` | `updatedAt` | String | No | ISO 8601 last modification timestamp. |

---

## Example Configurations

### 1. Minimal Configuration
```yaml
id: "org.ga4gh.minimal-drs"
name: "Minimal DRS Service"
version: "1.0.0"
type:
  group: "org.ga4gh"
  artifact: "drs"
  version: "1.2.0"
organization:
  name: "GA4GH"
  url: "https://www.ga4gh.org"
```

### 2. Full Production Configuration
```yaml
id: "org.hospital.genomics-tes"
name: "Hospital Clinical Task Execution Service"
type:
  group: "org.ga4gh"
  artifact: "tes"
  version: "1.0.0"
organization:
  name: "Children's Genomic Hospital"
  url: "https://genomics.hospital.org"
version: "2.3.4"
environment: "production"
description: "High-performance production TES endpoint hosting local tumor analysis pipelines."
contactUrl: "mailto:genomic-support@hospital.org"
documentationUrl: "https://wiki.hospital.org/genomics/tes-user-guide"
createdAt: "2026-01-15T08:30:00Z"
updatedAt: "2026-08-20T17:45:00Z"
```

---

## Environment Variables

The service honors the following environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SERVICE_CONFIG_PATH` | `./configs/dummy_service_info.yaml` | The absolute or relative path to the YAML configuration file. |
| `PORT` | `8080` | Port on which the main HTTP server serves `/service-info`, `/healthz`, and `/readyz`. |

---

## How Hot-Reloading Works

The service automatically detects modifications to the configuration file using the `fsnotify` file system watch engine.

```
DevOps edits ConfigMap in Git
        │
        ▼
Kubernetes updates ConfigMap -> atomic symlink swap
        │
        ▼
fsnotify goroutine detects directory change
        │
        ▼
Validation runs (Required fields check)
 ├── PASS ──▶ RWMutex updates active config pointer (Zero downtime!)
 └── FAIL ──▶ Reject reload, keep existing config, log structured error
```

### Key Technical Aspects:
1. **Directory Watching:** In Kubernetes, ConfigMaps are updated via an atomic symlink swap. This changes the symlink rather than editing the file directly. To handle this properly, the watcher monitors the containing **directory** instead of the file itself.
2. **Atomic Swap:** Config updates are thread-safe and protected by a `sync.RWMutex`. HTTP handlers acquire a read lock (`RLock`), while the reloader thread grabs a write lock (`Lock`) only to swap the pointer, resulting in zero-downtime updates.
3. **Fail-Safe Validation:** If you update the configuration with invalid YAML or miss required fields, the reload is rejected with a structured error log. The service **continues serving the previous valid configuration** and the `/readyz` health probe remains healthy.
