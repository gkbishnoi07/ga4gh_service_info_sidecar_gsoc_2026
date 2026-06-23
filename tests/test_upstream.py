"""Tests for upstream service-info fetching.

Uses pytest-httpx to mock httpx transports — no real network calls.
"""

import httpx
import pytest

from sidecar.core.upstream import fetch_upstream_service_info

UPSTREAM_URL = "http://localhost:8081"
SERVICE_INFO_PATH = "/ga4gh/drs/v1/service-info"
FULL_URL = f"{UPSTREAM_URL}{SERVICE_INFO_PATH}"

VALID_UPSTREAM_RESPONSE = {
    "id": "org.ga4gh.starterkit.drs",
    "name": "GA4GH Starter Kit DRS Service",
    "type": {"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
    "organization": {
        "name": "Global Alliance for Genomics and Health",
        "url": "https://ga4gh.org/",
    },
    "version": "0.3.2",
}


# ──────────────────────────────────────────────
# 1. Success case
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_upstream_success(httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
    """Should return parsed JSON dict on 200 OK."""
    httpx_mock.add_response(url=FULL_URL, json=VALID_UPSTREAM_RESPONSE)  # type: ignore[attr-defined]
    result = await fetch_upstream_service_info(UPSTREAM_URL, SERVICE_INFO_PATH)
    assert result is not None
    assert result["id"] == "org.ga4gh.starterkit.drs"
    assert result["version"] == "0.3.2"


# ──────────────────────────────────────────────
# 2. Timeout
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_upstream_timeout(httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
    """Should return None on timeout."""
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"), url=FULL_URL)  # type: ignore[attr-defined]
    result = await fetch_upstream_service_info(UPSTREAM_URL, SERVICE_INFO_PATH, timeout=0.1)
    assert result is None


# ──────────────────────────────────────────────
# 3. Connection refused
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_upstream_connection_refused(httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
    """Should return None when upstream is unreachable."""
    httpx_mock.add_exception(httpx.ConnectError("refused"), url=FULL_URL)  # type: ignore[attr-defined]
    result = await fetch_upstream_service_info(UPSTREAM_URL, SERVICE_INFO_PATH)
    assert result is None


# ──────────────────────────────────────────────
# 4. Non-200 status code
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_upstream_500_error(httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
    """Should return None on 500 Internal Server Error."""
    httpx_mock.add_response(url=FULL_URL, status_code=500)  # type: ignore[attr-defined]
    result = await fetch_upstream_service_info(UPSTREAM_URL, SERVICE_INFO_PATH)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_upstream_404_error(httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
    """Should return None on 404 Not Found."""
    httpx_mock.add_response(url=FULL_URL, status_code=404)  # type: ignore[attr-defined]
    result = await fetch_upstream_service_info(UPSTREAM_URL, SERVICE_INFO_PATH)
    assert result is None


# ──────────────────────────────────────────────
# 5. Trailing slash normalization
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_upstream_trailing_slash(httpx_mock: pytest.fixture) -> None:  # type: ignore[type-arg]
    """Upstream URL with trailing slash should not produce double slash."""
    httpx_mock.add_response(url=FULL_URL, json=VALID_UPSTREAM_RESPONSE)  # type: ignore[attr-defined]
    result = await fetch_upstream_service_info("http://localhost:8081/", SERVICE_INFO_PATH)
    assert result is not None
    assert result["id"] == "org.ga4gh.starterkit.drs"
