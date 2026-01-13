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
"""This maintains access tokens for API calls."""
import base64
import json

import google.auth.transport.requests
import google.oauth2.id_token
from google.oauth2 import service_account

from colin_report_migration.config import Config
from colin_report_migration.utils.logging import logger


class GoogleAuthService:  # pylint: disable=too-few-public-methods
    """Google Auth Service implementation.

    Maintains a wrapper to get a service account access token and credentials for Google API calls.
    """

    # Google APIs and cloud storage os.getenv('GCP
    gcp_auth_key = None
    # https://developers.google.com/identity/protocols/oauth2/scopes
    gcp_sa_scopes = None
    service_account_info = None
    credentials = None
    # Use service account env var if available.
    if gcp_auth_key:
        sa_bytes = bytes(gcp_auth_key, "utf-8")
        service_account_info = json.loads(base64.b64decode(sa_bytes.decode("utf-8")))

    @staticmethod
    def init_app(config: Config):
        """Set up the service"""
        GoogleAuthService.gcp_auth_key = config.GCP_AUTH_KEY
        GoogleAuthService.gcp_sa_scopes = [config.GCP_CS_SA_SCOPES]
        if GoogleAuthService.gcp_auth_key:
            sa_bytes = bytes(GoogleAuthService.gcp_auth_key, "utf-8")
            GoogleAuthService.service_account_info = json.loads(base64.b64decode(sa_bytes.decode("utf-8")))

    @classmethod
    def get_token(cls):
        """Generate an OAuth access token with cloud storage access."""
        if cls.credentials is None:
            cls.credentials = service_account.Credentials.from_service_account_info(
                cls.service_account_info, scopes=cls.gcp_sa_scopes
            )
        request = google.auth.transport.requests.Request()
        cls.credentials.refresh(request)
        logger.info("Call successful: obtained token.")
        return cls.credentials.token

    @classmethod
    def get_credentials(cls):
        """Generate GCP auth credentials to pass to a GCP client."""
        if cls.credentials is None:
            cls.credentials = service_account.Credentials.from_service_account_info(
                cls.service_account_info, scopes=cls.gcp_sa_scopes
            )
        logger.info("Call successful: obtained credentials.")
        return cls.credentials
