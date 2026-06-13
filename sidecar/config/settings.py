"""Loads ServiceInfo configuration from a YAML file."""

from pathlib import Path

import yaml

from sidecar.models.service_info import Organization, Service, ServiceType

# Default config path can be overridden by the SIDECAR_CONFIG_FILE env var
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "service_info.yaml"


def load_service_info(config_path: Path | None = None) -> Service:
    """Read service_info.yaml and return a validated Service object.

    Args:
        config_path: Path to the YAML config file.
                     Defaults to configs/service_info.yaml at the project root.

    Returns:
        A validated GA4GH Service object.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If required fields are missing or invalid.
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"ServiceInfo config not found: {path}")

    raw: dict = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    return Service(
        id=raw["id"],
        name=raw["name"],
        version=raw["version"],
        description=raw.get("description"),
        environment=raw.get("environment"),
        type=ServiceType(**raw["type"]),
        organization=Organization(**raw["organization"]),
    )
