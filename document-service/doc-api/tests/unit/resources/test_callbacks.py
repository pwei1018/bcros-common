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

"""Tests to verify the endpoints for maintaining aysnchronous DRS callback requests.

Test-Suite to ensure that the /callbacks endpoint is working as expected.
"""
import copy
import requests
from http import HTTPStatus
import json

import pytest
from flask import current_app

from doc_api.models import Document
from doc_api.resources.v1.callbacks import build_update_json, build_legacy_scan_json
from doc_api.services.document_storage.storage_service import GoogleStorageService
from doc_api.utils.logging import logger


TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
PARAM_TEST_APIKEY = "?x-apikey={api_key}"
DOC_REC_PATH: str = "/api/v1/callbacks/document-records"
LEGACY_SCAN_PATH: str = "/api/v1/callbacks/legacy-scan-files"
DOC_REC_UPDATE_PATH: str = "/api/v1/callbacks/update/document-records"
TEST_DOC_REC_LEGACY = {
    "accountId": "123456",
    "consumerDocumentId": "99990950",
    "consumerIdentifier": "108924",
    "documentType": "TRAN",
    "documentClass": "MHR"
}
TEST_DOC_REC_MODERN = {
    "accountId": "123456",
    "consumerDocumentId": "1099990950",
    "consumerIdentifier": "108924",
    "documentType": "TRAN",
    "documentClass": "MHR"
}
TEST_DOC_REC_INVALID = {
    "accountId": "123456",
    "consumerDocumentId": "99990950",
    "consumerIdentifier": "108924",
}
TEST_DOC_REC_BUSINESS_API = {
    "accountId": "business-api",
    "consumerDocumentId": "99980991",
    "consumerIdentifier": "BC1108924",
    "consumerFilingType": "annualReport",
    "consumerReferenceId": "1629808",
    "documentClass": "CORP"
}
TEST_DOC_REC_BUSINESS_API_WRAPPED = {
    "data": {
        "accountId": "business-api",
        "consumerDocumentId": None,
        "consumerIdentifier": "BC0223072",
        "consumerFilingType": "changeOfReceivers",
        "consumerReferenceId": 233834,
        "documentClass": "CORP"
    }
}
TEST_UPDATE_BUSINESS_API_1 = {
    "accountId": "business-api",
    "fileKey": "CORP-DS9000101951",
    "businessIdentifier": "BC1108924",
    "filingId": 1629808,
    "filingDate": "2026-06-09T23:02:02+00:00"
}
TEST_UPDATE_BUSINESS_API_2 = {
    "accountId": "business-api",
    "documentServiceId": "DS9000101951",
    "consumerIdentifier": "BC1108924",
    "consumerReferenceId": "1629808",
    "consumerFilingDate": "2026-06-09T23:02:02+00:00"
}
TEST_UPDATE_BUSINESS_API_WRAPPED = {
    "data": {
        "accountId": "business-api",
        "fileKey": "CORP-DS9000101951",
        "businessIdentifier": "BC1108924",
        "filingId": 1629808,
        "filingDate": "2026-06-09T23:02:02+00:00"
    }
}
TEST_LEGACY_SCAN_PAYLOAD = {
    "name": "BC 0108924.pdf",
    "timeCreated": "2026-09-09T23:11:00.589Z",
    "size": 123456,
    "bucket": "docs_nr_dev",
}
TEST_LEGACY_SCAN_PAYLOAD_WRAPPED = {
    "data": {
        "name": "BC 0108924.pdf",
        "timeCreated": "2026-09-09T23:11:00.589Z",
        "size": 123456,
        "bucket": "docs_nr_dev",
    }
}

