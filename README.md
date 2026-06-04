# GA4GH ServiceInfo Sidecar

A reusable sidecar service for standardizing and extending GA4GH ServiceInfo metadata across implementations such as TES, WES, DRS, and TRS.

Built as part of **Google Summer of Code 2026** under [GA4GH](https://www.ga4gh.org/).

The goal of this project is to provide a reusable, standards-compliant ServiceInfo implementation that can be shared across GA4GH services instead of each implementation maintaining its own custom ServiceInfo logic.

---

## Project Roadmap

The project is currently in its initial setup and design phase. The immediate focus is establishing the repository structure, CI/CD pipelines, documentation, and the FastAPI application skeleton.

The first implementation milestone will focus on understanding and integrating with the GA4GH Starter Kit DRS as a reference implementation. This will help validate the sidecar architecture and establish a standards-compliant ServiceInfo workflow.

Following that, the project will investigate configuration and metadata management strategies, including how ServiceInfo data should be obtained, overridden, and extended in a reusable and maintainable way.

Once the architecture has been validated, the sidecar will be integrated with TESK to address real-world migration challenges where ServiceInfo functionality is already implemented within existing services.

Finally, the project will explore support for additional trust and security metadata, including attestation-related extensions, while maintaining compatibility with existing GA4GH ServiceInfo specifications.


---

## Prerequisites

- Python 3.12+
- Git
- Docker (optional)

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026.git
cd ga4gh_service_info_sidecar_gsoc_2026
```

### Create a Virtual Environment

**Linux / macOS**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

## Related Specifications

- [GA4GH ServiceInfo v1](https://github.com/ga4gh-discovery/ga4gh-service-info)
- [GA4GH Starter Kit DRS](https://github.com/ga4gh/ga4gh-starter-kit-drs)
- [GA4GH TES](https://github.com/ga4gh/task-execution-schemas)

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).