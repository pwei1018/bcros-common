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

"""Tests to verify the endpoints for maintaining document scanning records.

Test-Suite to ensure that the /scanning endpoint is working as expected.
"""
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import DocumentScanning
from doc_api.models import utils as model_utils, ScanningAuthor
from doc_api.models.type_tables import DocumentClasses
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE
from doc_api.utils.logging import logger
from tests.unit.services.utils import create_header, create_header_account

MOCK_AUTH_URL = "https://bcregistry-bcregistry-mock.apigee.net/mockTarget/auth/api/v1/"
STAFF_ROLES = [STAFF_ROLE, BC_REGISTRY]
INVALID_ROLES = [COLIN_ROLE]
DOC_CLASS1 = DocumentClasses.CORP.value
PATH: str = "/api/v1/scanning/{doc_class}/{consumerDocumentId}"
PATH_CLASSES: str = "/api/v1/scanning/document-classes"
PATH_TYPES: str = "/api/v1/scanning/document-types"
PATH_AUTHORS: str = "/api/v1/scanning/authors"
CONTENT_TYPE_JSON = "application/json"
PAYLOAD_INVALID = {}
PAYLOAD_VALID = {
    "scanDateTime": "2024-07-01T19:00:00+00:00",
    "accessionNumber": "AN-0001",
    "batchId": "1234",
    "author": "Jane Smith",
    "pageCount": 3,
}
PATCH_PAYLOAD_VALID = {
    "scanDateTime": "2024-07-01T19:00:00+00:00",
    "accessionNumber": "AN-0001",
    "batchId": "1234",
    "author": "Jane Smith",
    "pageCount": 3,
}
AUTHOR = {
    "firstName": "Bob",
    "lastName": "Smith",
    "jobTitle": "Analyst",
    "email": "bsmith-12@gmail.com",
    "phoneNumber": "250 721-1234",
}
# testdata pattern is ({description}, {payload}, {roles}, {account}, {doc_class}, {cons_doc_id}, {status})
TEST_CREATE_DATA = [
    ("Invalid doc class", PAYLOAD_VALID, STAFF_ROLES, "UT1234", "JUNK", "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid payload", PAYLOAD_INVALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Staff missing account", PAYLOAD_VALID, STAFF_ROLES, None, DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid role", PAYLOAD_VALID, INVALID_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", PAYLOAD_VALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.CREATED),
]
# testdata pattern is ({description}, {payload}, {roles}, {account}, {doc_class}, {cons_doc_id}, {status})
TEST_PATCH_DATA = [
    ("Invalid doc class", PAYLOAD_VALID, STAFF_ROLES, "UT1234", "JUNK", "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid payload", PAYLOAD_INVALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Staff missing account", PAYLOAD_VALID, STAFF_ROLES, None, DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid role", PAYLOAD_VALID, INVALID_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.UNAUTHORIZED),
    ("Invalid no record", PATCH_PAYLOAD_VALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.NOT_FOUND),
    ("Valid staff", PATCH_PAYLOAD_VALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {doc_class}, {cons_doc_id}, {status})
TEST_GET_DATA = [
    ("Staff missing account", STAFF_ROLES, None, DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.UNAUTHORIZED),
    ("Invalid doc service id", STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.NOT_FOUND),
    ("Valid staff", STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_CLASSES = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_TYPES = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_AUTHORS = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]


@pytest.mark.parametrize("desc,payload,roles,account,doc_class,cons_doc_id,status", TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, payload, roles, account, doc_class, cons_doc_id, status):
    """Assert that a post save new document scanning record works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    req_path = PATH.format(doc_class=doc_class, consumerDocumentId=cons_doc_id)
    # test
    response = client.post(req_path, json=payload, headers=headers, content_type=CONTENT_TYPE_JSON)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        scan_json = response.json
        assert scan_json
        assert scan_json.get("consumerDocumentId") == cons_doc_id
        assert scan_json.get("documentClass") == doc_class
        assert scan_json.get("scanDateTime")
        assert scan_json.get("accessionNumber")
        assert scan_json.get("batchId")
        assert scan_json.get("author")
        assert scan_json.get("pageCount")
        scan_doc: DocumentScanning = DocumentScanning.find_by_document_id(cons_doc_id, doc_class)
        assert scan_doc
        assert scan_doc.document_class == doc_class
        assert scan_doc.consumer_document_id == cons_doc_id


@pytest.mark.parametrize("desc,payload,roles,account,doc_class,cons_doc_id,status", TEST_PATCH_DATA)
def test_update(session, client, jwt, desc, payload, roles, account, doc_class, cons_doc_id, status):
    """Assert that a patch update document scanning record works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    req_path = PATH.format(doc_class=doc_class, consumerDocumentId=cons_doc_id)
    if status == HTTPStatus.OK:
        scan_doc: DocumentScanning = DocumentScanning.create_from_json(PAYLOAD_VALID, cons_doc_id, doc_class)
        scan_doc.id = 200000000
        scan_doc.save()
    # test
    response = client.patch(req_path, json=payload, headers=headers, content_type=CONTENT_TYPE_JSON)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        scan_json = response.json
        assert scan_json
        assert scan_json.get("consumerDocumentId") == cons_doc_id
        assert scan_json.get("documentClass") == doc_class
        assert scan_json.get("scanDateTime")
        assert scan_json.get("accessionNumber")
        assert scan_json.get("batchId")
        assert scan_json.get("author")
        assert scan_json.get("pageCount")
        scan_doc: DocumentScanning = DocumentScanning.find_by_document_id(cons_doc_id, doc_class)
        assert scan_doc
        assert scan_doc.document_class == doc_class
        assert scan_doc.consumer_document_id == cons_doc_id


@pytest.mark.parametrize("desc,roles,account,doc_class,cons_doc_id,status", TEST_GET_DATA)
def test_get(session, client, jwt, desc, roles, account, doc_class, cons_doc_id, status):
    """Assert that get a document scanning record works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    req_path = PATH.format(doc_class=doc_class, consumerDocumentId=cons_doc_id)
    if status == HTTPStatus.OK:
        scan_doc: DocumentScanning = DocumentScanning.create_from_json(PAYLOAD_VALID, cons_doc_id, doc_class)
        scan_doc.id = 200000000
        scan_doc.save()
    # test
    response = client.get(req_path, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        scan_json = response.json
        assert scan_json
        assert scan_json.get("consumerDocumentId") == cons_doc_id
        assert scan_json.get("documentClass") == doc_class
        assert scan_json.get("scanDateTime")
        assert scan_json.get("accessionNumber")
        assert scan_json.get("batchId")
        assert scan_json.get("author")
        assert scan_json.get("pageCount")
        scan_doc: DocumentScanning = DocumentScanning.find_by_document_id(cons_doc_id, doc_class)
        assert scan_doc
        assert scan_doc.document_class == doc_class
        assert scan_doc.consumer_document_id == cons_doc_id


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_CLASSES)
def test_get_classes(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get scanning document classes works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    response = client.get(PATH_CLASSES, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        for class_json in results_json:
            assert class_json.get("ownerType")
            assert class_json.get("documentClass")
            assert class_json.get("documentClassDescription")
            assert "active" in class_json
            assert "scheduleNumber" in class_json


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_TYPES)
def test_get_types(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get scanning document types works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    response = client.get(PATH_TYPES, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        for type_json in results_json:
            assert type_json.get("documentType")
            assert type_json.get("documentTypeDescription")
            assert "active" in type_json
            assert type_json.get("applicationId")


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_AUTHORS)
def test_get_authors(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get scanning authors works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if status == HTTPStatus.OK:
        author: ScanningAuthor = ScanningAuthor.create_from_json(AUTHOR)
        author.id = 200000000
        author.save()
    response = client.get(PATH_AUTHORS, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        for author_json in results_json:
            assert author_json.get("firstName")
            assert author_json.get("lastName")
