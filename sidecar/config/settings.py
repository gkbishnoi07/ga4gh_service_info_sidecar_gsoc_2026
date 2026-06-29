"""Loads sidecar configuration from a YAML file and environment variables.

The configuration has two parts:
1. **Operational settings** — where the upstream is, what service type, etc.
2. **Operator overrides** — ServiceInfo fields to merge on top of the upstream response.

Operational settings can be overridden by ``SIDECAR_*`` environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sidecar.models.service_info import Organization, Service, ServiceType

# Default config path can be overridden by the SIDECAR_CONFIG_FILE env var
DEFAULT_CONFIG_PATH = Path.cwd() / "configs" / "service_info.yaml"


@dataclass
class SidecarSettings:
    """Operational configuration for the sidecar.

    Attributes:
        upstream_url: Base URL of the upstream GA4GH service.
        service_type: Which GA4GH service type (drs, tes, wes, trs).
        service_info_path: URL path to intercept for service-info.
        upstream_merge: Whether to fetch and merge upstream service-info.
        overrides: Remaining YAML keys — the operator metadata overrides.
    """

    upstream_url: str = "http://localhost:8081"
    service_type: str = "drs"
    service_info_path: str = "/ga4gh/drs/v1/service-info"
    upstream_merge: bool = True
    overrides: dict[str, Any] = field(default_factory=dict)


def load_config(config_path: Path | None = None) -> SidecarSettings:
    """Load sidecar configuration from YAML + environment variables.

    Args:
        config_path: Path to the YAML config file.
                     Defaults to configs/service_info.yaml at the project root,
                     overridable by ``SIDECAR_CONFIG_FILE`` env var.

    Returns:
        A ``SidecarSettings`` instance with operational settings and
        operator overrides separated.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML cannot be parsed.
        TypeError: If the top-level YAML is not a mapping.
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
        raw = dict(loaded)  # shallow copy to avoid mutating the parsed YAML

    # Extract operational settings from the raw dict
    upstream_url = raw.pop("upstream_url", "http://localhost:8081")
    service_type = raw.pop("service_type", "drs")
    service_info_path = raw.pop("service_info_path", "/ga4gh/drs/v1/service-info")
    upstream_merge_raw = raw.pop("upstream_merge", True)
    # Handle both bool and string values correctly:
    # YAML "false"/"False" are parsed as bool by pyyaml, but if a string
    # slips through (e.g. env injection), bool("false") would be True.
    if isinstance(upstream_merge_raw, bool):
        upstream_merge = upstream_merge_raw
    elif isinstance(upstream_merge_raw, str):
        upstream_merge = upstream_merge_raw.lower() in ("true", "1", "yes")
    else:
        upstream_merge = bool(upstream_merge_raw)

    # Apply SIDECAR_* environment variable overrides for operational settings
    upstream_url = os.getenv("SIDECAR_UPSTREAM_URL", upstream_url)
    service_type = os.getenv("SIDECAR_SERVICE_TYPE", service_type)
    service_info_path = os.getenv("SIDECAR_SERVICE_INFO_PATH", service_info_path)

    env_merge = os.getenv("SIDECAR_UPSTREAM_MERGE")
    if env_merge is not None:
        upstream_merge = env_merge.lower() in ("true", "1", "yes")

    # Everything remaining in raw is operator metadata overrides
    return SidecarSettings(
        upstream_url=upstream_url,
        service_type=service_type,
        service_info_path=service_info_path,
        upstream_merge=upstream_merge,
        overrides=raw,
    )


def load_service_info(config_path: Path | None = None) -> Service:
    """Read service_info.yaml and return a validated Service object.

    This is a **compatibility wrapper** that preserves the MVP API.
    It calls ``load_config()`` internally and constructs a ``Service``
    from the operator overrides.

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
    settings = load_config(config_path)
    raw = settings.overrides

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
