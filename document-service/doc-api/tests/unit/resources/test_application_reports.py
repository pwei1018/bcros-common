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
import copy
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import ApplicationReport, Document
from doc_api.models import utils as model_utils
from doc_api.utils.logging import logger
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE, SYSTEM_ROLE
from tests.unit.services.utils import (
    create_header_account,
    create_header_account_report,
    create_header_account_upload,
)


USER_ROLES = [BC_REGISTRY]
PRODUCT_ROLES_SYSTEM = [SYSTEM_ROLE]
PRODUCT_ROLES_STAFF = [STAFF_ROLE]
PRODUCT_ROLES_COLIN = [COLIN_ROLE]
TEST_DOC1 = {
    "consumerDocumentId": "T0000003",
    "consumerFilename": "change-address.pdf",
    "consumerIdentifier": "T0000005",
    "documentType": "ADDR",
    "documentClass": "CORP",
    "consumerFilingDateTime": "2025-06-01T19:00:00+00:00",
    "description": "A meaningful description of the document.",
    "author": "John Smith",
    "consumerReferenceId": "3333001"
}
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
PATH_PRODUCT: str = "/api/v1/application-reports/{prod_code}/{entity_id}/{event_id}/{report_type}"
CHANGE_PATH_PRODUCT = "/api/v1/application-reports/{prod_code}/{doc_service_id}"
EVENT_PATH_PRODUCT = "/api/v1/application-reports/events/{prod_code}/{entity_id}/{event_id}"
HISTORY_PATH_PRODUCT = "/api/v1/application-reports/history/{prod_code}/{entity_id}"
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
CC_NOA_LEGACY_INFILE = "tests/unit/reports/data/legacy-noa.pdf"
CC_NOA_LEGACY_OUTFILE = "tests/unit/resources/legacy-noa-certified.pdf"
CC_FILING_LEGACY_INFILE = "tests/unit/reports/data/legacy-filing.pdf"
CC_FILING_LEGACY_OUTFILE = "tests/unit/resources/legacy-filing-certified.pdf"
CC_NOA_INFILE = "tests/unit/reports/data/noa.pdf"
CC_NOA_OUTFILE = "tests/unit/resources/noa-certified.pdf"
CC_FILING_INFILE = "tests/unit/reports/data/filing.pdf"
CC_FILING_OUTFILE = "tests/unit/resources/filing-certified.pdf"

# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_CREATE_DATA = [
    ("Invalid entity ID", "1", "12345", "FILING", HTTPStatus.BAD_REQUEST),
    ("Invalid event ID", "UT-123456", "JUNK", "FILING", HTTPStatus.BAD_REQUEST),
    ("Invalid report type", "UT-123456", "123456", "F", HTTPStatus.BAD_REQUEST),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST),
    ("Valid minimal", "UT-123456", "123456", "FILING", HTTPStatus.CREATED),
    ("Valid all", "UT-123456", "123456", "FILING", HTTPStatus.CREATED),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {prod_code}, {roles})
TEST_CREATE_DATA_PRODUCT = [
    ("Invalid entity ID", "1", "12345", "FILING", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid event ID", "UT-123456", "JUNK", "FILING", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid report type", "UT-123456", "123456", "F", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Valid minimal SA", "UT-123456", "123456", "FILING", HTTPStatus.CREATED, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Valid all staff", "UT-123456", "123456", "FILING", HTTPStatus.CREATED, "BUSINESS", PRODUCT_ROLES_STAFF),
    ("Invalid role", "UT-123456", "123456", "FILING", HTTPStatus.UNAUTHORIZED, "BUSINESS", PRODUCT_ROLES_COLIN),
    ("Invalid product code", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "XXX", PRODUCT_ROLES_SYSTEM),
 ]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {payload})
TEST_PATCH_DATA = [
    ("Invalid name", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD1),
    ("Invalid event ID", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD2),
    ("Invalid report type", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD3),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD_EMPTY),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK, PATCH_PAYLOAD),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {payload}, {prod_code}, {roles})
