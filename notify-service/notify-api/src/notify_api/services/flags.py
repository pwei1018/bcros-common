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
"""LaunchDarkly feature flags for notification provider toggles."""

from enum import StrEnum

from flask import Flask
import ldclient
from ldclient import Context
from ldclient.config import Config as LDConfig
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()


class FeatureFlag(StrEnum):
    """LaunchDarkly flag keys."""

    GC_NOTIFY = "enable-gc-notify"
    BC_NOTIFY = "enable-bc-notify"
    BC_NOTIFY_HOUSING = "enable-bc-notify-housing"
    BC_NOTIFY_SMS = "enable-bc-notify-sms"
    BC_NOTIFY_HOUSING_SMS = "enable-bc-notify-housing-sms"


class Flags:
    """Evaluate boolean LaunchDarkly flags, falling back to the supplied default when unavailable."""

    CONTEXT_KEY = "notify-api"

    def __init__(self, app: Flask | None = None):
        """Initialize the extension."""
        self.client = None
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Create the LaunchDarkly client when an SDK key is configured."""
        sdk_key = app.config.get("LD_SDK_KEY")
        if not sdk_key:
            logger.info("LD_SDK_KEY not set; feature flags use configuration defaults")
            return

        ldclient.set_config(LDConfig(sdk_key))
        self.client = ldclient.get()
        if not self.client.is_initialized():
            logger.warning("LaunchDarkly client failed to initialize; feature flags use configuration defaults")

    def is_on(self, flag: str, default: bool) -> bool:
        """Return the flag value, or *default* if LaunchDarkly is not available."""
        if not self.client or not self.client.is_initialized():
            return default
        try:
            context = Context.builder(self.CONTEXT_KEY).name(self.CONTEXT_KEY).build()
            return bool(self.client.variation(str(flag), context, default))
        except Exception as err:
            logger.error(f"Error evaluating feature flag {flag}: {err}")
            return default


flags = Flags()
