// Package main is the entrypoint for the GA4GH ServiceInfo Sidecar.
package main

import (
	"fmt"
	"log/slog"
	"net/http"
	"os"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/handler"
)

func main() {
	// 1. Initialize structured logging
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, nil)))

	// 2. Read configuration path from environment variable fallback to local dummy config
	configPath := os.Getenv("SIDECAR_CONFIG_PATH")
	if configPath == "" {
		configPath = "./configs/dummy_service_info.yaml"
	}

	// 3. Initialize the config watcher (synchronous initial load)
	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		slog.Error("Failed to initialize sidecar configuration", "error", err)
		os.Exit(1)
	}

	// 4. Start the background fsnotify hot-reload goroutine
	go watcher.Watch(configPath)

	// 5. Wire up the HTTP handlers
	mux := http.NewServeMux()
	mux.HandleFunc("/service-info", handler.ServiceInfoHandler(watcher))
	mux.HandleFunc("/healthz", handler.HealthzHandler())
	mux.HandleFunc("/readyz", handler.ReadyzHandler(watcher))

	// 6. Start the server
	cfg := watcher.GetConfig()
	addr := fmt.Sprintf(":%s", cfg.Port)
	slog.Info("GA4GH ServiceInfo Sidecar starting", "port", cfg.Port, "config_path", configPath)

	if err := http.ListenAndServe(addr, mux); err != nil {
		slog.Error("HTTP server failed", "error", err)
		os.Exit(1)
	}
}
