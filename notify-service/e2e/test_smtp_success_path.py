"""E2E success path through the SMTP provider: request -> validate -> queue -> send -> archived."""

import base64
from http import HTTPStatus
from unittest.mock import patch

from notify_api.models import Content, Notification, NotificationHistory, db
from notify_api.services.gcp_queue import queue
from notify_api.utils.enums import Role

from conftest import SMTP_FROM, SMTP_TOPIC

RECIPIENT = "smtp-recipient@gov.bc.ca"
# An inline image routes the request to SMTP instead of the default BC Notify provider.
HTML_BODY = '<p>Hello</p><img src="cid:logo" alt="logo">'


def test_smtp_success_path(api_app, api_client, delivery_smtp_client, auth_headers):
    published = []

    with patch.object(
        queue,
        "publish",
        side_effect=lambda topic, payload, **_: published.append((topic, payload)),
    ):
        response = api_client.post(
            "/api/v1/notify",
            json={
                "recipients": RECIPIENT,
                "requestBy": "e2e",
                "content": {"subject": "SMTP subject", "body": HTML_BODY},
            },
            headers=auth_headers(Role.SYSTEM.value),
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json["notifyStatus"] == "QUEUED"
    notification_id = response.json["id"]
    assert len(published) == 1
    topic, payload = published[0]
    assert topic == SMTP_TOPIC

    with api_app.app_context():
        notification = db.session.get(Notification, notification_id)
        assert notification.provider_code == Notification.NotificationProvider.SMTP

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
    smtp_class.assert_called_once_with(host="smtp.e2e.test", port=25)
    smtp_server.sendmail.assert_called_once()
    sender, recipients, raw_message = smtp_server.sendmail.call_args.args
    assert sender == SMTP_FROM
    assert recipients == [RECIPIENT]
    assert "Subject: SMTP subject" in raw_message

    # SMTP has no callback, so the record is archived as soon as it is sent.
    with api_app.app_context():
        assert db.session.get(Notification, notification_id) is None
        assert Content.query.filter_by(notification_id=notification_id).count() == 0

        history = NotificationHistory.find_by_notification_id(notification_id)
        assert history is not None
        assert history.status_code == "SENT"
        assert history.provider_code == "SMTP"
        assert history.recipients == RECIPIENT
        assert history.subject == "SMTP subject"

    lookup = api_client.get(
        f"/api/v1/notify/{notification_id}", headers=auth_headers(Role.SYSTEM.value)
    )
    assert lookup.status_code == HTTPStatus.OK
    assert lookup.json["notifyStatus"] == "SENT"
