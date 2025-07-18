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

from flask import current_app
from notifications_python_client import NotificationsAPIClient
from notify_api.models import Notification
from structured_logging import StructuredLogging

from notify_delivery.services.providers.gc_notify import GCNotify

logger = StructuredLogging.get_logger()


class GCNotifyHousing(GCNotify):
    """Send notification via GC Notify service for Housing."""

    HOUSING_CONFIG_KEYS = {
        "api_key": "GC_NOTIFY_HOUSING_API_KEY",
        "template_id": "GC_NOTIFY_HOUSING_TEMPLATE_ID",
        "reply_to_id": "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID",
    }

    def __init__(self, notification: Notification):
        # Initialize parent to set all attributes from default config keys
        super().__init__(notification)

        # Apply housing-specific configuration
        self._apply_housing_config()

        # Initialize the client
        self._initialize_client()

    def _apply_housing_config(self):
        """Apply housing-specific configuration overrides."""
        config = current_app.config

        # Override with housing-specific values if they exist and are not empty
        self.api_key = self._get_config_value(config, "api_key", self.api_key)
        self.gc_notify_template_id = self._get_config_value(config, "template_id", self.gc_notify_template_id)
        self.gc_notify_email_reply_to_id = self._get_config_value(
            config, "reply_to_id", self.gc_notify_email_reply_to_id
        )

    def _get_config_value(self, config, key_type, default_value):
        """Get configuration value with fallback to default."""
        housing_key = self.HOUSING_CONFIG_KEYS[key_type]
        housing_value = config.get(housing_key)

        # Use housing value if it exists, is not None, and is not just whitespace
        if housing_value and housing_value.strip():
            return housing_value
        return default_value

    def _initialize_client(self):
        """Initialize the notifications client with current configuration."""
        if self.api_key:
            self.client = NotificationsAPIClient(api_key=self.api_key, base_url=self.gc_notify_url)
        else:
            self.client = None
            logger.warning("No API key available for GC Notify Housing service")
