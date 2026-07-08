# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions."""

import contextlib
import ipaddress
import os
import socket
from urllib.parse import urlparse

from flask import Flask
import httpx
from sqlalchemy import event
from sqlalchemy.engine.url import make_url
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()

_TRUTHY_VALUES = {"true", "yes", "1", "on"}

# SSRF protections for outbound file downloads.
_ALLOWED_DOWNLOAD_SCHEMES = {"http", "https"}
_MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
_DOWNLOAD_TIMEOUT_SECONDS = 30


def _host_resolves_to_blocked_ip(host: str) -> bool:
    """Return True when *host* resolves to a non-public (internal) address.

    Blocking private, loopback, link-local, and reserved ranges prevents
    server-side request forgery (SSRF) against internal services and the cloud
    metadata endpoint (169.254.169.254).
    """
    try:
        addr_infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # Unresolvable host: let the HTTP client surface the failure normally.
        return False

    for info in addr_infos:
        ip_text = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            continue
        blocked_flags = (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_reserved,
            ip.is_multicast,
            ip.is_unspecified,
        )
        if any(blocked_flags):
            return True
    return False


def download_file(url: str) -> bytes:
    """Download a file from an external URL with SSRF protections.

    Only ``http``/``https`` URLs that resolve to public hosts are permitted.
    The ``file://`` scheme and requests targeting private, loopback, or
    link-local addresses are rejected to prevent local file disclosure and
    server-side request forgery. Downloads are bounded by a timeout and a
    maximum size, and redirects are not followed (a redirect could otherwise
    bypass the address checks).
    """
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_DOWNLOAD_SCHEMES:
        raise ValueError(f"Unsupported URL scheme for file download: {parsed.scheme or '<none>'}")

    host = parsed.hostname
    if not host:
        raise ValueError("File download URL must include a host.")

    if _host_resolves_to_blocked_ip(host):
        raise ValueError("Refusing to download from a non-public (internal) address.")

    with (
        httpx.Client(timeout=_DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=False) as client,
        client.stream("GET", url) as response,
    ):
        response.raise_for_status()

        declared_length = response.headers.get("Content-Length")
        if declared_length is not None and declared_length.isdigit() and int(declared_length) > _MAX_DOWNLOAD_BYTES:
            raise ValueError("Remote file exceeds the maximum allowed size.")

        chunks: list[bytes] = []
        downloaded = 0
        for chunk in response.iter_bytes():
            downloaded += len(chunk)
            if downloaded > _MAX_DOWNLOAD_BYTES:
                raise ValueError("Remote file exceeds the maximum allowed size.")
            chunks.append(chunk)

    return b"".join(chunks)


def to_camel(string: str) -> str:
    """Convert string to camel format."""
    if "_" not in string or string.startswith("_"):
        return string
    return "".join([x.capitalize() if i > 0 else x for i, x in enumerate(string.split("_"))])


def env_truthy(name: str, default: str = "false") -> bool:
    """Return True when an environment flag is set to a truthy value (true/yes/1/on)."""
    return os.getenv(name, default).strip().lower() in _TRUTHY_VALUES


def describe_database_target(app: Flask) -> tuple[str, str]:
    """Return a ``(mode, safe_dsn)`` tuple describing the active database connection.

    ``mode`` is one of ``cloud-sql-proxy-sidecar``, ``cloud-sql-connector`` or
    ``direct``. ``safe_dsn`` is the SQLAlchemy URL with any password masked so it
    is safe to log.
    """
    if app.config.get("CLOUD_SQL_PROXY_SIDECAR", False):
        mode = "cloud-sql-proxy-sidecar"
    elif app.config.get("DB_INSTANCE_CONNECTION_NAME"):
        mode = "cloud-sql-connector"
    else:
        mode = "direct"

    try:
        safe_dsn = make_url(app.config["SQLALCHEMY_DATABASE_URI"]).render_as_string(hide_password=True)
    except Exception:  # pragma: no cover - defensive only; logging must never block startup
        safe_dsn = "<unavailable>"

    return mode, safe_dsn


def _log_sidecar_socket_peer(dbapi_connection) -> None:
    """Best-effort: log the TCP peer of the raw DBAPI socket (the sidecar).

    Different drivers expose the underlying socket differently:

    * ``pg8000`` keeps a ``socket.socket`` on ``_usock``.
    * ``psycopg`` (v3) exposes the libpq socket file descriptor via
      ``pgconn.socket``.
    """
    # pg8000 exposes the raw socket object directly.
    socket_obj = getattr(dbapi_connection, "_usock", None) or getattr(
        getattr(dbapi_connection, "_c", None), "_usock", None
    )
    if socket_obj is not None:
        with contextlib.suppress(OSError):
            logger.debug("Sidecar socket peer (client-side evidence): %s", socket_obj.getpeername())
        return

    # psycopg (v3) exposes the libpq socket file descriptor; wrap a dup of it so
    # closing our view never disturbs the live connection.
    fd = getattr(getattr(dbapi_connection, "pgconn", None), "socket", None)
    if isinstance(fd, int) and fd >= 0:
        with contextlib.suppress(OSError), socket.socket(fileno=os.dup(fd)) as socket_view:
            logger.debug("Sidecar socket peer (client-side evidence): %s", socket_view.getpeername())


def log_sidecar_connection_evidence(engine, port: str) -> None:
    """Register a one-time listener that logs evidence traffic flows via the sidecar.

    The Cloud SQL Auth Proxy sidecar listens on ``127.0.0.1:<port>`` and performs
    IAM authentication. A successful localhost connection together with the
    server-side session details below are strong evidence the connection is
    tunneled through the proxy rather than reaching the database by another path.
    """
    state = {"logged": False}

    @event.listens_for(engine, "connect")
    def _log_evidence_on_connect(dbapi_connection, _connection_record):  # pragma: no cover - requires a live DB
        if state["logged"]:
            return
        state["logged"] = True

        logger.debug("Connecting through Cloud SQL Auth Proxy sidecar at 127.0.0.1:%s", port)

        # Client-side evidence: the underlying TCP socket peer should be the sidecar.
        _log_sidecar_socket_peer(dbapi_connection)

        # Server-side evidence: the IAM user and the actual Cloud SQL backend address.
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute(
                "SELECT current_user, session_user, current_database(), inet_server_addr()::text, inet_server_port()"
            )
            current_user, session_user, database, server_addr, server_port = cursor.fetchone()
            cursor.close()
            logger.info(
                "Database connected via Cloud SQL Auth Proxy sidecar \u2014 current_user=%s database=%s backend=%s:%s",
                current_user,
                database,
                server_addr,
                server_port,
            )
            logger.debug("Sidecar session detail: session_user=%s", session_user)
        except Exception as exc:  # pragma: no cover - evidence logging must never break startup
            logger.debug("Unable to gather sidecar session evidence: %s", exc)
