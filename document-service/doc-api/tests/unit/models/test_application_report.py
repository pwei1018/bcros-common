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

"""Tests to assure the application_reports table Model.

Test-Suite to ensure that the ApplicationReport Model is working as expected.
"""
import copy

import pytest

from doc_api.models import ApplicationReport
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import ProductCodes


REPORT1 = {
    "productCode": "BUSINESS",
    "entityIdentifier": "T0000001",
    "eventIdentifier": 1000000,
    "reportType": "RECEIPT",
    "name": "test.pdf",
    "datePublished": "2024-07-01T19:00:00+00:00"
}
REPORT2 = {
    "productCode": "BUSINESS",
    "identifier": "1",
    "entityIdentifier": "T0000001",
    "eventIdentifier": 1000000,
    "reportType": "RECEIPT",
    "name": "test.pdf",
    "datePublished": "2024-07-01T19:00:00+00:00",
    "url": ""
}
REPORT3 = {
    "productCode": "BUSINESS",
    "entityIdentifier": "T0000001",
    "eventIdentifier": 1000000,
    "reportType": "FILING",
    "name": "test_filing.pdf",
    "datePublished": "2024-07-01T19:00:00+00:00"
}
REPORT4 = {
    "productCode": "BUSINESS",
    "entityIdentifier": "T0000001",
    "eventIdentifier": 1000000,
    "reportType": "CERTIFICATE",
    "name": "test_cert.pdf",
    "datePublished": "2024-07-01T19:00:00+00:00"
}
REPORT5 = {
    "productCode": "BUSINESS",
    "entityIdentifier": "T0000001",
    "eventIdentifier": 1000001,
    "reportType": "RECEIPT",
    "name": "test_receipt.pdf",
    "datePublished": "2024-07-02T19:00:00+00:00"
}

UPDATE_REPORT = {
    "reportType": "MOD_RECEIPT",
    "name": "mod-test.pdf",
    "datePublished": "2024-10-31T19:00:00+00:00"
}
TEST_REPORT = ApplicationReport(
    id=1,
    document_service_id="1",
    create_ts=model_utils.now_ts(),
    entity_id="T0000001",
    event_id=1000000,
    report_type = "RECEIPT",
    filename="test.pdf",
    filing_date=model_utils.ts_from_iso_format("2024-07-01T19:00:00+00:00"),
    product_code = ProductCodes.BUSINESS
)

# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class})
TEST_ID_DATA = [
    (200000001, True),
    (300000000, False),
]
# testdata pattern is ({id}, {has_result}, {product_code})
TEST_DOC_SERVICE_ID_DATA = [
    ("T0000001", True, None),
    ("T0000001", True, ProductCodes.BUSINESS.value),
    ("T0000001", False, ProductCodes.PPR.value),
    ("XXXD0000", False, None),
]
# testdata pattern is ({id}, {has_result}, {entity_id}, {product_code})
TEST_EVENT_ID_DATA = [
    (1000000, True, None, None),
    (1000000, True, 'T0000001', ProductCodes.BUSINESS.value),
    (1000000, False, 'T0000001', ProductCodes.MHR.value),
    (1000000, False, 'T000000X', ProductCodes.BUSINESS.value),
    (100000000, False, None, None),
]
# testdata pattern is ({id}, {has_result}, {product_code})
TEST_ENTITY_ID_DATA = [
    ("T0000001", True, None),
    ("T0000001", True, ProductCodes.BUSINESS.value),
    ("T0000001", False, ProductCodes.NRO.value),
    ("XXXTXX001", False, None),
]
# testdata pattern is ({has_name}, {has_filing_date}, {filename})
TEST_CREATE_JSON_DATA = [
    (True, True, "test.pdf"),
    (False, False, "T0000001-1000000-receipt.pdf")
]
# testdata pattern is ({report_info}, {update_report_info})
TEST_UPDATE_JSON_DATA = [
    (REPORT1, UPDATE_REPORT),
]


