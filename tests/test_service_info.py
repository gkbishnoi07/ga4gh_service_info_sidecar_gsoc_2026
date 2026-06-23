"""Tests for the GA4GH ServiceInfo Sidecar.

Covers:
- GET /service-info endpoint (happy path + response structure)
- Full response schema validation via model_validate
- Pydantic model validation (required fields, optional fields, invalid data)
- Config loader (missing file, empty YAML, invalid YAML syntax, missing keys,
  wrong data types, missing nested fields, custom path)
- Endpoint behavior when config loading fails
- Provider layer
"""

from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from pydantic import ValidationError

from sidecar.config.settings import load_service_info
from sidecar.core.provider import get_service_info_sync
from sidecar.main import app
from sidecar.models.service_info import Organization, Service, ServiceType

client = TestClient(app)


# ──────────────────────────────────────────────
# 1. API Endpoint — Happy Path
# ──────────────────────────────────────────────


def test_service_info_returns_200() -> None:
    """GET /service-info should return HTTP 200."""
    response = client.get("/service-info")
    assert response.status_code == 200


def test_service_info_content_type_is_json() -> None:
    """Response should be application/json."""
    response = client.get("/service-info")
    assert "application/json" in response.headers["content-type"]


def test_service_info_response_validates_against_schema() -> None:
    """Full response must validate against the Pydantic Service model.

    This is stronger than checking individual keys — it proves the entire
    response JSON is a valid GA4GH ServiceInfo document.
    """
    data = client.get("/service-info").json()
    service = Service.model_validate(data)

    # Verify the validated object has the required fields populated
    assert service.id
    assert service.name
    assert service.version
    assert service.type
    assert service.organization


def test_service_info_id_is_string() -> None:
    """id field must be a non-empty string."""
    response = client.get("/service-info")
    assert isinstance(response.json()["id"], str)
    assert len(response.json()["id"]) > 0


# ──────────────────────────────────────────────
# 2. API Endpoint — Response values match config
# ──────────────────────────────────────────────


def test_response_values_match_default_config() -> None:
    """Response values should match what is in configs/service_info.yaml."""
    data = client.get("/service-info").json()

    assert data["id"] == "org.ga4gh.serviceinfo-sidecar"
    assert data["name"] == "GA4GH ServiceInfo Sidecar"
    assert data["version"] == "0.1.0"
    assert data["type"]["group"] == "org.ga4gh"
    assert data["type"]["artifact"] == "drs"
    assert data["type"]["version"] == "1.3.0"
    assert data["organization"]["name"] == "GA4GH"
    assert data["organization"]["url"] == "https://www.ga4gh.org/"


def test_response_excludes_none_optional_fields() -> None:
    """Optional fields that are None should NOT appear in the JSON response."""
    data = client.get("/service-info").json()

    # These are commented out in the default config, so should be absent
    assert "contactUrl" not in data
    assert "documentationUrl" not in data
    assert "createdAt" not in data
    assert "updatedAt" not in data


def test_response_includes_set_optional_fields() -> None:
    """Optional fields that ARE set in the config should appear in the response."""
    data = client.get("/service-info").json()

    # These are set in the default config
    assert "description" in data
    assert "environment" in data
    assert data["description"] == (
        "A reusable sidecar service for standardizing GA4GH ServiceInfo metadata."
    )
    assert data["environment"] == "dev"


def test_response_uses_camelcase_keys() -> None:
    """JSON keys must use camelCase as per GA4GH spec, not snake_case."""
    data = client.get("/service-info").json()

    # snake_case keys should NOT be present
    assert "contact_url" not in data
    assert "documentation_url" not in data
    assert "created_at" not in data
    assert "updated_at" not in data


# ──────────────────────────────────────────────
# 3. Pydantic Models — Valid construction
# ──────────────────────────────────────────────


def test_organization_model_valid() -> None:
    """Organization model accepts valid data."""
    org = Organization(name="TestOrg", url="https://example.com")
    assert org.name == "TestOrg"
    assert str(org.url) == "https://example.com/"


