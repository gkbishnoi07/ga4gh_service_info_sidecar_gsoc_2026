package middleware_test

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/middleware"
)

func TestCORSMiddleware(t *testing.T) {
	mockHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	cors := middleware.CORSMiddleware(mockHandler)

	t.Run("GET request sets headers and calls next handler", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/service-info", nil)
		rec := httptest.NewRecorder()

		cors.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected status 200, got %d", rec.Code)
		}

		if origin := rec.Header().Get("Access-Control-Allow-Origin"); origin != "*" {
			t.Errorf("expected Access-Control-Allow-Origin '*', got %q", origin)
		}

		if methods := rec.Header().Get("Access-Control-Allow-Methods"); methods != "GET, OPTIONS" {
			t.Errorf("expected Access-Control-Allow-Methods 'GET, OPTIONS', got %q", methods)
		}

		if body := rec.Body.String(); body != "ok" {
			t.Errorf("expected next handler response body 'ok', got %q", body)
		}
	})

	t.Run("OPTIONS preflight request returns 200 without calling next handler", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodOptions, "/service-info", nil)
		rec := httptest.NewRecorder()

		cors.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected status 200, got %d", rec.Code)
		}

		if origin := rec.Header().Get("Access-Control-Allow-Origin"); origin != "*" {
			t.Errorf("expected Access-Control-Allow-Origin '*', got %q", origin)
		}

		if body := rec.Body.String(); body != "" {
			t.Errorf("expected empty body for OPTIONS preflight, got %q", body)
		}
	})
}
