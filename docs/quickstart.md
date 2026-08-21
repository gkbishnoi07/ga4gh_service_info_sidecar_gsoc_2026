# Quick Start Guide

This guide will help you get the **GA4GH ServiceInfo service** up and running in your Kubernetes cluster or local environment in under 5 minutes.

---

## 1. Local Quick Start

If you want to run the service locally (outside Kubernetes) using Docker:

### Step A: Create a ServiceInfo YAML File
Create a file named `service_info.yaml` with the metadata details for your genomics service:

```yaml
id: "org.example.drs"
name: "Example DRS Service"
type:
  group: "org.ga4gh"
  artifact: "drs"
  version: "1.4.0"
organization:
  name: "My Genome Center"
  url: "https://example.org"
version: "1.0.0"
environment: "dev"
description: "A quickstart DRS instance metadata helper"
```

### Step B: Run the Pre-built Docker Container
Run the container and mount your `service_info.yaml` config file. We configure the `SERVICE_CONFIG_PATH` environment variable pointing to the mounted file path inside the container:

```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/service_info.yaml:/etc/service-info/service_info.yaml \
  -e SERVICE_CONFIG_PATH=/etc/service-info/service_info.yaml \
  ghcr.io/gkbishnoi07/ga4gh_service_info_sidecar_gsoc_2026:latest
```

### Step C: Query the Metadata
Run curl to inspect the response:
```bash
curl http://localhost:8080/service-info
```

Expected JSON response:
```json
{
  "id": "org.example.drs",
  "name": "Example DRS Service",
  "type": {
    "group": "org.ga4gh",
    "artifact": "drs",
    "version": "1.4.0"
  },
  "organization": {
    "name": "My Genome Center",
    "url": "https://example.org"
  },
  "version": "1.0.0",
  "description": "A quickstart DRS instance metadata helper",
  "environment": "dev"
}
```

---

## 2. Kubernetes Deployment (Helm)

The recommended way to deploy the service in production is using our **Helm Chart**.

### Step A: Install the Helm Chart
Add the service to your cluster with customized metadata values:

```bash
helm install my-serviceinfo ./deploy/helm/ga4gh-service-info \
  --set serviceInfo.id="org.myinstitute.wes" \
  --set serviceInfo.name="Institute WES Service" \
  --set serviceInfo.type.artifact="wes" \
  --set serviceInfo.organization.name="My Institute" \
  --set serviceInfo.organization.url="https://myinstitute.org"
```

### Step B: Wire Up Ingress (Routing)
To route `/service-info` requests to this microservice while leaving other genomics API paths untouched, add this rule to your genomics service Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-wes-ingress
spec:
  rules:
    - host: wes.myinstitute.org
      http:
        paths:
          # Route ServiceInfo metadata path to our standalone service
          - path: /service-info
            pathType: Exact
            backend:
              service:
                name: my-serviceinfo-ga4gh-service-info
                port:
                  number: 8080
                  
          # All other genomics requests route to your main WES engine
          - path: /ga4gh/wes/v1/
            pathType: Prefix
            backend:
              service:
                name: my-wes-backend-service
                port:
                  number: 5000
```

That's it! `/service-info` requests will be handled cleanly by the lightweight sidecar, and the configuration can be modified later via ConfigMaps with zero restarts.
