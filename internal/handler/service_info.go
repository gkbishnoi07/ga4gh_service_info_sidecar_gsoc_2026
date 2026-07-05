package handler

import (
	"bytes"
	"encoding/json"
	"net/http"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
)

// ServiceInfoHandler returns an HTTP handler that serves the GA4GH ServiceInfo
// response as JSON. It dynamically reads from the ConfigWatcher.
func ServiceInfoHandler(watcher *config.ConfigWatcher) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		if watcher == nil {
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
			return
		}

		cfg := watcher.GetConfig()
		if cfg == nil {
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
			return
		}

		var buf bytes.Buffer
		if err := json.NewEncoder(&buf).Encode(cfg.ServiceInfo); err != nil {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(buf.Bytes())
	}
}
