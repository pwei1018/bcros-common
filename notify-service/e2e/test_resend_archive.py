"""E2E resend and archive: the resend endpoint republishes stale work and archives expired work."""

import base64
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch

from notify_api.models import Content, Notification, NotificationHistory, db
from notify_api.services.gcp_queue import queue
from notify_api.utils.enums import Role

from conftest import SMTP_TOPIC

RECIPIENT = "resend-recipient@gov.bc.ca"
# An inline image routes the request to SMTP, which completes without a provider callback.
HTML_BODY = '<p>Hello</p><img src="cid:logo" alt="logo">'


def _create_notification(api_client, auth_headers) -> int:
    """Create a queued SMTP notification through the API, discarding the initial publish."""
    with patch.object(queue, "publish"):
        response = api_client.post(
            "/api/v1/notify",
            json={
                "recipients": RECIPIENT,
                "requestBy": "e2e",
                "content": {"subject": "Resend subject", "body": HTML_BODY},
            },
            headers=auth_headers(Role.SYSTEM.value),
        )
    assert response.status_code == HTTPStatus.OK
    return response.json["id"]


def _set_age(
    api_app,
    notification_id: int,
    age: timedelta,
    status=Notification.NotificationStatus.QUEUED,
):
    with api_app.app_context():
        notification = db.session.get(Notification, notification_id)
        notification.request_date = datetime.now(UTC) - age
        notification.status_code = status
        db.session.commit()


def test_resend_republishes_and_delivery_archives(
    api_app, api_client, delivery_smtp_client, auth_headers
):
    notification_id = _create_notification(api_client, auth_headers)
    # Old enough to no longer be in flight, young enough to still be worth sending.
    _set_age(
        api_app,
        notification_id,
        timedelta(hours=1),
        Notification.NotificationStatus.FAILURE,
    )

    published = []
    with patch.object(
        queue,
        "publish",
        side_effect=lambda topic, payload, **_: published.append((topic, payload)),
    ):
        resend = api_client.post(
            "/api/v2/resend", json={}, headers=auth_headers(Role.SYSTEM.value)
        )

    assert resend.status_code == HTTPStatus.OK
    assert len(published) == 1
    topic, payload = published[0]
    assert topic == SMTP_TOPIC

    with api_app.app_context():
        notification = db.session.get(Notification, notification_id)
        assert notification.status_code == Notification.NotificationStatus.QUEUED
        assert notification.retry_count == 1

    envelope = {
        "subscription": "projects/e2e/subscriptions/smtp",
        "message": {"data": base64.b64encode(payload).decode()},
    }
    with patch(
        "notify_delivery.services.providers.email_smtp.smtplib.SMTP"
    ) as smtp_class:
        smtp_server = smtp_class.return_value.__enter__.return_value
        push = delivery_smtp_client.post("/smtp/", json=envelope)

    assert push.status_code == HTTPStatus.OK
    smtp_server.sendmail.assert_called_once()

    with api_app.app_context():
        assert db.session.get(Notification, notification_id) is None
        history = NotificationHistory.find_by_notification_id(notification_id)
        assert history is not None
        assert history.status_code == "SENT"
        assert history.provider_code == "SMTP"


def test_resend_archives_expired_notification(api_app, api_client, auth_headers):
    notification_id = _create_notification(api_client, auth_headers)
    _set_age(api_app, notification_id, timedelta(days=31))

    with patch.object(queue, "publish") as publish:
        resend = api_client.post(
            "/api/v2/resend", json={}, headers=auth_headers(Role.SYSTEM.value)
        )

    assert resend.status_code == HTTPStatus.OK
    publish.assert_not_called()

    with api_app.app_context():
        assert db.session.get(Notification, notification_id) is None
        assert Content.query.filter_by(notification_id=notification_id).count() == 0

        history = NotificationHistory.find_by_notification_id(notification_id)
        assert history is not None
        assert history.status_code == "EXPIRED"
        assert history.provider_code == "SMTP"
        assert history.subject == "Resend subject"

    lookup = api_client.get(
        f"/api/v1/notify/{notification_id}", headers=auth_headers(Role.SYSTEM.value)
    )
    assert lookup.status_code == HTTPStatus.OK
    assert lookup.json["notifyStatus"] == "EXPIRED"