@pytest.mark.parametrize("id, has_results", TEST_ID_DATA)
def test_find_by_id(session, id, has_results):
    """Assert that find report by primary key contains all expected elements."""
    if not has_results:
        report: ApplicationReport = ApplicationReport.find_by_id(id)
        assert not report
    else:
        save_report: ApplicationReport = ApplicationReport.create_from_json(REPORT1)
        save_report.id = id
        assert save_report.event_id
        assert save_report.report_type
        assert save_report.filename
        assert save_report.filing_date
        assert save_report.create_ts
        save_report.save()
        assert save_report.id == id
        assert save_report.document_service_id
        report: ApplicationReport = ApplicationReport.find_by_id(id)
        assert report
        assert report.entity_id == save_report.entity_id
        assert not report.doc_storage_url
        report_json = report.json
        assert report_json
        assert report_json.get("identifier") == save_report.document_service_id
        assert report_json.get("entityIdentifier") == REPORT1.get("entityIdentifier")
        assert report_json.get("eventIdentifier") == REPORT1.get("eventIdentifier")
        assert report_json.get("reportType") == REPORT1.get("reportType")
        assert report_json.get("name") == REPORT1.get("name")
        assert report_json.get("dateCreated")
        assert report_json.get("datePublished")
        assert report_json.get("productCode")
        assert "url" in report_json and not report_json.get("url")


@pytest.mark.parametrize("id, has_results, product_code", TEST_DOC_SERVICE_ID_DATA)
def test_find_by_doc_service_id(session, id, has_results, product_code):
    """Assert that find a report by document service id contains all expected elements."""
    if not has_results:
        report: ApplicationReport = ApplicationReport.find_by_doc_service_id(id, product_code)
        assert not report
    else:
        save_report: ApplicationReport = ApplicationReport.create_from_json(REPORT1)
        save_report.document_service_id = id
        assert save_report.event_id
        assert save_report.report_type
        assert save_report.filename
        assert save_report.filing_date
        assert save_report.create_ts
        save_report.save()
        assert save_report.id
        assert save_report.document_service_id == id
        report: ApplicationReport = ApplicationReport.find_by_doc_service_id(id, product_code)
        assert report
        assert report.document_service_id == id
        assert report.entity_id == save_report.entity_id
        assert not report.doc_storage_url
        report_json = report.json
        assert report_json
        assert report_json.get("identifier") == save_report.document_service_id
        assert report_json.get("entityIdentifier") == REPORT1.get("entityIdentifier")
        assert report_json.get("eventIdentifier") == REPORT1.get("eventIdentifier")
        assert report_json.get("reportType") == REPORT1.get("reportType")
        assert report_json.get("name") == REPORT1.get("name")
        assert report_json.get("dateCreated")
        assert report_json.get("datePublished")
        if product_code:
            assert report_json.get("productCode") == product_code
        else:
            assert report_json.get("productCode")
        assert "url" in report_json and not report_json.get("url")


@pytest.mark.parametrize("id, has_results,entity_id,product_code", TEST_EVENT_ID_DATA)
def test_find_by_event_id(session, id, has_results, entity_id, product_code):
    """Assert that find reports by event id contains all expected elements."""
    report = None
    if not has_results:
        if product_code and entity_id:
            reports = ApplicationReport.find_by_event_id(id, entity_id, product_code)
        else:
            reports = ApplicationReport.find_by_event_id(id)
        assert not reports
    else:
        save_report: ApplicationReport = ApplicationReport.create_from_json(REPORT1)
        save_report.save()
        save_report2: ApplicationReport = ApplicationReport.create_from_json(REPORT3)
        save_report2.save()
        save_report3: ApplicationReport = ApplicationReport.create_from_json(REPORT4)
        save_report3.save()
        if product_code and entity_id:
            reports = ApplicationReport.find_by_event_id(id, entity_id, product_code)
        else:
            reports = ApplicationReport.find_by_event_id(id)
        assert reports
        assert len(reports) >= 3
        for report in reports:
            assert report.event_id == id
        report_json = ApplicationReport.find_by_event_id_json(id)
        assert report_json
        assert len(report_json) >= 3
        for json in report_json:
            assert json.get("eventIdentifier") == id
            if product_code:
                assert json.get("productCode") == product_code
            else:
                assert json.get("productCode")


