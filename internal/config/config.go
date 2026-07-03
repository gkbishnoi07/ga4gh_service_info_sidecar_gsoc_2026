package config

import (
	"fmt"
	"os"

	"github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/internal/model"
	"gopkg.in/yaml.v3"
)

// Config holds the sidecar's runtime configuration.
type Config struct {
	// Port the HTTP server listens on.
	Port string

	// ServiceInfo is the metadata to serve on GET /service-info.
	ServiceInfo model.ServiceInfo
}

// Load reads configuration from the given YAML file path and environment variables.
func Load(configPath string) (*Config, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file %q: %w", configPath, err)
	}

	var serviceInfo model.ServiceInfo
	if err := yaml.Unmarshal(data, &serviceInfo); err != nil {
		return nil, fmt.Errorf("failed to parse config file %q: %w", configPath, err)
	}

	if serviceInfo.ID == "" || serviceInfo.Name == "" || serviceInfo.Version == "" ||
		serviceInfo.Type.Group == "" || serviceInfo.Type.Artifact == "" || serviceInfo.Type.Version == "" ||
		serviceInfo.Organization.Name == "" || serviceInfo.Organization.URL == "" {
		return nil, fmt.Errorf("invalid serviceInfo in %q: missing required fields", configPath)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	return &Config{
		Port:        port,
		ServiceInfo: serviceInfo,
	}, nil
}
