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
"""Common setup and fixtures for the pytest suite used by this service."""

from contextlib import contextmanager
import datetime
from functools import cache
from unittest.mock import Mock, patch

import pytest

from notify_api import create_app
from notify_api import jwt as _jwt
from notify_api.models import db as _db

from . import FROZEN_DATETIME


# Optimized helper functions for mock creation
@cache
def _create_mock_query():
    """Create a cached mock query object for reuse."""
    mock_query = Mock()
    mock_query.filter = Mock(return_value=mock_query)
    mock_query.filter_by = Mock(return_value=mock_query)
    mock_query.all = Mock(return_value=[])
    mock_query.first = Mock(return_value=None)
    mock_query.count = Mock(return_value=0)
    mock_query.order_by = Mock(return_value=mock_query)
    mock_query.limit = Mock(return_value=mock_query)
    mock_query.offset = Mock(return_value=mock_query)
    return mock_query


def _create_mock_session():
    """Create a standardized mock session with common operations."""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.flush = Mock()
    mock_session.delete = Mock()
    mock_session.close = Mock()
    mock_session.begin_nested = Mock()
    mock_session.refresh = Mock()
    mock_session.query = Mock(return_value=_create_mock_query())
    return mock_session


@contextmanager
def not_raises(exception):
    """Corallary to the pytest raises builtin.

    Assures that an exception is NOT thrown.
    """
    try:
        yield
    except exception:
        raise pytest.fail(f"DID RAISE {exception}")  # pylint: disable=raise-missing-from


# fixture to freeze utcnow to a fixed date-time
@pytest.fixture
def freeze_datetime_utcnow(monkeypatch):
    """Fixture to return a static time for utcnow()."""

    class _Datetime:
        @classmethod
        def utcnow(cls):
            """UTC NOW"""
            return FROZEN_DATETIME

    monkeypatch.setattr(datetime, "datetime", _Datetime)


@pytest.fixture(scope="session")
def app():
    """Return a session-wide application configured in TEST mode."""
    _app = create_app("unitTesting")

    with _app.app_context():
        yield _app


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    """Return a session-wide Flask test client."""
    return app.test_client()


@pytest.fixture(scope="session")
def jwt():
    """Return a session-wide jwt manager."""
    return _jwt


@pytest.fixture(scope="session")
def db(app, request):  # pylint: disable=redefined-outer-name
    """Session-wide mock test database."""
    mock_db = Mock()
    mock_db.app = app
    mock_db.session = _create_mock_session()

    # Mock database management operations
    mock_db.create_all = Mock()
    mock_db.drop_all = Mock()

    def teardown():
        pass  # No real cleanup needed for mock

    request.addfinalizer(teardown)
    return mock_db


@pytest.fixture
def session(db, request):  # pylint: disable=redefined-outer-name
    """Return a function-scoped mock session."""
    # Create a fresh mock session for each test
    mock_session = _create_mock_session()

    def teardown():
        pass  # No real cleanup needed for mock

    request.addfinalizer(teardown)
    return mock_session


# Enhanced fixtures for comprehensive testing with mocks
@pytest.fixture
def mock_db_session():
    """Mock database session for enhanced testing with context manager."""
    mock_session = _create_mock_session()
    with patch("notify_api.models.db.db.session", mock_session):
        yield mock_session


# Optimized model fixtures
@pytest.fixture(scope="session")
def mock_notification_model():
    """Mock Notification model class for enhanced testing."""
    with patch("notify_api.models.Notification") as mock_model:
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.recipients = "test@example.com"
        mock_instance.status_code = "PENDING"
        mock_instance.provider_code = "GC_NOTIFY"
        mock_instance.request_date = datetime.datetime.now(datetime.UTC)
        mock_instance.request_by = "test_user"
        mock_instance.type_code = "EMAIL"
        mock_instance.json = {"id": 1, "recipients": "test@example.com", "status": "PENDING"}

        mock_model.return_value = mock_instance
        mock_model.find_notification_by_id.return_value = mock_instance
        mock_model.find_notifications_by_status.return_value = [mock_instance]
        mock_model.query.filter.return_value.all.return_value = [mock_instance]
        yield mock_model


@pytest.fixture(scope="session")
def mock_content_model():
    """Mock Content model class for enhanced testing."""
    with patch("notify_api.models.Content") as mock_model:
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.subject = "Test Subject"
        mock_instance.body = "Test body content"
        mock_instance.attachments = []
        mock_instance.attachment_name = None
        mock_instance.notification_id = 1
        mock_instance.json = {"id": 1, "subject": "Test Subject", "body": "Test body content"}

        mock_model.return_value = mock_instance
        yield mock_model


@pytest.fixture(scope="session")
def mock_notify_service():
    """Mock NotifyService for comprehensive testing."""
    with patch("notify_api.services.notify_service.NotifyService") as mock_service_class:
        mock_service = Mock()

        # Mock service methods
        mock_service.get_provider.return_value = "GC_NOTIFY"
        mock_service.send_notification.return_value = {"id": 1, "status": "QUEUED"}
        mock_service.validate_email.return_value = True
        mock_service.get_notification_by_id.return_value = None
        mock_service.get_notifications_by_status.return_value = []

        mock_service_class.return_value = mock_service
        yield mock_service


# Consolidated database and provider fixtures
@pytest.fixture(scope="session")
def mock_providers():
    """Mock notification providers."""
    providers = {"gc_notify": Mock(), "smtp": Mock(), "housing": Mock()}

    for provider in providers.values():
        provider.send.return_value = {"success": True, "id": "mock-123"}

    with patch.dict("notify_api.services.providers", providers):
        yield providers


