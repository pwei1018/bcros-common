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
"""Google Storage token tests."""
import base64
import json
import os

from flask import current_app

from doc_api.config import get_mock_auth
from doc_api.services.gcp_auth.auth_service import GoogleAuthService
from doc_api.utils.logging import logger


def test_get_token(session, client, jwt):
    """Assert that the configuration to get a google storage token works as expected (no exceptions)."""
    token = GoogleAuthService.get_token()
    if current_app.config.get("GCP_AUTH_KEY"):
        logger.debug(token)
        assert token
    else:
        assert not token


def test_get_credentials(session, client, jwt):
    """Assert that the configuration to get a google storage token works as expected (no exceptions)."""
    credentials = GoogleAuthService.get_credentials()
    if current_app.config.get("GCP_AUTH_KEY"):
        assert credentials
    else:
        assert not credentials


def test_security_account(session, client, jwt):
    """Assert that the configuration to get the GCP service account from the environment works as expected."""
    decoded_sa = None
    encoded_sa: bytes = None
    #
    default_sa = current_app.config.get("GCP_AUTH_KEY")
    if default_sa:
        encoded_sa = bytes(default_sa, "utf-8")
        assert encoded_sa
        decoded_sa = json.loads(base64.b64decode(encoded_sa.decode("utf-8")))
        logger.info(f"sa email={decoded_sa.get('client_email')} project={decoded_sa.get('project_id')}")
        assert decoded_sa
        assert decoded_sa.get("type")
        assert decoded_sa.get("project_id")
        assert decoded_sa.get("private_key_id")
        assert decoded_sa.get("private_key")
        assert decoded_sa.get("client_email")
        assert decoded_sa.get("client_id")
        assert decoded_sa.get("auth_uri")
        assert decoded_sa.get("token_uri")
        assert decoded_sa.get("auth_provider_x509_cert_url")
        assert decoded_sa.get("client_x509_cert_url")


def test_mock_auth(session, client, jwt):
    """Assert that the mock auth sa works as expected."""
    value = get_mock_auth()
    logger.debug(value)
    assert value
