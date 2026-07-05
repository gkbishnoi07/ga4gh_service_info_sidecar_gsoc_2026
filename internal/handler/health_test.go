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
// (Duplicated here from service_info_test.go to keep test packages independent)
func setupMockWatcherForHealth(t *testing.T) *config.ConfigWatcher {
	t.Helper()

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

func TestHealthzHandler_ReturnsOK(t *testing.T) {
	h := handler.HealthzHandler()
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestReadyzHandler_ReturnsOK(t *testing.T) {
	watcher := setupMockWatcherForHealth(t)
	h := handler.ReadyzHandler(watcher)

	req := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	rec := httptest.NewRecorder()

	h.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}

	var result map[string]string
	if err := json.NewDecoder(rec.Body).Decode(&result); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}

	if result["status"] != "ready" {
		t.Errorf("expected status 'ready', got %q", result["status"])
	}
}
