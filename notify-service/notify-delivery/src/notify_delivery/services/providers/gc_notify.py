# Copyright © 2022 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This provides send email through GC Notify Service."""

import base64
import time

from flask import current_app
from notifications_python_client import NotificationsAPIClient
from notifications_python_client.errors import HTTPError
from notify_api.models import (
    Content,
    Notification,
    NotificationSendResponse,
    NotificationSendResponses,
)
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()


class GCNotify:
    """Send notification via GC Notify service."""

    # Retry configuration for rate limiting and transient errors
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 10  # seconds
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self, notification: Notification) -> None:
        """Construct object."""
        config = current_app.config
        self.api_key = config.get("GC_NOTIFY_API_KEY")
        self.gc_notify_url = config.get("GC_NOTIFY_API_URL")
        self.gc_notify_template_id = config.get("GC_NOTIFY_TEMPLATE_ID")
        self.gc_notify_email_reply_to_id = config.get("GC_NOTIFY_EMAIL_REPLY_TO_ID")
        self.notification = notification
        if self.api_key:
            self.client = NotificationsAPIClient(api_key=self.api_key, base_url=self.gc_notify_url)
        else:
            self.client = None

    def _prepare_personalisation(self, content: Content) -> dict:
        """Prepare the personalisation dictionary for GC Notify."""
        deployment_env = current_app.config.get("DEPLOYMENT_ENV", "production").lower()
        subject = content.subject
        if deployment_env != "production":
            subject += f" - from {deployment_env.upper()} environment"

        personalisation = {
            "email_subject": subject,
            "email_body": content.body,
        }

        if content.attachments:
            for idx, attachment in enumerate(content.attachments):
                personalisation[f"attachment{idx + 1}"] = {
                    "file": base64.b64encode(attachment.file_bytes).decode(),
                    "filename": attachment.file_name,
                    "sending_method": "attach",
                }
        return personalisation

    def send(self) -> NotificationSendResponses:
        """Send email through GC Notify."""
        if not self.notification.content:
            logger.error("No message content available for notification")
            return NotificationSendResponses(recipients=[])

        content = self.notification.content[0]
        if not all(hasattr(content, attr) for attr in ["subject", "body"]):
            logger.error("Invalid message content structure - missing subject or body")
            return NotificationSendResponses(recipients=[])

        personalisation = self._prepare_personalisation(content)

        response_list: list[NotificationSendResponse] = []
        recipients = [r.strip() for r in self.notification.recipients.split(",") if r.strip()]

        for recipient in recipients:
            try:
                response = self._send_with_retry(recipient, personalisation)
                if response:
                    response_list.append(NotificationSendResponse(response_id=response["id"], recipient=recipient))
            except HTTPError as e:
                logger.error(f"Error sending email to {recipient}: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred when sending email to {recipient}: {e}")

        return NotificationSendResponses(recipients=response_list)

    def _send_with_retry(self, recipient: str, personalisation: dict) -> dict | None:
        """Send email with retry on rate limit (429) and transient server errors (5xx)."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return self.client.send_email_notification(
                    email_address=recipient,
                    template_id=self.gc_notify_template_id,
                    personalisation=personalisation,
                    email_reply_to_id=self.gc_notify_email_reply_to_id,
                )
            except HTTPError as e:
                if e.status_code in self.RETRYABLE_STATUS_CODES and attempt < self.MAX_RETRIES:
                    delay = self.RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        f"Retryable error ({e.status_code}) sending to {recipient}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                else:
                    raise
        return None
