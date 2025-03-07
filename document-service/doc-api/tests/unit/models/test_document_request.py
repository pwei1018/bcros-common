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

"""Tests to assure the document Model.

Test-Suite to ensure that the document Model is working as expected.
"""
import copy

import pytest

from doc_api.models import Document, DocumentRequest
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes, RequestTypes

DOC1 = {
    "consumerDocumentId": "T0000001",
    "consumerFilename": "test.pdf",
    "consumerIdentifer": "T0000002",
    "documentType": "CORR",
    "documentClass": "PPR",
    "consumerFilingDateTime": "2024-07-01T19:00:00+00:00",
}
REQUEST1 = {
    "requestType": RequestTypes.ADD.value,
    "accountId": "T_ACCOUNT",
    "documentId": 0,
    "status": 200,
    "statusMessage": "message",
    "requestData": DOC1,
}
TEST_DOCUMENT = Document(
    id=1,
    document_service_id="1",
    document_type=DocumentTypes.CORR.value,
    document_class=DocumentClasses.PPR.value,
    add_ts=model_utils.now_ts(),
    consumer_document_id="T0000001",
    consumer_identifier="T0000002",
    consumer_filename="test.pdf",
    consumer_filing_date=model_utils.ts_from_iso_date_noon("2024-07-01"),
)
TEST_REQUEST = DocumentRequest(
    id=1,
    request_type=RequestTypes.ADD.value,
    request_ts=model_utils.now_ts(),
    account_id="T_ACCOUNT",
    username="T_USER",
    status=200,
    status_message="message",
    request_data=DOC1,
)


# testdata pattern is ({id}, {has_results}, doc_type, request_type)
TEST_ID_DATA = [
    (200000001, True, DocumentTypes.CORR.value, RequestTypes.ADD.value),
    (300000000, False, DocumentTypes.CORR.value, RequestTypes.ADD.value),
]


@pytest.mark.parametrize("id, has_results, doc_type, doc_class", TEST_ID_DATA)
def test_find_by_id(session, id, has_results, doc_type, doc_class):
    """Assert that find document request by primary key contains all expected elements."""
    if not has_results:
        doc_request: DocumentRequest = DocumentRequest.find_by_id(id)
        assert not doc_request
    else:
        save_doc: Document = Document.create_from_json(DOC1, doc_type)
        save_doc.id = id
        save_request: DocumentRequest = TEST_REQUEST
        save_request.id = id
        save_doc.save()
        save_request.document_id = save_doc.id
        save_request.save()
        assert save_doc.id
        assert save_request.id
        assert save_request.document_id == save_doc.id
        doc_request: DocumentRequest = DocumentRequest.find_by_id(save_request.id)
        assert doc_request
        assert doc_request.document_id == save_doc.id
        assert doc_request.request_type == save_request.request_type
        assert doc_request.account_id == save_request.account_id
        assert doc_request.username == save_request.username
        assert doc_request.status == save_request.status
        assert doc_request.status_message == save_request.status_message
        assert doc_request.request_data == save_request.request_data


def test_doc_request_json(session):
    """Assert that the document request model renders to a json format correctly."""
    doc_request: DocumentRequest = TEST_REQUEST
    request_json = doc_request.json
    test_json = copy.deepcopy(REQUEST1)
    test_json["createDateTime"] = request_json.get("createDateTime")
    test_json["documentId"] = request_json.get("documentId")
    assert request_json == test_json
