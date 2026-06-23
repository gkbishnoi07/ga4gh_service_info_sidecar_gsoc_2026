"""Deep merge utility for combining metadata from multiple sources.

Used to merge operator-controlled overrides (from ConfigMap/YAML) on top of
an upstream GA4GH service's ServiceInfo response. The override dict wins on
scalar conflicts; nested dicts are merged recursively.
"""

from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    Rules:
    - Keys only in *base* are preserved.
    - Keys only in *override* are added.
    - When both dicts have the same key:
      - If both values are dicts → recurse.
      - Otherwise → *override* value wins.
    - ``None`` values in *override* are **skipped** (they do not delete
      a real value in *base*).
    - Arrays (lists) are replaced entirely by *override*, not appended.

    Args:
        base: The lower-priority dict (e.g. upstream service response).
        override: The higher-priority dict (e.g. operator ConfigMap values).

    Returns:
        A new merged dict. Neither *base* nor *override* is mutated.
    """
    result: dict[str, Any] = {}

    # Start with all keys from base
    for key, base_value in base.items():
        if key in override:
            override_value = override[key]

            # None in override does NOT delete a real base value
            if override_value is None:
                result[key] = base_value
            # Both are dicts → recurse
            elif isinstance(base_value, dict) and isinstance(override_value, dict):
                result[key] = deep_merge(base_value, override_value)
            # Otherwise override wins (scalars, lists, type mismatch)
            else:
                result[key] = override_value
        else:
            result[key] = base_value

    # Add keys that only exist in override (and are not None)
    for key, override_value in override.items():
        if key not in base and override_value is not None:
            result[key] = override_value

    return result
