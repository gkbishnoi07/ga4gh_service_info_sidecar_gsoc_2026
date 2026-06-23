"""ServiceInfo provider — orchestrates the full metadata pipeline.

Pipeline:
1. Load config (YAML + env vars) → SidecarSettings
2. If upstream_merge is enabled, fetch upstream service-info
3. Deep merge: upstream (base) + operator overrides (wins)
4. Validate merged data against the correct service-type Pydantic model
5. Return serialized dict ready for JSON response
"""

import logging
from typing import Any

from sidecar.config.merge import deep_merge
from sidecar.config.settings import SidecarSettings, load_config, load_service_info
from sidecar.core.upstream import fetch_upstream_service_info
from sidecar.models.registry import get_model_for_service_type
from sidecar.models.service_info import Service

logger = logging.getLogger(__name__)


async def get_service_info_response(
    settings: SidecarSettings | None = None,
) -> dict[str, Any]:
    """Assemble the final ServiceInfo response.

    When ``upstream_merge`` is enabled, the upstream service's response is
    fetched and deep-merged with the operator overrides from config.  The
    operator overrides always win on conflict.

    When ``upstream_merge`` is disabled (or the upstream is unreachable),
    the operator overrides from config are used as the sole data source.

    Args:
        settings: Optional pre-loaded settings.  If ``None``, settings are
            loaded from config on each call.

    Returns:
        A dict ready to be returned as a JSON response (camelCase keys,
        None values excluded).
    """
    if settings is None:
        settings = load_config()

    merged: dict[str, Any]

    if settings.upstream_merge:
        upstream_data = await fetch_upstream_service_info(
            settings.upstream_url,
            settings.service_info_path,
        )
        if upstream_data is not None:
            merged = deep_merge(upstream_data, settings.overrides)
            logger.info("Merged upstream + operator overrides for service-info")
        else:
            # Upstream unreachable — fall back to config-only
            merged = settings.overrides
            logger.warning("Upstream unreachable, falling back to config-only service-info")
    else:
        merged = settings.overrides

    # Validate against the correct model for this service type
    model_class = get_model_for_service_type(settings.service_type)
    validated = model_class.model_validate(merged)

    return validated.model_dump(mode="json", by_alias=True, exclude_none=True)


def get_service_info_sync() -> Service:
    """Synchronous compatibility wrapper for the MVP route handler.

    Used by the existing ``GET /service-info`` route which is still
    synchronous. Delegates to ``load_service_info()`` for backward
    compatibility.
    """
    return load_service_info()
