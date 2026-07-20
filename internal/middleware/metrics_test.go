package middleware_test

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/middleware"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func TestMetricsMiddleware(t *testing.T) {
	mockHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte("created"))
	})

	metrics := middleware.MetricsMiddleware(mockHandler)

	req := httptest.NewRequest(http.MethodPost, "/test-path", nil)
	rec := httptest.NewRecorder()

	metrics.ServeHTTP(rec, req)

	if rec.Code != http.StatusCreated {
		t.Errorf("expected status 201, got %d", rec.Code)
	}

	if body := rec.Body.String(); body != "created" {
		t.Errorf("expected next handler body 'created', got %q", body)
	}

	// Scrape the Prometheus handler to verify registration and values
	scrapeReq := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	scrapeRec := httptest.NewRecorder()
	promhttp.Handler().ServeHTTP(scrapeRec, scrapeReq)

	if scrapeRec.Code != http.StatusOK {
		t.Fatalf("expected status 200 for metrics scrape, got %d", scrapeRec.Code)
	}

	scrapeBody := scrapeRec.Body.String()

	// Verify our custom metrics are present in the Prometheus output
	if !strings.Contains(scrapeBody, "ga4gh_sidecar_http_requests_total") {
		t.Errorf("expected 'ga4gh_sidecar_http_requests_total' metric in scrape body, got:\n%s", scrapeBody)
	}

	if !strings.Contains(scrapeBody, "ga4gh_sidecar_http_request_duration_seconds") {
		t.Errorf("expected 'ga4gh_sidecar_http_request_duration_seconds' metric in scrape body")
	}

	// Verify the request details are tracked in the metrics format
	expectedLabel := `ga4gh_sidecar_http_requests_total{method="POST",path="/test-path",status="201"} 1`
	if !strings.Contains(scrapeBody, expectedLabel) {
		t.Errorf("expected label pattern %q in scrape body, got:\n%s", expectedLabel, scrapeBody)
	}
}



