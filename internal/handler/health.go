package handler

import (
	"encoding/json"
	"net/http"
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
// Always returns 200 with {"status": "ready"}.
// Phase 2 will check config-loaded state before reporting ready.
func ReadyzHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(healthResponse{Status: "ready"}) //nolint:errcheck
	}
}
