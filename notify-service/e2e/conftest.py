"""Fixtures that run notify-api and notify-delivery in one process against a shared SQLite database.

Pub/Sub and BC Notify are the only faked boundaries; routing, validation, persistence and
the callback lifecycle run through the real application code.
"""

from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
import sys
import tempfile
import time

import pytest

# Run against the sibling sources so either package's venv works, even with a stale installed copy.
_SERVICE_ROOT = Path(__file__).resolve().parent.parent
for _src in (
    _SERVICE_ROOT / "notify-delivery" / "src",
    _SERVICE_ROOT / "notify-api" / "src",
):
    sys.path.insert(0, str(_src))

try:
    distribution("notify_delivery")
except PackageNotFoundError:
    # notify_delivery.metadata reads its own package metadata; fake it when the package isn't installed.
    _dist_info = Path(tempfile.mkdtemp()) / "notify_delivery-0.dist-info"
    _dist_info.mkdir()
    (_dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: notify-delivery\nVersion: 0\n"
    )
    sys.path.append(str(_dist_info.parent))

from notify_api import create_app as create_api_app  # noqa: E402
from notify_api import jwt as api_jwt
from notify_api.config import UnitTestingConfig as ApiUnitTestingConfig
from notify_api.config import config as api_config
from notify_api.models import db
from notify_delivery import create_app as create_delivery_app
from notify_delivery.config import UnitTestingConfig as DeliveryUnitTestingConfig
from notify_delivery.config import (
    UnitTestingSMTPConfig as DeliveryUnitTestingSMTPConfig,
)
from notify_delivery.config import config as delivery_config

BC_NOTIFY_TOPIC = "projects/e2e/topics/bc-notify"
SMTP_TOPIC = "projects/e2e/topics/smtp"
SMTP_FROM = "notify@e2e.gov.bc.ca"


@pytest.fixture(scope="session")
def database_uri(tmp_path_factory):
    """Return a file-backed SQLite URI so both apps see the same data."""
    return f"sqlite:///{tmp_path_factory.mktemp('e2e') / 'notify.db'}"


@pytest.fixture(scope="session")
def api_app(database_uri):
    """Return the notify-api app with BC Notify as the default provider."""

    class E2EApiConfig(ApiUnitTestingConfig):
        SQLALCHEMY_DATABASE_URI = database_uri
        BC_NOTIFY_ENABLE = True
        DELIVERY_BC_NOTIFY_TOPIC = BC_NOTIFY_TOPIC
        DELIVERY_SMTP_TOPIC = SMTP_TOPIC

    api_config["e2e"] = E2EApiConfig
    app = create_api_app("e2e")
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture(scope="session")
def delivery_app(database_uri, api_app):  # noqa: ARG001  (api_app creates the schema first)
    """Return the notify-delivery app pointing at the same database."""

    class E2EDeliveryConfig(DeliveryUnitTestingConfig):
        SQLALCHEMY_DATABASE_URI = database_uri
        VERIFY_PUBSUB_VIA_JWT = False
        DEPLOYMENT_ENV = "production"
        BC_NOTIFY_API_URL = "https://bc-notify.example.test"
        BC_NOTIFY_API_KEY = "e2e-key"  # noqa: S105

    delivery_config["e2e"] = E2EDeliveryConfig
    return create_delivery_app("e2e")


@pytest.fixture(scope="session")
def delivery_smtp_app(database_uri, api_app):  # noqa: ARG001
    """Return the notify-delivery app in OCP mode, where the SMTP worker is mounted."""

    class E2EDeliverySMTPConfig(DeliveryUnitTestingSMTPConfig):
        SQLALCHEMY_DATABASE_URI = database_uri
        VERIFY_PUBSUB_VIA_JWT = False
        DEPLOYMENT_ENV = "production"
        MAIL_SERVER = "smtp.e2e.test"
        MAIL_PORT = 25
        MAIL_FROM_ID = SMTP_FROM

    delivery_config["e2e-smtp"] = E2EDeliverySMTPConfig
    return create_delivery_app("e2e-smtp")


@pytest.fixture
def delivery_smtp_client(delivery_smtp_app):
    """Return a notify-delivery (SMTP mode) test client."""
    return delivery_smtp_app.test_client()


@pytest.fixture(autouse=True)
def clean_tables(api_app):
    """Empty every table after each test; SQLite reuses ids, so stale history rows would collide."""
    yield
    with api_app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def api_client(api_app):
    """Return a notify-api test client."""
    return api_app.test_client()


@pytest.fixture
def delivery_client(delivery_app):
    """Return a notify-delivery test client."""
    return delivery_app.test_client()


@pytest.fixture
def auth_headers():
    """Return a factory for bearer headers carrying the given realm roles."""

    def _headers(*roles: str) -> dict:
        claims = {
            "realm_access": {"roles": list(roles)},
            "aud": "example",
            "iss": "https://example.localdomain/auth/realms/example",
            "sub": "e2e-user",
            "exp": int(time.time()) + 60,
        }
        token = api_jwt.create_jwt(
            claims=claims, header={"kid": "flask-jwt-oidc-test-client"}
        )
        return {"Authorization": f"Bearer {token}"}

    return _headers
