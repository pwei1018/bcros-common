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
"""This provides send email through BC Notify Service (GC Notify variant)."""

import time

import requests
from flask import current_app
from notify_api.models import Notification
from requests.exceptions import RequestException
from structured_logging import StructuredLogging

from notify_delivery.services.providers.gc_notify import GCNotify

logger = StructuredLogging.get_logger()


class BCNotify(GCNotify):
    """Send notification via BC Notify service (a GC Notify variant with BC-specific configuration).

    BC Notify is fronted by the BC Gov API gateway, which is a different host from
    GC Notify (``BC_NOTIFY_API_URL``). The gateway issues the service/client id
    (``BC_NOTIFY_API_CLIENT_ID``) separately from the API secret
    (``BC_NOTIFY_API_KEY``). ``NotificationsAPIClient`` derives the service id from
    ``api_key[-73:-37]`` and the secret from ``api_key[-36:]``, so the two values are
    combined into that composite layout before the client is constructed.
    """

    BC_NOTIFY_CONFIG_KEYS = {
        "api_url": "BC_NOTIFY_API_URL",
        "api_key": "BC_NOTIFY_API_KEY",
        "client_id": "BC_NOTIFY_API_CLIENT_ID",
        "template_id": "BC_NOTIFY_TEMPLATE_ID",
        "reply_to_id": "BC_NOTIFY_EMAIL_REPLY_TO_ID",
    }

    def __init__(self, notification: Notification):
        """Construct object, initialising with BC Notify-specific configuration."""
        # Initialise parent to set all attributes from default GC Notify config keys
        super().__init__(notification)

        # Client/service identifier issued by the BC Gov API gateway (kept separate
        # from the API secret and combined at client-construction time).
        self.api_client_id = None

        # Apply BC Notify-specific configuration overrides
        self._apply_bc_notify_config()

        if not self.api_key:
            logger.warning("No API key available for BC Notify service")

    def _apply_bc_notify_config(self):
        """Apply BC Notify-specific configuration overrides."""
        config = current_app.config

        self.gc_notify_url = self._get_bc_notify_config_value(config, "api_url", self.gc_notify_url)
        self.api_key = self._get_bc_notify_config_value(config, "api_key", self.api_key)
        self.api_client_id = self._get_bc_notify_config_value(config, "client_id", self.api_client_id)
        self.gc_notify_template_id = self._get_bc_notify_config_value(config, "template_id", self.gc_notify_template_id)
        self.gc_notify_email_reply_to_id = self._get_bc_notify_config_value(
            config, "reply_to_id", self.gc_notify_email_reply_to_id
        )

    def _get_bc_notify_config_value(self, config, key_type: str, default_value):
        """Return BC Notify config value, falling back to *default_value* when absent or blank."""
        bc_key = self.BC_NOTIFY_CONFIG_KEYS[key_type]
        bc_value = config.get(bc_key)

        if bc_value and bc_value.strip():
            return bc_value
        return default_value

    def _send_with_retry(self, recipient: str, personalisation: dict) -> dict | None:
        """Send email directly to BC Gov API Gateway with retry on rate limit (429) and transient server errors (5xx)."""
        if not self.api_key:
            logger.error("No API key configured for BC Notify.")
            return None

        url = f"{self.gc_notify_url.rstrip('/')}/v2/notifications/email"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "email_address": recipient,
            "template_id": self.gc_notify_template_id,
            "personalisation": personalisation,
        }
        if self.gc_notify_email_reply_to_id:
            payload["email_reply_to_id"] = self.gc_notify_email_reply_to_id

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