def test_service_type_model_valid() -> None:
    """ServiceType model accepts valid data."""
    st = ServiceType(group="org.ga4gh", artifact="drs", version="1.0.0")
    assert st.group == "org.ga4gh"
    assert st.artifact == "drs"
    assert st.version == "1.0.0"


def test_service_model_required_fields_only() -> None:
    """Service model works with only required fields (all optional = None)."""
    svc = Service(
        id="test.service",
        name="Test",
        version="1.0.0",
        type=ServiceType(group="org.ga4gh", artifact="tes", version="1.0.0"),
        organization=Organization(name="Org", url="https://example.com"),
    )
    assert svc.description is None
    assert svc.environment is None
    assert svc.contact_url is None
    assert svc.documentation_url is None
    assert svc.created_at is None
    assert svc.updated_at is None


def test_service_model_all_optional_fields() -> None:
    """Service model accepts all optional fields when provided."""
    svc = Service(
        id="test.service",
        name="Test",
        version="1.0.0",
        type=ServiceType(group="org.ga4gh", artifact="wes", version="1.0.0"),
        organization=Organization(name="Org", url="https://example.com"),
        description="A test service",
        environment="staging",
        contact_url="https://contact.example.com",
        documentation_url="https://docs.example.com",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-06-01T00:00:00Z",
    )
    assert svc.description == "A test service"
    assert svc.environment == "staging"
    assert svc.contact_url == "https://contact.example.com"
    assert str(svc.documentation_url) == "https://docs.example.com/"
    assert svc.created_at == "2026-01-01T00:00:00Z"
    assert svc.updated_at == "2026-06-01T00:00:00Z"


def test_service_model_populate_by_alias() -> None:
    """Service model can be constructed using camelCase alias names."""
    svc = Service(
        id="test.service",
        name="Test",
        version="1.0.0",
        type=ServiceType(group="org.ga4gh", artifact="trs", version="1.0.0"),
        organization=Organization(name="Org", url="https://example.com"),
        contactUrl="https://contact.example.com",
        documentationUrl="https://docs.example.com",
        createdAt="2026-01-01T00:00:00Z",
        updatedAt="2026-06-01T00:00:00Z",
    )
    assert svc.contact_url == "https://contact.example.com"
    assert str(svc.documentation_url) == "https://docs.example.com/"
    assert svc.created_at == "2026-01-01T00:00:00Z"
    assert svc.updated_at == "2026-06-01T00:00:00Z"


def test_service_model_serialization_by_alias() -> None:
    """model_dump(by_alias=True) should produce camelCase keys."""
    svc = Service(
        id="test.service",
        name="Test",
        version="1.0.0",
        type=ServiceType(group="org.ga4gh", artifact="drs", version="1.0.0"),
        organization=Organization(name="Org", url="https://example.com"),
        contact_url="https://contact.example.com",
        created_at="2026-01-01T00:00:00Z",
    )
    dumped = svc.model_dump(mode="json", by_alias=True, exclude_none=True)

    assert "contactUrl" in dumped
    assert "createdAt" in dumped
    # snake_case keys should NOT be in aliased output
    assert "contact_url" not in dumped
    assert "created_at" not in dumped


# ──────────────────────────────────────────────
# 4. Pydantic Models — Validation errors
# ──────────────────────────────────────────────


def test_organization_missing_name_raises() -> None:
    """Organization without 'name' should raise ValidationError."""
    with pytest.raises(ValidationError):
        Organization(url="https://example.com")  # type: ignore[call-arg]


def test_organization_missing_url_raises() -> None:
    """Organization without 'url' should raise ValidationError."""
    with pytest.raises(ValidationError):
        Organization(name="TestOrg")  # type: ignore[call-arg]


def test_organization_invalid_url_raises() -> None:
    """Organization with an invalid URL should raise ValidationError."""
    with pytest.raises(ValidationError):
        Organization(name="TestOrg", url="not-a-valid-url")


def test_service_type_missing_group_raises() -> None:
    """ServiceType without 'group' should raise ValidationError."""
    with pytest.raises(ValidationError):
        ServiceType(artifact="drs", version="1.0.0")  # type: ignore[call-arg]


def test_service_type_missing_artifact_raises() -> None:
    """ServiceType without 'artifact' should raise ValidationError."""
    with pytest.raises(ValidationError):
        ServiceType(group="org.ga4gh", version="1.0.0")  # type: ignore[call-arg]


