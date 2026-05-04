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
from doc_api.resources.v1.application_reports import (
    build_event_zip, get_zip_filename,
    is_certified_copy_report_type,
    is_certified_copy_request
)
from doc_api.services.authz import BC_REGISTRY, COLIN_ROLE, STAFF_ROLE, SYSTEM_ROLE
from doc_api.services.document_storage.storage_service import GoogleStorageService
from doc_api.utils.logging import logger
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
TEST_STORAGE_FILE = "unit_test/unit_test.pdf"
TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
TEST_DATAFILE_FILING = "tests/unit/reports/data/filing.pdf"
TEST_DATAFILE_FILING_2 = "tests/unit/reports/data/legacy-filing.pdf"
TEST_FILENAME = "updated_name.pdf"
PARAM_TEST_FILENAME = "?consumerFilename=updated_name.pdf"
MOCK_AUTH_URL = "https://test.api.connect.gov.bc.ca/mockTarget/auth/api/v1/"
MEDIA_PDF = model_utils.CONTENT_TYPE_PDF
PARAMS1 = "?consumerFilename=test.pdf&consumerFilingDate=2005-10-31"
PARAMS2 = "?consumerFilename=test2.pdf&consumerFilingDate=2005-10-31"
PATH: str = "/api/v1/application-reports/{entity_id}/{event_id}/{report_type}"
CHANGE_PATH = "/api/v1/application-reports/{doc_service_id}"
EVENT_PATH = "/api/v1/application-reports/events/{event_id}"
HISTORY_PATH = "/api/v1/application-reports/history/{entity_id}"
PATH_PRODUCT: str = "/api/v1/application-reports/{prod_code}/{entity_id}/{event_id}/{report_type}"
CHANGE_PATH_PRODUCT = "/api/v1/application-reports/{prod_code}/{doc_service_id}"
EVENT_PATH_PRODUCT = "/api/v1/application-reports/events/{prod_code}/{entity_id}/{event_id}"
EVENT_ALL_PATH_PRODUCT = "/api/v1/application-reports/all/{prod_code}/{entity_id}/{event_id}"
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
ZIP_NAMES = [
    {"name": "receipt-name.pdf", "reportType": "RECEIPT"},
    {"name": "cert-name.pdf", "reportType": "CERT"},
    {"name": "filing-name.pdf", "reportType": "FILING"},
    {"name": "filing-2-name.pdf", "reportType": "FILING-2"},
    {"name": "noa-name.pdf", "reportType": "NOA"},
    {"name": "addr-name.pdf", "documentType": "ADDR"},
]
ZIP_REPORT_RECEIPT= {
    "productCode": "BUSINESS",
    "entityIdentifier": "UT-000001",
    "eventIdentifier": 9990000,
    "reportType": "RECEIPT",
    "name": "test-receipt.pdf",
    "datePublished": "2024-07-01T19:00:00+00:00",
}
ZIP_REPORT_FILING= {
    "productCode": "BUSINESS",
    "entityIdentifier": "UT-000001",
    "eventIdentifier": 9990000,
    "reportType": "FILING",
    "name": "test-filing.pdf",
    "datePublished": "2024-07-01T19:00:00+00:00",
}
PAYLOAD_ZIP1 = [
    {"name": "filing-name.pdf", "reportType": "FILING"}
]
PAYLOAD_ZIP2 = [
    {"name": "filing-name.pdf", "reportType": "X"}
]
REPORT_TYPES_ZIP = ["CERT", "FILING", "NOA", "RECEIPT"]
REPORT_TYPES_ZIP2 = ["FILING", "FILING-3", "RECEIPT"]
PAYLOAD_EMPTY = []
OUTFILE_ZIP1 = "tests/unit/resources/test-event-all.zip"
OUTFILE_ZIP2 = "tests/unit/resources/test-event-all-2.zip"
CC_NOA_LEGACY_INFILE = "tests/unit/reports/data/legacy-noa.pdf"
CC_NOA_LEGACY_OUTFILE = "tests/unit/resources/legacy-noa-certified.pdf"
CC_FILING_LEGACY_INFILE = "tests/unit/reports/data/legacy-filing.pdf"
CC_FILING_LEGACY_OUTFILE = "tests/unit/resources/legacy-filing-certified.pdf"
CC_NOA_INFILE = "tests/unit/reports/data/noa.pdf"
CC_NOA_OUTFILE = "tests/unit/resources/noa-certified.pdf"
CC_FILING_INFILE = "tests/unit/reports/data/filing.pdf"
CC_FILING_OUTFILE = "tests/unit/resources/filing-certified.pdf"
CC_FILING_AR_LEGACY_INFILE = "tests/unit/reports/data/legacy-conv-ar-filing.pdf"
CC_FILING_AR_LEGACY_OUTFILE = "tests/unit/reports/data/legacy-conv-ar-certified.pdf"

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
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {rtype2}, {status}, {prod_code}, {roles})
TEST_CREATE_DATA_PRODUCT_ADDITIONAL = [
    ("Valid minimal SA", "UT-123456", "123456", model_utils.REPORT_TYPE_FILING, model_utils.REPORT_TYPE_FILING_2,
     HTTPStatus.CREATED, "BUSINESS", PRODUCT_ROLES_SYSTEM),
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
    ("Conversion AR legacy", "UT9900003", 99900003, "FILING", CC_FILING_AR_LEGACY_INFILE, CC_FILING_AR_LEGACY_OUTFILE,
     "UT9900003-CONVL-FILING.pdf"),
]
# testdata pattern is ({description}, {report_type}, {certified_requested}, {certified_allowed})
TEST_CERTIFIED_COPY_REQUEST_DATA = [
    ("NOA not certified", model_utils.REPORT_TYPE_NOA, False, False),
    ("NOA certified", model_utils.REPORT_TYPE_NOA, True, True),
    ("FILING not certified", model_utils.REPORT_TYPE_FILING, False, False),
    ("FILING certified", model_utils.REPORT_TYPE_FILING, True, True),
    ("RECEIPT not certified", model_utils.REPORT_TYPE_RECEIPT, False, False),
    ("RECEIPT certified", model_utils.REPORT_TYPE_RECEIPT, True, False),
    ("CERT not certified", model_utils.REPORT_TYPE_CERT, False, False),
    ("CERT certified", model_utils.REPORT_TYPE_CERT, True, False),
    ("FILING additional 2 not certified", model_utils.REPORT_TYPE_FILING_2, False, False),
    ("FILING additional 2 certified", model_utils.REPORT_TYPE_FILING_2, True, True),
    ("FILING additional 3 not certified", model_utils.REPORT_TYPE_FILING_3, False, False),
    ("FILING additional 3 certified requested", model_utils.REPORT_TYPE_FILING_3, True, False),
    ("FILING additional 4 not certified", model_utils.REPORT_TYPE_FILING_4, False, False),
    ("FILING additional 4 certified", model_utils.REPORT_TYPE_FILING_4, True, True),
]
# testdata pattern is ({description}, {report_type}, {certified})
TEST_CERTIFIED_COPY_TYPE_DATA = [
    ("NOA certified", model_utils.REPORT_TYPE_NOA, True),
    ("FILING certified", model_utils.REPORT_TYPE_FILING, True),
    ("RECEIPT not certified", model_utils.REPORT_TYPE_RECEIPT, False),
    ("CERT not certified", model_utils.REPORT_TYPE_CERT, False),
    ("FILING additional 2 certified", model_utils.REPORT_TYPE_FILING_2, True),
    ("FILING additional 3 not certified", model_utils.REPORT_TYPE_FILING_3, False),
    ("FILING additional 4 certified", model_utils.REPORT_TYPE_FILING_4, True),
    ("None not certified", None, False),
    ("Ad hoc not certified", None, False),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtype}, {status}, {prod_code}, {roles})
