package config_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"gopkg.in/yaml.v3"
)

// makeConfig creates a temp YAML config file and returns the path.
func makeConfig(t *testing.T, data map[string]interface{}) string {
	t.Helper()
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")
	yamlBytes, err := yaml.Marshal(data)
	if err != nil {
		t.Fatalf("failed to marshal config: %v", err)
	}
	if err := os.WriteFile(configPath, yamlBytes, 0644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}
	return configPath
}

func TestValidation_EmptyID(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "",
		"name":    "Test",
		"version": "1.0.0",
		"type":    map[string]string{"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
		"organization": map[string]string{"name": "GA4GH", "url": "https://ga4gh.org"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for empty id, got nil")
	}
}

func TestValidation_EmptyName(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "",
		"version": "1.0.0",
		"type":    map[string]string{"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
		"organization": map[string]string{"name": "GA4GH", "url": "https://ga4gh.org"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for empty name, got nil")
	}
}

func TestValidation_EmptyVersion(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test",
		"version": "",
		"type":    map[string]string{"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
		"organization": map[string]string{"name": "GA4GH", "url": "https://ga4gh.org"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for empty version, got nil")
	}
}

func TestValidation_MissingTypeGroup(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test",
		"version": "1.0.0",
		"type":    map[string]string{"artifact": "drs", "version": "1.0.0"},
		"organization": map[string]string{"name": "GA4GH", "url": "https://ga4gh.org"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for missing type.group, got nil")
	}
}

func TestValidation_MissingTypeArtifact(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test",
		"version": "1.0.0",
		"type":    map[string]string{"group": "org.ga4gh", "version": "1.0.0"},
		"organization": map[string]string{"name": "GA4GH", "url": "https://ga4gh.org"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for missing type.artifact, got nil")
	}
}

func TestValidation_MissingOrganizationURL(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test",
		"version": "1.0.0",
		"type":    map[string]string{"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
		"organization": map[string]string{"name": "GA4GH"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for missing organization.url, got nil")
	}
}

func TestValidation_MissingOrganizationName(t *testing.T) {
	cfg := map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test",
		"version": "1.0.0",
		"type":    map[string]string{"group": "org.ga4gh", "artifact": "drs", "version": "1.0.0"},
		"organization": map[string]string{"url": "https://ga4gh.org"},
	}
	_, err := config.NewWatcher(makeConfig(t, cfg))
	if err == nil {
		t.Error("expected error for missing organization.name, got nil")
	}
}

func TestValidation_NonExistentFile(t *testing.T) {
	_, err := config.NewWatcher("/nonexistent/path/config.yaml")
	if err == nil {
		t.Error("expected error for non-existent file, got nil")
	}
}

func TestValidation_CompleteValidConfig(t *testing.T) {
	cfg := map[string]interface{}{
		"id":               "org.ga4gh.test",
		"name":             "Full Test Service",
		"version":          "2.0.0",
		"description":      "A fully configured test service",
		"environment":      "production",
		"contactUrl":       "mailto:test@ga4gh.org",
		"documentationUrl": "https://docs.ga4gh.org",
		"type":             map[string]string{"group": "org.ga4gh", "artifact": "drs", "version": "1.4.0"},
		"organization":     map[string]string{"name": "GA4GH", "url": "https://ga4gh.org"},
	}
	watcher, err := config.NewWatcher(makeConfig(t, cfg))
	if err != nil {
		t.Fatalf("expected success for complete config, got error: %v", err)
	}

	got := watcher.GetConfig()
	if got.ServiceInfo.Description != "A fully configured test service" {
		t.Errorf("expected description %q, got %q", "A fully configured test service", got.ServiceInfo.Description)
	}
	if got.ServiceInfo.Environment != "production" {
		t.Errorf("expected environment %q, got %q", "production", got.ServiceInfo.Environment)
	}
	if got.ServiceInfo.ContactURL != "mailto:test@ga4gh.org" {
		t.Errorf("expected contactUrl %q, got %q", "mailto:test@ga4gh.org", got.ServiceInfo.ContactURL)
	}
}
