"""GET /service-info route handler."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from sidecar.models.service_info import Service

router = APIRouter()


@router.get(
    "/service-info",
    response_model=Service,
    summary="Retrieve service metadata",
    description=(
        "Returns a GA4GH-compliant ServiceInfo response. "
        "Implements the [GA4GH ServiceInfo v1 specification]"
        "(https://github.com/ga4gh-discovery/ga4gh-service-info)."
    ),
    tags=["Service Info"],
)
async def get_service_info() -> JSONResponse:
    """Return GA4GH ServiceInfo metadata loaded from configuration."""
    from sidecar.core.provider import get_service_info_response

    service: Service = get_service_info_response()
    return JSONResponse(
        content=service.model_dump(mode="json", exclude_none=True, by_alias=True),
        media_type="application/json",
    )
