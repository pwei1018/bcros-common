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

"""Tests to verify the endpoints for maintaining application reports.

Test-Suite to ensure that the /applicaton-reports endpoint is working as expected.
"""
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import ApplicationReport
from doc_api.models import utils as model_utils
from doc_api.utils.logging import logger
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE, SYSTEM_ROLE
from doc_api.services.pdf_convert import MediaTypes
from tests.unit.services.utils import create_header_account


USER_ROLES = [BC_REGISTRY]
USER_ROLES_SYSTEM = [SYSTEM_ROLE]
USER_ROLES_STAFF = [STAFF_ROLE]
USER_ROLES_COLIN = [COLIN_ROLE]
CONVERT_TEST_JPG = "tests/unit/services/data/test-image.jpg"
CONVERT_TEST_PNG = "tests/unit/services/data/test-image.png"
CONTENT_TYPE_INVALID = "application/sql"
MOCK_AUTH_URL = "https://test.api.connect.gov.bc.ca/mockTarget/auth/api/v1/"
PATH: str = "/api/v1/pdf-conversions"
# testdata pattern is ({description}, {filename}, {content_type}, {status}, {roles})
TEST_CONVERT_DATA = [
    ("Invalid role", CONVERT_TEST_JPG, MediaTypes.CONTENT_TYPE_JPEG.value, HTTPStatus.UNAUTHORIZED, USER_ROLES_COLIN),
    ("Invalid no payload", None, MediaTypes.CONTENT_TYPE_JPEG.value, HTTPStatus.BAD_REQUEST, USER_ROLES_SYSTEM),
    ("Invalid no content type", CONVERT_TEST_JPG, None, HTTPStatus.BAD_REQUEST, USER_ROLES_STAFF),
    ("Invalid content type", CONVERT_TEST_JPG, CONTENT_TYPE_INVALID, HTTPStatus.BAD_REQUEST, USER_ROLES_STAFF),
    ("Valid service account", CONVERT_TEST_JPG, MediaTypes.CONTENT_TYPE_JPEG.value, HTTPStatus.OK, USER_ROLES_SYSTEM),
    ("Valid staff", CONVERT_TEST_PNG, MediaTypes.CONTENT_TYPE_PNG.value, HTTPStatus.OK, USER_ROLES_STAFF),
 ]


@pytest.mark.parametrize("desc,filename,content_type,status,roles", TEST_CONVERT_DATA)
def test_pdf_convert(session, client, jwt, desc, filename, content_type, status, roles):
    """Assert that a post pdf convert request works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = create_header_account(jwt, roles, "UT-TEST", "PS12345")
    if not content_type:
        if headers.get("Content-Type"):
            del headers["Content-Type"]
    else:
        headers["Content-Type"] = content_type

    if desc in ("Invalid role", "Invalid no payload"):
        response = client.post(PATH, data=None, headers=headers)
    else:
        raw_data = None
        with open(filename, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(PATH, data=raw_data, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        assert len(response.data) > 0


def is_ci_testing() -> bool:
    """Check unit test environment: exclude pub/sub for CI testing."""
    return  current_app.config.get("DEPLOYMENT_ENV", "testing") == "testing"
