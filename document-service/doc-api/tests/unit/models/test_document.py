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

from doc_api.models import Document, DocumentScanning
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentType, DocumentTypes

DOC1 = {
    "consumerDocumentId": "T0000001",
    "consumerFilename": "test.pdf",
    "consumerIdentifier": "T0000002",
    "documentType": "PPR_MISC",
    "documentClass": "PPR",
    "consumerFilingDateTime": "2024-07-01T19:00:00+00:00",
    "description": "A meaningful description of the document.",
}
DOC_SCAN = {
    "scanDateTime": "2024-08-15T19:00:00+00:00",
    "accessionNumber": "AN-0002",
    "batchId": "12345",
    "author": "Janet Smith",
    "pageCount": 4,
}
TEST_DOCUMENT = Document(
    id=1,
    document_service_id="1",
    document_type=DocumentTypes.PPR_MISC.value,
    document_class=DocumentClasses.PPR.value,
    add_ts=model_utils.now_ts(),
    consumer_document_id="T0000001",
    consumer_identifier="T0000002",
    consumer_filename="test.pdf",
    consumer_filing_date=model_utils.ts_from_iso_date_noon("2024-07-01"),
    description="A meaningful description of the document.",
)

# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class})
TEST_ID_DATA = [
    (200000001, True, DocumentTypes.PPR_MISC.value, DocumentClasses.PPR.value),
    (300000000, False, DocumentTypes.PPR_MISC.value, DocumentClasses.PPR.value),
]
TEST_DOC_SERVICE_ID_DATA = [
    ("T0000001", True, DocumentTypes.MHR_MISC.value, DocumentClasses.MHR.value),
    ("XXXD0000", False, DocumentTypes.MHR_MISC.value, DocumentClasses.MHR.value),
]
# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class}, {has_scan})
TEST_DOC_ID_DATA = [
    ("T0000001", True, DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, True),
    ("T0000001", True, DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, False),
    ("XXXD0000", False, DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, False),
]
# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class}, {query_doc_type})
TEST_CONSUMER_ID_DATA = [
    ("T0000001", True, DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, False),
    ("T0000001", True, DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, True),
    ("XXXD0000", False, DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, False),
]
# testdata pattern is ({has_doc_id}, {doc_type})
TEST_CREATE_JSON_DATA = [(True, DocumentTypes.CORP_MISC.value), (False, DocumentTypes.MHR_MISC.value)]


@pytest.mark.parametrize("id, has_results, doc_type, doc_class", TEST_ID_DATA)
def test_find_by_id(session, id, has_results, doc_type, doc_class):
    """Assert that find document by primary key contains all expected elements."""
    if not has_results:
        document: Document = Document.find_by_id(id)
        assert not document
    else:
        save_doc: Document = Document.create_from_json(DOC1, doc_type)
        save_doc.save()
        assert save_doc.id
        assert save_doc.document_service_id
        document: Document = Document.find_by_id(save_doc.id)
        assert document
        assert document.consumer_document_id == save_doc.consumer_document_id
        assert document.document_type == doc_type
        doc_json = document.json
        assert doc_json
        assert doc_json.get("documentClass") == doc_class
        assert doc_json.get("documentTypeDescription")


@pytest.mark.parametrize("id, has_results, doc_type, doc_class", TEST_DOC_SERVICE_ID_DATA)
def test_find_by_doc_service_id(session, id, has_results, doc_type, doc_class):
    """Assert that find document by document service id contains all expected elements."""
    if not has_results:
        document: Document = Document.find_by_doc_service_id(id)
        assert not document
    else:
        save_doc: Document = Document.create_from_json(DOC1, doc_type)
        save_doc.save()
        assert save_doc.id
        assert save_doc.document_service_id
        document: Document = Document.find_by_doc_service_id(save_doc.document_service_id)
        assert document
        assert document.consumer_document_id == save_doc.consumer_document_id
        assert document.document_type == doc_type
        doc_json = document.json
        assert doc_json
        assert doc_json.get("documentClass") == doc_class
        assert doc_json.get("documentTypeDescription")


