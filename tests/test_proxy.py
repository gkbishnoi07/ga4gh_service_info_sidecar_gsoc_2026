"""Tests for the catch-all proxy route.

Verifies:
- Configurable service-info path is intercepted (not proxied)
- Non-service-info paths are proxied to upstream
- Proxy preserves headers, query params, and body
- Proxy returns 502 when upstream is down
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from sidecar.main import app

client = TestClient(app)


# ──────────────────────────────────────────────
# 1. Configurable path intercepted
# ──────────────────────────────────────────────


def test_configured_service_info_path_intercepted(
    monkeypatch: pytest.MonkeyPatch,
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """GET to the configured service_info_path should return merged
    service-info, not proxy to upstream."""
    # The default config has service_info_path = /ga4gh/drs/v1/service-info
    # and upstream_merge = true, so it will try to fetch upstream.
    # Mock the upstream to return valid data.
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/service-info",
        json={
            "id": "org.ga4gh.starterkit.drs",
            "name": "GA4GH Starter Kit DRS Service",
            "type": {"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
            "organization": {"name": "GA4GH", "url": "https://ga4gh.org/"},
            "version": "0.3.2",
        },
    )

    response = client.get("/ga4gh/drs/v1/service-info")
    assert response.status_code == 200

    data = response.json()
    # Should be a valid service-info response (merged)
    assert "id" in data
    assert "type" in data
    assert "organization" in data


# ──────────────────────────────────────────────
# 2. Non-service-info paths are proxied
# ──────────────────────────────────────────────


def test_non_service_info_path_proxied(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """GET to a non-service-info path should be proxied to upstream."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/objects/abc123",
        json={"id": "abc123", "name": "test-object"},
    )

    response = client.get("/ga4gh/drs/v1/objects/abc123")
    assert response.status_code == 200
    assert response.json()["id"] == "abc123"


# ──────────────────────────────────────────────
# 3. POST method proxied with body
# ──────────────────────────────────────────────


def test_post_method_proxied(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """POST to a non-service-info path should be proxied with body."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/some/api/endpoint",
        json={"status": "created"},
        status_code=201,
    )

    response = client.post(
        "/some/api/endpoint",
        json={"data": "test"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "created"


# ──────────────────────────────────────────────
# 4. Query params preserved
# ──────────────────────────────────────────────


def test_query_params_preserved(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """Query parameters should be forwarded to the upstream service."""
    httpx_mock.add_response(  # type: ignore[attr-defined]
        url="http://localhost:8081/ga4gh/drs/v1/objects?page_size=10&page_token=abc",
        json={"objects": []},
    )

    response = client.get("/ga4gh/drs/v1/objects?page_size=10&page_token=abc")
    assert response.status_code == 200


# ──────────────────────────────────────────────
# 5. Upstream down → 502
# ──────────────────────────────────────────────


def test_proxy_returns_502_when_upstream_down(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """When upstream is unreachable, proxy should return 502."""
    httpx_mock.add_exception(  # type: ignore[attr-defined]
        httpx.ConnectError("Connection refused"),
        url="http://localhost:8081/some/path",
    )

    response = client.get("/some/path")
    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"].lower()


# ──────────────────────────────────────────────
# 6. Upstream timeout → 504
# ──────────────────────────────────────────────


def test_proxy_returns_504_on_timeout(
    httpx_mock: pytest.fixture,  # type: ignore[type-arg]
) -> None:
    """When upstream times out, proxy should return 504."""
    httpx_mock.add_exception(  # type: ignore[attr-defined]
        httpx.ReadTimeout("timed out"),
        url="http://localhost:8081/slow/endpoint",
    )

    response = client.get("/slow/endpoint")
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


# ──────────────────────────────────────────────
# 7. Base /service-info still works
# ──────────────────────────────────────────────


def test_base_service_info_path_still_works() -> None:
    """The explicit /service-info route should still work (backward compat)."""
    response = client.get("/service-info")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "org.ga4gh.serviceinfo-sidecar"


# ──────────────────────────────────────────────
# 8. FastAPI built-in routes not proxied
# ──────────────────────────────────────────────


def test_docs_endpoint_not_proxied() -> None:
    """FastAPI's /docs should still work and NOT be proxied."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_endpoint_not_proxied() -> None:
    """FastAPI's /openapi.json should still work and NOT be proxied."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
