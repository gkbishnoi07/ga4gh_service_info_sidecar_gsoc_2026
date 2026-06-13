"""Pydantic models for the GA4GH ServiceInfo v1 specification.

Spec: https://github.com/ga4gh-discovery/ga4gh-service-info
"""

from pydantic import AnyHttpUrl, BaseModel, Field


class Organization(BaseModel):
    """The organization responsible for the service."""

    name: str = Field(..., description="Name of the organization.", examples=["GA4GH"])
    url: AnyHttpUrl = Field(
        ..., description="URL of the organization's website.", examples=["https://www.ga4gh.org"]
    )


class ServiceType(BaseModel):
    """Identifies the GA4GH specification this service implements."""

    group: str = Field(
        ..., description="Namespace in reverse domain notation.", examples=["org.ga4gh"]
    )
    artifact: str = Field(
        ...,
        description="Name of the GA4GH specification implemented.",
        examples=["service-info", "drs", "tes", "wes"],
    )
    version: str = Field(
        ..., description="Version of the specification.", examples=["1.0.0"]
    )


class Service(BaseModel):
    """GA4GH-compliant ServiceInfo response.

    Required fields per the specification: id, name, version, type, organization.
    All other fields are optional.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this service (reverse domain notation recommended).",
        examples=["org.ga4gh.serviceinfo-sidecar"],
    )
    name: str = Field(
        ...,
        description="Human-readable name of the service.",
        examples=["GA4GH ServiceInfo Sidecar"],
    )
    version: str = Field(
        ..., description="Version of the service.", examples=["0.1.0"]
    )
    type: ServiceType = Field(..., description="GA4GH specification type implemented.")
    organization: Organization = Field(
        ..., description="Organization responsible for this service."
    )
    description: str | None = Field(default=None, description="Optional longer description.")
    environment: str | None = Field(
        default=None,
        description="Deployment environment.",
        examples=["prod", "staging", "dev"],
    )
    contact_url: AnyHttpUrl | None = Field(
        default=None,
        alias="contactUrl",
        description="URL to contact the service provider.",
    )
    documentation_url: AnyHttpUrl | None = Field(
        default=None,
        alias="documentationUrl",
        description="URL to the service documentation.",
    )
    created_at: str | None = Field(
        default=None,
        alias="createdAt",
        description="ISO 8601 timestamp of first deployment.",
    )
    updated_at: str | None = Field(
        default=None,
        alias="updatedAt",
        description="ISO 8601 timestamp of last update.",
    )

    model_config = {"populate_by_name": True}