@pytest.mark.parametrize("id, has_results,product_code", TEST_ENTITY_ID_DATA)
def test_find_by_entity_id(session, id, has_results, product_code):
    """Assert that find reports by entity id contains all expected elements."""
    reports = None
    if not has_results:
        if not product_code:
            reports = ApplicationReport.find_by_entity_id(id)
        else:
            reports = ApplicationReport.find_by_entity_id(id, product_code)
        assert not reports
    else:
        save_report: ApplicationReport = ApplicationReport.create_from_json(REPORT1)
        save_report.save()
        save_report2: ApplicationReport = ApplicationReport.create_from_json(REPORT3)
        save_report2.save()
        save_report3: ApplicationReport = ApplicationReport.create_from_json(REPORT5)
        save_report3.save()
        if product_code:
            reports = ApplicationReport.find_by_entity_id(id, product_code)
        else:
            reports = ApplicationReport.find_by_entity_id(id)
        assert reports
        assert len(reports) >= 3
        assert reports[0].event_id == REPORT5.get("eventIdentifier")
        for report in reports:
            assert report.entity_id == id
        report_json = ApplicationReport.find_by_entity_id_json(id)
        assert report_json
        assert len(report_json) >= 3
        assert report_json[0].get("eventIdentifier") == REPORT5.get("eventIdentifier")
        for json in report_json:
            assert json.get("entityIdentifier") == id
            if product_code:
                assert json.get("productCode") == product_code
            else:
                assert json.get("productCode")


def test_report_json(session):
    """Assert that the application report model renders to a json format correctly."""
    report: ApplicationReport = TEST_REPORT
    report_json = report.json
    test_json = copy.deepcopy(REPORT2)
    test_json["dateCreated"] = report_json.get("dateCreated")
    assert report_json == test_json


@pytest.mark.parametrize("has_name, has_filing_date, filename", TEST_CREATE_JSON_DATA)
def test_create_from_json(session, has_name, has_filing_date, filename):
    """Assert that the new document is created from new request json data correctly."""
    json_data = copy.deepcopy(REPORT1)
    if not has_name:
        del json_data["name"]
    if not has_filing_date:
        del json_data["datePublished"]
    report: ApplicationReport = ApplicationReport.create_from_json(json_data)
    assert report
    assert report.id
    assert report.document_service_id
    assert report.entity_id == json_data.get("entityIdentifier")
    assert report.event_id == json_data.get("eventIdentifier")
    assert report.report_type == json_data.get("reportType")
    assert report.create_ts
    assert report.filing_date
    assert report.product_code == ProductCodes.BUSINESS
    if not has_filing_date:
        assert report.filing_date == report.create_ts
    assert report.filename == filename


@pytest.mark.parametrize("report_info, update_report_info", TEST_UPDATE_JSON_DATA)
def test_update(session, report_info, update_report_info):
    """Assert that updating report information contains all expected elements."""
    save_report: ApplicationReport = ApplicationReport.create_from_json(report_info)
    save_report.save()
    test_report: ApplicationReport = ApplicationReport.find_by_id(save_report.id)
    assert test_report
    assert test_report.filename == report_info.get("name")
    assert test_report.report_type == report_info.get("reportType")
    test_report.update(update_report_info)
    test_report.save()
    update_report: ApplicationReport = ApplicationReport.find_by_id(save_report.id)
    assert update_report
    assert update_report.filename == update_report_info.get("name")
    assert update_report.report_type == update_report_info.get("reportType")
    assert model_utils.format_ts(update_report.filing_date) == update_report_info.get("datePublished")
