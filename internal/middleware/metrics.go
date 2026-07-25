package middleware

import (
	"net/http"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "ga4gh_SERVICE_http_requests_total",
			Help: "Total number of HTTP requests processed by the GA4GH service-info service.",
		},
		[]string{"path", "method", "status"},
	)

	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "ga4gh_SERVICE_http_request_duration_seconds",
			Help:    "HTTP request latency in seconds for the GA4GH service-info service.",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"path", "method"},
	)
)

// responseWriterDelegator wraps a http.ResponseWriter to capture the HTTP status code.
type responseWriterDelegator struct {
	http.ResponseWriter
	status int
}

func (r *responseWriterDelegator) WriteHeader(status int) {
	r.status = status
	r.ResponseWriter.WriteHeader(status)
}

func (r *responseWriterDelegator) Write(b []byte) (int, error) {
	if r.status == 0 {
		r.status = http.StatusOK
	}
	return r.ResponseWriter.Write(b)
}

// MetricsMiddleware instruments HTTP handlers to record Prometheus metrics.
func MetricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		delegator := &responseWriterDelegator{ResponseWriter: w}

		next.ServeHTTP(delegator, r)

		status := delegator.status
		if status == 0 {
			status = http.StatusOK
		}

		duration := time.Since(start).Seconds()
		path := r.URL.Path

		httpRequestsTotal.WithLabelValues(path, r.Method, strconv.Itoa(status)).Inc()
		httpRequestDuration.WithLabelValues(path, r.Method).Observe(duration)
	})
}
