"""Loads ServiceInfo configuration from a YAML file."""

import os
from pathlib import Path
from typing import Any

import yaml

from sidecar.models.service_info import Organization, Service, ServiceType

# Default config path can be overridden by the SIDECAR_CONFIG_FILE env var
DEFAULT_CONFIG_PATH = Path.cwd() / "configs" / "service_info.yaml"


def load_service_info(config_path: Path | None = None) -> Service:
    """Read service_info.yaml and return a validated Service object.

    Args:
        config_path: Path to the YAML config file.
                     Defaults to configs/service_info.yaml at the project root.

    Returns:
        A validated GA4GH Service object.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML cannot be parsed.
        KeyError: If required keys are missing from the YAML mapping.
        TypeError: If expected nested mappings (e.g. type/organization) are not mappings.
        pydantic.ValidationError: If the parsed config cannot be validated
            as a ServiceInfo document.
    """
    env_path = os.getenv("SIDECAR_CONFIG_FILE")
    path = config_path or (Path(env_path) if env_path else DEFAULT_CONFIG_PATH)

    if not path.exists():
        raise FileNotFoundError(f"ServiceInfo config not found: {path}")

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        raw: dict[str, Any] = {}
    elif not isinstance(loaded, dict):
        raise TypeError(
            f"ServiceInfo config must be a YAML mapping at the top level, got "
            f"{type(loaded).__name__}"
        )
    else:
        raw = loaded

    return Service(
        id=raw["id"],
        name=raw["name"],
        version=raw["version"],
        description=raw.get("description"),
        environment=raw.get("environment"),
        type=ServiceType(**raw["type"]),
        organization=Organization(**raw["organization"]),
        contact_url=raw.get("contactUrl") or raw.get("contact_url"),
        documentation_url=raw.get("documentationUrl") or raw.get("documentation_url"),
        created_at=raw.get("createdAt") or raw.get("created_at"),
        updated_at=raw.get("updatedAt") or raw.get("updated_at"),
    )
