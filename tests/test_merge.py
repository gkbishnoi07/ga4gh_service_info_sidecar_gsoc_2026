"""Tests for the deep_merge utility function.

Covers:
- Flat dicts with no overlap
- Flat dicts with overlap (override wins)
- Nested dict merging (recursive)
- Override adds new keys
- Base keys preserved when absent from override
- Array (list) replacement, not append
- None in override does NOT delete base value
- Empty dicts (both sides)
- Deeply nested (3+ levels)
- Mixed types (dict vs scalar conflict)
- Both empty
- Override completely replaces base
"""

from sidecar.config.merge import deep_merge

# ──────────────────────────────────────────────
# 1. Flat dicts — no overlap
# ──────────────────────────────────────────────


def test_flat_no_overlap() -> None:
    """Disjoint keys should all appear in the result."""
    base = {"name": "DRS", "version": "1.0"}
    override = {"environment": "production"}
    result = deep_merge(base, override)
    assert result == {"name": "DRS", "version": "1.0", "environment": "production"}


# ──────────────────────────────────────────────
# 2. Flat dicts — overlap (override wins)
# ──────────────────────────────────────────────


def test_flat_overlap_override_wins() -> None:
    """When both dicts have the same scalar key, override wins."""
    base = {"environment": "dev", "version": "1.0"}
    override = {"environment": "production"}
    result = deep_merge(base, override)
    assert result["environment"] == "production"
    assert result["version"] == "1.0"


# ──────────────────────────────────────────────
# 3. Nested dict merging
# ──────────────────────────────────────────────


def test_nested_dict_merge() -> None:
    """Nested dicts should be merged recursively, not replaced."""
    base = {"organization": {"name": "Old Institute", "url": "https://old.org"}}
    override = {"organization": {"name": "New Institute"}}
    result = deep_merge(base, override)
    assert result == {"organization": {"name": "New Institute", "url": "https://old.org"}}


# ──────────────────────────────────────────────
# 4. Override adds new keys
# ──────────────────────────────────────────────


def test_override_adds_new_keys() -> None:
    """Keys only in override should be added to result."""
    base = {"name": "DRS"}
    override = {"environment": "staging", "contactUrl": "mailto:admin@example.com"}
    result = deep_merge(base, override)
    assert result["environment"] == "staging"
    assert result["contactUrl"] == "mailto:admin@example.com"
    assert result["name"] == "DRS"


# ──────────────────────────────────────────────
# 5. Base keys preserved
# ──────────────────────────────────────────────


def test_base_keys_preserved() -> None:
    """Keys only in base should be preserved in result."""
    base = {"id": "org.ga4gh.drs", "name": "DRS", "version": "0.3.2"}
    override = {"environment": "prod"}
    result = deep_merge(base, override)
    assert result["id"] == "org.ga4gh.drs"
    assert result["name"] == "DRS"
    assert result["version"] == "0.3.2"


# ──────────────────────────────────────────────
# 6. Array replacement (not append)
# ──────────────────────────────────────────────


def test_arrays_replaced_not_appended() -> None:
    """Lists should be replaced entirely, not merged or appended."""
    base = {"storage": ["s3://bucket-a", "file:///data"]}
    override = {"storage": ["gs://bucket-b"]}
    result = deep_merge(base, override)
    assert result["storage"] == ["gs://bucket-b"]


# ──────────────────────────────────────────────
# 7. None in override does NOT delete base value
# ──────────────────────────────────────────────


def test_none_in_override_does_not_delete() -> None:
    """None in override should be skipped — base value preserved."""
    base = {"environment": "production", "version": "1.0"}
    override = {"environment": None}
    result = deep_merge(base, override)
    assert result["environment"] == "production"
    assert result["version"] == "1.0"


def test_none_in_override_for_missing_base_key() -> None:
    """None in override for a key absent in base should NOT add it."""
    base = {"name": "DRS"}
    override = {"description": None}
    result = deep_merge(base, override)
    assert "description" not in result


# ──────────────────────────────────────────────
# 8. Empty dicts
# ──────────────────────────────────────────────


def test_empty_base() -> None:
    """Empty base should return override (minus None values)."""
    base: dict[str, object] = {}
    override = {"name": "DRS", "version": "1.0"}
    result = deep_merge(base, override)
    assert result == {"name": "DRS", "version": "1.0"}


