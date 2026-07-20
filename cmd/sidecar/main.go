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
	"sync"
	"syscall"
	"time"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/handler"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/middleware"
	"github.com/prometheus/client_golang/prometheus/promhttp"
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

	// 5. Wire up the HTTP handlers for the main server (port 8080)
	mainMux := http.NewServeMux()
	mainMux.HandleFunc("/service-info", handler.ServiceInfoHandler(watcher))
	mainMux.HandleFunc("/healthz", handler.HealthzHandler())
	mainMux.HandleFunc("/readyz", handler.ReadyzHandler(watcher))

	// Apply CORS and metrics middleware globally to the main server
	var globalHandler http.Handler = mainMux
	globalHandler = middleware.MetricsMiddleware(globalHandler)
	globalHandler = middleware.CORSMiddleware(globalHandler)

	// 6. Set up the main application server
	cfg := watcher.GetConfig()
	mainAddr := fmt.Sprintf(":%s", cfg.Port)
	mainServer := &http.Server{
		Addr:         mainAddr,
		Handler:      globalHandler,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// 7. Set up the private metrics server (port 9090)
	metricsMux := http.NewServeMux()
	metricsMux.Handle("/metrics", promhttp.Handler())
	metricsServer := &http.Server{
		Addr:         ":9090",
		Handler:      metricsMux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	slog.Info("GA4GH ServiceInfo Sidecar starting", "port", cfg.Port, "metrics_port", "9090", "config_path", configPath)

	var wg sync.WaitGroup

	// Start main server
	wg.Add(1)
	go func() {
		defer wg.Done()
		if err := mainServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("Main HTTP server failed", "error", err)
			os.Exit(1)
		}
	}()

	// Start metrics server
	wg.Add(1)
	go func() {
		defer wg.Done()
		if err := metricsServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("Metrics HTTP server failed", "error", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	<-ctx.Done()
	slog.Info("Shutting down gracefully, press Ctrl+C again to force")

	// Create a timeout context for the shutdown
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := mainServer.Shutdown(shutdownCtx); err != nil {
		slog.Error("Main server shutdown error", "error", err)
	}
	if err := metricsServer.Shutdown(shutdownCtx); err != nil {
		slog.Error("Metrics server shutdown error", "error", err)
	}

	// Wait for both servers to stop
	wg.Wait()
	slog.Info("Server exited")
}