@pytest.mark.parametrize("id, has_results, doc_type, doc_class, has_scan", TEST_DOC_ID_DATA)
def test_find_by_document_id(session, id, has_results, doc_type, doc_class, has_scan):
    """Assert that find document by consumer document id contains all expected elements."""
    if not has_results:
        document: Document = Document.find_by_document_id(id)
        assert not document
    else:
        if has_scan:
            scan_doc: DocumentScanning = DocumentScanning.create_from_json(DOC_SCAN, id, doc_class)
            scan_doc.id = 200000000
            scan_doc.save()
        save_doc: Document = Document.create_from_json(DOC1, doc_type)
        save_doc.save()
        assert save_doc.id
        assert save_doc.document_service_id
        assert save_doc.consumer_document_id
        documents = Document.find_by_document_id(save_doc.consumer_document_id)
        assert documents
        document: Document = documents[0]
        assert document.consumer_document_id == save_doc.consumer_document_id
        assert document.document_type == doc_type
        doc_json = document.json
        assert doc_json
        assert doc_json.get("documentClass") == doc_class
        assert doc_json.get("documentTypeDescription")
        assert doc_json.get("description") == DOC1.get("description")
        if has_scan:
            assert doc_json.get("scanningInformation")
        else:
            assert not doc_json.get("scanningInformation")


@pytest.mark.parametrize("id, has_results, doc_type, doc_class, query_doc_type", TEST_CONSUMER_ID_DATA)
def test_find_by_consumer_id(session, id, has_results, doc_type, doc_class, query_doc_type):
    """Assert that find document by consumer identifier contains all expected elements."""
    if not has_results:
        document: Document = Document.find_by_consumer_id(id)
        assert not document
    else:
        save_doc: Document = Document.create_from_json(DOC1, doc_type)
        save_doc.save()
        assert save_doc.id
        assert save_doc.document_service_id
        assert save_doc.consumer_document_id
        assert save_doc.consumer_identifier
        documents = Document.find_by_consumer_id(save_doc.consumer_identifier, doc_type if query_doc_type else None)
        assert documents
        document: Document = documents[0]
        assert document.consumer_document_id == save_doc.consumer_document_id
        assert document.consumer_identifier == save_doc.consumer_identifier
        assert document.document_type == doc_type
        doc_json = document.json
        assert doc_json
        assert doc_json.get("documentClass") == doc_class
        assert doc_json.get("documentTypeDescription")
        assert doc_json.get("description") == DOC1.get("description")


def test_document_json(session):
    """Assert that the document model renders to a json format correctly."""
    document: Document = TEST_DOCUMENT
    document.doc_type = DocumentType.find_by_doc_type(document.document_type)
    doc_json = document.json
    test_json = copy.deepcopy(DOC1)
    test_json["documentServiceId"] = document.document_service_id
    test_json["createDateTime"] = doc_json.get("createDateTime")
    test_json["documentClass"] = doc_json.get("documentClass")
    test_json["documentTypeDescription"] = doc_json.get("documentTypeDescription")
    test_json["documentURL"] = doc_json.get("documentURL")
    assert doc_json == test_json


@pytest.mark.parametrize("has_doc_id, doc_type", TEST_CREATE_JSON_DATA)
def test_create_from_json(session, has_doc_id, doc_type):
    """Assert that the new document is created from a new request json data correctly."""
    json_data = copy.deepcopy(DOC1)
    if not has_doc_id:
        del json_data["consumerDocumentId"]
    document: Document = Document.create_from_json(json_data, doc_type)
    assert document
    assert document.id
    assert document.document_service_id
    if has_doc_id:
        assert document.consumer_document_id == json_data.get("consumerDocumentId")
    else:
        assert document.consumer_document_id
    assert document.add_ts
    assert document.document_type == doc_type
    assert document.consumer_filing_date
    assert document.consumer_filename == json_data.get("consumerFilename")
    assert document.consumer_identifier == json_data.get("consumerIdentifier")
    assert document.description == json_data.get("description")