TEST_PATCH_DATA_PRODUCT = [
    ("Invalid name", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD1, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid event ID", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD2, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid report type", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD3, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD_EMPTY, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid role", "UT-123456", "123456", "FILING", HTTPStatus.UNAUTHORIZED, PATCH_PAYLOAD, "BUSINESS", PRODUCT_ROLES_COLIN),
    ("Invalid product_code", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, PATCH_PAYLOAD, "XXX", PRODUCT_ROLES_SYSTEM),
    ("Valid SA", "UT-123456", "123456", "FILING", HTTPStatus.OK, PATCH_PAYLOAD, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Valid staff", "UT-123456", "123456", "FILING", HTTPStatus.OK, PATCH_PAYLOAD, "BUSINESS", PRODUCT_ROLES_STAFF),
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND, PATCH_PAYLOAD, "BUSINESS", PRODUCT_ROLES_SYSTEM),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_GET_ID_DATA = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {prod_code}, {roles})
TEST_GET_ID_DATA_PRODUCT = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid role", "UT-123456", "123456", "FILING", HTTPStatus.UNAUTHORIZED, "BUSINESS", USER_ROLES),
    ("Invalid product code", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "XXX", PRODUCT_ROLES_SYSTEM),
    ("Valid SA", "UT-123456", "123456", "FILING", HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Valid staff", "UT-123456", "123456", "FILING", HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_STAFF),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_GET_EVENT_DATA = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {prod_code}, {roles})
TEST_GET_EVENT_DATA_PRODUCT = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Valid SA", "UT-123456", "123456", "FILING", HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Valid staff", "UT-123456", "123456", "FILING", HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_STAFF),
    ("Invalid role", "UT-123456", "123456", "FILING", HTTPStatus.UNAUTHORIZED, "BUSINESS", USER_ROLES),
    ("Invalid product code", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "XXX", PRODUCT_ROLES_SYSTEM),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status})
TEST_GET_HISTORY_DATA = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND),
    ("Valid", "UT-123456", "123456", "FILING", HTTPStatus.OK),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {prod_code}, {roles}, {include_docs})
TEST_GET_HISTORY_DATA_PRODUCT = [
    ("Invalid not found", "UT-123456", "123456", "FILING", HTTPStatus.NOT_FOUND, "BUSINESS", PRODUCT_ROLES_SYSTEM, False),
    ("Valid SA", "UT-123456", "123456", "FILING", HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_SYSTEM, False),
    ("Valid staff", "UT-123456", "123456", "FILING", HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_STAFF, False),
    ("Invalid role", "UT-123456", "123456", "FILING", HTTPStatus.UNAUTHORIZED, "BUSINESS", USER_ROLES, True),
    ("Invalid product code", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "XXX", PRODUCT_ROLES_STAFF, False),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {infile}, {outfile}, {filename})
