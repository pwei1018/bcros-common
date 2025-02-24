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
from doc_api.services.authz import BC_REGISTRY
from tests.unit.services.utils import (
    create_header_account,
    create_header_account_upload,
)


USER_ROLES = [BC_REGISTRY]
TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
TEST_FILENAME = "updated_name.pdf"
PARAM_TEST_FILENAME = "?consumerFilename=updated_name.pdf"
MOCK_AUTH_URL = "https://test.api.connect.gov.bc.ca/mockTarget/auth/api/v1/"
MEDIA_PDF = model_utils.CONTENT_TYPE_PDF
PARAMS1 = (
    "?consumerFilename=test.pdf&consumerFilingDate=2005-10-31"
)
PATH: str = "/api/v1/application-reports/{entity_id}/{event_id}/{report_type}"
CHANGE_PATH = "/api/v1/application-reports/{doc_service_id}"
EVENT_PATH = "/api/v1/application-reports/events/{event_id}"
HISTORY_PATH = "/api/v1/application-reports/history/{entity_id}"
PATCH_PAYLOAD_EMPTY = {}
PATCH_PAYLOAD = {
    "name": "new-name.pdf",
    "datePublished": "2022-10-31T19:00:00+00:00",
    "reportType": "NEW_TYPE"
}
PATCH_PAYLOAD1 = {
    "name": ".pdf",
    "datePublished": "2022-10-31T19:00:00+00:00",
    "reportType": "NEW_TYPE"
}
PATCH_PAYLOAD2 = {
    "name": "new-name.pdf",
    "datePublished": "February 2, 2020",
    "reportType": "NEW_TYPE"
}
PATCH_PAYLOAD3 = {
    "name": "new-name.pdf",
    "datePublished": "2022-10-31T19:00:00+00:00",
    "reportType": "N"
}
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_CREATE_DATA = [
    ("Invalid entity ID", "1", "12345", "FILING", HTTPStatus.BAD_REQUEST),
    ("Invalid event ID", "UT-123456", "JUNK", "FILING", HTTPStatus.BAD_REQUEST),
    ("Invalid report type", "UT-123456", "123456", "F", HTTPStatus.BAD_REQUEST),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST),
    ("Valid minimal", "UT-123456", "123456", "FILING", HTTPStatus.CREATED),
    ("Valid all", "UT-123456", "123456", "FILING", HTTPStatus.CREATED),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {payload})
TEST_PATCH_DATA = [
    ("Invalid name", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD1),
    ("Invalid event ID", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD2),
    ("Invalid report type", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD3),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD_EMPTY),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK, PATCH_PAYLOAD),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_GET_ID_DATA = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_GET_EVENT_DATA = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_GET_HISTORY_DATA = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK),
]


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status", TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, entity_id, event_id, report_type, status):
    """Assert that a post save new report works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    headers = create_header_account_upload(jwt, USER_ROLES, "UT-TEST", "PS12345", MEDIA_PDF)
    req_path = PATH.format(entity_id=entity_id, event_id=event_id, report_type=report_type)
    if desc == "Valid all":
        req_path += PARAMS1
    # test
    if status != HTTPStatus.CREATED:
        response = client.post(req_path, data=None, headers=headers, content_type=MEDIA_PDF)
    else:
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        report_json = response.json
        assert report_json
        assert report_json.get("identifier")
        assert report_json.get("url")
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(report_json.get("identifier"))
        assert app_report


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,payload", TEST_PATCH_DATA)
def test_update(session, client, jwt, desc, entity_id, event_id, report_type, status, payload):
    """Assert that a request to update report information (not the report itself) works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH.format(entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, USER_ROLES, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, USER_ROLES, "UT-TEST", "PS12345")
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
    response = client.patch(req_path, json=payload, headers=headers, content_type="application/json")

    # check
    # logger.info(response.json)
    assert response.status_code == status


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status", TEST_GET_ID_DATA)
def test_get_by_id(session, client, jwt, desc, entity_id, event_id, report_type, status):
    """Assert that a request to get report information (not the report itself) by DRS ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH.format(entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, USER_ROLES, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, USER_ROLES, "UT-TEST", "PS12345")
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
    if status == HTTPStatus.OK:
        assert response.json


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status", TEST_GET_EVENT_DATA)
def test_get_event_id(session, client, jwt, desc, entity_id, event_id, report_type, status):
    """Assert that a request to get report information (not the report itself) by an event ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH.format(entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, USER_ROLES, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, USER_ROLES, "UT-TEST", "PS12345")
    req_path = EVENT_PATH.format(event_id=event_id)
    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)

    # test
    response = client.get(req_path, headers=headers, content_type="application/json")

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if status == HTTPStatus.OK:
        assert response.json


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status", TEST_GET_HISTORY_DATA)
def test_get_entity_id(session, client, jwt, desc, entity_id, event_id, report_type, status):
    """Assert that a request to get report information (not the report itself) by an entity ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH.format(entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, USER_ROLES, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, USER_ROLES, "UT-TEST", "PS12345")
    req_path = HISTORY_PATH.format(entity_id=entity_id)
    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)

    # test
    response = client.get(req_path, headers=headers, content_type="application/json")

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if status == HTTPStatus.OK:
        assert response.json
