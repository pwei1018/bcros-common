from datetime import datetime
from unittest.mock import patch

from notify_api.models import Notification, NotificationHistory


def test_notification_history_has_notification_id_column(session):
    """Assert that the NotificationHistory model has the new column."""
    # This checks the SQLAlchemy model definition
    assert hasattr(NotificationHistory, "notification_id")

    # We can also check if the column is defined in the table metadata mock
    # (Since we are using sqlite in tests, the table schema might not update unless we run migration there too,
    # but SQLAlchemy model binding should be there)


def test_create_history_populates_notification_id(session):
    """Assert that create_history uses the notification.id."""
    from unittest.mock import Mock

    notify_id = 123

    # Use Mock instead of real Notification to avoid SQLAlchemy issues
    notification = Mock()
    notification.recipients = "test@example.com"
    notification.request_by = "tester"
    notification.type_code = "EMAIL"
    notification.status_code = "PENDING"
    notification.provider_code = "GC_NOTIFY"
    notification.id = notify_id
    notification.request_date = datetime.now()
    notification.sent_date = datetime.now()

    # Mock content
    content = Mock()
    content.subject = "Test Subject"
    notification.content = [content]

    # Mock session
    with patch("notify_api.models.notification_history.db.session") as mock_session:
        # Create history
        NotificationHistory.create_history(notification)

        # Verify it was added to session
        mock_session.add.assert_called_once()
        args = mock_session.add.call_args[0]
        added_history = args[0]

        assert added_history.notification_id == notify_id
        assert added_history.json["notificationId"] == notify_id
