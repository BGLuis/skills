# Language-Specific Heuristics for Docker Optimization

Read and apply these heuristics only when the target application is written in one of the languages listed below.

## Node.js
- Use `npm ci` instead of `npm install` for reproducible builds.
- Add `--only=production` or set `NODE_ENV=production`.
- Use `CMD ["node", "src/index.js"]`. NEVER use `CMD ["npm", "start"]` due to PID 1 signal handling issues (zombie processes).

## Python
- Use Virtual Environments (`python -m venv /opt/venv`) in the builder stage, and copy them to the runtime stage.
- Use `pip install --no-cache-dir`. Use `--only-binary=:all:` when possible.
- Set `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`.

## Rust
- Utilize `cargo-chef` to cache dependencies effectively across multi-stage builds.

## Go
- Compile statically using `CGO_ENABLED=0`.
- Always use `scratch` as the final runtime image for maximum security and smallest size.
- Ensure root CA certificates are copied (`ca-certificates.crt`) if the app makes outbound HTTPS requests.

## Java (Spring Boot)
- Avoid Fat JARs. Use Spring Boot Layered JARs.
- Utilize `jlink` to create a custom JRE.
