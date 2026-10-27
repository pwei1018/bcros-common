# Copyright © 2026 Province of British Columbia
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
"""This provides SMS delivery through BC Notify."""

from notify_api.models import Content

from notify_delivery.services.providers.bc_notify import BCNotify


class BCNotifySMS(BCNotify):
    """Send SMS notification via BC Notify ``/api/v1/notifysimple/sms``."""

    def _build_url(self) -> str:
        """Return the BC Notify SMS send endpoint."""
        return f"{self.bc_notify_url.rstrip('/')}/api/v1/notifysimple/sms"

    def _build_payload(self, recipient: str, content: Content) -> dict:
        """Return the BC Notify SMS request body for a single recipient."""
        return {
            "sms": {
                "recipients": {"to": [recipient]},
                "content": {"body": content.body},
            }
        }
