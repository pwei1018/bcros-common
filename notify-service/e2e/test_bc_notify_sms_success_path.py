"""E2E SMS success path: request -> validate -> queue -> send -> callback -> completed -> archived."""

import base64
from http import HTTPStatus
from unittest.mock import patch

import pytest
from notify_api.models import (
    BCNotifyCallback,
    Content,
    Notification,
    NotificationHistory,
    db,
)
from notify_api.services.gcp_queue import queue
from notify_api.utils.enums import Role

from conftest import (
    BC_NOTIFY_API_KEY,
    BC_NOTIFY_HOUSING_API_KEY,
    BC_NOTIFY_HOUSING_SMS_TOPIC,
    BC_NOTIFY_SMS_TOPIC,
)

PROVIDER_RESPONSE_ID = "bc-notify-sms-response-1"
RECIPIENT = "250-555-0123"
RECIPIENT_E164 = "+12505550123"
SMS_BODY = "E2E SMS body"


def _pubsub_push(payload: bytes) -> dict:
    """Wrap a published payload in the envelope Pub/Sub pushes to a subscription."""
    return {
        "subscription": "projects/e2e/subscriptions/bc-notify-sms",
        "message": {"data": base64.b64encode(payload).decode()},
    }


def _callback_body(status: str) -> dict:
    return {
        "event": "notification.status.changed",
        "notificationId": "bc-notify-sms-notification-1",
        "tenantId": "tenant-1",
        "data": {
            "notifyId": PROVIDER_RESPONSE_ID,
            "status": status,
            "statusDisplayName": status.title(),
            "channel": "SMS",
            "createdAt": "2026-01-01T10:00:00Z",
            "updatedAt": "2026-01-01T10:00:05Z",
        },
        "deliveredAt": "2026-01-01T10:00:05Z",
    }


def test_invalid_sms_request_is_rejected(api_client, auth_headers):
    """A bad phone number fails validation and nothing is queued."""
    with patch.object(queue, "publish") as publish:
        response = api_client.post(
            "/api/v2/sms",
            json={"recipients": "not-a-phone", "body": SMS_BODY},
            headers=auth_headers(Role.SYSTEM.value),
        )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    publish.assert_not_called()


@pytest.mark.parametrize(
    ("request_by", "topic", "push_path", "provider", "api_key"),
    [
        (
            "e2e",
            BC_NOTIFY_SMS_TOPIC,
            "/bcnotify-sms/",
            Notification.NotificationProvider.BC_NOTIFY_SMS,
            BC_NOTIFY_API_KEY,
        ),
        (
            "STRR",
            BC_NOTIFY_HOUSING_SMS_TOPIC,
            "/bcnotify-housing-sms/",
            Notification.NotificationProvider.BC_NOTIFY_HOUSING_SMS,
            BC_NOTIFY_HOUSING_API_KEY,
        ),
    ],
)
def test_bc_notify_sms_success_path(
    api_app,
    api_client,
    delivery_client,
    auth_headers,
    request_by,
    topic,
    push_path,
    provider,
    api_key,
):
    published = []

    # 1. API validates the request, normalises the number, persists it and publishes a CloudEvent.
    with patch.object(
        queue,
        "publish",
        side_effect=lambda topic, payload, **_: published.append((topic, payload)),
    ):
        response = api_client.post(
            "/api/v2/sms",
            json={"recipients": RECIPIENT, "requestBy": request_by, "body": SMS_BODY},
            headers=auth_headers(Role.SYSTEM.value),
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json["notifyStatus"] == "QUEUED"
    notification_id = response.json["id"]
    assert len(published) == 1
    published_topic, payload = published[0]
    assert published_topic == topic

    with api_app.app_context():
        notification = db.session.get(Notification, notification_id)
        assert notification.recipients == RECIPIENT_E164
        assert notification.type_code == Notification.NotificationType.TEXT
        assert notification.status_code == Notification.NotificationStatus.QUEUED
        assert notification.provider_code == provider
        assert notification.content[0].body == SMS_BODY

    # 2. Delivery receives the push and sends it through the BC Notify SMS endpoint.
    with patch(
        "notify_delivery.services.providers.bc_notify.requests.post"
    ) as provider_post:
        provider_post.return_value.json.return_value = {
            "notifyId": PROVIDER_RESPONSE_ID
        }
        provider_post.return_value.raise_for_status.return_value = None
        push = delivery_client.post(push_path, json=_pubsub_push(payload))

    assert push.status_code == HTTPStatus.OK
    provider_post.assert_called_once()
    assert (
        provider_post.call_args.args[0]
        == "https://bc-notify.example.test/api/v1/notifysimple/sms"
    )
    assert provider_post.call_args.kwargs["headers"]["X-API-KEY"] == api_key
    assert provider_post.call_args.kwargs["json"] == {
        "sms": {"recipients": {"to": [RECIPIENT_E164]}, "content": {"body": SMS_BODY}}
    }

    # 3. Sent, but still active while waiting for the provider callback.
    with api_app.app_context():
        notification = db.session.get(Notification, notification_id)
        assert notification.status_code == Notification.NotificationStatus.SENT
        assert notification.notify_response_id == PROVIDER_RESPONSE_ID
        assert NotificationHistory.find_by_notification_id(notification_id) is None

    # 4. An intermediate callback status leaves the notification in place.
    callback_headers = auth_headers(Role.BC_NOTIFY_CALLBACK.value)
    sending = api_client.post(
        "/api/v2/callback/", json=_callback_body("sending"), headers=callback_headers
    )
    assert sending.status_code == HTTPStatus.OK
    with api_app.app_context():
        assert db.session.get(Notification, notification_id) is not None
        assert NotificationHistory.find_by_notification_id(notification_id) is None

    # 5. The completed callback marks it delivered and archives it.
    completed = api_client.post(
        "/api/v2/callback/", json=_callback_body("completed"), headers=callback_headers
    )
    assert completed.status_code == HTTPStatus.OK

    with api_app.app_context():
        assert db.session.get(Notification, notification_id) is None
        assert Content.query.filter_by(notification_id=notification_id).count() == 0

        history = NotificationHistory.find_by_notification_id(notification_id)
        assert history is not None
        assert history.recipients == RECIPIENT_E164
        assert history.type_code == "TEXT"
        assert history.status_code == "DELIVERED"
        assert history.provider_code == provider.name
        assert history.notify_response_id == PROVIDER_RESPONSE_ID
        assert history.notify_status == "completed"
        assert (
            BCNotifyCallback.query.filter_by(
                notify_id=PROVIDER_RESPONSE_ID, channel="SMS"
            ).count()
            == 2
        )

    # 6. The archived record is still retrievable through the API.
    lookup = api_client.get(
        f"/api/v1/notify/{notification_id}", headers=auth_headers(Role.SYSTEM.value)
    )
    assert lookup.status_code == HTTPStatus.OK
    assert lookup.json["notifyStatus"] == "DELIVERED"
    assert lookup.json["notifyType"] == "TEXT"
