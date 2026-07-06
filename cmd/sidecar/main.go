// Package main is the entrypoint for the GA4GH ServiceInfo Sidecar.
package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

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

	// Setup context that cancels on SIGTERM or SIGINT for graceful shutdown
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	// 4. Start the background fsnotify hot-reload goroutine
	go watcher.Watch(ctx, configPath)

	// 5. Wire up the HTTP handlers
	mux := http.NewServeMux()
	mux.HandleFunc("/service-info", handler.ServiceInfoHandler(watcher))
	mux.HandleFunc("/healthz", handler.HealthzHandler())
	mux.HandleFunc("/readyz", handler.ReadyzHandler(watcher))

	// 6. Start the server
	cfg := watcher.GetConfig()
	addr := fmt.Sprintf(":%s", cfg.Port)
	server := &http.Server{
		Addr:    addr,
		Handler: mux,
	}

	slog.Info("GA4GH ServiceInfo Sidecar starting", "port", cfg.Port, "config_path", configPath)

	go func() {
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("HTTP server failed", "error", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	<-ctx.Done()
	slog.Info("Shutting down gracefully, press Ctrl+C again to force")

	// Create a timeout context for the shutdown
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		slog.Error("HTTP server shutdown error", "error", err)
	}

	slog.Info("Server exited")
}
