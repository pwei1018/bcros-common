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
"""This provides send email through BC Notify Service for Housing."""

from flask import current_app
from notifications_python_client import NotificationsAPIClient
from notify_api.models import Notification
from structured_logging import StructuredLogging

from notify_delivery.services.providers.bc_notify import BCNotify

logger = StructuredLogging.get_logger()


class BCNotifyHousing(BCNotify):
    """Send notification via BC Notify service for Housing.

    Inherits BC Notify behaviour and applies Housing-specific configuration
    overrides, falling back to the BC Notify (and ultimately GC Notify) defaults
    resolved by the parent classes.
    """

    BC_NOTIFY_HOUSING_CONFIG_KEYS = {
        "api_key": "BC_NOTIFY_HOUSING_API_KEY",
        "template_id": "BC_NOTIFY_HOUSING_TEMPLATE_ID",
        "reply_to_id": "BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID",
    }

    def __init__(self, notification: Notification):
        """Construct object, initialising with BC Notify Housing-specific configuration."""
        # Initialise parent (BCNotify) to resolve BC Notify / GC Notify defaults
        super().__init__(notification)

        # Apply Housing-specific configuration overrides
        self._apply_bc_notify_housing_config()

        # Re-initialise the client with the resolved configuration
        self._initialize_client()

    def _apply_bc_notify_housing_config(self):
        """Apply BC Notify Housing-specific configuration overrides."""
        config = current_app.config

        self.api_key = self._get_bc_notify_housing_config_value(config, "api_key", self.api_key)
        self.gc_notify_template_id = self._get_bc_notify_housing_config_value(
            config, "template_id", self.gc_notify_template_id
        )
        self.gc_notify_email_reply_to_id = self._get_bc_notify_housing_config_value(
            config, "reply_to_id", self.gc_notify_email_reply_to_id
        )

    def _get_bc_notify_housing_config_value(self, config, key_type: str, default_value: str) -> str:
        """Return BC Notify Housing config value, falling back to *default_value* when absent or blank."""
        housing_key = self.BC_NOTIFY_HOUSING_CONFIG_KEYS[key_type]
        housing_value = config.get(housing_key)

        if housing_value and housing_value.strip():
            return housing_value
        return default_value

    def _initialize_client(self):
        """(Re-)initialise the notifications client with the current API key and URL."""
        if self.api_key:
            self.client = NotificationsAPIClient(api_key=self.api_key, base_url=self.gc_notify_url)
        else:
            self.client = None
            logger.warning("No API key available for BC Notify Housing service")
