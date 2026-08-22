# Optimized Docker Compose Example: Development

This is an excellent example to follow when the user asks for a `docker-compose.yml` for local development.

## Why is this a GOOD example?
1. **Hot-Reload (Docker Watch)**: Utilizes the `watch` feature introduced in Docker Compose v2.22+, allowing code synchronization without resorting to heavy bind mounts across all files or continuous full rebuilds.
2. **Environment Isolation**: Keeps variables isolated for development.
3. **Basic Resource Limits**: Ensures the container doesn't exhaust the host machine's RAM in case of a memory leak during development.

## Code:
```yaml
services:
  api:
    build:
      context: .
      # In dev, we usually target a stage with a shell, e.g., a 'dev' stage
      target: dev 
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    develop:
      watch:
        # Syncs the src/ directory directly to the container without a full rebuild
        - action: sync
          path: ./src
          target: /app/src
          ignore:
            - node_modules/
        # If package.json changes, forces a quick rebuild
        - action: rebuild
          path: package.json
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```
