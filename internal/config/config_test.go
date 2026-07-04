package config_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"gopkg.in/yaml.v3"
)

func writeTempConfig(t *testing.T, data map[string]interface{}) string {
	t.Helper()
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	bytes, _ := yaml.Marshal(data)
	os.WriteFile(configPath, bytes, 0644)
	return configPath
}

func TestNewWatcher_Success(t *testing.T) {
	configPath := writeTempConfig(t, map[string]interface{}{
		"id":      "org.ga4gh.test",
		"name":    "Test Service",
		"version": "1.0.0",
		"type": map[string]string{
			"group":    "org.ga4gh",
			"artifact": "service-info",
			"version":  "1.0.0",
		},
		"organization": map[string]string{
			"name": "GA4GH",
			"url":  "https://www.ga4gh.org",
		},
	})

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}

	if !watcher.IsReady() {
		t.Errorf("expected watcher to be ready")
	}

	cfg := watcher.GetConfig()
	if cfg.ServiceInfo.ID != "org.ga4gh.test" {
		t.Errorf("expected ID 'org.ga4gh.test', got %q", cfg.ServiceInfo.ID)
	}
}

func TestNewWatcher_FailsOnMissingFields(t *testing.T) {
	// Missing "version" field
	configPath := writeTempConfig(t, map[string]interface{}{
		"id":   "org.ga4gh.test",
		"name": "Test Service",
	})

	_, err := config.NewWatcher(configPath)
	if err == nil {
		t.Fatalf("expected error due to missing required fields, got nil")
	}
}

func TestNewWatcher_FailsOnBadYAML(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")
	os.WriteFile(configPath, []byte("bad: yaml: content: {"), 0644)

	_, err := config.NewWatcher(configPath)
	if err == nil {
		t.Fatalf("expected error due to bad YAML, got nil")
	}
}
