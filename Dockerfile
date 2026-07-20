FROM golang:1.24-alpine AS builder

WORKDIR /app

# Install system dependencies needed for the build
RUN apk add --no-cache git ca-certificates

# Copy Go module manifests and download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy the entire workspace
COPY . .

# Statically compile the Go binary with optimizations and CGO disabled
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server cmd/server/main.go

# Final scratch stage for an ultra-lightweight and secure runtime
FROM scratch

# Copy SSL certificates for potential outbound HTTPS requests (e.g. metadata sync)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy passwd file so scratch has a non-root user entry
COPY --from=builder /etc/passwd /etc/passwd

# Copy the statically compiled binary
COPY --from=builder /app/server /server

# Copy default config file as a fallback configuration
COPY configs/dummy_service_info.yaml /configs/dummy_service_info.yaml

# Run as non-root user for security hardening.
# The server binds to an unprivileged port (8080) and only needs read access to config.
USER nobody

EXPOSE 8080

ENTRYPOINT ["/server"]

