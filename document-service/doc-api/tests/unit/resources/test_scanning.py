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
from doc_api.models import ScanningAuthor, ScanningBox, ScanningParameter, ScanningSchedule
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
PATH_SCHEDULES: str = "/api/v1/scanning/schedules"
PATH_PARAMETERS: str = "/api/v1/scanning/parameters"
PATH_BATCH_ID: str = "/api/v1/scanning/batchid/{accession_number}"
PATH_BOXES: str = "/api/v1/scanning/boxes"
PATH_BOXES_SEQUENCE: str = "/api/v1/scanning/boxes/{sequence_num}/{schedule_num}"
CONTENT_TYPE_JSON = "application/json"
PAYLOAD_INVALID = {}
PAYLOAD_VALID = {
    "scanDateTime": "2024-07-01T19:00:00+00:00",
    "accessionNumber": "AN-0001",
    "batchId": "1234",
    "author": "Jane Smith",
    "pageCount": 3,
}
PAYLOAD_VALID_MINIMAL = {
    "pageCount": 1,
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
SCHEDULE = {
    "scheduleNumber": 20,
    "sequenceNumber": 10,
}
PARAMETERS = {
    "useDocumentFeeder": True,
    "showTwainUi": True,
    "showTwainProgress": True,
    "useFullDuplex": True,
    "useLowResolution": True,
    "maxPagesInBox": 1000,
}
UPDATE_PARAMETERS = {
    "useDocumentFeeder": False,
    "showTwainUi": False,
    "showTwainProgress": False,
    "useFullDuplex": False,
    "useLowResolution": False,
    "maxPagesInBox": 10,
}
BOX = {
    "boxId": 200000000,
    "boxNumber": 10,
    "sequenceNumber": 20,
    "scheduleNumber": 30,
    "openedDate": "2024-09-22",
    "closedDate": "2024-09-23",
    "pageCount": 1000,
}
UPDATE_BOX = {
    "boxId": 200000000,
    "boxNumber": 10,
    "sequenceNumber": 20,
    "scheduleNumber": 30,
    "openedDate": "2024-09-21",
    "closedDate": "2024-09-24",
    "pageCount": 1500,
}
# testdata pattern is ({description}, {payload}, {roles}, {account}, {doc_class}, {cons_doc_id}, {status})
TEST_CREATE_DATA = [
    ("Invalid doc class", PAYLOAD_VALID, STAFF_ROLES, "UT1234", "JUNK", "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid payload", PAYLOAD_INVALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Staff missing account", PAYLOAD_VALID, STAFF_ROLES, None, DOC_CLASS1, "UT900001", HTTPStatus.BAD_REQUEST),
    ("Invalid role", PAYLOAD_VALID, INVALID_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", PAYLOAD_VALID, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.CREATED),
    ("Valid staff minimal", PAYLOAD_VALID_MINIMAL, STAFF_ROLES, "UT1234", DOC_CLASS1, "UT900001", HTTPStatus.CREATED),
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
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_SCHEDULES = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_PARAMETERS = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_CREATE_DATA_PARAMETERS = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Invalid exists", STAFF_ROLES, "UT1234", HTTPStatus.BAD_REQUEST),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.CREATED),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_PATCH_DATA_PARAMETERS = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Invalid does not exist", STAFF_ROLES, "UT1234", HTTPStatus.BAD_REQUEST),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_BATCH_ID = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_GET_DATA_BOXES = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.OK),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_CREATE_DATA_BOXES = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Valid staff", STAFF_ROLES, "UT1234", HTTPStatus.CREATED),
]
# testdata pattern is ({description}, {roles}, {account}, {status})
TEST_PATCH_DATA_BOXES = [
    ("Staff missing account", STAFF_ROLES, None, HTTPStatus.BAD_REQUEST),
    ("Invalid role", INVALID_ROLES, "UT1234", HTTPStatus.UNAUTHORIZED),
    ("Invalid does not exist", STAFF_ROLES, "UT1234", HTTPStatus.NOT_FOUND),
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
        assert scan_json.get("createDateTime")
        if payload.get("scanDateTime"):
            assert scan_json.get("scanDateTime")
        if payload.get("accessionNumber"):
            assert scan_json.get("accessionNumber") == payload.get("accessionNumber")
        if payload.get("batchId"):
            assert scan_json.get("batchId") == payload.get("batchId")
        if payload.get("author"):
            assert scan_json.get("author") == payload.get("author")
        if payload.get("pageCount"):
            assert scan_json.get("pageCount") == payload.get("pageCount")
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


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_SCHEDULES)
def test_get_schedules(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get scanning schedules works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if status == HTTPStatus.OK:
        schedule: ScanningSchedule = ScanningSchedule.create_from_json(SCHEDULE)
        schedule.id = 200000000
        schedule.save()
    response = client.get(PATH_SCHEDULES, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        for result_json in results_json:
            assert result_json.get("sequenceNumber")
            assert result_json.get("scheduleNumber")


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_PARAMETERS)
def test_get_parameters(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get scanning parameters works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if status == HTTPStatus.OK:
        parameters: ScanningParameter = ScanningParameter.create_from_json(PARAMETERS)
        parameters.id = 200000000
        parameters.save()
    response = client.get(PATH_PARAMETERS, headers=headers)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        result_json = response.json
        assert result_json
        assert result_json.get("useDocumentFeeder")
        assert result_json.get("showTwainUi")
        assert result_json.get("showTwainProgress")
        assert result_json.get("useFullDuplex")
        assert result_json.get("useLowResolution")
        assert result_json.get("maxPagesInBox") > 0


@pytest.mark.parametrize("desc,roles,account,status", TEST_CREATE_DATA_PARAMETERS)
def test_create_parameters(session, client, jwt, desc, roles, account, status):
    """Assert that a request to create scanning parameters works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if desc == "Invalid exists":
        parameters: ScanningParameter = ScanningParameter.create_from_json(PARAMETERS)
        parameters.id = 200000000
        parameters.save()
    response = client.post(PATH_PARAMETERS, json=PARAMETERS, headers=headers, content_type=CONTENT_TYPE_JSON)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        result_json = response.json
        assert result_json
        assert result_json.get("useDocumentFeeder")
        assert result_json.get("showTwainUi")
        assert result_json.get("showTwainProgress")
        assert result_json.get("useFullDuplex")
        assert result_json.get("useLowResolution")
        assert result_json.get("maxPagesInBox") > 0


@pytest.mark.parametrize("desc,roles,account,status", TEST_PATCH_DATA_PARAMETERS)
def test_patch_parameters(session, client, jwt, desc, roles, account, status):
    """Assert that a request to update scanning parameters works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if status == HTTPStatus.OK:
        parameters: ScanningParameter = ScanningParameter.create_from_json(PARAMETERS)
        parameters.id = 200000000
        parameters.save()
    response = client.patch(PATH_PARAMETERS, json=UPDATE_PARAMETERS, headers=headers, content_type=CONTENT_TYPE_JSON)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        result_json = response.json
        assert result_json
        assert result_json.get("useDocumentFeeder") == UPDATE_PARAMETERS.get("useDocumentFeeder")
        assert result_json.get("showTwainUi") == UPDATE_PARAMETERS.get("showTwainUi")
        assert result_json.get("showTwainProgress") == UPDATE_PARAMETERS.get("showTwainProgress")
        assert result_json.get("useFullDuplex") == UPDATE_PARAMETERS.get("useFullDuplex")
        assert result_json.get("useLowResolution") == UPDATE_PARAMETERS.get("useLowResolution")
        assert result_json.get("maxPagesInBox") == UPDATE_PARAMETERS.get("maxPagesInBox")


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_BATCH_ID)
def test_get_max_batch_id(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get the scanning maximum batch id by accession number works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    test_accession_num: str = "UT-MAX-000099"
    if status == HTTPStatus.OK:
        scan_doc: DocumentScanning = DocumentScanning.create_from_json(PAYLOAD_VALID, "UT-MAX-999999", DOC_CLASS1)
        scan_doc.accession_number = test_accession_num
        scan_doc.id = 200000000
        scan_doc.save()
    req_path = PATH_BATCH_ID.format(accession_number=test_accession_num)
    response = client.get(req_path, headers=headers)
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        result_json = response.json
        assert result_json
        assert str(result_json.get("batchId")) == PAYLOAD_VALID.get("batchId")


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_BOXES)
def test_get_all_boxes(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get all scanning boxes works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if status == HTTPStatus.OK:
        box: ScanningBox = ScanningBox.create_from_json(BOX)
        box.id = 200000000
        box.save()
    response = client.get(PATH_BOXES, headers=headers)
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        assert len(results_json) >= 1
        for result_json in results_json:
            assert result_json.get("boxId")
            assert result_json.get("boxNumber")
            assert result_json.get("sequenceNumber")
            assert result_json.get("scheduleNumber")


@pytest.mark.parametrize("desc,roles,account,status", TEST_GET_DATA_BOXES)
def test_get_sequence_boxes(session, client, jwt, desc, roles, account, status):
    """Assert that a request to get all scanning boxes by sequence and schedule numbers works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    sequence_num: str = BOX.get("sequenceNumber")
    schedule_num: str = BOX.get("scheduleNumber")
    # test
    if status == HTTPStatus.OK:
        box: ScanningBox = ScanningBox.create_from_json(BOX)
        box.id = 200000000
        box.save()
    req_path = PATH_BOXES_SEQUENCE.format(sequence_num=sequence_num, schedule_num=schedule_num)
    response = client.get(req_path, headers=headers)
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        assert len(results_json) >= 1
        for result_json in results_json:
            assert result_json.get("boxId")
            assert result_json.get("boxNumber")
            assert result_json.get("sequenceNumber") == sequence_num
            assert result_json.get("scheduleNumber") == schedule_num


@pytest.mark.parametrize("desc,roles,account,status", TEST_CREATE_DATA_BOXES)
def test_create_boxes(session, client, jwt, desc, roles, account, status):
    """Assert that a request to create a scanning box works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    response = client.post(PATH_BOXES, json=BOX, headers=headers, content_type=CONTENT_TYPE_JSON)
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        result_json = response.json
        assert result_json
        assert result_json.get("boxId")
        assert result_json.get("boxNumber") == BOX.get("boxNumber")
        assert result_json.get("sequenceNumber") == BOX.get("sequenceNumber")
        assert result_json.get("scheduleNumber") == BOX.get("scheduleNumber")


@pytest.mark.parametrize("desc,roles,account,status", TEST_PATCH_DATA_BOXES)
def test_update_boxes(session, client, jwt, desc, roles, account, status):
    """Assert that a request to update an existing scanning box works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, "UT-TEST", account)
    else:
        headers = create_header(jwt, roles)
    # test
    if status == HTTPStatus.OK:
        box: ScanningBox = ScanningBox.create_from_json(BOX)
        box.id = UPDATE_BOX.get("boxId")
        box.save()
    response = client.patch(PATH_BOXES, json=UPDATE_BOX, headers=headers, content_type=CONTENT_TYPE_JSON)
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        result_json = response.json
        assert result_json
        assert result_json.get("boxId") == UPDATE_BOX.get("boxId")
        assert result_json.get("pageCount") == UPDATE_BOX.get("pageCount")
