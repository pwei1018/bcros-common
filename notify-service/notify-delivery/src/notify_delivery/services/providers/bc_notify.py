# Copyright © 2024 Province of British Columbia
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
"""This provides email delivery through BC Notify."""

import base64
import mimetypes
import re
import time
from html.parser import HTMLParser

import requests
from flask import current_app
from notify_api.models import (
    Content,
    Notification,
    NotificationSendResponse,
    NotificationSendResponses,
)
from requests.exceptions import RequestException
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()


class _HTMLTagDetector(HTMLParser):
    """Detect whether a body contains HTML tags."""

    def __init__(self) -> None:
        super().__init__()
        self.has_tags = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.has_tags = True

    def handle_endtag(self, tag: str) -> None:
        self.has_tags = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.has_tags = True


class BCNotify:
    """Send notification via BC Notify service.

    BC Notify is fronted by the BC Gov API gateway and uses a direct email payload.
    """

    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 10
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    BC_NOTIFY_CONFIG_KEYS = {
        "api_url": "BC_NOTIFY_API_URL",
        "api_key": "BC_NOTIFY_API_KEY",
    }

    def __init__(self, notification: Notification) -> None:
        """Construct object, initialising with BC Notify-specific configuration."""
        self.notification = notification
        self.bc_notify_url = None
        self.api_key = None
        self._apply_bc_notify_config()

        if not self.api_key:
            logger.warning("No API key available for BC Notify service")

    def _apply_bc_notify_config(self) -> None:
        """Load BC Notify configuration."""
        config = current_app.config

        self.bc_notify_url = self._get_bc_notify_config_value(config, "api_url", self.bc_notify_url)
        self.api_key = self._get_bc_notify_config_value(config, "api_key", self.api_key)

    def _get_bc_notify_config_value(self, config: dict, key_type: str, default_value: str | None) -> str | None:
        """Return BC Notify config value, falling back to *default_value* when absent or blank."""
        bc_key = self.BC_NOTIFY_CONFIG_KEYS[key_type]
        bc_value = config.get(bc_key)

        if bc_value and bc_value.strip():
            return bc_value
        return default_value

    def send(self) -> NotificationSendResponses:
        """Send the notification to each recipient through BC Notify."""
        if not self.notification.content:
            logger.error("No message content available for notification")
            return NotificationSendResponses(recipients=[])

        content = self.notification.content[0]
        if not all(hasattr(content, attr) for attr in ("subject", "body")):
            logger.error("Invalid message content structure - missing subject or body")
            return NotificationSendResponses(recipients=[])

        responses: list[NotificationSendResponse] = []
        recipients = [recipient.strip() for recipient in self.notification.recipients.split(",") if recipient.strip()]

        for recipient in recipients:
            try:
                response = self._send_with_retry(recipient, content)
                if response:
                    responses.append(NotificationSendResponse(response_id=response["notifyId"], recipient=recipient))
            except RequestException as error:
                logger.error(f"Error sending email to {recipient}: {error}")
            except Exception as error:
                logger.error(f"An unexpected error occurred when sending email to {recipient}: {error}")

        return NotificationSendResponses(recipients=responses)

    @staticmethod
    def _build_attachment(attachment) -> dict:
        """Build a BC Notify attachment entry from a notification attachment."""
        mime_type = mimetypes.guess_type(attachment.file_name)[0] or "application/octet-stream"
        return {
            "filename": attachment.file_name,
            "mimeType": mime_type,
            "content": base64.b64encode(attachment.file_bytes).decode(),
        }

    @staticmethod
    def _determine_body_type(body: str) -> str:
        """Infer the body format from HTML and Markdown syntax, defaulting to plain text."""
        markdown_patterns = (
            r"(?m)^\s{0,3}#{1,6}\s+\S",
            r"(?m)^\s{0,3}(?:[-*+]|\d+[.)])\s+\S",
            r"(?m)^\s{0,3}>\s+\S",
            r"```|~~~",
            r"(\*\*|__|~~).+?\1",
            r"(?<!\w)(\*|_).+?\1(?!\w)",
            r"`[^`\n]+`",
            r"\[[^\]]+\]\([^)]+\)",
        )
        if any(re.search(pattern, body) for pattern in markdown_patterns):
            return "markdown"

        html_detector = _HTMLTagDetector()
        html_detector.feed(body)
        if html_detector.has_tags:
            return "html"
        return "text"

    def _send_with_retry(self, recipient: str, content: Content) -> dict | None:
        """Send email with retries for rate limits and transient server errors."""
        if not self.api_key or not self.bc_notify_url:
            logger.error("BC Notify API URL or key is not configured.")
            return None

        url = f"{self.bc_notify_url.rstrip('/')}/api/v1/notifysimple/email"
        headers = {"X-API-KEY": f"{self.api_key}", "Content-Type": "application/json"}
        deployment_env = current_app.config.get("DEPLOYMENT_ENV", "production").lower()
        subject = content.subject
        if deployment_env != "production":
            subject += f" - from {deployment_env.upper()} environment"

        payload = {
            "recipients": {"to": [recipient]},
            "content": {
                "subject": subject,
                "body": content.body,
                "bodyType": self._determine_body_type(content.body),
            },
        }

        if content.attachments:
            payload["attachments"] = [self._build_attachment(attachment) for attachment in content.attachments]

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else None
                if status_code in self.RETRYABLE_STATUS_CODES and attempt < self.MAX_RETRIES:
                    delay = self.RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        f"Retryable error ({status_code}) sending to {recipient}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"HTTPError sending to {recipient}: {e.response.text if e.response is not None else str(e)}"
                    )
                    raise e
            except RequestException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        f"Connection error sending to {recipient}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"RequestException sending to {recipient}: {str(e)}")
                    raise e
        return None
