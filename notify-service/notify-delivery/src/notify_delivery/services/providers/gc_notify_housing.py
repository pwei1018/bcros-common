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
from notify_api.models import Notification
from structured_logging import StructuredLogging

from notify_delivery.services.providers.gc_notify import GCNotify

logger = StructuredLogging.get_logger()


class GCNotifyHousing(GCNotify):
    """Send notification via GC Notify service for Housing."""

    def __init__(self, notification: Notification):
        # Initialize parent to set all attributes from default config keys
        super().__init__(notification)

        # Override specific config values with Housing-specific keys
        self.api_key = current_app.config.get("GC_NOTIFY_HOUSING_API_KEY")
        self.gc_notify_template_id = current_app.config.get(
            "GC_NOTIFY_HOUSING_TEMPLATE_ID"
        )
        self.gc_notify_email_reply_to_id = current_app.config.get(
            "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID"
        )
