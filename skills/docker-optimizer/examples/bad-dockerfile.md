# Negative Dockerfile Example: Anti-Patterns

This is an example of what **NOT** to do. If you generate a Dockerfile that looks like this, you have failed the optimization rules.

## Why is this a BAD example?
1. **No Multi-stage build**: Compiling and running in the same stage leaves compilers, source code, and build tools in the final image, bloating its size and increasing security risks.
2. **Running as root**: There is no `USER` directive, meaning the app runs as the root user. If compromised, the attacker has root access inside the container.
3. **Using `latest` tag**: `FROM node:latest` can break unpredictably when a new major version is released.
4. **Inefficient Layer Caching**: Copying all source code (`COPY . .`) *before* installing dependencies means that any minor code change will invalidate the dependency installation cache, slowing down every build.
5. **No BuildKit Cache**: Missing `--mount=type=cache` makes the dependency fetch slower on subsequent builds.
6. **No `.dockerignore` context**: Assuming a standard `COPY . .` without explicitly enforcing a strict `.dockerignore` often leads to `node_modules` or `.git` folders being copied into the image.

## Code (DO NOT GENERATE THIS):
```dockerfile
# Anti-pattern: Using latest and a heavy base image for production
FROM node:latest
WORKDIR /app

# Anti-pattern: Invalidates cache for npm install on any code change
COPY . .

# Anti-pattern: Missing BuildKit cache, using npm install instead of ci
RUN npm install

# Anti-pattern: Missing USER directive, runs as root!
EXPOSE 3000

# Anti-pattern: PID 1 issues when using npm start
CMD ["npm", "start"]
```
