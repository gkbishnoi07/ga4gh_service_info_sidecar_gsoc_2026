package model

// ServiceInfo represents a GA4GH Service as defined by the ServiceInfo v1 specification.
// See: https://github.com/ga4gh-discovery/ga4gh-service-info
type ServiceInfo struct {
	ID               string       `json:"id" yaml:"id"`
	Name             string       `json:"name" yaml:"name"`
	Type             ServiceType  `json:"type" yaml:"type"`
	Organization     Organization `json:"organization" yaml:"organization"`
	Version          string       `json:"version" yaml:"version"`
	Description      string       `json:"description,omitempty" yaml:"description,omitempty"`
	Environment      string       `json:"environment,omitempty" yaml:"environment,omitempty"`
	ContactURL       string       `json:"contactUrl,omitempty" yaml:"contactUrl,omitempty"`
	DocumentationURL string       `json:"documentationUrl,omitempty" yaml:"documentationUrl,omitempty"`
	CreatedAt        string       `json:"createdAt,omitempty" yaml:"createdAt,omitempty"`
	UpdatedAt        string       `json:"updatedAt,omitempty" yaml:"updatedAt,omitempty"`
}

// ServiceType identifies the type of GA4GH service (DRS, TES, WES, TRS).
type ServiceType struct {
	Group    string `json:"group" yaml:"group"`
	Artifact string `json:"artifact" yaml:"artifact"`
	Version  string `json:"version" yaml:"version"`
}

// Organization describes the organization responsible for the service.
type Organization struct {
	Name string `json:"name" yaml:"name"`
	URL  string `json:"url" yaml:"url"`
}
