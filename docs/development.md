# Developer Setup Guide

Welcome to the contributor guidelines! This document describes how to set up your local development environment to work on the GA4GH ServiceInfo microservice.

---

## 🛠️ Prerequisites

To build, test, and run the service, ensure you have the following installed:

- **Go:** Version 1.22 or higher. [Install Go](https://go.dev/doc/install).
- **Linter:** `golangci-lint` to run codebase static analysis. [Install golangci-lint](https://golangci-lint.run/usage/install/).
- **Docker:** Optional, but required to build container images locally.
- **Minikube & Helm:** Optional, but required for local E2E Kubernetes testing.

---

## 🚀 Setting Up Locally

### 1. Clone the Repository
```bash
git clone https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026.git
cd ga4gh_service_info_sidecar_gsoc_2026
```

### 2. Run the Server
Use standard Go toolchain commands to run the server locally:
```bash
go run ./cmd/server
```
The server will start on port `8080` (and metrics on `9090`) using the fallback `configs/dummy_service_info.yaml` configuration file.

To run with a custom configuration or custom port, set the corresponding environment variables:
```bash
# On Linux/macOS
PORT=9000 SERVICE_CONFIG_PATH=/path/to/my_config.yaml go run ./cmd/server

# On Windows (PowerShell)
$env:PORT="9000"
$env:SERVICE_CONFIG_PATH="C:\path\to\my_config.yaml"
go run ./cmd/server
```

---

## 🧪 Running Tests

### Running Unit Tests
Our unit test suite runs without external dependencies and executes in milliseconds:
```bash
go test ./... -v -count=1
```

### Running Integration Tests
Integration tests test the real HTTP server, Prometheus metrics, and CORS handling using real HTTP requests on dynamically assigned free loopback ports. They are excluded by default from standard test runs. Run them with the `integration` build tag:
```bash
go test -tags=integration ./... -v -count=1
```

### Checking Coverage
To measure coverage, output a profile report:
```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

---

## 🧹 Code Style & Quality Control

Before committing or opening a pull request, run local quality checks:

### Linting
We enforce formatting and static analysis rules using `golangci-lint`.
```bash
golangci-lint run
```

### Go Vet and Formatting
Format your code automatically using `gofmt`:
```bash
go fmt ./...
go vet ./...
```

---

## 📂 Codebase Layout

```
ga4gh_service_info_sidecar_gsoc_2026/
├── cmd/
│   └── server/
│       └── main.go          # Entrypoint (HTTP routing, server configuration)
├── configs/
│   └── dummy_service_info.yaml # Sample fallback config for local dev
├── deploy/                  # Kubernetes manifests (Raw & Helm charts)
├── docs/                    # MkDocs documentation pages
├── internal/
│   ├── config/              # YAML config parsing & fsnotify hot-reloader
│   ├── handler/             # HTTP endpoint handler logic
│   ├── middleware/          # CORS & metrics middlewares
│   └── model/               # GA4GH ServiceInfo JSON/YAML model structs
├── go.mod                   # Module requirements & dependencies
└── integration_test.go      # E2E integration test suite
```