def test_empty_override() -> None:
    """Empty override should return base unchanged."""
    base = {"name": "DRS", "version": "1.0"}
    override: dict[str, object] = {}
    result = deep_merge(base, override)
    assert result == {"name": "DRS", "version": "1.0"}


def test_both_empty() -> None:
    """Both empty should return empty dict."""
    result = deep_merge({}, {})
    assert result == {}


# ──────────────────────────────────────────────
# 9. Deeply nested (3+ levels)
# ──────────────────────────────────────────────


def test_deeply_nested_merge() -> None:
    """Three levels of nesting should all merge correctly."""
    base = {
        "type": {
            "group": "org.ga4gh",
            "artifact": "drs",
            "metadata": {"revision": 1, "author": "upstream"},
        }
    }
    override = {
        "type": {
            "metadata": {"revision": 2, "reviewer": "operator"},
        }
    }
    result = deep_merge(base, override)
    assert result == {
        "type": {
            "group": "org.ga4gh",
            "artifact": "drs",
            "metadata": {"revision": 2, "author": "upstream", "reviewer": "operator"},
        }
    }


# ──────────────────────────────────────────────
# 10. Mixed types (dict vs scalar conflict)
# ──────────────────────────────────────────────


def test_override_scalar_replaces_dict() -> None:
    """If override has a scalar where base has a dict, override wins."""
    base = {"type": {"group": "org.ga4gh", "artifact": "drs"}}
    override = {"type": "custom-string"}
    result = deep_merge(base, override)
    assert result["type"] == "custom-string"


def test_override_dict_replaces_scalar() -> None:
    """If override has a dict where base has a scalar, override wins."""
    base = {"type": "flat-string"}
    override = {"type": {"group": "org.ga4gh", "artifact": "drs"}}
    result = deep_merge(base, override)
    assert result["type"] == {"group": "org.ga4gh", "artifact": "drs"}


# ──────────────────────────────────────────────
# 11. Immutability — inputs are not mutated
# ──────────────────────────────────────────────


def test_inputs_not_mutated() -> None:
    """Neither base nor override should be modified by deep_merge."""
    base = {"organization": {"name": "Old", "url": "https://old.org"}}
    override = {"organization": {"name": "New"}}

    # Save copies
    base_copy = {"organization": {"name": "Old", "url": "https://old.org"}}
    override_copy = {"organization": {"name": "New"}}

    deep_merge(base, override)

    assert base == base_copy
    assert override == override_copy


# ──────────────────────────────────────────────
# 12. Realistic GA4GH merge scenario
# ──────────────────────────────────────────────


def test_realistic_ga4gh_merge() -> None:
    """Full realistic merge scenario matching the project spec."""
    upstream = {
        "id": "org.ga4gh.starterkit.drs",
        "name": "GA4GH Starter Kit DRS Service",
        "type": {"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
        "organization": {
            "name": "Global Alliance for Genomics and Health",
            "url": "https://ga4gh.org/",
        },
        "version": "0.3.2",
        "description": "Starter Kit DRS implementation",
        "createdAt": "2020-01-15T12:00:00Z",
        "updatedAt": "2020-01-15T12:00:00Z",
    }
    operator_overrides = {
        "environment": "production",
        "organization": {
            "name": "My Research Institute",
            "url": "https://myinstitute.org",
        },
        "contactUrl": "mailto:devops@myinstitute.org",
        "updatedAt": "2026-06-22T00:00:00Z",
    }

    result = deep_merge(upstream, operator_overrides)

    # Upstream-only fields preserved
    assert result["id"] == "org.ga4gh.starterkit.drs"
    assert result["name"] == "GA4GH Starter Kit DRS Service"
    assert result["version"] == "0.3.2"
    assert result["description"] == "Starter Kit DRS implementation"
    assert result["createdAt"] == "2020-01-15T12:00:00Z"
    assert result["type"] == {"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"}

    # Override-only fields added
    assert result["environment"] == "production"
    assert result["contactUrl"] == "mailto:devops@myinstitute.org"

    # Override wins on conflict
    assert result["organization"]["name"] == "My Research Institute"
    assert result["organization"]["url"] == "https://myinstitute.org"
    assert result["updatedAt"] == "2026-06-22T00:00:00Z"
