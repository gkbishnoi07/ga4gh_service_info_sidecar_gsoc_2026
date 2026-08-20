package model_test

import (
	"encoding/json"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/model"
)

func TestServiceInfo_JSONFieldNames(t *testing.T) {
	si := model.ServiceInfo{
		ID:               "org.ga4gh.test",
		Name:             "Test Service",
		Version:          "1.0.0",
		Description:      "Test description",
		Environment:      "production",
		ContactURL:       "mailto:test@ga4gh.org",
		DocumentationURL: "https://docs.example.com",
		CreatedAt:        "2026-01-01T00:00:00Z",
		UpdatedAt:        "2026-08-20T00:00:00Z",
		Type: model.ServiceType{
			Group:    "org.ga4gh",
			Artifact: "drs",
			Version:  "1.4.0",
		},
		Organization: model.Organization{
			Name: "GA4GH",
			URL:  "https://ga4gh.org",
		},
	}

	data, err := json.Marshal(si)
	if err != nil {
		t.Fatalf("failed to marshal ServiceInfo: %v", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("failed to unmarshal JSON: %v", err)
	}

	// Verify GA4GH camelCase field names
	expectedKeys := []string{
		"id", "name", "version", "description", "environment",
		"contactUrl", "documentationUrl", "createdAt", "updatedAt",
		"type", "organization",
	}
	for _, key := range expectedKeys {
		if _, ok := result[key]; !ok {
			t.Errorf("expected JSON key %q to be present, but it was missing", key)
		}
	}

	// Verify no snake_case keys leaked (Go default would be PascalCase)
	forbiddenKeys := []string{
		"ID", "Name", "Version", "ContactURL", "DocumentationURL",
		"CreatedAt", "UpdatedAt", "contact_url", "documentation_url",
		"created_at", "updated_at",
	}
	for _, key := range forbiddenKeys {
		if _, ok := result[key]; ok {
			t.Errorf("unexpected JSON key %q found — should be camelCase per GA4GH spec", key)
		}
	}
}

func TestServiceInfo_OmitEmptyOptionalFields(t *testing.T) {
	// Only required fields set — optional fields should NOT appear in JSON
	si := model.ServiceInfo{
		ID:      "org.ga4gh.test",
		Name:    "Minimal Service",
		Version: "1.0.0",
		Type: model.ServiceType{
			Group:    "org.ga4gh",
			Artifact: "drs",
			Version:  "1.4.0",
		},
		Organization: model.Organization{
			Name: "GA4GH",
			URL:  "https://ga4gh.org",
		},
	}

	data, err := json.Marshal(si)
	if err != nil {
		t.Fatalf("failed to marshal ServiceInfo: %v", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("failed to unmarshal JSON: %v", err)
	}

	// These optional fields should be omitted when empty
	omittedKeys := []string{
		"description", "environment", "contactUrl",
		"documentationUrl", "createdAt", "updatedAt",
	}
	for _, key := range omittedKeys {
		if _, ok := result[key]; ok {
			t.Errorf("expected optional field %q to be omitted when empty, but it was present", key)
		}
	}

	// Required fields must still be present
	requiredKeys := []string{"id", "name", "version", "type", "organization"}
	for _, key := range requiredKeys {
		if _, ok := result[key]; !ok {
			t.Errorf("expected required field %q to be present, but it was missing", key)
		}
	}
}

func TestServiceType_JSONFieldNames(t *testing.T) {
	st := model.ServiceType{
		Group:    "org.ga4gh",
		Artifact: "drs",
		Version:  "1.4.0",
	}

	data, err := json.Marshal(st)
	if err != nil {
		t.Fatalf("failed to marshal ServiceType: %v", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("failed to unmarshal JSON: %v", err)
	}

	for _, key := range []string{"group", "artifact", "version"} {
		if _, ok := result[key]; !ok {
			t.Errorf("expected JSON key %q in ServiceType, but it was missing", key)
		}
	}
}

func TestOrganization_JSONFieldNames(t *testing.T) {
	org := model.Organization{
		Name: "GA4GH",
		URL:  "https://ga4gh.org",
	}

	data, err := json.Marshal(org)
	if err != nil {
		t.Fatalf("failed to marshal Organization: %v", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("failed to unmarshal JSON: %v", err)
	}

	for _, key := range []string{"name", "url"} {
		if _, ok := result[key]; !ok {
			t.Errorf("expected JSON key %q in Organization, but it was missing", key)
		}
	}
}
