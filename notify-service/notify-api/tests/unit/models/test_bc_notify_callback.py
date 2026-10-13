"""Tests for BC Notify callback models."""

from datetime import UTC, datetime
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from notify_api.models import BCNotifyCallback, BCNotifyCallbackRequest


class TestBCNotifyCallbackRequest:
    """Tests for parsing BC Notify callback events."""

    @staticmethod
    def test_parses_status_changed_event_payload():
        payload = {
            "event": "notification.status.changed",
            "notificationId": "notification-id-test",
            "tenantId": "your-tenant-id",
            "data": {
                "notifyId": "notify-id-test",
                "status": "completed",
                "statusDisplayName": "Completed",
                "channel": "EMAIL",
                "createdAt": "2026-10-08T17:02:11.123Z",
                "updatedAt": "2026-10-08T17:02:14.456Z",
            },
            "deliveredAt": "2026-10-08T17:02:15.012Z",
        }

        callback = BCNotifyCallbackRequest.model_validate(payload)

        assert callback.event == "notification.status.changed"
        assert callback.notification_id == payload["notificationId"]
        assert callback.tenant_id == "your-tenant-id"
        assert callback.data.notify_id == payload["data"]["notifyId"]
        assert callback.data.status == "completed"
        assert callback.data.status_display_name == "Completed"
        assert callback.data.channel == "EMAIL"
        assert callback.data.created_at == datetime(2026, 10, 8, 17, 2, 11, 123000, tzinfo=UTC)
        assert callback.data.updated_at == datetime(2026, 10, 8, 17, 2, 14, 456000, tzinfo=UTC)
        assert callback.delivered_at == datetime(2026, 10, 8, 17, 2, 15, 12000, tzinfo=UTC)

    @staticmethod
    def test_channel_must_be_a_single_supported_value():
        with pytest.raises(ValidationError):
            BCNotifyCallbackRequest.model_validate({
                "event": "notification.status.changed",
                "notificationId": "notification-123",
                "tenantId": "tenant-456",
                "data": {
                    "notifyId": "notify-789",
                    "status": "completed",
                    "statusDisplayName": "Completed",
                    "channel": "EMAIL, SMS",
                    "createdAt": "2026-10-08T17:02:11.123Z",
                    "updatedAt": "2026-10-08T17:02:14.456Z",
                },
                "deliveredAt": "2026-10-08T17:02:15.012Z",
            })


class TestBCNotifyCallback:
    """Tests for persistence mapping of BC Notify callback events."""

    @staticmethod
    def test_save_maps_event_payload_to_database_record():
        callback = BCNotifyCallbackRequest.model_validate({
            "event": "notification.status.changed",
            "notificationId": "notification-123",
            "tenantId": "tenant-456",
            "data": {
                "notifyId": "notify-789",
                "status": "completed",
                "statusDisplayName": "Completed",
                "channel": "EMAIL",
                "createdAt": "2026-10-08T17:02:11.123Z",
                "updatedAt": "2026-10-08T17:02:14.456Z",
            },
            "deliveredAt": "2026-10-08T17:02:15.012Z",
        })

        with patch("notify_api.models.bc_notify_callback.db.session") as mock_session:
            BCNotifyCallback.save(callback)

        mock_session.add.assert_called_once()
        record = mock_session.add.call_args.args[0]
        assert isinstance(record, BCNotifyCallback)
        assert record.event == callback.event
        assert record.notification_id == "notification-123"
        assert record.tenant_id == "tenant-456"
        assert record.notify_id == "notify-789"
        assert record.status == "completed"
        assert record.status_display_name == "Completed"
        assert record.channel == "EMAIL"
        assert record.created_at == callback.data.created_at
        assert record.updated_at == callback.data.updated_at
        assert record.delivered_at == callback.delivered_at

    @staticmethod
    def test_table_name():
        assert BCNotifyCallback.__tablename__ == "bc_notify_callback"
