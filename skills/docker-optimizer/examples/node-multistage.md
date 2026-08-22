# Optimized Dockerfile Example: Node.js (Production)

This is an excellent example to follow when the user asks for a production Dockerfile for a Node.js application.

## Why is this a GOOD example?
1. **Multi-stage build**: Separates the build environment (`builder`) from the runtime environment (`runner`).
2. **BuildKit Cache**: Uses `--mount=type=cache` for npm, significantly speeding up subsequent rebuilds.
3. **Security (Rootless and Distroless)**: The final container uses a Google distroless image, has no shell (reducing the attack surface), and runs as the `nonroot` user.
4. **Precise Dependencies**: Uses `npm ci` for deterministic builds.

## Code:
```dockerfile
# syntax=docker/dockerfile:1.4
# Build Stage
FROM node:20-bookworm-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci
COPY . .
# (Example: RUN npm run build if TypeScript transpilation was needed)

# Runtime Stage (Production)
FROM gcr.io/distroless/nodejs20-debian12:nonroot AS runner
WORKDIR /app
ENV NODE_ENV=production
# Copy only the strictly necessary artifacts and node_modules
COPY --from=builder --chown=nonroot:nonroot /app/node_modules ./node_modules
COPY --from=builder --chown=nonroot:nonroot /app/src ./src
COPY --from=builder --chown=nonroot:nonroot /app/package.json ./

USER nonroot
EXPOSE 3000
CMD ["src/index.js"]
```
