FROM python:3.13-slim-trixie AS builder

USER root

ARG VCS_REF="missing"
ARG BUILD_DATE="missing"

ENV VCS_REF=${VCS_REF}
ENV BUILD_DATE=${BUILD_DATE}
ENV PORT=8080

LABEL org.label-schema.vcs-ref=${VCS_REF} \
  org.label-schema.build-date=${BUILD_DATE}

LABEL vendor="BCROS"

ARG APP_ENV \
  # Needed for fixing permissions of files created by Docker:
  UID=1000 \
  GID=1000

ENV APP_ENV=${APP_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  # uv:
  UV_HOME="/usr/local" \
  PATH="/root/.local/bin:$PATH"

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
  build-essential \
  ca-certificates \
  curl \
  git \
  && curl -LsSf https://astral.sh/uv/install.sh | sh \
  && mv /root/.local/bin/uv /usr/local/bin/uv \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy only requirements first, to cache them in docker layer.
# Chown to UID/GID 65532 — the 'nonroot' user baked into the distroless runtime image.
COPY --chown=65532:65532 ./pyproject.toml /code/
COPY --chown=65532:65532 ./uv.lock /code/
COPY --chown=65532:65532 ./src /code/src
COPY --chown=65532:65532 ./README.md /code/

# Install dependencies first (better caching)
RUN --mount=type=cache,target="/root/.cache/uv" \
  uv sync --no-default-groups --frozen

# Then copy the rest of the application
COPY --chown=65532:65532 ./wsgi.py /code/
COPY --chown=65532:65532 ./gunicorn_config.py /code/
COPY --chown=65532:65532 ./update_db.sh /code/
COPY --chown=65532:65532 ./devops /code/devops
COPY --chown=65532:65532 ./migrations /code/migrations

# Ensure the uv-created venv is also owned by the runtime user
RUN chown -R 65532:65532 /code/.venv

# ---------------------------------------------------------------------------
# Runtime: Google distroless. No shell, no package manager, no pip.
# Default ENTRYPOINT is /usr/bin/python; we override to launch gunicorn as a module.
# Image already runs as the 'nonroot' user (UID/GID 65532) via the :nonroot tag.
#
# NOTE: update_db.sh / `flask db upgrade` cannot run from this image (no shell,
# no uv). Run DB migrations from a separate, non-distroless image or job.
# ---------------------------------------------------------------------------
FROM gcr.io/distroless/python3-debian13:nonroot AS production

ARG VCS_REF="missing"
ARG BUILD_DATE="missing"

LABEL org.label-schema.vcs-ref=${VCS_REF} \
  org.label-schema.build-date=${BUILD_DATE} \
  vendor="BCROS"

ENV PORT=8080 \
  # Make the uv-built venv importable without relying on its bin/python shebang
  # (distroless python lives at /usr/bin/python, not /usr/local/bin).
  PYTHONPATH="/code/src:/code/.venv/lib/python3.13/site-packages" \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

# Copy the entire application (already chowned to 65532 in the builder stage)
COPY --from=builder /code /code

# Distroless :nonroot already sets USER 65532:65532 — declared here for clarity.
USER 65532:65532

# Bind is sourced from the PORT env var inside gunicorn_config.py.
ENTRYPOINT ["python", "-m", "gunicorn", "-c", "/code/gunicorn_config.py", "wsgi:app"]
