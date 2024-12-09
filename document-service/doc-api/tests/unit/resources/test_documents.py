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

"""Tests to verify the endpoints for maintaining business documents.

Test-Suite to ensure that the /business endpoint is working as expected.
"""
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import Document
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE
from doc_api.utils.logging import logger
from tests.unit.services.utils import (
    create_header,
    create_header_account,
    create_header_account_upload,
    create_header_upload,
)

TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
TEST_FILENAME = "updated_name.pdf"
PARAM_TEST_FILENAME = "?consumerFilename=updated_name.pdf"
MOCK_AUTH_URL = "https://bcregistry-bcregistry-mock.apigee.net/mockTarget/auth/api/v1/"
STAFF_ROLES = [STAFF_ROLE, BC_REGISTRY]
INVALID_ROLES = [COLIN_ROLE]
DOC_CLASS1 = DocumentClasses.CORP.value
DOC_TYPE1 = DocumentTypes.CORP_MISC.value
MEDIA_PDF = model_utils.CONTENT_TYPE_PDF
PARAMS1 = (
    "?consumerIdentifier=UTBUS&consumerFilename=test.pdf&consumerFilingDate=2024-07-25" + "&consumerDocumentId=UT999999"
)
PATH: str = "/api/v1/documents/{doc_class}/{doc_type}" + PARAMS1
CHANGE_PATH = "/api/v1/documents/{doc_service_id}"
VERIFY_PATH = "/api/v1/documents/verify/{doc_id}"
DOC_TYPE_PATH = "/api/v1/documents/document-types"
PATCH_PAYLOAD_INVALID = {}
PATCH_PAYLOAD = {
    "consumerDocumentId": "P0000001",
    "consumerFilename": "test_patch.pdf",
    "consumerIdentifier": "P8888999",
    "consumerFilingDateTime": "2024-08-08",
}
PATCH_REMOVE_PAYLOAD = {
    "removed": True
}


