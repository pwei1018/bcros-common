# Copyright © 2026 Province of British Columbia
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
"""Tests for the v2 SMS API endpoint and request model."""

from http import HTTPStatus
import time
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from notify_api.models import Notification, SmsRequest
from notify_api.utils.enums import Role

API_V2_SMS = "/api/v2/sms"


def create_header(jwt, roles, **kwargs):
    """Create a JWT header with roles and a short expiry."""
    claims = {
        "realm_access": {"roles": roles},
        "aud": "example",
        "iss": "https://example.localdomain/auth/realms/example",
        "sub": "test-user",
        "exp": int(time.time()) + 60,
    }
    token = jwt.create_jwt(claims=claims, header={"kid": "flask-jwt-oidc-test-client"})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    headers.update(kwargs)
    return headers


class TestSmsRequest:
    """Test suite for the SMS request model."""

    @staticmethod
    def test_recipients_normalised_to_e164():
        """Phone numbers are normalised to E.164, defaulting to the CA region."""
        request = SmsRequest(recipients="250 555 0123, +1 (604) 555-0147", body="Hello")
        assert request.recipients == "+12505550123,+16045550147"

    @staticmethod
    @pytest.mark.parametrize("recipients", ["", " , ", "not-a-number", "test@example.com", "123"])
    def test_invalid_recipients_rejected(recipients):
        """Invalid or empty phone numbers are rejected."""
        with pytest.raises(ValidationError):
            SmsRequest(recipients=recipients, body="Hello")

    @staticmethod
    @pytest.mark.parametrize("body", ["", "   "])
    def test_empty_body_rejected(body):
        """An empty body is rejected."""
        with pytest.raises(ValidationError):
            SmsRequest(recipients="+12505550123", body=body)


class TestSmsEndpoint:
    """Test suite for the v2 SMS endpoint."""

    @staticmethod
    def test_requires_authentication(client):
        """Requests without a token are rejected."""
        response = client.post(API_V2_SMS, json={"recipients": "+12505550123", "body": "Hello"})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @staticmethod
    def test_job_role_forbidden(client, jwt):
        """The JOB role cannot send SMS."""
        headers = create_header(jwt, [Role.JOB.value])
        response = client.post(API_V2_SMS, json={"recipients": "+12505550123", "body": "Hello"}, headers=headers)
        assert response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}

    @staticmethod
    @pytest.mark.parametrize("role", [Role.SYSTEM.value, Role.PUBLIC_USER.value, Role.STAFF.value])
    def test_send_sms(client, jwt, role):
        """Authorized roles can queue an SMS."""
        headers = create_header(jwt, [role])
        notification = Notification(id=1, recipients="+12505550123", status_code=Notification.NotificationStatus.QUEUED)

        with patch("notify_api.services.notify.queue_publish_sms", return_value=notification) as mock_publish:
            response = client.post(
                API_V2_SMS,
                json={"recipients": "250-555-0123", "requestBy": "test", "body": "Hello"},
                headers=headers,
            )

        assert response.status_code == HTTPStatus.OK
        assert response.get_json()["recipients"] == "+12505550123"
        sms_request = mock_publish.call_args.args[0]
        assert sms_request.recipients == "+12505550123"
        assert sms_request.body == "Hello"

    @staticmethod
    def test_send_sms_invalid_phone(client, jwt):
        """Invalid phone numbers are rejected before queueing."""
        headers = create_header(jwt, [Role.SYSTEM.value])

        with patch("notify_api.services.notify.queue_publish_sms") as mock_publish:
            response = client.post(API_V2_SMS, json={"recipients": "abc", "body": "Hello"}, headers=headers)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        mock_publish.assert_not_called()
