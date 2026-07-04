# API Reference

The GA4GH ServiceInfo Sidecar exposes three HTTP endpoints. All responses use `Content-Type: application/json`.

---

## `GET /service-info`

Returns the GA4GH ServiceInfo metadata as JSON, conforming to the [ServiceInfo v1 specification](https://github.com/ga4gh-discovery/ga4gh-service-info).

### Response

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | Unique identifier for the service |
| `name` | string | ✅ | Human-readable name |
| `type` | object | ✅ | Service type (`group`, `artifact`, `version`) |
| `organization` | object | ✅ | Organization info (`name`, `url`) |
| `version` | string | ✅ | Service version |
| `description` | string | ❌ | Human-readable description |
| `environment` | string | ❌ | Deployment environment (e.g. `production`, `staging`) |
| `contactUrl` | string | ❌ | Contact URL or mailto |
| `documentationUrl` | string | ❌ | Documentation URL |
| `createdAt` | string | ❌ | ISO 8601 creation timestamp |
| `updatedAt` | string | ❌ | ISO 8601 last update timestamp |

### Example Response

```json
{
  "id": "org.ga4gh.myinstitute.drs",
  "name": "My Institute DRS",
  "type": {
    "group": "org.ga4gh",
    "artifact": "drs",
    "version": "1.4.0"
  },
  "organization": {
    "name": "My Research Institute",
    "url": "https://myinstitute.org"
  },
  "version": "1.2.0",
  "description": "DRS service for genomic data access.",
  "environment": "production"
}
```

---

## `GET /healthz`

Kubernetes **liveness probe**. Returns `200 OK` if the process is alive.

### Response

```json
{
  "status": "ok"
}
```

---

## `GET /readyz`

Kubernetes **readiness probe**. Returns `200 OK` only after configuration has been successfully loaded. If the initial config load fails, this endpoint returns `503 Service Unavailable` to prevent Kubernetes from routing traffic to a broken pod.

### Response

```json
{
  "status": "ready"
}
```

---

## Error Responses

| Status Code | Meaning |
|---|---|
| `405 Method Not Allowed` | Non-GET request to any endpoint |
| `500 Internal Server Error` | JSON encoding failure (should not happen in practice) |