# testdata pattern is ({description}, {payload_json}, {has_key}, {author}, {status}, {ref_id})
TEST_CREATE_DATA = [
    ("Invalid no doc class type", TEST_DOC_REC_INVALID, True, "John Smith", HTTPStatus.BAD_REQUEST, None),
    ("Invalid no api key", TEST_DOC_REC_LEGACY, False, "John Smith", HTTPStatus.UNAUTHORIZED, None),
    ("Invalid bad api key", TEST_DOC_REC_LEGACY, False, "John Smith", HTTPStatus.UNAUTHORIZED, None),
    ("Valid legacy", TEST_DOC_REC_LEGACY, True, "John Smith", HTTPStatus.CREATED, None),
    ("Valid modern", TEST_DOC_REC_MODERN, True, "John Smith", HTTPStatus.CREATED, "9014005"),
    ("Valid business api", TEST_DOC_REC_BUSINESS_API, True, None, HTTPStatus.CREATED, None),
    ("Valid business api wrapped", TEST_DOC_REC_BUSINESS_API_WRAPPED, True, None, HTTPStatus.CREATED, None),
]
# testdata pattern is ({description}, {payload_json}, {status}, {update_doc_type}, {update_filing_type})
TEST_UPDATE_DATA = [
    ("Valid business api", TEST_DOC_REC_BUSINESS_API, HTTPStatus.CREATED, "ADDR", "changeOfAddress"),
]
# testdata pattern is ({payload_json}, {drs_id}, {consumer_id}, {consumer_date}, {consumer_ref})
TEST_PATCH_PAYLOAD_DATA = [
    (TEST_UPDATE_BUSINESS_API_1, None, None, None, None),
    (TEST_UPDATE_BUSINESS_API_2, None, None, None, None),
    (TEST_UPDATE_BUSINESS_API_1, "DS9000101951", "BC1108924", "2026-06-09T23:02:02+00:00", "1629808"),
    (TEST_UPDATE_BUSINESS_API_2, "DS9000101951", "BC1108924", "2026-06-09T23:02:02+00:00", "1629808"),
]
# testdata pattern is ({description}, {payload_json}, {has_key}, {status})
TEST_PATCH_DATA = [
    ("Invalid no DRS ID", TEST_UPDATE_BUSINESS_API_1, True, HTTPStatus.BAD_REQUEST),
    ("Invalid DRS ID", TEST_UPDATE_BUSINESS_API_1, True, HTTPStatus.NOT_FOUND),
    ("Invalid no api key", TEST_UPDATE_BUSINESS_API_1, False, HTTPStatus.UNAUTHORIZED),
    ("Invalid bad api key", TEST_UPDATE_BUSINESS_API_2, False, HTTPStatus.UNAUTHORIZED),
    ("Valid ", TEST_UPDATE_BUSINESS_API_2, True, HTTPStatus.OK),
    ("Valid business api", TEST_UPDATE_BUSINESS_API_1, True, HTTPStatus.OK),
    ("Valid business api wrapped", TEST_UPDATE_BUSINESS_API_WRAPPED, True, HTTPStatus.OK),
]
# testdata pattern is ({entity_types}, {doc_class}, {size})
TEST_LEGACY_SCAN_DOC_DATA = [
    (["CP", "XC"], "COOP", "500000"),
    (["C", "A", "BC", "LLP"], "CORP", "1500000"),
    (["FM", "SP", "GP", "MF"], "FIRM", "2100000"),
    (["LP", "LL", "XP", "XL"], "LP_LLP", "2100000"),
    (["MH", "MHR"], "MHR", "100000"),
    (["NR"], "NR", "100000"),
    (["PP", "PPR"], "PPR", "100000"),
    (["XS", "S"], "SOCIETY", "2100000"),
]
# testdata pattern is ({description}, {payload_json}, {has_key}, {status}, {storage_doc_type})
TEST_CREATE_LEGACY_SCAN_DATA = [
    ("Invalid no api key", TEST_LEGACY_SCAN_PAYLOAD, False, HTTPStatus.UNAUTHORIZED, "NR"),
    ("Invalid bad api key", TEST_LEGACY_SCAN_PAYLOAD, False, HTTPStatus.UNAUTHORIZED, "NR"),
    ("Valid", TEST_LEGACY_SCAN_PAYLOAD, True, HTTPStatus.CREATED, "NR"),
    ("Valid wrapped", TEST_LEGACY_SCAN_PAYLOAD_WRAPPED, True, HTTPStatus.CREATED, "NR"),
]


