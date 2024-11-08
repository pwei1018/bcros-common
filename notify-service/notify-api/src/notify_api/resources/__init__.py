# Copyright © 2019 Province of British Columbia
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
"""Exposes all of the resource endpoints mounted in Flask-Blueprint style."""

from .constants import EndpointVersionPath
from .meta import meta_bp
from .ops import ops_bp
from .v1 import notify_bp
from .v2 import callback_bp_v2, email_validation_bp_v2, resend_bp_v2, safe_list_bp_v2
from .version_endpoint import VersionEndpoint

meta_endpoint = VersionEndpoint(name="META", path=EndpointVersionPath.META, bps=[meta_bp])  # pylint: disable=invalid-name

ops_endpoint = VersionEndpoint(name="OPS", path=EndpointVersionPath.OPS, bps=[ops_bp])  # pylint: disable=invalid-name

v1_endpoint = VersionEndpoint(  # pylint: disable=invalid-name
    name="API_V1", path=EndpointVersionPath.API_V1, bps=[notify_bp]
)

v2_endpoint = VersionEndpoint(  # pylint: disable=invalid-name
    name="API_V2",
    path=EndpointVersionPath.API_V2,
    bps=[email_validation_bp_v2, safe_list_bp_v2, callback_bp_v2, resend_bp_v2],
)

TRACING_EXCLUED_URLS = [
    "/meta",
    "/ops",
    "/api/v2/callback",
    "/api/v2/email_validation",
    "/api/v2/safe_list",
    "/api/v2/resend",
]