# Optimized sample data fixtures (session-scoped for immutable data)
@pytest.fixture(scope="session")
def sample_notification_data():
    """Sample notification data for testing."""
    return {
        "recipients": "test@example.com",
        "requestBy": "test_user",
        "content": {"subject": "Test Subject", "body": "Test body content", "attachments": []},
        "notifyType": "EMAIL",
    }


@pytest.fixture(scope="session")
def sample_content_data():
    """Sample content data for testing."""
    return {"subject": "Test Email Subject", "body": "This is test email content", "attachments": []}


@pytest.fixture(scope="session")
def sample_attachment_data():
    """Sample attachment data for testing."""
    return {
        "file_name": "document.pdf",
        "file_bytes": b"fake_pdf_content",
        "attach_order": 1,
        "content_id": 1,
    }


@pytest.fixture(scope="session")
def sample_safe_list_emails():
    """Sample safe list emails for testing."""
    return ["safe1@example.com", "safe2@example.com", "admin@test.com"]


@pytest.fixture(scope="session")
def sample_html_notification_data():
    """Sample HTML notification data for testing."""
    return {
        "recipients": "test@example.com",
        "requestBy": "test_user",
        "content": {"subject": "HTML Test Subject", "body": "<p>This is <b>HTML</b> content</p>", "attachments": []},
        "notifyType": "EMAIL",
    }


# Additional optimized model fixtures
@pytest.fixture(scope="session")
def mock_safe_list():
    """Mock SafeList model."""
    with patch("notify_api.models.SafeList") as mock_safe_list_class:
        mock_safe_list = Mock()
        mock_safe_list.is_in_safe_list.return_value = True
        mock_safe_list.email = "safe@example.com"
        mock_safe_list_class.return_value = mock_safe_list
        mock_safe_list_class.find_by_email.return_value = mock_safe_list
        yield mock_safe_list


@pytest.fixture
def mock_notification():
    """Mock Notification model (function-scoped for test isolation)."""
    with patch("notify_api.models.Notification") as mock_notification_class:
        mock_notification = Mock()
        mock_notification.id = 1
        mock_notification.recipients = "test@example.com"
        mock_notification.status_code = "PENDING"
        mock_notification.provider_code = "GC_NOTIFY"
        mock_notification_class.return_value = mock_notification
        mock_notification_class.find_notification_by_id.return_value = mock_notification
        yield mock_notification


@pytest.fixture
def fully_mocked_environment(mock_db_session, mock_providers, mock_safe_list):
    """Comprehensive mock environment for integration testing."""
    return {"database": mock_db_session, "providers": mock_providers, "safe_list": mock_safe_list}


# Additional comprehensive fixtures for enhanced testing


@pytest.fixture(scope="session")
def mock_attachment_model():
    """Mock Attachment model for testing."""
    with patch("notify_api.models.Attachment") as mock_model:
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.file_name = "test.pdf"
        mock_instance.file_bytes = b"test content"
        mock_instance.attach_order = 1
        mock_instance.content_id = 1

        mock_model.return_value = mock_instance
        yield mock_model


@pytest.fixture(scope="session")
def mock_notification_history_model():
    """Mock NotificationHistory model for testing."""
    with patch("notify_api.models.NotificationHistory") as mock_model:
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.recipients = "test@example.com"
        mock_instance.subject = "Test Subject"
        mock_instance.type_code = "EMAIL"
        mock_instance.status_code = "DELIVERED"
        mock_instance.provider_code = "GC_NOTIFY"
        mock_instance.sent_date = datetime.datetime.now(datetime.UTC)
        mock_instance.request_date = datetime.datetime.now(datetime.UTC)
        mock_instance.gc_notify_response_id = "gc_123"

        mock_model.return_value = mock_instance
        yield mock_model


# Service and infrastructure mocks
@pytest.fixture(scope="session")
def mock_gcp_queue():
    """Mock GCP Queue operations."""
    with patch("notify_api.services.gcp_queue.publisher.GcpQueuePublisher") as mock_publisher:
        mock_instance = Mock()
        mock_instance.publish.return_value = "publish_future_mock"
        mock_publisher.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="session")
def mock_current_app():
    """Mock Flask current_app."""
    with patch("notify_api.services.notify_service.current_app") as mock_app:
        mock_app.config.get.side_effect = lambda key, default=None: {
            "DEVELOPMENT": True,
            "DELIVERY_GCNOTIFY_TOPIC": "test-gc-topic",
            "DELIVERY_SMTP_TOPIC": "test-smtp-topic",
            "DELIVERY_GCNOTIFY_HOUSING_TOPIC": "test-housing-topic",
        }.get(key, default)
        yield mock_app


# Utility fixtures
@pytest.fixture(scope="session")
def mock_email_validator():
    """Mock email validation functions."""
    min_email_length = 5

    def validate_email(email):
        return "@" in email and "." in email and len(email) > min_email_length

    return validate_email


@pytest.fixture(scope="session")
def mock_html_detector():
    """Mock HTML content detection."""

    def is_html_content(content):
        if not content:
            return False
        return any(tag in content.lower() for tag in ["<p>", "<div>", "<html>", "<body>", "<script>"])

    return is_html_content


@pytest.fixture(scope="session")
def performance_test_data():
    """Generate test data for performance testing."""
    return {
        "batch_size": 100,
        "notifications": [{"id": i, "recipients": f"user{i}@example.com", "status": "PENDING"} for i in range(100)],
        "expected_processing_time": 1.0,  # seconds
    }


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging functionality."""
    with patch("notify_api.services.notify_service.logger") as mock_log:
        yield mock_log