@pytest.mark.parametrize("desc,payload_json,has_key,author,status,ref_id", TEST_CREATE_DATA)
def test_create_doc_rec(session, client, jwt, desc, payload_json, has_key, author, status, ref_id):
    """Assert that a post save new callback document record works as expected."""
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
    # setup
    headers = None   # {**kwargs, **{"Content-Type": "application/json"}}
    req_path = DOC_REC_PATH
    api_key = current_app.config.get("SUBSCRIPTION_API_KEY")
    if has_key and api_key:
        if desc == "Invalid bad api key":
            api_key += "JUNK"
        params = PARAM_TEST_APIKEY.format(api_key=api_key)
        req_path += params
    req_json = copy.deepcopy(payload_json)
    if author:
        req_json["author"] = author
    if ref_id:
        req_json["consumerReferenceId"] = ref_id
    # test
    payload = json.dumps(req_json).encode("utf-8")
    response = client.post(req_path, data=payload, headers=headers)
    # logger.info(response.json)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("documentServiceId")
        assert not doc_json.get("documentURL")
        if ref_id:
            assert doc_json.get("consumerReferenceId") == ref_id
        doc: Document = Document.find_by_doc_service_id(doc_json.get("documentServiceId"))
        assert doc
        doc_json = doc.json
        assert not doc_json.get("scanningInformation")
        if desc == "Valid business api wrapped":
            logger.info(doc_json)


@pytest.mark.parametrize("desc,payload_json,has_key,status", TEST_PATCH_DATA)
def test_patch_doc_rec(session, client, jwt, desc, payload_json, has_key, status):
    """Assert that a post callback update/patch document record works as expected."""
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
    # setup
    patch_payload = copy.deepcopy(payload_json)
    api_key = current_app.config.get("SUBSCRIPTION_API_KEY")
    params = PARAM_TEST_APIKEY.format(api_key=api_key)
    headers = None   # {**kwargs, **{"Content-Type": "application/json"}}
    if status == HTTPStatus.OK:
        req_path = DOC_REC_PATH
        req_path += params
        # test
        payload = json.dumps(TEST_DOC_REC_BUSINESS_API).encode("utf-8")
        response = client.post(req_path, data=payload, headers=headers)
        # logger.info(response.json)

        # check
        assert response.status_code == HTTPStatus.CREATED

        if patch_payload.get("documentServiceId"):
            patch_payload["documentServiceId"] = response.json.get("documentServiceId")
        elif patch_payload.get("data"):
            patch_payload["data"]["fileKey"] = "CORP-" + response.json.get("documentServiceId")
        else:
            patch_payload["fileKey"] = "CORP-" + response.json.get("documentServiceId")

    # Patch setup
    req_path = DOC_REC_UPDATE_PATH
    if has_key and api_key:
        if desc == "Invalid bad api key":
            params += "JUNK"
        req_path += params
    if desc == "Invalid no DRS ID":
        if patch_payload.get("documentServiceId"):
            del patch_payload["documentServiceId"]
        else:
            del patch_payload["fileKey"] 
    elif desc == "Invalid DRS ID":
        if patch_payload.get("documentServiceId"):
            patch_payload["documentServiceId"] = "JUNK"
        else:
            patch_payload["fileKey"] = "JUNK-JUNK"

    payload = json.dumps(patch_payload).encode("utf-8")
    response = client.post(req_path, data=payload, headers=headers)
    # logger.info(response.json)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("documentServiceId")
        doc: Document = Document.find_by_doc_service_id(doc_json.get("documentServiceId"))
        assert doc.consumer_filing_date
        if patch_payload.get("data"):
            assert doc.consumer_identifier == patch_payload["data"].get("businessIdentifier")
            assert doc.consumer_reference_id == str(patch_payload["data"].get("filingId"))
        else:
            if patch_payload.get("consumerIdentifier"):
                assert doc.consumer_identifier == patch_payload.get("consumerIdentifier")
            else:
                assert doc.consumer_identifier == patch_payload.get("businessIdentifier")
            if patch_payload.get("consumerReferenceId"):
                assert doc.consumer_reference_id == patch_payload.get("consumerReferenceId")
            else:
                assert doc.consumer_reference_id == str(patch_payload.get("filingId"))


