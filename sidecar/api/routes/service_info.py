"""GET /service-info route handler (base path).

Serves GA4GH ServiceInfo at the root ``/service-info`` path.
This is the backward-compatible MVP route. The configurable path
(e.g. ``/ga4gh/drs/v1/service-info``) is handled by the catch-all
proxy route.
"""

from fastapi import APIRouter

from sidecar.models.service_info import Service

router = APIRouter()


@router.get(
    "/service-info",
    response_model=Service,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="Retrieve service metadata",
    description=(
        "Returns a GA4GH-compliant ServiceInfo response. "
        "Implements the [GA4GH ServiceInfo v1 specification]"
        "(https://github.com/ga4gh-discovery/ga4gh-service-info)."
    ),
    tags=["Service Info"],
)
def get_service_info() -> Service:
    """Return GA4GH ServiceInfo metadata loaded from configuration."""
    from sidecar.core.provider import get_service_info_sync

    return get_service_info_sync()
