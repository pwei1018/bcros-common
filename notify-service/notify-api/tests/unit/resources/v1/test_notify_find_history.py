from http import HTTPStatus
from unittest.mock import MagicMock, patch

from notify_api.models import Notification


def test_find_notification_returns_notification(client, session, jwt):
    """Assert that find_notification returns from Notification table if present."""
    token = jwt.create_jwt(
        claims={
            "realm_access": {"roles": ["system"]},
            "aud": "example",
            "iss": "https://example.localdomain/auth/realms/example",
            "sub": "test-user",
        },
        header={"kid": "flask-jwt-oidc-test-client"},
    )
    headers = {"Authorization": f"Bearer {token}"}
    notify_id = 123

    # Mock Notification found
    with patch.object(Notification, "find_notification_by_id") as mock_find:
        mock_notification = MagicMock()
        mock_notification.json = {"id": notify_id, "type": "notification"}
        mock_find.return_value = mock_notification

        response = client.get(f"/api/v1/notify/{notify_id}", headers=headers)

        assert response.status_code == HTTPStatus.OK
        assert response.json["type"] == "notification"


def test_find_notification_returns_history_fallback(client, session, jwt):
    """Assert that find_notification falls back to NotificationHistory."""
    token = jwt.create_jwt(
        claims={
            "realm_access": {"roles": ["system"]},
            "aud": "example",
            "iss": "https://example.localdomain/auth/realms/example",
            "sub": "test-user",
        },
        header={"kid": "flask-jwt-oidc-test-client"},
    )
    headers = {"Authorization": f"Bearer {token}"}
    notify_id = 123

    # Mock Notification not found, History found
    with (
        patch.object(Notification, "find_notification_by_id", return_value=None),
        patch("notify_api.resources.v1.notify.NotificationHistory") as mock_history,
    ):
        mock_history_instance = MagicMock()
        mock_history_instance.json = {
            "id": 999,
            "notificationId": notify_id,
            "recipients": "test@example.com",
            # Fields requested by user
            "notifyProvider": None,
            "notifyStatus": "QUEUED",
            "notifyType": None,
            "requestBy": None,
            "requestDate": None,
            "sentDate": None,
            "gc_notify_status": "sent",
        }
        mock_history.find_by_notification_id.return_value = mock_history_instance

        response = client.get(f"/api/v1/notify/{notify_id}", headers=headers)

        assert response.status_code == HTTPStatus.OK
        data = response.json
        assert data["notificationId"] == notify_id
        assert data["recipients"] == "test@example.com"
        assert data["notifyStatus"] == "QUEUED"
        # Check new/fallback fields exist
        assert "gc_notify_status" in data

        mock_history.find_by_notification_id.assert_called_with(int(notify_id))


def test_find_notification_not_found(client, session, jwt):
    """Assert 404 if neither found."""
    token = jwt.create_jwt(
        claims={
            "realm_access": {"roles": ["system"]},
            "aud": "example",
            "iss": "https://example.localdomain/auth/realms/example",
            "sub": "test-user",
        },
        header={"kid": "flask-jwt-oidc-test-client"},
    )
    headers = {"Authorization": f"Bearer {token}"}
    notify_id = 123

    with (
        patch.object(Notification, "find_notification_by_id", return_value=None),
        patch("notify_api.resources.v1.notify.NotificationHistory") as mock_history,
    ):
        mock_history.find_by_notification_id.return_value = None

        response = client.get(f"/api/v1/notify/{notify_id}", headers=headers)

        assert response.status_code == HTTPStatus.NOT_FOUND


def test_find_notifications_combines_results(client, session, jwt):
    """Assert that find_notifications merges results from Notification and NotificationHistory."""
    token = jwt.create_jwt(
        claims={
            "realm_access": {"roles": ["system"]},
            "aud": "example",
            "iss": "https://example.localdomain/auth/realms/example",
            "sub": "test-user",
        },
        header={"kid": "flask-jwt-oidc-test-client"},
    )
    headers = {"Authorization": f"Bearer {token}"}
    id_1 = 1
    id_2 = 2
    notify_id = 123
    expected_count = 2

    with (
        patch.object(Notification, "find_notifications_by_status") as mock_find_notifications,
        patch("notify_api.models.NotificationHistory") as mock_history,
    ):
        # Mock Notification results
        mock_notif_1 = MagicMock()
        mock_notif_1.json = {"id": id_1, "notifyStatus": "FAILURE"}
        mock_find_notifications.return_value = [mock_notif_1]

        # Mock History results
        mock_hist_1 = MagicMock()
        mock_hist_1.json = {"id": id_2, "notifyStatus": "FAILURE", "notificationId": notify_id}
        mock_history.find_by_status.return_value = [mock_hist_1]

        response = client.get("/api/v1/notify/status/FAILURE", headers=headers)

        assert response.status_code == HTTPStatus.OK
        data = response.json
        assert "notifications" in data
        assert len(data["notifications"]) == expected_count

        ids = [item["id"] for item in data["notifications"]]
        assert id_1 in ids
        assert id_2 in ids

        mock_find_notifications.assert_called_with("FAILURE")
        mock_history.find_by_status.assert_called_with("FAILURE")
