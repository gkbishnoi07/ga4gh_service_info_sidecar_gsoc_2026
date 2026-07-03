# GA4GH ServiceInfo Sidecar

Welcome to the **ServiceInfo Sidecar** documentation!

A lightweight, standalone Go service that standardizes GA4GH ServiceInfo metadata across implementations such as DRS, TES, WES, and TRS.

## How It Works

Instead of proxying all traffic, the sidecar runs as its own Kubernetes Pod. The cluster's **Ingress controller** routes `/service-info` requests to the sidecar, while everything else goes directly to the real GA4GH service. If the sidecar is down, only `/service-info` is affected — the real service keeps running.

## Key Features

- **Go** — Single static binary, `scratch` container (<20MB), starts in <100ms
- **Ingress Routing** — No reverse proxy overhead, no blast radius, one Ingress rule
- **ConfigMap Hot Reload** — Update metadata via GitOps with zero restart
- **GA4GH Compliant** — Validated against the ServiceInfo v1 specification
- **Kubernetes Native** — `/healthz` + `/readyz` probes, ConfigMap volumes

---

!!! info "Active Development"
    This project is in active development as part of **Google Summer of Code 2026** under **GA4GH**.

---

## 🏛️ Project Governance

<div style="display: flex; align-items: center; justify-content: center; gap: 50px; margin: 30px 0; flex-wrap: wrap;">
  <img src="assets/ga4gh-logo.svg" alt="GA4GH Logo" style="height: 60px; width: auto;" />
  <img src="https://upload.wikimedia.org/wikipedia/commons/0/08/GSoC_logo.svg" alt="Google Summer of Code Logo" style="height: 90px; width: auto;" />
</div>

ServiceInfo Sidecar is an open-source project initiated during **Google Summer of Code (GSoC) 2026** under the **Global Alliance for Genomics and Health (GA4GH)** organization.

The project is developed under the formal governance of **GA4GH**. We align with open-source community standards and welcome contributions from developers of all backgrounds. Please refer to our [Contributing Guidelines](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/blob/main/CODE_OF_CONDUCT.md) to get started.
