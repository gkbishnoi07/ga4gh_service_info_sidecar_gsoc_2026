# GA4GH ServiceInfo service

Welcome to the **ServiceInfo service** documentation! 

A lightweight, standalone Go service that standardizes and dynamically serves GA4GH ServiceInfo metadata across implementations such as DRS, TES, WES, and TRS.

---

## 💡 What is this project?

In production GA4GH deployments (like DRS or TES), instances are required to expose a `/service-info` endpoint. Historically, this metadata has been hardcoded within the application binaries. This makes updating details (like organization URL, contact information, or environment) difficult, requiring a full code review, rebuild, CI run, and pod restart.

The **ServiceInfo service** solves this problem by running as a separate cloud-native microservice. It is deployed as its own Kubernetes Pod alongside your genomics service. Using Kubernetes Ingress rules, `/service-info` requests are redirected to this microservice, while all other paths go directly to the primary genomics service.

```mermaid
graph TD
    Client[External Client] -->|HTTP Request| Ingress[Kubernetes Ingress]
    
    Ingress -->|/service-info| SI["ServiceInfo Service (Go, ~10MB)"]
    Ingress -->|/* (all else)| Backend["GA4GH Genomics Service<br/>(DRS / TES / WES / TRS)"]
    
    SI -->|Hot Reloads| ConfigMap[ConfigMap volume]
```

---

## 🎯 Who is this for?

- **Genomics Platform Administrators:** Deploying and managing GA4GH endpoints in a Kubernetes cluster who want metadata updates without service interruption.
- **Software Engineers / Contributors:** Developing new features or standard compliance improvements for GA4GH specifications.
- **Security & Compliance Officers:** Requiring valid, standard-compliant ServiceInfo formats and active endpoints.

---

## ⚡ Key Features

- **Go-Powered:** Single static binary, scratch base image (<20MB), starts in under 50ms with extremely low memory footprints (~15MB).
- **Zero-Downtime Hot Reloading:** Automatically monitors ConfigMap changes using file watcher routines, revalidating and refreshing metadata dynamically in-memory without server restarts.
- **Standard Compliant:** Automatically validates YAML configuration schemas against the official GA4GH ServiceInfo JSON specification.
- **Kubernetes Native:** Includes `/healthz` and `/readyz` probes, metrics reporting for Prometheus via `/metrics`, and support for native Kubernetes Ingress routing.
- **Helm Support:** Simple deployment via structured templates and standard values.

---

## 🧭 Navigation

- To get started running and testing the service in under 5 minutes, see the [Quick Start Guide](quickstart.md).
- For a complete list of configurable variables, see the [Configuration Reference](configuration.md).
- To inspect available endpoints, see the [API Reference](api.md).
- For detailed setup guidelines on how to build and contribute, see the [Developer Setup Guide](development.md).

---

## 🏛️ Project Governance

<div style="display: flex; align-items: center; justify-content: center; gap: 50px; margin: 30px 0; flex-wrap: wrap;">
  <img src="assets/ga4gh-logo.svg" alt="GA4GH Logo" style="height: 60px; width: auto;" />
  <img src="https://upload.wikimedia.org/wikipedia/commons/0/08/GSoC_logo.svg" alt="Google Summer of Code Logo" style="height: 90px; width: auto;" />
</div>

ServiceInfo service is an open-source project developed under the formal governance of the **Global Alliance for Genomics and Health (GA4GH)** during **Google Summer of Code (GSoC) 2026**.

We welcome contributions from developers of all backgrounds. Please refer to our [Contributing Guidelines](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/blob/main/CODE_OF_CONDUCT.md) to get started.