def test_service_type_missing_version_raises() -> None:
    """ServiceType without 'version' should raise ValidationError."""
    with pytest.raises(ValidationError):
        ServiceType(group="org.ga4gh", artifact="drs")  # type: ignore[call-arg]


def test_service_missing_id_raises() -> None:
    """Service without 'id' should raise ValidationError."""
    with pytest.raises(ValidationError):
        Service(  # type: ignore[call-arg]
            name="Test",
            version="1.0.0",
            type=ServiceType(group="org.ga4gh", artifact="drs", version="1.0.0"),
            organization=Organization(name="Org", url="https://example.com"),
        )


def test_service_missing_organization_raises() -> None:
    """Service without 'organization' should raise ValidationError."""
    with pytest.raises(ValidationError):
        Service(  # type: ignore[call-arg]
            id="test.service",
            name="Test",
            version="1.0.0",
            type=ServiceType(group="org.ga4gh", artifact="drs", version="1.0.0"),
        )


def test_service_missing_type_raises() -> None:
    """Service without 'type' should raise ValidationError."""
    with pytest.raises(ValidationError):
        Service(  # type: ignore[call-arg]
            id="test.service",
            name="Test",
            version="1.0.0",
            organization=Organization(name="Org", url="https://example.com"),
        )


# ──────────────────────────────────────────────
# 5. Config Loader — Edge cases
# ──────────────────────────────────────────────


def test_load_config_file_not_found(tmp_path: Path) -> None:
    """load_service_info should raise FileNotFoundError for a missing file."""
    fake_path = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError, match="ServiceInfo config not found"):
        load_service_info(config_path=fake_path)


def test_load_config_empty_yaml(tmp_path: Path) -> None:
    """An empty YAML file should raise KeyError (required keys missing)."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(KeyError):
        load_service_info(config_path=empty_file)


def test_load_config_missing_required_key(tmp_path: Path) -> None:
    """YAML with a missing required key (e.g. 'id') should raise KeyError."""
    incomplete = tmp_path / "incomplete.yaml"
    incomplete.write_text(
        dedent("""\
            name: "Test"
            version: "1.0.0"
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization:
              name: "Org"
              url: "https://example.com"
        """),
        encoding="utf-8",
    )
    with pytest.raises(KeyError, match="id"):
        load_service_info(config_path=incomplete)


def test_load_config_invalid_organization_url(tmp_path: Path) -> None:
    """YAML with an invalid organization URL should raise ValidationError."""
    bad_config = tmp_path / "bad_url.yaml"
    bad_config.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: "1.0.0"
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization:
              name: "Org"
              url: "not-a-url"
        """),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_service_info(config_path=bad_config)


def test_load_config_custom_valid_path(tmp_path: Path) -> None:
    """load_service_info should work with a custom config_path."""
    custom = tmp_path / "custom.yaml"
    custom.write_text(
        dedent("""\
            id: "custom.service"
            name: "Custom Service"
            version: "2.0.0"
            type:
              group: "org.custom"
              artifact: "test"
              version: "1.0.0"
            organization:
              name: "Custom Org"
              url: "https://custom.example.com"
        """),
        encoding="utf-8",
    )
    service = load_service_info(config_path=custom)
    assert service.id == "custom.service"
    assert service.name == "Custom Service"
    assert service.version == "2.0.0"
    assert service.organization.name == "Custom Org"


def test_load_config_with_optional_fields(tmp_path: Path) -> None:
    """Optional fields in YAML should be loaded into the Service model."""
    full_config = tmp_path / "full.yaml"
    full_config.write_text(
        dedent("""\
            id: "full.service"
            name: "Full Service"
            version: "1.0.0"
            description: "A fully configured service"
            environment: "prod"
            contactUrl: "https://contact.example.com"
            documentation_url: "https://docs.example.com"
            createdAt: "2026-01-01T00:00:00Z"
            updated_at: "2026-06-01T00:00:00Z"
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization:
              name: "Full Org"
              url: "https://full.example.com"
        """),
        encoding="utf-8",
    )
    service = load_service_info(config_path=full_config)
    assert service.description == "A fully configured service"
    assert service.environment == "prod"
    assert service.contact_url == "https://contact.example.com"
    assert str(service.documentation_url) == "https://docs.example.com/"
    assert service.created_at == "2026-01-01T00:00:00Z"
    assert service.updated_at == "2026-06-01T00:00:00Z"


