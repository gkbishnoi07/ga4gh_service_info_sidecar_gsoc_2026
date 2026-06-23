"""Integration tests for the full sidecar pipeline.

Tests the complete flow: config → upstream fetch → merge → validate → response.
Uses pytest-httpx to mock the upstream service.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from sidecar.main import app

client = TestClient(app)

# A realistic DRS Starter Kit response
DRS_UPSTREAM_RESPONSE = {
    "id": "org.ga4gh.starterkit.drs",
    "name": "GA4GH Starter Kit DRS Service",
    "type": {"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
    "organization": {
        "name": "Global Alliance for Genomics and Health",
        "url": "https://ga4gh.org/",
    },
    "version": "0.3.2",
    "description": "Starter Kit DRS implementation",
    "createdAt": "2020-01-15T12:00:00Z",
    "updatedAt": "2020-01-15T12:00:00Z",
}


# ──────────────────────────────────────────────
# 1. Full merge pipeline via catch-all route
# ──────────────────────────────────────────────


def test_merged_response_via_configured_path(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """GET /ga4gh/drs/v1/service-info should return merged response."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/service-info",
        json=DRS_UPSTREAM_RESPONSE,
    )

    response = client.get("/ga4gh/drs/v1/service-info")
    assert response.status_code == 200

    data = response.json()

    # description comes from the operator config, NOT upstream,
    # because deep merge gives operator overrides higher precedence.
    assert data["description"] == (
        "A reusable sidecar service for standardizing GA4GH ServiceInfo metadata."
    )

    # version comes from the operator config (0.1.0), NOT from upstream (0.3.2),
    # because deep merge gives operator overrides higher precedence.
    assert data["version"] == "0.1.0"

    # Operator overrides applied (from default config)
    assert data["environment"] == "dev"


def test_merged_response_operator_override_wins(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """Operator override values should win over upstream values."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/service-info",
        json=DRS_UPSTREAM_RESPONSE,
    )

    response = client.get("/ga4gh/drs/v1/service-info")
    data = response.json()

    # The default config overrides organization.name to "GA4GH"
    # and organization.url to "https://www.ga4gh.org"
    assert data["organization"]["name"] == "GA4GH"
    assert data["organization"]["url"] == "https://www.ga4gh.org/"


# ──────────────────────────────────────────────
# 2. Upstream-only fields preserved
# ──────────────────────────────────────────────


def test_upstream_only_fields_preserved(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """Fields only present in the upstream should be preserved."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/service-info",
        json=DRS_UPSTREAM_RESPONSE,
    )

    response = client.get("/ga4gh/drs/v1/service-info")
    data = response.json()

    # createdAt and updatedAt only exist in upstream
    assert data["createdAt"] == "2020-01-15T12:00:00Z"


# ──────────────────────────────────────────────
# 3. Graceful fallback when upstream is down
# ──────────────────────────────────────────────


def test_fallback_to_config_when_upstream_down(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """When upstream is unreachable, should fall back to config-only response."""
    httpx_mock.add_exception(  # type: ignore[attr-defined]
        httpx.ConnectError("Connection refused"),
        url="http://localhost:8081/ga4gh/drs/v1/service-info",
    )

    response = client.get("/ga4gh/drs/v1/service-info")
    assert response.status_code == 200

    data = response.json()
    # Should still return valid service-info from config
    assert data["id"] == "org.ga4gh.serviceinfo-sidecar"
    assert data["environment"] == "dev"


# ──────────────────────────────────────────────
# 4. Proxy passthrough for non-service-info
# ──────────────────────────────────────────────


def test_drs_objects_endpoint_proxied(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """DRS data object endpoints should be proxied transparently."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/objects/abc123",
        json={
            "id": "abc123",
            "name": "test-object.bam",
            "size": 1234567,
            "checksums": [{"checksum": "abc123def", "type": "md5"}],
        },
    )

    response = client.get("/ga4gh/drs/v1/objects/abc123")
    assert response.status_code == 200
    assert response.json()["id"] == "abc123"


# ──────────────────────────────────────────────
# 5. Valid GA4GH ServiceInfo schema in response
# ──────────────────────────────────────────────


def test_merged_response_is_valid_service_info(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """Merged response must validate against the GA4GH Service schema."""
    from sidecar.models.service_info import Service

    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/service-info",
        json=DRS_UPSTREAM_RESPONSE,
    )

    response = client.get("/ga4gh/drs/v1/service-info")
    data = response.json()

    # This will raise ValidationError if the response is not valid
    service = Service.model_validate(data)
    assert service.id is not None
    assert service.name is not None
    assert service.version is not None
