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
from http import HTTPStatus
import json

import pytest
from flask import current_app

from doc_api.models import Document
from doc_api.utils.logging import logger

PARAM_TEST_APIKEY = "?x-apikey={api_key}"
DOC_REC_PATH: str = "/api/v1/callbacks/document-records"
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


# testdata pattern is ({description}, {payload_json}, {has_key}, {author}, {status}, {ref_id})
TEST_CREATE_DATA = [
    ("Invalid no doc class type", TEST_DOC_REC_INVALID, True, "John Smith", HTTPStatus.BAD_REQUEST, None),
    ("Invalid no api key", TEST_DOC_REC_LEGACY, False, "John Smith", HTTPStatus.UNAUTHORIZED, None),
    ("Invalid bad api key", TEST_DOC_REC_LEGACY, False, "John Smith", HTTPStatus.UNAUTHORIZED, None),
    ("Valid legacy", TEST_DOC_REC_LEGACY, True, "John Smith", HTTPStatus.CREATED, None),
    ("Valid modern", TEST_DOC_REC_MODERN, True, "John Smith", HTTPStatus.CREATED, "9014005"),
    ("Valid business api", TEST_DOC_REC_BUSINESS_API, True, None, HTTPStatus.CREATED, None),
]
# testdata pattern is ({description}, {payload_json}, {status}, {update_doc_type}, {update_filing_type})
TEST_UPDATE_DATA = [
    ("Valid business api", TEST_DOC_REC_BUSINESS_API, HTTPStatus.CREATED, "ADDR", "changeOfAddress"),
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


def is_ci_testing() -> bool:
    """Check unit test environment: exclude pub/sub for CI testing."""
    return  current_app.config.get("DEPLOYMENT_ENV", "testing") == "testing"