def test_load_config_env_var_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """load_service_info should use the path from SIDECAR_CONFIG_FILE env var if set."""
    env_config = tmp_path / "env_override.yaml"
    env_config.write_text(
        dedent("""\
            id: "env.service"
            name: "Env Service"
            version: "1.0.0"
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization:
              name: "Env Org"
              url: "https://env.example.com"
        """),
        encoding="utf-8",
    )
    monkeypatch.setenv("SIDECAR_CONFIG_FILE", str(env_config))
    service = load_service_info()
    assert service.id == "env.service"
    assert service.name == "Env Service"


def test_load_config_default_path_works() -> None:
    """load_service_info() with no arguments should use the default config."""
    service = load_service_info()
    assert service.id == "org.ga4gh.serviceinfo-sidecar"


# ──────────────────────────────────────────────
# 6. Provider layer
# ──────────────────────────────────────────────


def test_provider_returns_service_object() -> None:
    """get_service_info_sync should return a Service instance."""
    result = get_service_info_sync()
    assert isinstance(result, Service)


def test_provider_returns_valid_data() -> None:
    """Provider output should have the correct id from the default config."""
    result = get_service_info_sync()
    assert result.id == "org.ga4gh.serviceinfo-sidecar"
    assert result.name == "GA4GH ServiceInfo Sidecar"


# ──────────────────────────────────────────────
# 7. Config Loader — Invalid YAML syntax
# ──────────────────────────────────────────────


def test_load_config_invalid_yaml_syntax(tmp_path: Path) -> None:
    """Malformed YAML (bad indentation/syntax) should raise yaml.YAMLError."""
    bad_yaml = tmp_path / "bad_syntax.yaml"
    bad_yaml.write_text(
        dedent("""\
            id: "test"
            name: "Test"
            type:
              group: "org.ga4gh"
               artifact: "drs"   # wrong indentation — breaks YAML
              version: "1.0.0"
        """),
        encoding="utf-8",
    )
    with pytest.raises(yaml.YAMLError):
        load_service_info(config_path=bad_yaml)


def test_load_config_yaml_with_tabs(tmp_path: Path) -> None:
    """YAML with tab indentation should raise yaml.YAMLError."""
    tabbed = tmp_path / "tabs.yaml"
    tabbed.write_text(
        'id: "test"\n\tname: "Test"\n',
        encoding="utf-8",
    )
    with pytest.raises(yaml.YAMLError):
        load_service_info(config_path=tabbed)


# ──────────────────────────────────────────────
# 8. Config Loader — Non-dict top-level YAML
# ──────────────────────────────────────────────


def test_load_config_yaml_top_level_string(tmp_path: Path) -> None:
    """A YAML file containing a plain string should raise TypeError."""
    string_yaml = tmp_path / "string.yaml"
    string_yaml.write_text('"just a string"', encoding="utf-8")
    with pytest.raises(TypeError, match="YAML mapping"):
        load_service_info(config_path=string_yaml)


def test_load_config_yaml_top_level_list(tmp_path: Path) -> None:
    """A YAML file containing a list should raise TypeError."""
    list_yaml = tmp_path / "list.yaml"
    list_yaml.write_text("- item1\n- item2\n", encoding="utf-8")
    with pytest.raises(TypeError, match="YAML mapping"):
        load_service_info(config_path=list_yaml)


# ──────────────────────────────────────────────
# 9. Config Loader — Wrong data types in YAML
# ──────────────────────────────────────────────


