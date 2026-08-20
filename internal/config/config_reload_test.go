package config_test

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"gopkg.in/yaml.v3"
)

// validConfig returns a minimal valid GA4GH ServiceInfo config map.
func validConfig() map[string]interface{} {
	return map[string]interface{}{
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
	}
}

// writeConfig marshals data to YAML and writes it to configPath.
func writeConfig(t *testing.T, configPath string, data map[string]interface{}) {
	t.Helper()
	yamlBytes, err := yaml.Marshal(data)
	if err != nil {
		t.Fatalf("failed to marshal config: %v", err)
	}
	if err := os.WriteFile(configPath, yamlBytes, 0644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}
}

func TestReload_UpdatesConfigOnFileChange(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	// Write initial valid config
	writeConfig(t, configPath, validConfig())

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("NewWatcher failed: %v", err)
	}

	// Verify initial load
	cfg := watcher.GetConfig()
	if cfg.ServiceInfo.Name != "Test Service" {
		t.Fatalf("expected initial name %q, got %q", "Test Service", cfg.ServiceInfo.Name)
	}

	// Start the watcher goroutine
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go watcher.Watch(ctx, configPath)

	// Give fsnotify time to set up
	time.Sleep(200 * time.Millisecond)

	// Write updated config
	updated := validConfig()
	updated["name"] = "Updated Service"
	writeConfig(t, configPath, updated)

	// Wait for the reload to pick up the change
	time.Sleep(500 * time.Millisecond)

	cfg = watcher.GetConfig()
	if cfg.ServiceInfo.Name != "Updated Service" {
		t.Errorf("expected reloaded name %q, got %q", "Updated Service", cfg.ServiceInfo.Name)
	}
}

func TestReload_RetainsPreviousConfigOnInvalidYAML(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	// Write initial valid config
	writeConfig(t, configPath, validConfig())

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("NewWatcher failed: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go watcher.Watch(ctx, configPath)
	time.Sleep(200 * time.Millisecond)

	// Overwrite with invalid YAML
	if err := os.WriteFile(configPath, []byte("bad: yaml: {broken"), 0644); err != nil {
		t.Fatalf("failed to write bad config: %v", err)
	}
	time.Sleep(500 * time.Millisecond)

	// Config should still be the original valid one
	cfg := watcher.GetConfig()
	if cfg.ServiceInfo.Name != "Test Service" {
		t.Errorf("expected retained name %q after bad reload, got %q", "Test Service", cfg.ServiceInfo.Name)
	}
}

func TestReload_RetainsPreviousConfigOnMissingRequiredFields(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	// Write initial valid config
	writeConfig(t, configPath, validConfig())

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("NewWatcher failed: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go watcher.Watch(ctx, configPath)
	time.Sleep(200 * time.Millisecond)

	// Write config missing required fields
	incomplete := map[string]interface{}{
		"id":   "org.ga4gh.test",
		"name": "Incomplete Service",
		// missing: version, type, organization
	}
	writeConfig(t, configPath, incomplete)
	time.Sleep(500 * time.Millisecond)

	// Config should still be the original valid one
	cfg := watcher.GetConfig()
	if cfg.ServiceInfo.Name != "Test Service" {
		t.Errorf("expected retained name %q after incomplete reload, got %q", "Test Service", cfg.ServiceInfo.Name)
	}
}

func TestReload_WatcherShutdownOnContextCancel(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	writeConfig(t, configPath, validConfig())

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("NewWatcher failed: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})
	go func() {
		watcher.Watch(ctx, configPath)
		close(done)
	}()

	time.Sleep(200 * time.Millisecond)
	cancel()

	select {
	case <-done:
		// Watcher exited successfully
	case <-time.After(2 * time.Second):
		t.Error("watcher did not shut down within 2 seconds after context cancel")
	}
}
