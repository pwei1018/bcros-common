# Copyright © 2024 Province of British Columbia
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
"""Prove the ORM models round-trip on both PostgreSQL drivers (psycopg and pg8000).

The service runs on ``postgresql+psycopg`` behind the Cloud SQL Auth Proxy sidecar
and on ``postgresql+pg8000`` via the cloud-sql-connector. Because the same models
are shared by both notify-api and notify-delivery, they must behave identically on
either driver.

These tests connect to a real PostgreSQL instance (for example the docker-compose
service in the repository root) and verify that every driver-sensitive column type
used by the models round-trips correctly:

* ``LargeBinary`` / BYTEA  -> must return real ``bytes`` (psycopg2's ``memoryview``
  quirk does not apply to psycopg3 or pg8000, and the attachment bytes are later
  base64-encoded / attached to emails, which requires ``bytes``).
* native ``Enum``          -> must return the Python enum member.
* ``DateTime(timezone=True)`` / timestamptz -> must stay timezone-aware.

They are skipped automatically when the driver or database is unavailable, so the
default (fully mocked) unit run is never affected. To exercise them, start the
docker-compose Postgres and run ``pytest -m integration``.
"""

from __future__ import annotations

from datetime import UTC, datetime
import os

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from notify_api.models import Attachment, Content, Notification
from notify_api.models.db import db

pytestmark = pytest.mark.integration

# A distinctive payload containing every byte value (including NULs and 0xFF) so a
# driver that mishandles binary as text would corrupt it and fail the assertion.
_BINARY_PAYLOAD = bytes(range(256)) + b"\x00PDF\xff\x00"

# Per-driver connect args that keep the reachability probe fast so an absent
# database results in a quick skip rather than a long hang.
_CONNECT_ARGS = {
    "psycopg": {"connect_timeout": 3},
    "pg8000": {"timeout": 3},
}


def _dsn(driver: str) -> str:
    """Build a DSN for the driver, preferring DATABASE_TEST_* then NOTIFY_DATABASE_*."""
    user = os.getenv("DATABASE_TEST_USERNAME") or os.getenv("NOTIFY_DATABASE_USERNAME", "notifyuser")
    password = os.getenv("DATABASE_TEST_PASSWORD") or os.getenv("NOTIFY_DATABASE_PASSWORD", "notify")
    host = os.getenv("DATABASE_TEST_HOST", "localhost")
    port = os.getenv("DATABASE_TEST_PORT", "5433")
    name = os.getenv("DATABASE_TEST_NAME") or os.getenv("NOTIFY_DATABASE_NAME", "notify")
    return f"postgresql+{driver}://{user}:{password}@{host}:{port}/{name}"


def _engine_or_skip(driver: str, schema: str):
    """Return an engine pinned to ``schema``, or skip when the driver/database is unavailable.

    The ``search_path`` listener is attached *before the first connection is made*
    so that every physical connection — including the reachability probe and the
    ones ``create_all`` reuses from the pool — is confined to the isolated schema.
    Registering it later (after a pooled connection already exists) would let DDL
    fall back to ``public`` and pollute the shared database, because the ``connect``
    event only fires for brand-new connections, not for pooled reuse.
    """
    pytest.importorskip(driver, reason=f"{driver} driver not installed")

    engine = create_engine(_dsn(driver), connect_args=_CONNECT_ARGS[driver])

    @event.listens_for(engine, "connect")
    def _set_search_path(dbapi_connection, _connection_record):  # pragma: no cover - fires per connect
        cursor = dbapi_connection.cursor()
        # The isolated schema is first so unqualified CREATE TABLE / CREATE TYPE
        # land there; public stays as a read-only fallback and is never written to.
        cursor.execute(f'SET search_path TO "{schema}", public')
        cursor.close()

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL not reachable via {driver}: {exc.__class__.__name__}")
    return engine


def _prepare_isolated_schema(engine, schema: str) -> None:
    """Create a clean, isolated schema and route all model DDL/DML into it.

    A dedicated schema keeps the test non-destructive (it never touches existing
    data) and lets ``create_all`` build the native ENUM types and tables in one
    place that is dropped wholesale during teardown. The engine already pins every
    connection to this schema via the ``search_path`` listener set up in
    ``_engine_or_skip``.
    """
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    db.metadata.create_all(engine)


@pytest.mark.parametrize("driver", ["psycopg", "pg8000"])
def test_models_round_trip_through_driver(driver):
    """The full Notification -> Content -> Attachment chain persists and reloads intact."""
    schema = f"driver_compat_{driver}"
    engine = _engine_or_skip(driver, schema)
    try:
        _prepare_isolated_schema(engine, schema)

        requested_at = datetime.now(UTC)
        with Session(engine) as session:
            notification = Notification(
                recipients="round.trip@example.com",
                request_by="driver-compat",
                request_date=requested_at,
                sent_date=requested_at,
                type_code=Notification.NotificationType.EMAIL,
                status_code=Notification.NotificationStatus.PENDING,
                provider_code=Notification.NotificationProvider.GC_NOTIFY,
            )
            session.add(notification)
            session.flush()

            content = Content(subject="subject", body="body", notification_id=notification.id)
            session.add(content)
            session.flush()

            attachment = Attachment(
                file_name="doc.pdf",
                file_bytes=_BINARY_PAYLOAD,
                attach_order=1,
                content_id=content.id,
            )
            session.add(attachment)
            session.commit()

            notification_id = notification.id
            attachment_id = attachment.id

        # A fresh session forces a real read from the database rather than serving
        # the just-added instances from the identity map.
        with Session(engine) as session:
            stored_attachment = session.get(Attachment, attachment_id)
            stored_notification = session.get(Notification, notification_id)

            # BYTEA must come back as real bytes on both drivers.
            assert isinstance(stored_attachment.file_bytes, bytes | bytearray)
            assert bytes(stored_attachment.file_bytes) == _BINARY_PAYLOAD

            # Native ENUM columns round-trip to their Python enum members.
            assert stored_notification.type_code == Notification.NotificationType.EMAIL
            assert stored_notification.status_code == Notification.NotificationStatus.PENDING
            assert stored_notification.provider_code == Notification.NotificationProvider.GC_NOTIFY

            # timestamptz preserves timezone awareness through the driver.
            assert stored_notification.request_date.tzinfo is not None
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()
