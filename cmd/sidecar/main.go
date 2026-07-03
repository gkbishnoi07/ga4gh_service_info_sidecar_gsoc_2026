// Package main is the entrypoint for the GA4GH ServiceInfo Sidecar.
package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/config"
	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/handler"
)

func main() {
	configPath := flag.String("config", "configs/service_info.yaml", "Path to the configuration YAML file")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("Configuration error: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/service-info", handler.ServiceInfoHandler(cfg.ServiceInfo))
	mux.HandleFunc("/healthz", handler.HealthzHandler())
	mux.HandleFunc("/readyz", handler.ReadyzHandler())

	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("GA4GH ServiceInfo Sidecar starting on %s", addr)
	log.Printf("Using config file: %s", *configPath)
	log.Printf("Endpoints: GET /service-info, GET /healthz, GET /readyz")

	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
