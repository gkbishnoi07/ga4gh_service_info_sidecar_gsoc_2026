//go:build integration

package integration_test

import (
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/handler"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/middleware"
	"gopkg.in/yaml.v3"
)

// startTestServer creates a real HTTP server on a random port and returns its base URL.
func startTestServer(t *testing.T) (string, *config.ConfigWatcher) {
	t.Helper()

	// Write a valid config file
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "config.yaml")

	cfg := map[string]interface{}{
		"id":      "org.ga4gh.integration-test",
		"name":    "Integration Test Service",
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
		"environment": "test",
	}

	yamlBytes, err := yaml.Marshal(cfg)
	if err != nil {
		t.Fatalf("failed to marshal config: %v", err)
	}
	if err := os.WriteFile(configPath, yamlBytes, 0644); err != nil {
		t.Fatalf("failed to write config: %v", err)
	}

	watcher, err := config.NewWatcher(configPath)
	if err != nil {
		t.Fatalf("failed to create watcher: %v", err)
	}

	// Wire up handlers
	mux := http.NewServeMux()
	mux.HandleFunc("/service-info", handler.ServiceInfoHandler(watcher))
	mux.HandleFunc("/healthz", handler.HealthzHandler())
	mux.HandleFunc("/readyz", handler.ReadyzHandler(watcher))

	var h http.Handler = mux
	h = middleware.CORSMiddleware(h)

	// Find a random free port
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to find free port: %v", err)
	}

	server := &http.Server{Handler: h}
	go func() {
		_ = server.Serve(listener)
	}()
	t.Cleanup(func() {
		_ = server.Close()
	})

	baseURL := fmt.Sprintf("http://%s", listener.Addr().String())

	// Wait for server to be ready
	for i := 0; i < 20; i++ {
		resp, err := http.Get(baseURL + "/healthz")
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return baseURL, watcher
			}
		}
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatal("server did not become ready in time")
	return "", nil
}

func TestIntegration_ServiceInfoEndpoint(t *testing.T) {
	baseURL, _ := startTestServer(t)

	resp, err := http.Get(baseURL + "/service-info")
	if err != nil {
		t.Fatalf("GET /service-info failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	ct := resp.Header.Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected Content-Type application/json, got %q", ct)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode JSON response: %v", err)
	}

	if result["id"] != "org.ga4gh.integration-test" {
		t.Errorf("expected id %q, got %q", "org.ga4gh.integration-test", result["id"])
	}
	if result["name"] != "Integration Test Service" {
		t.Errorf("expected name %q, got %q", "Integration Test Service", result["name"])
	}
}

func TestIntegration_HealthzEndpoint(t *testing.T) {
	baseURL, _ := startTestServer(t)

	resp, err := http.Get(baseURL + "/healthz")
	if err != nil {
		t.Fatalf("GET /healthz failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	var result map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}
	if result["status"] != "ok" {
		t.Errorf("expected status 'ok', got %q", result["status"])
	}
}

func TestIntegration_ReadyzEndpoint(t *testing.T) {
	baseURL, _ := startTestServer(t)

	resp, err := http.Get(baseURL + "/readyz")
	if err != nil {
		t.Fatalf("GET /readyz failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	var result map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}
	if result["status"] != "ready" {
		t.Errorf("expected status 'ready', got %q", result["status"])
	}
}

func TestIntegration_CORSHeaders(t *testing.T) {
	baseURL, _ := startTestServer(t)

	resp, err := http.Get(baseURL + "/service-info")
	if err != nil {
		t.Fatalf("GET /service-info failed: %v", err)
	}
	defer resp.Body.Close()

	origin := resp.Header.Get("Access-Control-Allow-Origin")
	if origin != "*" {
		t.Errorf("expected CORS header Access-Control-Allow-Origin '*', got %q", origin)
	}
}

func TestIntegration_MethodNotAllowed(t *testing.T) {
	baseURL, _ := startTestServer(t)

	resp, err := http.Post(baseURL+"/service-info", "application/json", nil)
	if err != nil {
		t.Fatalf("POST /service-info failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Errorf("expected status 405 for POST, got %d", resp.StatusCode)
	}
}
