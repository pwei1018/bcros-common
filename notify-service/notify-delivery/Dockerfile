FROM python:3.12-bullseye AS builder

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
  bash \
  brotli \
  build-essential \
  curl \
  gettext \
  git \
  libpq-dev \
  wait-for-it \
  && curl -LsSf https://astral.sh/uv/install.sh | sh \
  && mv /root/.local/bin/uv /usr/local/bin/uv \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /code

RUN groupadd -g "${GID}" -r web \
  && useradd -d '/code' -g web -l -r -u "${UID}" web \
  && chown web:web -R '/code'

# Copy only requirements first, to cache them in docker layer
COPY --chown=web:web ./pyproject.toml /code/
COPY --chown=web:web ./uv.lock /code/

# Install dependencies first (better caching)
RUN --mount=type=cache,target="/root/.cache/uv" \
  uv sync --no-default-groups --frozen

# Then copy the rest of the application
COPY --chown=web:web ./src /code/src
COPY --chown=web:web ./README.md /code/
COPY --chown=web:web ./wsgi.py /code/
COPY --chown=web:web ./gunicorn_config.py /code/
COPY --chown=web:web ./devops /code/devops

FROM python:3.12-slim-bullseye AS production

USER root

ARG UID=1000
ARG GID=1000

ENV PORT=8080 \
  PYTHONPATH="/code/src" \
  # Production Python settings
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq5 \
  curl \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN groupadd -g "${GID}" -r web \
  && useradd -d '/code' -g web -l -r -u "${UID}" web \
  && mkdir -p /code \
  && chown web:web -R '/code'

WORKDIR /code

# Copy the entire application from builder stage
COPY --from=builder --chown=web:web /code /code

# Copy uv binary from builder stage
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

USER web

CMD exec /code/.venv/bin/gunicorn --bind :$PORT -c /code/gunicorn_config.py wsgi:app