# Copyright © 2019 Province of British Columbia
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
"""Verify Google-signed OIDC tokens issued to a trusted Cloud Scheduler service account.

This is intentionally separate from the Keycloak-based `flask_jwt_oidc` auth used
for normal API callers. It lets a specific, narrowly-scoped GCP service account
(e.g. a Cloud Scheduler job) call an endpoint directly with a Google ID token,
without needing Keycloak client credentials.
"""

from flask import current_app, request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()

_google_request = google_requests.Request()


def is_authorized_scheduler_request() -> bool:
    """Return True if the current request carries a valid Google ID token.

    The token must be signed by Google, have the configured audience, and
    belong to the configured trusted service account email. Any failure
    (missing header, bad token, wrong audience/email) returns False so the
    caller can fall back to normal auth instead of raising.
    """
    expected_sa_email = current_app.config.get("RESEND_SCHEDULER_SA_EMAIL")
    expected_audience = current_app.config.get("RESEND_SCHEDULER_AUDIENCE")

    if not expected_sa_email or not expected_audience:
        # Feature not configured for this environment - always fall back.
        return False

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return False

    try:
        payload = id_token.verify_oauth2_token(token, _google_request, audience=expected_audience)
    except Exception as err:  # pylint: disable=broad-except
        logger.debug(f"Google ID token verification failed: {err}")
        return False

    token_email = payload.get("email")
    email_verified = payload.get("email_verified", False)

    if token_email != expected_sa_email or not email_verified:
        logger.warning(f"Google ID token rejected - unexpected service account: {token_email}")
        return False

    return True