def test_load_config_type_is_string_instead_of_dict(tmp_path: Path) -> None:
    """If 'type' is a plain string instead of a mapping, it should fail."""
    wrong_type = tmp_path / "wrong_type.yaml"
    wrong_type.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: "1.0.0"
            type: "should-be-a-dict"
            organization:
              name: "Org"
              url: "https://example.com"
        """),
        encoding="utf-8",
    )
    with pytest.raises(TypeError):
        load_service_info(config_path=wrong_type)


def test_load_config_organization_is_string_instead_of_dict(tmp_path: Path) -> None:
    """If 'organization' is a plain string instead of a mapping, it should fail."""
    wrong_org = tmp_path / "wrong_org.yaml"
    wrong_org.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: "1.0.0"
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization: "should-be-a-dict"
        """),
        encoding="utf-8",
    )
    with pytest.raises(TypeError):
        load_service_info(config_path=wrong_org)


def test_load_config_version_is_number_instead_of_string(tmp_path: Path) -> None:
    """Numeric version (e.g. 1.0) is parsed as float by YAML.
    Pydantic v2 does NOT coerce float to str, so this should raise ValidationError."""
    num_version = tmp_path / "num_version.yaml"
    num_version.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: 1.0
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization:
              name: "Org"
              url: "https://example.com"
        """),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="version"):
        load_service_info(config_path=num_version)


# ──────────────────────────────────────────────
# 10. Config Loader — Missing nested YAML fields
# ──────────────────────────────────────────────


def test_load_config_type_missing_artifact(tmp_path: Path) -> None:
    """type section without 'artifact' should raise ValidationError."""
    missing_artifact = tmp_path / "no_artifact.yaml"
    missing_artifact.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: "1.0.0"
            type:
              group: "org.ga4gh"
              version: "1.0.0"
            organization:
              name: "Org"
              url: "https://example.com"
        """),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_service_info(config_path=missing_artifact)


def test_load_config_organization_missing_url(tmp_path: Path) -> None:
    """organization section without 'url' should raise ValidationError."""
    no_url = tmp_path / "no_org_url.yaml"
    no_url.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: "1.0.0"
            type:
              group: "org.ga4gh"
              artifact: "drs"
              version: "1.0.0"
            organization:
              name: "Org"
        """),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_service_info(config_path=no_url)


def test_load_config_type_section_completely_empty(tmp_path: Path) -> None:
    """An empty type mapping should raise ValidationError."""
    empty_type = tmp_path / "empty_type.yaml"
    empty_type.write_text(
        dedent("""\
            id: "test.service"
            name: "Test"
            version: "1.0.0"
            type: {}
            organization:
              name: "Org"
              url: "https://example.com"
        """),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_service_info(config_path=empty_type)


# ──────────────────────────────────────────────
# 11. Endpoint behavior when config loading fails
# ──────────────────────────────────────────────


def test_endpoint_returns_500_when_config_missing() -> None:
    """If the config file cannot be loaded, GET /service-info should return 500."""
    error_client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "sidecar.core.provider.load_service_info",
        side_effect=FileNotFoundError("config missing"),
    ):
        response = error_client.get("/service-info")
        assert response.status_code == 500


def test_endpoint_returns_500_when_validation_fails() -> None:
    """If config data is invalid, GET /service-info should return 500."""
    error_client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "sidecar.core.provider.load_service_info",
        side_effect=ValidationError.from_exception_data(
            title="Service",
            line_errors=[],
        ),
    ):
        response = error_client.get("/service-info")
        assert response.status_code == 500


# ──────────────────────────────────────────────
# 12. Full response schema validation
# ──────────────────────────────────────────────


def test_full_response_round_trips_through_model() -> None:
    """The JSON response should round-trip: JSON -> model_validate -> model_dump -> same JSON."""
    data = client.get("/service-info").json()

    # Parse the raw JSON into a Service model
    service = Service.model_validate(data)

    # Dump it back out with the same settings the route uses
    re_serialized = service.model_dump(mode="json", exclude_none=True, by_alias=True)

    assert re_serialized == data


def test_response_has_no_extra_unexpected_fields() -> None:
    """Response should only contain known GA4GH ServiceInfo fields."""
    data = client.get("/service-info").json()

    allowed_keys = {
        "id",
        "name",
        "version",
        "type",
        "organization",
        "description",
        "environment",
        "contactUrl",
        "documentationUrl",
        "createdAt",
        "updatedAt",
    }
    assert set(data.keys()).issubset(allowed_keys)
