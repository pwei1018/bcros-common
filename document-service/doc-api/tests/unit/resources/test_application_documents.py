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

"""Tests to verify the endpoints for maintaining application documents.

Test-Suite to ensure that the /application-documents endpoint is working as expected.
"""
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import Document
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE
from doc_api.services.pdf_convert import MediaTypes
from doc_api.utils.logging import logger
from tests.unit.services.utils import (
    create_header,
    create_header_account,
    create_header_account_upload,
    create_header_upload,
)

TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
TEST_SVG_DATAFILE = "tests/unit/services/data/test-image.svg"
TEST_FILENAME = "updated_name.pdf"
PARAM_TEST_FILENAME = "?consumerFilename=updated_name.pdf"
MOCK_AUTH_URL = "https://test.api.connect.gov.bc.ca/mockTarget/auth/api/v1/"
STAFF_ROLES = [STAFF_ROLE, BC_REGISTRY]
INVALID_ROLES = [COLIN_ROLE]
BASIC_ROLES = [BC_REGISTRY]
DOC_CLASS1 = DocumentClasses.CORP.value
DOC_TYPE1 = DocumentTypes.CORR.value
MEDIA_PDF = model_utils.CONTENT_TYPE_PDF
PARAMS1 = (
    "?name=test.pdf&datePublished=2024-07-25"
)
PATH: str = "/api/v1/application-documents" + PARAMS1
CHANGE_PATH = "/api/v1/application-documents/{doc_service_id}"
PATCH_PAYLOAD_INVALID = {}
PATCH_PAYLOAD = {
    "name": "test_patch.pdf",
    "datePublished": "2024-08-08",
}
# testdata pattern is ({description}, {content_type}, {roles}, {account}, {status}, {datafile})
TEST_CREATE_DATA = [
    ("Invalid no payload", MEDIA_PDF, BASIC_ROLES, "UT1234", HTTPStatus.BAD_REQUEST, None),
    ("Invalid content type", "XXXXX", STAFF_ROLES, "UT1234", HTTPStatus.BAD_REQUEST, TEST_DATAFILE),
    ("Missing account", MEDIA_PDF, STAFF_ROLES, None, HTTPStatus.BAD_REQUEST, TEST_DATAFILE),
    ("Valid pdf", MEDIA_PDF, STAFF_ROLES, "UT1234", HTTPStatus.CREATED, TEST_DATAFILE),
    ("Valid image", MediaTypes.CONTENT_TYPE_SVG.value, BASIC_ROLES, "UT1234", HTTPStatus.CREATED, TEST_SVG_DATAFILE),
]
# testdata pattern is ({description}, {roles}, {account}, {doc_service_id}, {payload}, {status})
TEST_PATCH_DATA = [
    ("Missing account", BASIC_ROLES, None, "INVALID", PATCH_PAYLOAD, HTTPStatus.BAD_REQUEST),
    ("No payload", BASIC_ROLES, "UT1234", "INVALID", None, HTTPStatus.BAD_REQUEST),
    ("Invalid doc service id", BASIC_ROLES, "UT1234", "INVALID", PATCH_PAYLOAD, HTTPStatus.NOT_FOUND),
    ("Valid", BASIC_ROLES, "UT1234", None, PATCH_PAYLOAD, HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status}, {ds_id},)
TEST_GET_DATA = [
    ("Invalid not found", BASIC_ROLES, "123456", HTTPStatus.NOT_FOUND, "1234"),
    ("Missing account", BASIC_ROLES, None, HTTPStatus.BAD_REQUEST, "1234"),
    ("Valid", BASIC_ROLES, "123456", HTTPStatus.OK, "DS99999999"),
]


@pytest.mark.parametrize("desc,roles,account_id,status,ds_id", TEST_GET_DATA)
def test_get(session, client, jwt, desc, roles, account_id, status, ds_id):
    """Assert that a request to get application document information by DRS ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account_id, MEDIA_PDF)
    elif account_id:
        headers = create_header_account(jwt, roles, "UT-TEST", account_id)
    else:
        headers = create_header(jwt, roles, "UT-TEST")
    req_path = CHANGE_PATH.format(doc_service_id="test")
 
    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)
        resp_json = response.json
        valid_id = resp_json.get("identifier")
        req_path = CHANGE_PATH.format(doc_service_id=valid_id)
    # test
    response = client.get(req_path, headers=headers, content_type="application/json")
    # check
    # logger.info(response.json)
    assert response.status_code == status


@pytest.mark.parametrize("desc,content_type,roles,account,status,datafile", TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, content_type, roles, account, status, datafile):
    """Assert that a post save new application document works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account, content_type)
    else:
        headers = create_header_upload(jwt, roles, content_type)
    req_path = PATH
    # test
    if not datafile:
        response = client.post(req_path, data=None, headers=headers, content_type=content_type)
    else:
        raw_data = None
        with open(datafile, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path, data=raw_data, headers=headers, content_type=content_type)
        # logger.info(response.json)
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("identifier")
        assert doc_json.get("name")
        assert doc_json.get("url")
        assert doc_json.get("dateCreated")


@pytest.mark.parametrize("desc,roles,account,doc_service_id,payload,status", TEST_PATCH_DATA)
def test_update(session, client, jwt, desc, roles, account, doc_service_id, payload, status):
    """Assert that a request to update document information (not the document itself) works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account, MEDIA_PDF)
    elif account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    req_path = CHANGE_PATH.format(doc_service_id=doc_service_id)

    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(PATH, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)
        resp_json = response.json
        valid_id = resp_json.get("identifier")
        req_path = CHANGE_PATH.format(doc_service_id=valid_id)
    # test
    response = client.patch(req_path, json=payload, headers=headers, content_type="application/json")
    logger.info(response.json)

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("identifier")
        assert doc_json.get("name") == payload.get("name")
        assert doc_json.get("datePublished")
        assert doc_json.get("dateCreated")
        assert not doc_json.get("url")