# testdata pattern is ({description}, {content_type}, {roles}, {account}, {doc_class}, {doc_type}, {status})
TEST_CREATE_DATA = [
    ("Invalid doc type", MEDIA_PDF, STAFF_ROLES, "UT1234", DOC_CLASS1, "JUNK", HTTPStatus.BAD_REQUEST),
    ("Invalid content type", "XXXXX", STAFF_ROLES, "UT1234", DOC_CLASS1, DOC_TYPE1, HTTPStatus.BAD_REQUEST),
    ("Staff missing account", MEDIA_PDF, STAFF_ROLES, None, DOC_CLASS1, DOC_TYPE1, HTTPStatus.BAD_REQUEST),
    ("Invalid role", MEDIA_PDF, INVALID_ROLES, "UT1234", DOC_CLASS1, DOC_TYPE1, HTTPStatus.UNAUTHORIZED),
    ("Valid staff", MEDIA_PDF, STAFF_ROLES, "UT1234", DOC_CLASS1, DOC_TYPE1, HTTPStatus.CREATED),
    ("Valid no payload", MEDIA_PDF, STAFF_ROLES, "UT1234", DOC_CLASS1, DOC_TYPE1, HTTPStatus.CREATED),
]
# testdata pattern is ({description}, {roles}, {account}, {doc_service_id}, {payload}, {status})
TEST_PATCH_DATA = [
    ("Staff missing account", STAFF_ROLES, None, "INVALID", PATCH_PAYLOAD, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", "INVALID", PATCH_PAYLOAD, HTTPStatus.UNAUTHORIZED),
    ("Invalid doc service id", STAFF_ROLES, "UT1234", "INVALID", PATCH_PAYLOAD, HTTPStatus.NOT_FOUND),
    ("Valid staff", STAFF_ROLES, "UT1234", None, PATCH_PAYLOAD, HTTPStatus.OK),
    ("Valid staff removed", STAFF_ROLES, "UT1234", None, PATCH_REMOVE_PAYLOAD, HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {doc_service_id}, {status})
TEST_PUT_DATA = [
    ("Staff missing account", STAFF_ROLES, None, "INVALID", HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", "INVALID", HTTPStatus.UNAUTHORIZED),
    ("Invalid doc service id", STAFF_ROLES, "UT1234", "INVALID", HTTPStatus.NOT_FOUND),
    ("Valid staff", STAFF_ROLES, "UT1234", None, HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {doc_id}, {status})
TEST_DOC_ID_DATA = [
    ("Staff missing account", STAFF_ROLES, None, "INVALID", HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", "INVALID", HTTPStatus.UNAUTHORIZED),
    ("Not found doc id", STAFF_ROLES, "UT1234", "UT-99990001", HTTPStatus.NOT_FOUND),
    ("Doc ID exists", STAFF_ROLES, "UT1234", "UT999999", HTTPStatus.OK),
]
# testdata pattern is ({description}, {content_type}, {roles}, {account}, {doc_class}, {doc_type}, {status})
TEST_DELETE_DATA = [
    ("Invalid doc type", MEDIA_PDF, STAFF_ROLES, "UT1234", DOC_CLASS1, "JUNK", HTTPStatus.BAD_REQUEST),
    ("Staff missing account", MEDIA_PDF, STAFF_ROLES, None, DOC_CLASS1, DOC_TYPE1, HTTPStatus.BAD_REQUEST),
    ("Invalid role", MEDIA_PDF, INVALID_ROLES, "UT1234", DOC_CLASS1, DOC_TYPE1, HTTPStatus.UNAUTHORIZED),
    ("Valid staff", MEDIA_PDF, STAFF_ROLES, "UT1234", DOC_CLASS1, DOC_TYPE1, HTTPStatus.CREATED)
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_TYPE_DATA = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]


@pytest.mark.parametrize("desc,content_type,roles,account,doc_class,doc_type,status", TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, content_type, roles, account, doc_class, doc_type, status):
    """Assert that a post save new business document works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    json_data = {}
    if account:
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account, content_type)
    else:
        headers = create_header_upload(jwt, roles, content_type)
    req_path = PATH.format(doc_class=doc_class, doc_type=doc_type)
    # test
    if status != HTTPStatus.CREATED:
        response = client.post(req_path, json=json_data, headers=headers, content_type=content_type)
    elif desc != "Valid no payload":
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path, data=raw_data, headers=headers, content_type=content_type)
        logger.info(response.json)
    else:
        response = client.post(req_path, data=None, headers=headers, content_type=content_type)
        logger.info(response.json)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("documentServiceId")
        if desc != "Valid no payload":
            assert doc_json.get("documentURL")
        else:
            assert not doc_json.get("documentURL")
        doc: Document = Document.find_by_doc_service_id(doc_json.get("documentServiceId"))
        assert doc
        assert doc.document_type == doc_type


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
        response = client.post(
            PATH.format(doc_class=DOC_CLASS1, doc_type=DOC_TYPE1), data=None, headers=headers, content_type=MEDIA_PDF
        )
        # logger.info(response.json)
        resp_json = response.json
        valid_id = resp_json.get("documentServiceId")
        req_path = CHANGE_PATH.format(doc_service_id=valid_id)
    # test
    response = client.patch(req_path, json=payload, headers=headers, content_type="application/json")

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        if desc != "Valid staff removed":
            doc_json = response.json
            assert doc_json
            assert doc_json.get("documentServiceId")
            assert doc_json.get("documentClass")
            assert doc_json.get("consumerDocumentId") == payload.get("consumerDocumentId")
            assert doc_json.get("consumerIdentifier") == payload.get("consumerIdentifier")
            assert doc_json.get("consumerFilename") == payload.get("consumerFilename")
            assert not doc_json.get("documentURL")
        else:
            assert not response.json


@pytest.mark.parametrize("desc,roles,account,doc_service_id,status", TEST_PUT_DATA)
def test_replace(session, client, jwt, desc, roles, account, doc_service_id, status):
    """Assert that a request to add/replace a document works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account, MEDIA_PDF)
    else:
        headers = create_header_upload(jwt, roles, MEDIA_PDF)
    req_path = CHANGE_PATH.format(doc_service_id=doc_service_id)

    # test
    raw_data = None
    if status == HTTPStatus.OK:  # Create.
        response = client.post(
            PATH.format(doc_class=DOC_CLASS1, doc_type=DOC_TYPE1), data=None, headers=headers, content_type=MEDIA_PDF
        )
        # logger.info(response.json)
        resp_json = response.json
        valid_id = resp_json.get("documentServiceId")
        req_path = CHANGE_PATH.format(doc_service_id=valid_id) + PARAM_TEST_FILENAME
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
    response = client.put(req_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("documentServiceId")
        assert doc_json.get("documentClass")
        assert doc_json.get("consumerDocumentId")
        assert doc_json.get("consumerIdentifier")
        assert doc_json.get("consumerFilename") == TEST_FILENAME
        assert doc_json.get("documentURL")


@pytest.mark.parametrize("desc,content_type,roles,account,doc_class,doc_type,status", TEST_DELETE_DATA)
def test_delete(session, client, jwt, desc, content_type, roles, account, doc_class, doc_type, status):
    """Assert that a delete document from storage works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    json_data = {}
    if account:
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account, content_type)
    else:
        headers = create_header_upload(jwt, roles, content_type)
    req_path = PATH.format(doc_class=doc_class, doc_type=doc_type)
    # test
    if status != HTTPStatus.CREATED:
        response = client.post(req_path, json=json_data, headers=headers, content_type=content_type)
    else:
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path, data=raw_data, headers=headers, content_type=content_type)
        # logger.info(response.json)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("documentServiceId")
        assert doc_json.get("documentURL")
        req_path = CHANGE_PATH.format(doc_service_id=doc_json.get("documentServiceId"))
        response = client.delete(req_path, headers=headers)
        assert response.status_code == HTTPStatus.OK
        doc_json = response.json
        assert not doc_json.get("documentURL")
        doc: Document = Document.find_by_doc_service_id(doc_json.get("documentServiceId"))
        assert doc
        assert not doc.doc_storage_url


@pytest.mark.parametrize("desc,roles,account,doc_id,status", TEST_DOC_ID_DATA)
def test_verify_doc_id(session, client, jwt, desc, roles, account, doc_id, status):
    """Assert that a request to verify a consumer document ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account_upload(jwt, roles, "UT-TEST", account, MEDIA_PDF)
    else:
        headers = create_header_upload(jwt, roles, MEDIA_PDF)
    req_path = VERIFY_PATH.format(doc_id=doc_id)

    # test
    if status == HTTPStatus.OK:  # Create.
        response = client.post(
            PATH.format(doc_class=DOC_CLASS1, doc_type=DOC_TYPE1), data=None, headers=headers, content_type=MEDIA_PDF
        )
        # logger.info(response.json)
    # test
    response = client.get(req_path, headers=headers)

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        docs_json = response.json
        assert docs_json
        for doc_json in docs_json:
            assert doc_json.get("documentServiceId")
            assert doc_json.get("documentClass")
            assert doc_json.get("documentType")
            assert doc_json.get("consumerDocumentId") == doc_id
            assert not doc_json.get("documentURL")


@pytest.mark.parametrize("desc,roles,account,status", TEST_TYPE_DATA)
def test_get_types(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get document types works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    response = client.get(DOC_TYPE_PATH, headers=headers)

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        types_json = response.json
        assert types_json
        assert types_json.get("COOP")
        assert types_json.get("CORP")
        assert types_json.get("FIRM")
        assert types_json.get("LP_LLP")
        assert types_json.get("MHR")
        assert types_json.get("NR")
        assert types_json.get("OTHER")
        assert types_json.get("PPR")
        assert types_json.get("SOCIETY")
        assert types_json["SOCIETY"][0].get("documentType")
        assert types_json["SOCIETY"][0].get("documentTypeDescription")
