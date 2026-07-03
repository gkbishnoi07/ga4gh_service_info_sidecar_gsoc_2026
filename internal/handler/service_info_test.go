package handler_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/handler"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/model"
)

// testServiceInfo returns a minimal valid ServiceInfo for testing.
func testServiceInfo() model.ServiceInfo {
	return model.ServiceInfo{
		ID:   "org.ga4gh.test",
		Name: "Test Service",
		Type: model.ServiceType{
			Group:    "org.ga4gh",
			Artifact: "service-info",
			Version:  "1.0.0",
		},
		Organization: model.Organization{
			Name: "GA4GH",
			URL:  "https://www.ga4gh.org",
		},
		Version:     "0.1.0",
		Description: "Test description",
		Environment: "test",
	}
}

func TestServiceInfoHandler_ReturnsOK(t *testing.T) {
	h := handler.ServiceInfoHandler(testServiceInfo())
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestServiceInfoHandler_ContentTypeJSON(t *testing.T) {
	h := handler.ServiceInfoHandler(testServiceInfo())
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	ct := rec.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected Content-Type application/json, got %q", ct)
	}
}

func TestServiceInfoHandler_ValidJSON(t *testing.T) {
	h := handler.ServiceInfoHandler(testServiceInfo())
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	var result model.ServiceInfo
	if err := json.NewDecoder(rec.Body).Decode(&result); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}

	if result.ID != "org.ga4gh.test" {
		t.Errorf("expected id %q, got %q", "org.ga4gh.test", result.ID)
	}
	if result.Name != "Test Service" {
		t.Errorf("expected name %q, got %q", "Test Service", result.Name)
	}
	if result.Version != "0.1.0" {
		t.Errorf("expected version %q, got %q", "0.1.0", result.Version)
	}
}

func TestServiceInfoHandler_CamelCaseKeys(t *testing.T) {
	info := testServiceInfo()
	info.ContactURL = "https://contact.example.com"
	info.DocumentationURL = "https://docs.example.com"

	h := handler.ServiceInfoHandler(info)
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	var raw map[string]interface{}
	if err := json.NewDecoder(rec.Body).Decode(&raw); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}

	// Check camelCase keys from GA4GH spec
	for _, key := range []string{"id", "name", "type", "organization", "version", "contactUrl", "documentationUrl"} {
		if _, ok := raw[key]; !ok {
			t.Errorf("expected camelCase key %q in response", key)
		}
	}

	// Check that snake_case keys are NOT present
	for _, key := range []string{"contact_url", "documentation_url", "created_at", "updated_at"} {
		if _, ok := raw[key]; ok {
			t.Errorf("unexpected snake_case key %q in response", key)
		}
	}
}

func TestServiceInfoHandler_OmitsEmptyOptionalFields(t *testing.T) {
	info := model.ServiceInfo{
		ID:   "org.ga4gh.test",
		Name: "Test",
		Type: model.ServiceType{
			Group:    "org.ga4gh",
			Artifact: "service-info",
			Version:  "1.0.0",
		},
		Organization: model.Organization{
			Name: "GA4GH",
			URL:  "https://www.ga4gh.org",
		},
		Version: "0.1.0",
		// contactUrl, documentationUrl, createdAt, updatedAt are empty
	}

	h := handler.ServiceInfoHandler(info)
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	var raw map[string]interface{}
	if err := json.NewDecoder(rec.Body).Decode(&raw); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}

	for _, key := range []string{"contactUrl", "documentationUrl", "createdAt", "updatedAt"} {
		if _, ok := raw[key]; ok {
			t.Errorf("expected key %q to be omitted when empty, but it was present", key)
		}
	}
}

func TestServiceInfoHandler_RejectsPost(t *testing.T) {
	h := handler.ServiceInfoHandler(testServiceInfo())
	req := httptest.NewRequest(http.MethodPost, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected status 405 for POST, got %d", rec.Code)
	}
}

func TestServiceInfoHandler_NestedTypeObject(t *testing.T) {
	h := handler.ServiceInfoHandler(testServiceInfo())
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	var raw map[string]interface{}
	json.NewDecoder(rec.Body).Decode(&raw)

	typeObj, ok := raw["type"].(map[string]interface{})
	if !ok {
		t.Fatal("expected 'type' to be a nested object")
	}
	if typeObj["group"] != "org.ga4gh" {
		t.Errorf("expected type.group %q, got %v", "org.ga4gh", typeObj["group"])
	}
	if typeObj["artifact"] != "service-info" {
		t.Errorf("expected type.artifact %q, got %v", "service-info", typeObj["artifact"])
	}
}

func TestServiceInfoHandler_NestedOrganizationObject(t *testing.T) {
	h := handler.ServiceInfoHandler(testServiceInfo())
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	var raw map[string]interface{}
	json.NewDecoder(rec.Body).Decode(&raw)

	orgObj, ok := raw["organization"].(map[string]interface{})
	if !ok {
		t.Fatal("expected 'organization' to be a nested object")
	}
	if orgObj["name"] != "GA4GH" {
		t.Errorf("expected organization.name %q, got %v", "GA4GH", orgObj["name"])
	}
	if orgObj["url"] != "https://www.ga4gh.org" {
		t.Errorf("expected organization.url %q, got %v", "https://www.ga4gh.org", orgObj["url"])
	}
}
