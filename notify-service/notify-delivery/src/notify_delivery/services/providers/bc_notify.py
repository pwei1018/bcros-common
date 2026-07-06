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

from flask import current_app
from notifications_python_client import NotificationsAPIClient
from notify_api.models import Notification
from structured_logging import StructuredLogging

from notify_delivery.services.providers.gc_notify import GCNotify

logger = StructuredLogging.get_logger()


class BCNotify(GCNotify):
    """Send notification via BC Notify service (a GC Notify variant with BC-specific configuration)."""

    BC_NOTIFY_CONFIG_KEYS = {
        "api_key": "BC_NOTIFY_API_KEY",
        "template_id": "BC_NOTIFY_TEMPLATE_ID",
        "reply_to_id": "BC_NOTIFY_EMAIL_REPLY_TO_ID",
    }

    def __init__(self, notification: Notification):
        """Construct object, initialising with BC Notify-specific configuration."""
        # Initialise parent to set all attributes from default GC Notify config keys
        super().__init__(notification)

        # Apply BC Notify-specific configuration overrides
        self._apply_bc_notify_config()

        # Re-initialise the client with the resolved configuration. This is done
        # inline (rather than via an overridable method) so that subclasses which
        # add further configuration layers control their own client initialisation.
        if self.api_key:
            self.client = NotificationsAPIClient(api_key=self.api_key, base_url=self.gc_notify_url)
        else:
            self.client = None
            logger.warning("No API key available for BC Notify service")

    def _apply_bc_notify_config(self):
        """Apply BC Notify-specific configuration overrides."""
        config = current_app.config

        self.api_key = self._get_bc_notify_config_value(config, "api_key", self.api_key)
        self.gc_notify_template_id = self._get_bc_notify_config_value(config, "template_id", self.gc_notify_template_id)
        self.gc_notify_email_reply_to_id = self._get_bc_notify_config_value(
            config, "reply_to_id", self.gc_notify_email_reply_to_id
        )

    def _get_bc_notify_config_value(self, config, key_type: str, default_value: str) -> str:
        """Return BC Notify config value, falling back to *default_value* when absent or blank."""
        bc_key = self.BC_NOTIFY_CONFIG_KEYS[key_type]
        bc_value = config.get(bc_key)

        if bc_value and bc_value.strip():
            return bc_value
        return default_value
