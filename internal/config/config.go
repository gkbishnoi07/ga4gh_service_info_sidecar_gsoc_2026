package config

import (
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"sync"

	"github.com/fsnotify/fsnotify"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/model"
	"gopkg.in/yaml.v3"
)

// Config holds the sidecar's runtime configuration.
type Config struct {
	Port        string
	ServiceInfo model.ServiceInfo
}

// ConfigWatcher safely manages the sidecar configuration with hot-reload support.
type ConfigWatcher struct {
	mu     sync.RWMutex
	config *Config
	loaded bool
}

// NewWatcher initializes a ConfigWatcher and performs an initial synchronous load.
// It returns an error if the initial load fails, ensuring the server doesn't start
// without valid configuration.
func NewWatcher(path string) (*ConfigWatcher, error) {
	cw := &ConfigWatcher{}
	if err := cw.reload(path); err != nil {
		return nil, fmt.Errorf("initial config load failed: %w", err)
	}
	return cw, nil
}

// GetConfig returns the current configuration. It is safe for concurrent use.
func (cw *ConfigWatcher) GetConfig() *Config {
	cw.mu.RLock()
	defer cw.mu.RUnlock()
	return cw.config
}

// IsReady returns true if the configuration has been successfully loaded at least once.
func (cw *ConfigWatcher) IsReady() bool {
	cw.mu.RLock()
	defer cw.mu.RUnlock()
	return cw.loaded
}

// reload reads and parses the configuration file.
func (cw *ConfigWatcher) reload(configPath string) error {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return fmt.Errorf("failed to read config file %q: %w", configPath, err)
	}

	var serviceInfo model.ServiceInfo
	if err := yaml.Unmarshal(data, &serviceInfo); err != nil {
		return fmt.Errorf("failed to parse config file %q: %w", configPath, err)
	}

	// GA4GH schema validation for required fields
	if serviceInfo.ID == "" || serviceInfo.Name == "" || serviceInfo.Version == "" ||
		serviceInfo.Type.Group == "" || serviceInfo.Type.Artifact == "" || serviceInfo.Type.Version == "" ||
		serviceInfo.Organization.Name == "" || serviceInfo.Organization.URL == "" {
		return fmt.Errorf("invalid serviceInfo in %q: missing required fields", configPath)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	newConfig := &Config{
		Port:        port,
		ServiceInfo: serviceInfo,
	}

	cw.mu.Lock()
	cw.config = newConfig
	cw.loaded = true
	cw.mu.Unlock()

	return nil
}

// Watch runs in a background goroutine and listens for file modifications.
func (cw *ConfigWatcher) Watch(configPath string) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		slog.Error("Failed to create fsnotify watcher", "error", err)
		return
	}
	defer watcher.Close()

	// Watch the DIRECTORY, not the file, to survive Kubernetes symlink swaps.
	dir := filepath.Dir(configPath)
	if err := watcher.Add(dir); err != nil {
		slog.Error("Failed to watch config directory", "dir", dir, "error", err)
		return
	}

	slog.Info("Started watching configuration directory", "dir", dir)

	for {
		select {
		case event, ok := <-watcher.Events:
			if !ok {
				return
			}

			// React to any write/create in the directory — this catches both
			// direct file edits and Kubernetes symlink swaps.
			if event.Has(fsnotify.Write) || event.Has(fsnotify.Create) {
				slog.Info("Detected configuration change, reloading...", "event", event.Name, "config", configPath)
				if err := cw.reload(configPath); err != nil {
					slog.Error("Failed to reload configuration (keeping previous)", "error", err)
				} else {
					slog.Info("Configuration reloaded successfully")
				}
			}
		case err, ok := <-watcher.Errors:
			if !ok {
				return
			}
			slog.Error("fsnotify watcher error", "error", err)
		}
	}
}
