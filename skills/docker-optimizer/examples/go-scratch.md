# Optimized Dockerfile Example: Go (Production)

This is an excellent example to follow when the user asks for a production Dockerfile for a Go (Golang) application.

## Why is this a GOOD example?
1. **Multi-stage build**: Compiles the binary in a heavy builder stage and then copies only the binary to the runtime stage.
2. **Scratch Image**: Uses `scratch` (an empty image) for the runtime stage, making the final image extremely small (often < 10MB) and inherently secure (no shell, no OS utilities, zero attack surface).
3. **Static Compilation**: Disables CGO (`CGO_ENABLED=0`) to ensure the binary is statically linked and doesn't rely on OS-level C libraries (which `scratch` lacks).
4. **BuildKit Cache**: Uses cache mounts for Go modules and build cache to drastically speed up recompilations.

## Code:
```dockerfile
# syntax=docker/dockerfile:1.4
# Build Stage
FROM golang:1.22-alpine AS builder
WORKDIR /app

# Cache dependencies
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Copy source code and build
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o server ./cmd/api

# Runtime Stage (Production)
FROM scratch AS runner
WORKDIR /app

# Copy root certificates for HTTPS requests (required in scratch)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy the static binary
COPY --from=builder /app/server .

# Run as an unprivileged user (optional but recommended even in scratch)
# Requires copying /etc/passwd from builder or passing the UID directly
USER 10001

EXPOSE 8080
CMD ["./server"]
```
