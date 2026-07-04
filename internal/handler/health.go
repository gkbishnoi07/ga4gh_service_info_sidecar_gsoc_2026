package handler

import (
	"encoding/json"
	"net/http"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
)

// healthResponse is the JSON payload for health check endpoints.
type healthResponse struct {
	Status string `json:"status"`
}

// HealthzHandler returns an HTTP handler for the liveness probe.
// Always returns 200 with {"status": "ok"}.
func HealthzHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(healthResponse{Status: "ok"}) //nolint:errcheck
	}
}

// ReadyzHandler returns an HTTP handler for the readiness probe.
// It checks the ConfigWatcher and only returns 200 if the config has been loaded successfully.
func ReadyzHandler(watcher *config.ConfigWatcher) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		if !watcher.IsReady() {
			http.Error(w, `{"status":"not ready"}`, http.StatusServiceUnavailable)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(healthResponse{Status: "ready"}) //nolint:errcheck
	}
}
