package handler_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/handler"
	"gopkg.in/yaml.v3"
)

// setupMockWatcher creates a temporary YAML file and a ConfigWatcher for testing.
func setupMockWatcher(t *testing.T) *config.ConfigWatcher {
	t.Helper()

	// We need a real file for NewWatcher to succeed.
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	mockConfig := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test Service",
		"version": "0.1.0",
		"type": map[string]string{
			"group":    "org.ga4gh",
			"artifact": "service-info",
			"version":  "1.0.0",
		},
		"organization": map[string]string{
			"name": "GA4GH",
			"url":  "https://www.ga4gh.org",
		},
		"description":      "Test description",
		"environment":      "test",
		"contactUrl":       "https://contact.example.com",
		"documentationUrl": "https://docs.example.com",
	}

	data, err := yaml.Marshal(mockConfig)
	if err != nil {
		t.Fatalf("failed to marshal mock config: %v", err)
	}

	if err := os.WriteFile(configPath, data, 0644); err != nil {
		t.Fatalf("failed to write mock config file: %v", err)
	}

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("failed to initialize watcher: %v", err)
	}

	return watcher
}

func TestServiceInfoHandler_ReturnsOK(t *testing.T) {
	watcher := setupMockWatcher(t)
	h := handler.ServiceInfoHandler(watcher)

	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestServiceInfoHandler_ContentTypeJSON(t *testing.T) {
	watcher := setupMockWatcher(t)
	h := handler.ServiceInfoHandler(watcher)

	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	ct := rec.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected Content-Type application/json, got %q", ct)
	}
}

func TestServiceInfoHandler_ValidJSON(t *testing.T) {
	watcher := setupMockWatcher(t)
	h := handler.ServiceInfoHandler(watcher)

	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	var result map[string]interface{}
	if err := json.NewDecoder(rec.Body).Decode(&result); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}

	if result["id"] != "org.ga4gh.test" {
		t.Errorf("expected id %q, got %q", "org.ga4gh.test", result["id"])
	}

	// Verify camelCase keys from GA4GH spec are present
	if result["contactUrl"] != "https://contact.example.com" {
		t.Errorf("expected contactUrl %q, got %q", "https://contact.example.com", result["contactUrl"])
	}
	if result["documentationUrl"] != "https://docs.example.com" {
		t.Errorf("expected documentationUrl %q, got %q", "https://docs.example.com", result["documentationUrl"])
	}
}

func TestServiceInfoHandler_RejectsPost(t *testing.T) {
	watcher := setupMockWatcher(t)
	h := handler.ServiceInfoHandler(watcher)

	req := httptest.NewRequest(http.MethodPost, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected status 405 for POST, got %d", rec.Code)
	}
}

func TestServiceInfoHandler_Returns503OnNilWatcher(t *testing.T) {
	h := handler.ServiceInfoHandler(nil)
	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Errorf("expected status 503, got %d", rec.Code)
	}
}

func TestServiceInfoHandler_Returns503OnUnreadyWatcher(t *testing.T) {
	watcher := &config.ConfigWatcher{}
	h := handler.ServiceInfoHandler(watcher)

	req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Errorf("expected status 503, got %d", rec.Code)
	}
}
