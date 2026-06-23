"""Catch-all reverse proxy route.

Implements **Option A** routing: a single catch-all route that checks
the request path and either:
- Serves the merged service-info response (for the configured path), or
- Proxies the request transparently to the upstream GA4GH service.
"""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from sidecar.config.settings import load_config
from sidecar.core.provider import get_service_info_response

logger = logging.getLogger(__name__)

router = APIRouter()


async def _proxy_to_upstream(request: Request, upstream_url: str) -> Response:
    """Forward the request to the upstream service and return its response.

    Preserves method, path, query string, headers, and body.

    Args:
        request: The incoming FastAPI request.
        upstream_url: Base URL of the upstream service.

    Returns:
        A FastAPI Response mirroring the upstream response.
    """
    # Build the target URL
    path = request.url.path
    query = str(request.url.query)
    target = f"{upstream_url.rstrip('/')}{path}"
    if query:
        target = f"{target}?{query}"

    # Forward headers (exclude host — httpx sets it from the target URL)
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream_response = await client.request(
                method=request.method,
                url=target,
                headers=headers,
                content=body,
            )
    except httpx.ConnectError:
        logger.error("Proxy: could not connect to upstream %s", target)
        return JSONResponse(
            status_code=502,
            content={"detail": "Upstream service unavailable"},
        )
    except httpx.TimeoutException:
        logger.error("Proxy: upstream timed out %s", target)
        return JSONResponse(
            status_code=504,
            content={"detail": "Upstream service timed out"},
        )

    # Build response — strip hop-by-hop headers
    excluded_headers = {"transfer-encoding", "content-encoding", "content-length"}
    response_headers: dict[str, str] = {
        k: v for k, v in upstream_response.headers.items() if k.lower() not in excluded_headers
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def catch_all(request: Request, path: str) -> Any:
    """Unified catch-all: intercept service-info OR proxy to upstream.

    This route is registered **after** the explicit ``/service-info`` route
    and after FastAPI's built-in ``/docs``, ``/openapi.json``, ``/redoc``
    routes, so those are matched first by FastAPI's route precedence.

    For the configurable service-info path (e.g.
    ``/ga4gh/drs/v1/service-info``), this handler serves the merged
    service-info response.  For everything else, it proxies to upstream.
    """
    settings = load_config()
    full_path = request.url.path

    # Intercept the configured service-info path
    if full_path == settings.service_info_path and request.method == "GET":
        data = await get_service_info_response(settings)
        return JSONResponse(content=data)

    # Everything else → proxy to upstream
    return await _proxy_to_upstream(request, settings.upstream_url)