@pytest.mark.parametrize("desc,payload_json,status,update_doc_type,update_filing_type", TEST_UPDATE_DATA)
def test_update_doc_rec(session, client, jwt, desc, payload_json, status, update_doc_type, update_filing_type):
    """Assert that a post save new callback document record, then update it, works as expected."""
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
    # setup
    headers = None   # {**kwargs, **{"Content-Type": "application/json"}}
    req_path = DOC_REC_PATH
    api_key = current_app.config.get("SUBSCRIPTION_API_KEY")
    params = PARAM_TEST_APIKEY.format(api_key=api_key)
    req_path += params
    req_json = copy.deepcopy(payload_json)
    # test
    payload = json.dumps(req_json).encode("utf-8")
    response = client.post(req_path, data=payload, headers=headers)
    # logger.info(response.json)

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        doc_json = response.json
        assert doc_json
        assert doc_json.get("documentServiceId")
        assert not doc_json.get("documentURL")
        doc: Document = Document.find_by_doc_service_id(doc_json.get("documentServiceId"))
        assert doc

    req_json["consumerFilingType"] = update_filing_type
    payload = json.dumps(req_json).encode("utf-8")
    response = client.post(req_path, data=payload, headers=headers)
    assert response.status_code == HTTPStatus.OK
    doc_json = response.json
    assert doc_json
    assert doc_json.get("documentType") == update_doc_type


@pytest.mark.parametrize("desc,payload_json,has_key,status,storage_doc_type", TEST_CREATE_LEGACY_SCAN_DATA)
def test_create_legacy_scan(session, client, jwt, desc, payload_json, has_key, status, storage_doc_type):
    """Assert that a post save new callback legacy scan document works as expected."""
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
    # setup
    if status == HTTPStatus.CREATED:
        raw_data = None
        with open(TEST_DATAFILE, "rb") as data_file:
            raw_data = data_file.read()
            data_file.close()
        source_name = payload_json["data"].get("name") if payload_json.get("data") else payload_json.get("name")
        response = GoogleStorageService.save_document_link(source_name, raw_data, storage_doc_type, 2, "application/pdf")
        assert response

    headers = {"Content-Type": "application/json"}
    req_path = LEGACY_SCAN_PATH
    api_key = current_app.config.get("SUBSCRIPTION_API_KEY")
    params = PARAM_TEST_APIKEY.format(api_key=api_key)
    if has_key and api_key:
        if desc == "Invalid bad api key":
            params += "JUNK"
        req_path += params
    req_json = copy.deepcopy(payload_json)
    # test
    payload = json.dumps(req_json).encode("utf-8")
    response = client.post(req_path, data=payload, headers=headers)

    # check
    assert response.status_code == status


@pytest.mark.parametrize("payload_json,drs_id,consumer_id,consumer_date,consumer_ref", TEST_PATCH_PAYLOAD_DATA)
def test_build_update_json(session, payload_json, drs_id, consumer_id, consumer_date, consumer_ref):
    """Assert that the patch request payload set up works as expected."""
    test_json = copy.deepcopy(payload_json)
    if not drs_id:
        if test_json.get("documentServiceId"):
            del test_json["documentServiceId"]
        else:
            del test_json["fileKey"]
    if not consumer_id:
        if test_json.get("consumerIdentifier"):
            del test_json["consumerIdentifier"]
        else:
            del test_json["businessIdentifier"]
    if not consumer_date:
        if test_json.get("consumerFilingDate"):
            del test_json["consumerFilingDate"]
        else:
            del test_json["filingDate"]
    if not consumer_ref:
        if test_json.get("consumerReferenceId"):
            del test_json["consumerReferenceId"]
        else:
            del test_json["filingId"]
    test_json = build_update_json(test_json)
    if drs_id:
        assert test_json.get("documentServiceId") == drs_id
    else:
        assert not test_json.get("documentServiceId")
    if consumer_id:
        assert test_json.get("consumerIdentifier") == consumer_id
    else:
        assert not test_json.get("consumerIdentifier")
    if consumer_date:
        assert test_json.get("consumerFilingDate") == consumer_date
    else:
        assert not test_json.get("consumerFilingDate")
    if consumer_ref:
        assert test_json.get("consumerReferenceId") == consumer_ref
    else:
        assert not test_json.get("consumerReferenceId")


