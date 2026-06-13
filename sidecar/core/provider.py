"""ServiceInfo provider assembles the final response.

reads from configs/service_info.yaml only.
Future phases will add upstream fetching and metadata merging.
"""

from sidecar.config.settings import load_service_info
from sidecar.models.service_info import Service


def get_service_info_response() -> Service:
    """Return a validated GA4GH Service object.

    Phase 2: source is configs/service_info.yaml.
    """
    return load_service_info()
