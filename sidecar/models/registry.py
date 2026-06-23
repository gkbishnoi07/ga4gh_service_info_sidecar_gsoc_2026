"""Service-type registry mapping GA4GH service types to models and paths.

Currently supports DRS only. Additional service types (TES, WES, TRS)
can be added here when needed — just add a new entry with the model
class and default path.

One sidecar instance serves one service type. The ``service_type`` config
field selects which entry is used.
"""

from typing import Any

from sidecar.models.service_info import Service

# TypedDict would be cleaner here, but plain dict keeps mypy simple for now.
ServiceRegistryEntry = dict[str, Any]

SERVICE_REGISTRY: dict[str, ServiceRegistryEntry] = {
    "drs": {
        "model": Service,
        "default_path": "/ga4gh/drs/v1/service-info",
    },
}


def get_model_for_service_type(service_type: str) -> type[Service]:
    """Return the Pydantic model class for the given service type.

    Args:
        service_type: A supported service type (currently ``'drs'``).

    Returns:
        The corresponding Pydantic model class.

    Raises:
        KeyError: If the service type is not recognized.
    """
    entry = SERVICE_REGISTRY[service_type]
    model: type[Service] = entry["model"]
    return model


def get_default_path_for_service_type(service_type: str) -> str:
    """Return the default service-info URL path for the given service type.

    Args:
        service_type: A supported service type (currently ``'drs'``).

    Returns:
        The default URL path string.

    Raises:
        KeyError: If the service type is not recognized.
    """
    path: str = SERVICE_REGISTRY[service_type]["default_path"]
    return path
