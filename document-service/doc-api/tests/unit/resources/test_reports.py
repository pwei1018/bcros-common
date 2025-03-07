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

"""Tests to verify the endpoints for maintaining document service reports.

Test-Suite to ensure that the /reports endpoint is working as expected.
"""
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import utils as model_utils
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE
from doc_api.utils.logging import logger
from tests.unit.services.utils import create_header, create_header_account

TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
MOCK_AUTH_URL = "https://test.api.connect.gov.bc.ca/mockTarget/auth/api/v1/"
STAFF_ROLES = [STAFF_ROLE, BC_REGISTRY]
INVALID_ROLES = [COLIN_ROLE]
MEDIA_PDF = model_utils.CONTENT_TYPE_PDF
PARAMS1 = "?consumerIdentifier=UTBUS&consumerFilename=test.pdf&consumerFilingDate=2024-07-25"
TEST_DOC_ID: str = "UT-900000001"
GET_DOC_RECORD_PATH = "/api/v1/reports/document-records/"

# testdata pattern is ({description}, {doc_id}, {roles}, {account}, {status})
TEST_GET_DATA_DOC_RECORD = [
    ("Staff missing account", "xxxxxxx", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", "xxxxxxx", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid no results", TEST_DOC_ID, STAFF_ROLES, "UT1234", HTTPStatus.NOT_FOUND),
    ("Valid consumer doc id", TEST_DOC_ID, STAFF_ROLES, "UT1234", HTTPStatus.OK),
]


@pytest.mark.parametrize("desc,doc_id,roles,account,status", TEST_GET_DATA_DOC_RECORD)
def test_get_document_record(session, client, jwt, desc, doc_id, roles, account, status):
    """Assert that a get document record report request works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    req_path = GET_DOC_RECORD_PATH + doc_id

    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        create_path = "/api/v1/ppr/CORR" + PARAMS1 + "&consumerDocumentId=" + TEST_DOC_ID
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)
    # test
    response = client.get(req_path, headers=headers)

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        assert response.data