TEST_PUT_DATA_PRODUCT = [
    ("Invalid entity ID", "1", "12345", "FILING", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid event ID", "UT-123456", "JUNK", "FILING", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid report type", "UT-123456", "123456", "F", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid no payload", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM),
    ("Invalid role", "UT-123456", "123456", "FILING", HTTPStatus.UNAUTHORIZED, "BUSINESS", PRODUCT_ROLES_COLIN),
    ("Invalid product code", "UT-123456", "123456", "FILING", HTTPStatus.BAD_REQUEST, "XXX", PRODUCT_ROLES_SYSTEM),
    ("Valid SA", "UT-123456", "123456", "FILING", HTTPStatus.CREATED, "BUSINESS", PRODUCT_ROLES_SYSTEM),
]
# testdata pattern is ({description}, {request_data}, {app_rep_type}, {app_doc_type}, {app_filename}, {filename})
TEST_ZIP_NAME_REQUEST_DATA = [
    ("Request receipt name", ZIP_NAMES, "RECEIPT", None, "drs-receipt.pdf", "receipt-name.pdf"),
    ("DRS receipt name", [], "RECEIPT", None, "drs-receipt.pdf", "drs-receipt.pdf"),
    ("Request cert name", ZIP_NAMES, "CERT", None, "drs-cert.pdf", "cert-name.pdf"),
    ("DRS cert name", [], "CERT", None, "drs-cert.pdf", "drs-cert.pdf"),
    ("Request noa name", ZIP_NAMES, "NOA", None, "drs-noa.pdf", "noa-name.pdf"),
    ("DRS noa name", [], "NOA", None, "drs-noa.pdf", "drs-noa.pdf"),
    ("Request filing name", ZIP_NAMES, "FILING", None, "drs-filing.pdf", "filing-name.pdf"),
    ("DRS filing name", [], "FILING", None, "drs-filing.pdf", "drs-filing.pdf"),
    ("Request filing 2 name", ZIP_NAMES, "FILING-2", None, "drs-filing-2.pdf", "filing-2-name.pdf"),
    ("DRS filing 2 name", [], "FILING-2", None, "drs-filing-2.pdf", "drs-filing-2.pdf"),
    ("Request doc addr name", ZIP_NAMES, None, "ADDR", "drs-addr.pdf", "addr-name.pdf"),
    ("DRS doc addr name", [], None, "ADDR", "drs-addr.pdf", "drs-addr.pdf"),
    ("DRS default name", [], "FILING", None, "", "BC11111-22222-filing.pdf"),
]
# testdata pattern is ({description}, {entity_id}, {event_id}, {rtypes}, {status}, {prod_code}, {roles}, {payload}, {outfile})
TEST_GET_EVENT_DATA_PRODUCT_ALL = [
    ("Invalid not found", "UT-123456", "123456", REPORT_TYPES_ZIP, HTTPStatus.NOT_FOUND, "BUSINESS", PRODUCT_ROLES_SYSTEM, PAYLOAD_EMPTY, ""),
    ("Invalid payload", "UT-123456", "123456", REPORT_TYPES_ZIP, HTTPStatus.BAD_REQUEST, "BUSINESS", PRODUCT_ROLES_SYSTEM, PAYLOAD_ZIP2, ""),
    ("Valid", "UT-123456", "123456", REPORT_TYPES_ZIP, HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_SYSTEM, ZIP_NAMES, OUTFILE_ZIP1),
    ("Valid no payload", "UT-123456", "123456", REPORT_TYPES_ZIP2, HTTPStatus.OK, "BUSINESS", PRODUCT_ROLES_STAFF, PAYLOAD_EMPTY, OUTFILE_ZIP2),
    ("Invalid role", "UT-123456", "123456", REPORT_TYPES_ZIP, HTTPStatus.UNAUTHORIZED, "BUSINESS", USER_ROLES, PAYLOAD_EMPTY, ""),
    ("Invalid product code", "UT-123456", REPORT_TYPES_ZIP, "FILING", HTTPStatus.BAD_REQUEST, "XXX", PRODUCT_ROLES_SYSTEM, PAYLOAD_EMPTY, ""),
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


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,report_type2,status,prod_code,roles", TEST_CREATE_DATA_PRODUCT_ADDITIONAL)
def test_product_create_additional(session, client, jwt, desc, entity_id, event_id, report_type, report_type2, status, prod_code, roles):
    """Assert that a post save new product filing and additional filing reports works as expected."""
    if is_ci_testing():
        return

    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    req_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    # test
    if status != HTTPStatus.CREATED:
        response = client.post(req_path, data=None, headers=headers, content_type=MEDIA_PDF)
    else:
        raw_data = None
        req_path += PARAMS1
        with open(TEST_DATAFILE_FILING, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        report_json = response.json
        assert report_json
        assert report_json.get("identifier")
        assert report_json.get("url")
        assert report_json.get("productCode") == prod_code
        assert report_json.get("entityIdentifier") == entity_id
        assert report_json.get("eventIdentifier") == int(event_id)
        assert report_json.get("reportType") == report_type
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(report_json.get("identifier"))
        assert app_report
    if status == HTTPStatus.CREATED and report_type2:
        req_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type2)
        req_path += PARAMS2
        with open(TEST_DATAFILE_FILING_2, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        assert response.status_code == status
        report_json = response.json
        assert report_json
        assert report_json.get("identifier")
        assert report_json.get("url")
        assert report_json.get("productCode") == prod_code
        assert report_json.get("entityIdentifier") == entity_id
        assert report_json.get("eventIdentifier") == int(event_id)
        assert report_json.get("reportType") == report_type2
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(report_json.get("identifier"))
        assert app_report


@pytest.mark.parametrize("desc,entity_id,event_id,report_type,status,prod_code,roles", TEST_PUT_DATA_PRODUCT)
def test_product_replace(session, client, jwt, desc, entity_id, event_id, report_type, status, prod_code, roles):
    """Assert that a put replace product report works as expected."""
    if is_ci_testing():
        return
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
    req_path = PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type)
    # test
    if status != HTTPStatus.CREATED:
        response = client.post(req_path, data=None, headers=headers, content_type=MEDIA_PDF)
    else:
        req_path += PARAMS1
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
        drs_id: str = report_json.get("identifier")
        req_path = CHANGE_PATH_PRODUCT.format(prod_code=prod_code, doc_service_id=drs_id)
        raw_data = None
        with open(TEST_DATAFILE_FILING, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        response2 = client.put(req_path, data=raw_data, headers=headers, content_type=MEDIA_PDF)
        # logger.info(response2.json)
        assert response2.status_code == status
        report2_json = response.json
        assert report2_json
        assert report2_json.get("identifier") == drs_id
        assert report2_json.get("url")
        assert report2_json.get("productCode") == prod_code
        assert report2_json.get("entityIdentifier") == entity_id
        assert report2_json.get("eventIdentifier") == int(event_id)
        assert report2_json.get("reportType") == report_type


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


@pytest.mark.parametrize("desc,entity_id,event_id,report_types,status,prod_code,roles,payload,outfile", TEST_GET_EVENT_DATA_PRODUCT_ALL)
def test_get_product_event_all(session, client, jwt, desc, entity_id, event_id, report_types, status, prod_code, roles, payload, outfile):
    """Assert that a request to get all product documents as an archive zip file data by an event ID works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if status == HTTPStatus.OK:  # Create.
        headers = create_header_account_upload(jwt, roles, "UT-TEST", "PS12345", MEDIA_PDF)
        # Set up existing app report records. Using the same file is fine for testing.
        for report_type in report_types:
            rep_json = copy.deepcopy(ZIP_REPORT_RECEIPT)
            rep_json["entityIdentifier"] = entity_id
            rep_json["eventIdentifier"] = event_id
            rep_json["reportType"] = report_type
            rep_json["name"] = f"{entity_id}-unit-test-{event_id}-{report_type}.pdf"
            app_report: ApplicationReport = ApplicationReport.create_from_json(rep_json)
            app_report.doc_storage_url = TEST_STORAGE_FILE
            app_report.save()
    else:
        headers = create_header_account(jwt, roles, "UT-TEST", "PS12345")
    req_path = EVENT_ALL_PATH_PRODUCT.format(prod_code=prod_code, entity_id=entity_id, event_id=event_id)

    # test
    # logger.info(req_path)
    response = client.post(req_path, json=payload, headers=headers, content_type="application/json")
    # check
    # logger.info(response.json)
    assert response.status_code == status
    if status == HTTPStatus.OK:
        assert response.data
        assert len(response.data) > 0
        if outfile:
            with open(outfile, "wb") as pdf_file:
                pdf_file.write(response.data)
                pdf_file.close()


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
    logger.info(f"create_path={create_path}")
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


@pytest.mark.parametrize("desc,report_type,certified", TEST_CERTIFIED_COPY_TYPE_DATA)
def test_certified_copy_type(session, client, jwt, desc, report_type, certified):
    """Assert that the certified copy report type check works as expected."""
    result: bool = is_certified_copy_report_type(report_type)
    assert result == certified


@pytest.mark.parametrize("desc,report_type,certified_requested,certified_allowed", TEST_CERTIFIED_COPY_REQUEST_DATA)
def test_certified_copy_request(session, client, jwt, desc, report_type, certified_requested, certified_allowed):
    """Assert that the certified copy request for a report type works as expected."""
    app_report: ApplicationReport = ApplicationReport(report_type=report_type)
    result: bool = is_certified_copy_request(app_report, certified_requested)
    assert result == certified_allowed


@pytest.mark.parametrize("desc,request_data,app_rep_type,app_doc_type,app_filename,filename", TEST_ZIP_NAME_REQUEST_DATA)
def test_zip_filename(session, client, jwt, desc, request_data, app_rep_type, app_doc_type, app_filename, filename):
    """Assert that deriving a zip file doc filename works as expected."""
    app_rep_json: dict = {
        "entityIdentifier": "BC11111",
        "eventIdentifier": 22222,
        "name": app_filename
    }
    if app_rep_type:
        app_rep_json["reportType"] = app_rep_type
    else:
        app_rep_json["documentType"] = app_doc_type
    test_filename = get_zip_filename(request_data, app_rep_json)
    assert test_filename == filename


def test_build_event_zip(session, client, jwt):
    """Assert that building a filing zip file containing all reports and documents works as expected."""
    if is_ci_testing():
        return
    receipt_report: ApplicationReport = ApplicationReport.create_from_json(ZIP_REPORT_RECEIPT)
    receipt_report.doc_storage_url = TEST_STORAGE_FILE
    receipt_report.save()
    filing_report: ApplicationReport = ApplicationReport.create_from_json(ZIP_REPORT_FILING)
    filing_report.doc_storage_url = TEST_STORAGE_FILE
    filing_report.save()
    reports_json = [
        receipt_report.json,
        filing_report.json
    ]
    zip_data = build_event_zip(ZIP_NAMES, reports_json, "BUSINESS")
    assert zip_data
    assert len(zip_data) > 0
    with open("tests/unit/resources/test-event.zip", "wb") as zip_file:
        zip_file.write(zip_data)
        zip_file.close()


def is_ci_testing() -> bool:
    """Check unit test environment: exclude pub/sub for CI testing."""
    return  current_app.config.get("DEPLOYMENT_ENV", "testing") == "testing"
