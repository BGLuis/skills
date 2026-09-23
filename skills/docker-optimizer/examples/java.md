# Java (Spring Boot) — production Dockerfile

Validated with Docker Engine 29.7 (`docker build --check`: no warnings). Test app: Spring Boot 4.1 (webmvc + actuator), Java 25, Maven wrapper.

| | Naive (`FROM maven`, `COPY . .`, fat jar) | Stock JRE (`temurin:25-jre`) | **This file (jlink)** | jlink + AOT cache |
|---|---|---|---|---|
| Compressed image | 229 MB | 130 MB | **86 MB** | 100 MB |
| On disk | 821 MB | 513 MB | 267 MB | 339 MB |
| Startup (avg of 3) | — | — | 1.8 s | **1.3 s** |
| RSS (`-m 512m`) | — | — | 131 MiB | — |
| `docker stop` | — | — | 1.6 s, exit 0 | — |

Rebuild after changing only `App.java`: `dependency:go-offline` and the `dependencies`, `spring-boot-loader` and `snapshot-dependencies` layers are all **CACHED**. Only the `application` layer changes, so a deploy pulls only a few KB.

## Why it looks like this

1. **Layered jar** (`java -Djarmode=tools -jar app.jar extract --layers`). The fat jar is split into 4 directories, one `COPY` each, ordered from least to most frequently changed. A fat jar in a single layer invalidates ~100 MB of dependencies on every commit.
2. **jlink custom JRE**. `jdeps --print-module-deps` finds the modules the app uses, and `jlink` builds a JRE with only those. Add the modules that are loaded by reflection and that jdeps can't see: `jdk.crypto.ec` (TLS), `jdk.management` (actuator/JMX). If something fails at runtime with `ClassNotFoundException` for `java.*`/`jdk.*`, add the missing module.
3. **`ARG JAVA_VERSION` re-declared inside the stage that uses it**. A global `ARG` (before the first `FROM`) is only visible in `FROM` lines. Without re-declaring it, `${JAVA_VERSION}` expands to empty inside `RUN`. Real bug found in validation: `jdeps` failed with `Error: no value given for --multi-release`, that error text went into `$MODULES`, and `jlink` exited with code 2.
4. **`-XX:MaxRAMPercentage=75`**. The JVM already detects the cgroup limit, but its default heap is **25%** of it. Measured with `-m 512m`: 123 MB by default, 371 MB with 75%. `-XX:+ExitOnOutOfMemoryError` makes the process die (and restart) instead of limping along after an OOM.
5. **Exec-form `ENTRYPOINT`**. `java` is PID 1 and receives the `SIGTERM`. Spring Boot's graceful shutdown finishes in 1.6 s.

## Code

```dockerfile
# syntax=docker/dockerfile:1

ARG JAVA_VERSION=25

FROM eclipse-temurin:${JAVA_VERSION}-jdk AS build
WORKDIR /src
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
# Resolve dependencies once; cached until pom.xml changes.
RUN --mount=type=cache,target=/root/.m2 ./mvnw -q dependency:go-offline
COPY src/ src/
RUN --mount=type=cache,target=/root/.m2 ./mvnw -q package -DskipTests
# Split the fat jar into layers (dependencies change rarely, application often).
RUN java -Djarmode=tools -jar target/app.jar extract --layers --destination /layers

# Custom minimal JRE: only the modules the app actually uses.
FROM eclipse-temurin:${JAVA_VERSION}-jdk AS jre
# Global ARGs are only visible in FROM lines: re-declare to use it in RUN.
ARG JAVA_VERSION
COPY --from=build /src/target/app.jar /tmp/app.jar
RUN <<EOT
    set -eu
    mkdir /tmp/lib && cd /tmp/lib && jar xf /tmp/app.jar BOOT-INF/lib
    MODULES=$(jdeps --ignore-missing-deps --print-module-deps --multi-release ${JAVA_VERSION%%.*} \
              --recursive --class-path '/tmp/lib/BOOT-INF/lib/*' /tmp/app.jar)
    jlink --add-modules "$MODULES,jdk.crypto.ec,jdk.management" \
          --strip-debug --no-man-pages --no-header-files --compress=zip-6 --output /jre
EOT

FROM debian:trixie-slim AS runtime
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --no-log-init app
ENV JAVA_HOME=/opt/jre PATH="/opt/jre/bin:$PATH" \
    JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError"
COPY --from=jre /jre /opt/jre
WORKDIR /app
COPY --from=build /layers/dependencies/ ./
COPY --from=build /layers/spring-boot-loader/ ./
COPY --from=build /layers/snapshot-dependencies/ ./
COPY --from=build /layers/application/ ./
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

`.dockerignore`:

```
.git
target
.idea
*.iml
Dockerfile*
.dockerignore
```

## Variant: AOT cache (Java 25, JEP 483/514/515) for fast startup

A training run at build time boots the app, exits right after the context refresh, and writes `app.aot` with classes already loaded, linked and profiled. Measured: startup went from **1.8 s to 1.3 s** (-28%) for a +14 MB compressed image. The gain grows with the size of the app. Add this to the end of the `runtime` stage, before `USER`:

```dockerfile
RUN java -XX:AOTCacheOutput=app.aot -Dspring.context.exit=onRefresh -jar app.jar \
 && chown 10001:10001 app.aot
USER 10001:10001
ENTRYPOINT ["java", "-XX:AOTCache=app.aot", "-jar", "app.jar"]
```

`[warning][aot] Skipping <class>` lines during training are expected (CGLIB proxies). The cache only works with **the same JVM and the same classpath** used in training, so it has to be generated in the final stage itself. Use it when startup matters (autoscaling, scale-to-zero). For long-running services the gain is small.

## Other options

- **Gradle**: same pattern, with a cache mount on `/root/.gradle`, `./gradlew bootJar`, and the jar at `build/libs/`.
- **No jlink** (simpler): runtime `eclipse-temurin:25-jre`, or `gcr.io/distroless/java25-debian13:nonroot` (no shell, 73 MB base). About 45 MB bigger than jlink.
- **Small containers (≤ 1 CPU, ≤ 512 MB)**: the JVM picks SerialGC by itself when it sees < 2 CPUs or < 1792 MB. For low latency with 2+ CPUs, G1 (the default) is fine. Don't force ParallelGC in small containers.
- **GraalVM native-image**: startup in ms and RSS of tens of MB, but builds are slow and reflection needs configuration. Consider it for serverless or scale-to-zero.