TEST_GET_CERTIFIED_COPY_DATA = [
    ("NOA legacy", "UT9900001", 99900001, "NOA", CC_NOA_LEGACY_INFILE, CC_NOA_LEGACY_OUTFILE,
     "UT9900001-ICORP-NOA.pdf"),
    ("FILING legacy", "UT9900001", 99900001, "FILING", CC_FILING_LEGACY_INFILE, CC_FILING_LEGACY_OUTFILE,
     "UT9900001-ICORP-FILING.pdf"),
    ("NOA", "UT9900002", 99900002, "NOA", CC_NOA_INFILE, CC_NOA_OUTFILE,
     "UT9900002 Notice Of Articles - 2026-01-16"),
    ("FILING", "UT9900002", 99900002, "FILING", CC_FILING_INFILE, CC_FILING_OUTFILE,
     "UT9900002 BC Limited Company Incorporation Application - 2026-01-16.pdf"),
]


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,prod_code,roles", TEST_CREATE_DATA_PRODUCT)
def test_product_create(session, client, jwt, desc, entity_id, event_id, report_type, status, prod_code, roles):
    """Assert that a post save new product report works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    req_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    if desc == "Valid all staff":
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
        assert report_json.get("productCode")
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(report_json.get("identifier"))
        assert app_report


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,payload,prod_code,roles", TEST_PATCH_DATA_PRODUCT)
def test_product_update(session, client, jwt, desc, entity_id, event_id, report_type, status, payload, prod_code, roles):
    """Assert that a request to update report information (not the report itself) works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, roles, "UT-TEST", "PS12345")
    req_path = CHANGE_PATH_PRODUCT.format(prod_code=prod_code, doc_service_id="test")
 
    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)
        resp_json = response.json
        valid_id = resp_json.get("identifier")
        req_path = CHANGE_PATH_PRODUCT.format(prod_code=prod_code, doc_service_id=valid_id)

    # test
    response = client.patch(req_path, json=payload, headers=headers, content_type="application/json")

    # check
    # logger.info(response.json)
    assert response.status_code == status


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,prod_code,roles", TEST_GET_ID_DATA_PRODUCT)
def test_get_product_by_id(session, client, jwt, desc, entity_id, event_id, report_type, status, prod_code, roles):
    """Assert that a request to get product report information (not the report itself) by DRS ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, roles, "UT-TEST", "PS12345")
    req_path = CHANGE_PATH_PRODUCT.format(prod_code=prod_code, doc_service_id="test")
 
    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)
        resp_json = response.json
        valid_id = resp_json.get("identifier")
        req_path = CHANGE_PATH_PRODUCT.format(prod_code=prod_code, doc_service_id=valid_id)
    # test
    if desc == "Valid SA":
        headers = create_header_account_report(jwt, roles, "UT-TEST", "PS12345")
    response = client.get(req_path, headers=headers, content_type="application/json")
    # check
    # logger.info(response.json)
    assert response.status_code == status
    if status == HTTPStatus.OK:
        if desc != "Valid SA":
            assert response.json
        else:
            assert response.data


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,prod_code,roles", TEST_GET_EVENT_DATA_PRODUCT)
def test_get_product_event_id(session, client, jwt, desc, entity_id, event_id, report_type, status, prod_code, roles):
    """Assert that a request to get product report information by an event ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, roles, "UT-TEST", "PS12345")
    req_path = EVENT_PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id)
    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        # logger.info(create_path)
        response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response.json)

    # test
    # logger.info(req_path)
    response = client.get(req_path, headers=headers, content_type="application/json")
    # check
    # logger.info(response.json)
    assert response.status_code == status
    if status == HTTPStatus.OK:
        assert response.json
        reports_json = response.json
        for report in reports_json:
            if report.get("reportType") in (model_utils.REPORT_TYPE_FILING, model_utils.REPORT_TYPE_NOA):
                assert not report.get("url")
            else:
                assert report.get("url")


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,prod_code,roles,include_docs", TEST_GET_HISTORY_DATA_PRODUCT)
def test_get_product_entity_id(session, client, jwt, desc, entity_id, event_id, report_type, status, prod_code, roles, include_docs):
    """Assert that a request to get report information by a product entity ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    create_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    else:
        headers = create_header_account(jwt, roles, "UT-TEST", "PS12345")
    req_path = HISTORY_PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id)
    if include_docs:
        req_path += "?includeDocuments=True"
        doc_json = copy.deepcopy(TEST_DOC1)
        doc_json["consumerIdentifier"] = entity_id
        doc_json["consumerReferenceId"] = event_id
        save_doc: Document = Document.create_from_json(doc_json, doc_json.get("documentType"))
        save_doc.save()
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
        if include_docs:
            assert len(response.json) > 1
        reports_json = response.json
        for report in reports_json:
            assert not report.get("url")


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status", TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, entity_id, event_id, report_type, status):
    """Assert that a post save new report works as expected."""
    # setup
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
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
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
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
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
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
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
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
    if is_ci_testing():
        return
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


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,infile,outfile,filename", TEST_GET_CERTIFIED_COPY_DATA)
def test_get_certified_copy(session, client, jwt, desc, entity_id, event_id, report_type, infile, outfile, filename):
    """Assert that a request to get a certified copy application report works as expected."""
    if is_ci_testing():
        return
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    prod_code = "BUSINESS"
    create_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    create_path += "?consumerFilingDate=2025-11-22T19:30:30%2B00:00&consumerFilename=" + filename
    headers = create_header_account_upload(jwt, PRODUCT_ROLES_STAFF, "UT-TEST", "PS12345", MEDIA_PDF)
 
    raw_data = None
    with open(infile, "rb") as data_file:
        raw_data = data_file.read()
        data_file.close()
    logger.info(f"POST path={create_path}")
    response = client.post(create_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
    logger.info(response.json)
    resp_json = response.json
    valid_id = resp_json.get("identifier")
    req_path = CHANGE_PATH_PRODUCT.format(prod_code=prod_code, doc_service_id=valid_id) + "?certifiedCopy=true"
    logger.info(f"GET path={req_path}")

    # test
    response = client.get(req_path, headers=headers, content_type="application/pdf")
    # check
    # logger.info(response.json)
    assert response.status_code == HTTPStatus.OK
    assert response.data
    with open(outfile, "wb") as pdf_file:
        pdf_file.write(response.data)
        pdf_file.close()


def is_ci_testing() -> bool:
    """Check unit test environment: exclude pub/sub for CI testing."""
    return  current_app.config.get("DEPLOYMENT_ENV", "testing") == "testing"
