"""Fetch ServiceInfo from an upstream GA4GH service.

Used by the provider to retrieve the upstream service's own ServiceInfo
response before merging it with operator overrides.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def fetch_upstream_service_info(
    upstream_url: str,
    service_info_path: str,
    timeout: float = 5.0,
) -> dict[str, Any] | None:
    """Fetch ServiceInfo JSON from the upstream GA4GH service.

    Handles all failure cases gracefully by returning ``None``, which
    signals the provider to fall back to config-only mode.

    Args:
        upstream_url: Base URL of the upstream service (e.g. ``http://localhost:8081``).
        service_info_path: URL path for the service-info endpoint
            (e.g. ``/ga4gh/drs/v1/service-info``).
        timeout: HTTP request timeout in seconds.

    Returns:
        Parsed JSON dict on success, or ``None`` on any failure
        (timeout, connection refused, non-200 status, invalid JSON).
    """
    url = f"{upstream_url.rstrip('/')}{service_info_path}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
    except httpx.TimeoutException:
        logger.warning("Upstream service-info request timed out: %s", url)
        return None
    except httpx.ConnectError:
        logger.warning("Could not connect to upstream service: %s", url)
        return None
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Upstream service-info returned %d: %s",
            exc.response.status_code,
            url,
        )
        return None
    except Exception:
        logger.warning("Unexpected error fetching upstream service-info: %s", url, exc_info=True)
        return None