@pytest.mark.parametrize("entity_types,doc_class,size", TEST_LEGACY_SCAN_DOC_DATA)
def test_legacy_scan_json(session, client, jwt, entity_types,doc_class,size):
    """Assert that a building document json from a new legacy scan document works as expected."""
    for et in entity_types:
        request_json = {
            "name": et + " 0204750.pdf",
            "timeCreated": "2026-09-09T23:11:00.589Z",
            "size": size,
            "bucket": "docs_bcmail_receive_dev",
        }
        doc_json = build_legacy_scan_json(request_json)
        assert doc_json.get("documentType") == "PRE"
        assert doc_json.get("documentClass") == doc_class
        assert doc_json.get("consumerFilename")
        assert doc_json.get("consumerIdentifier")
        assert doc_json.get("author")
        assert doc_json.get("consumerReferenceId")
        assert doc_json.get("legacyScanInfo")
        assert doc_json["legacyScanInfo"].get("bucket")
        assert doc_json["legacyScanInfo"].get("name")
        assert not doc_json.get("consumerFilingDateTime")


def is_ci_testing() -> bool:
    """Check unit test environment: exclude pub/sub for CI testing."""
    return  current_app.config.get("DEPLOYMENT_ENV", "testing") == "testing"


def get_test_colin(session, client, jwt):
    """Assert ."""
    if is_ci_testing() or not current_app.config.get("SUBSCRIPTION_API_KEY"):
        return
    # setup
    headers = None   # {**kwargs, **{"Content-Type": "application/json"}}
    headers_get_menu = {
        "Connection": "keep-alive",
        "Content-Type": "text/plain; charset=ISO-8859-1"
    }
    base_path = "https://www.corporateonline.gov.bc.ca/corporateonline/colin"
    get_menu_path = base_path + "/accesstransaction/menu.do?action=overview&filingTypeCode=RPRNT&from=main"
    overview_path = base_path + "/accesstransaction/menu.do"
    search_path = base_path + "/identcorp/searchCorp.do"
    receipt_path = base_path + "/reprint/report.do?action=receiptReport&check_token=no&historyIndex=1"
    # get_menu_path = "https://www.corporateonline.gov.bc.ca/"
    # logger.info(get_menu_path)
    # api_key = current_app.config.get("SUBSCRIPTION_API_KEY")
    #params = PARAM_TEST_APIKEY.format(api_key=api_key)
    #req_path += params
    #req_json = copy.deepcopy(payload_json)
    # test
    #payload = json.dumps(req_json).encode("utf-8")
    response = requests.get(get_menu_path, headers=headers_get_menu)
    # logger.info(response.text)
    cookie: str = response.cookies["JSESSIONID"]
    logger.info(f"cookie={cookie}")
    cookies = dict(JSESSIONID=cookie)
    overview_data = {
        "formType": "overview",
        "navigationAction": "next",
        "nextButton.x": 28,
        "nextButton.y": 13
    }
    response = requests.post(overview_path, headers=headers, data=overview_data, cookies=cookies)
    logger.info(f"overview status={response.status_code}")
    # with open("tests/unit/resources/colin_overview_response.txt", "w") as overview_file:
    #    overview_file.write(response.text)
    #    overview_file.close()
    search_data = {
        "defaultAction": "next",
        "formType": "search",
        "corpNum": "BC0659569",
        "password": "PROVIDE",
        "navigationAction": "next",
        "nextButton.x": 27,
        "nextButton.y": 7
    }
    response2 = requests.post(search_path, headers=headers, data=search_data, cookies=cookies)
    logger.info(f"search status={response2.status_code}")
    logger.info(response2.headers)
    # with open("tests/unit/resources/colin_search_response.txt", "w") as search_file:
    #    search_file.write(response2.text)
    #    search_file.close()
    response = requests.get(receipt_path, cookies=cookies)
    logger.info(f"receipt report status={response.status_code}")
    with open("tests/unit/resources/colin_receipt.pdf", "wb") as receipt_file:
        receipt_file.write(response.content)
        receipt_file.close()


def colin_file(session, client, jwt):
    """Assert ."""
    test_file: str = None
    with open("tests/unit/resources/colin-BC1331031.html", "r") as data_file:
        test_file = data_file.read()
        data_file.close()
    # search_base = "/reprint/report.do?action={report_type}Report&check_token=no&historyIndex={filing_index}"
    # test_link = search_base.format(report_type="cert", filing_index="7")
    # result = test_file.find(test_link)
    # logger.info(f"search {test_link} find result={result}")
    index_first_filing_date = test_file.find("November 06, 2025")
    index_first_report = test_file.find("historyIndex=0")
    logger.info(f"first filing date={index_first_filing_date} first report link={index_first_report}")
