"""ServiceInfo provider assembles the final response.

Loads ServiceInfo from configuration (default configs/service_info.yaml; can
be overridden via SIDECAR_CONFIG_FILE). Future phases will add upstream fetching
and metadata merging.
"""

from sidecar.config.settings import load_service_info
from sidecar.models.service_info import Service


def get_service_info_response() -> Service:
    """Return a validated GA4GH Service object.

    Currently sourced from YAML configuration via load_service_info().
    """
    return load_service_info()
