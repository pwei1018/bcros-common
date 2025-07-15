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
import json

import pytest
from flask import current_app

from doc_api.models import Document, DocumentScanning
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentType, DocumentTypes
from doc_api.utils.logging import logger

APP_DOC1 = {
    "name": "test.pdf",
    "identifier": "1",
    "dateCreated": "2024-07-10T19:00:00+00:00",
    "datePublished": "2024-07-01T19:00:00+00:00",
    "url": ""
}
DOC1 = {
    "consumerDocumentId": "T0000001",
    "consumerFilename": "test.pdf",
    "consumerIdentifier": "T0000002",
    "documentType": "CORR",
    "documentClass": "PPR",
    "consumerFilingDateTime": "2024-07-01T19:00:00+00:00",
    "description": "A meaningful description of the document.",
    "author": "John Smith",
    "consumerReferenceId": "9014001"
}
DOC2 = {
    "consumerDocumentId": "T0000001",
    "consumerFilename": "test.pdf",
    "consumerIdentifier": "T0000002",
    "documentType": "CORR",
    "documentClass": "MHR",
    "consumerFilingDateTime": "2024-07-01T19:00:00+00:00",
    "description": "A meaningful description of the document.",
    "author": "John Smith",
    "consumerReferenceId": "9014001"
}
DOC3 = {
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
DOC_SCAN = {
    "scanDateTime": "2024-08-15T19:00:00+00:00",
    "accessionNumber": "AN-0002",
    "batchId": "12345",
    "author": "Janet Smith",
    "pageCount": 4,
}
UPDATE_DOC = {
    "consumerDocumentId": "T0000002",
    "consumerFilename": "test-update.pdf",
    "consumerIdentifier": "CI-0000002",
    "documentType": "TRAN",
    "documentClass": "CORP",
    "consumerFilingDateTime": "2024-08-01T19:00:00+00:00",
    "description": "Updated description of the document.",
    "author": "John Smith",
    "consumerReferenceId": "9014002"
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
    description="A meaningful description of the document.",
    author = "John Smith",
    consumer_reference_id = "9014001"
)
TEST_APP_DOCUMENT = Document(
    id=1,
    document_service_id="1",
    document_type=DocumentTypes.APP_FILE.value,
    document_class=DocumentClasses.OTHER.value,
    add_ts=model_utils.now_ts(),
    consumer_document_id="T0000001",
    consumer_filename="test.pdf",
    consumer_filing_date=model_utils.ts_from_iso_date_noon("2024-07-01")
)

# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class})
TEST_ID_DATA = [
    (200000001, True, DocumentTypes.CORR.value, DocumentClasses.PPR.value),
    (300000000, False, DocumentTypes.CORR.value, DocumentClasses.PPR.value),
]
TEST_DOC_SERVICE_ID_DATA = [
    ("T0000001", True, DocumentTypes.CORR.value, DocumentClasses.MHR.value),
    ("XXXD0000", False, DocumentTypes.CORR.value, DocumentClasses.MHR.value),
]
# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class}, {has_scan})
TEST_DOC_ID_DATA = [
    ("T0000001", True, DocumentTypes.CORR.value, DocumentClasses.CORP.value, True),
    ("T0000001", True, DocumentTypes.CORR.value, DocumentClasses.CORP.value, False),
    ("XXXD0000", False, DocumentTypes.CORR.value, DocumentClasses.CORP.value, False),
]
# testdata pattern is ({id}, {has_results}, {doc_type), {doc_class}, {query_doc_type})
TEST_CONSUMER_ID_DATA = [
    ("T0000001", True, DocumentTypes.CORR.value, DocumentClasses.CORP.value, False),
    ("T0000001", True, DocumentTypes.CORR.value, DocumentClasses.CORP.value, True),
    ("XXXD0000", False, DocumentTypes.CORR.value, DocumentClasses.CORP.value, False),
]
# testdata pattern is ({id}, {has_results})
TEST_HISTORY_CONSUMER_ID_DATA = [
    ("T0000003", True),
    ("XXXD0000", False),
]
# testdata pattern is ({has_doc_id}, {doc_type})
TEST_CREATE_JSON_DATA = [(True, DocumentTypes.CORR.value), (False, DocumentTypes.CORR.value)]
# testdata pattern is ({doc_info}, {update_doc_info}, {update_class_type})
TEST_UPDATE_JSON_DATA = [
    (DOC2, UPDATE_DOC, True),
    (DOC2, UPDATE_DOC, False)
]


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
        req_json = copy.deepcopy(DOC1)
        req_json["documentClass"] = doc_class
        save_doc: Document = Document.create_from_json(req_json, doc_type)
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
        save_doc.document_class = doc_class
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
        assert doc_json.get("consumerReferenceId") == DOC1.get("consumerReferenceId")


@pytest.mark.parametrize("id, has_results, doc_type, doc_class, query_doc_type", TEST_CONSUMER_ID_DATA)
def test_find_by_consumer_id(session, id, has_results, doc_type, doc_class, query_doc_type):
    """Assert that find document by consumer identifier contains all expected elements."""
    if not has_results:
        document: Document = Document.find_by_consumer_id(id)
        assert not document
    else:
        req_json = copy.deepcopy(DOC1)
        req_json["documentClass"] = doc_class
        save_doc: Document = Document.create_from_json(req_json, doc_type)
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


@pytest.mark.parametrize("id, has_results", TEST_HISTORY_CONSUMER_ID_DATA)
def test_find_history_by_consumer_id(session, id, has_results):
    """Assert that find document history by consumer identifier contains all expected elements."""
    if not has_results:
        document: Document = Document.find_by_consumer_id(id)
        assert not document
    else:
        req_json = copy.deepcopy(DOC3)
        save_doc: Document = Document.create_from_json(req_json, req_json.get("documentType"))
        save_doc.save()
        assert save_doc.id
        assert save_doc.document_service_id
        assert save_doc.consumer_document_id
        assert save_doc.consumer_identifier
        doc_history = Document.find_history_by_consumer_id(save_doc.consumer_identifier)
        assert doc_history
        doc_json = doc_history[0]
        assert doc_json
        assert doc_json.get("identifier")
        assert doc_json.get("dateCreated")
        assert doc_json.get("entityIdentifier")
        assert doc_json.get("name")
        assert doc_json.get("eventIdentifier")
        assert doc_json.get("datePublished")
        assert doc_json.get("documentType")
        assert doc_json.get("documentClass")
        assert doc_json.get("documentTypeDescription")
        assert doc_json.get("consumerDocumentId")


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


def test_app_document_json(session):
    """Assert that the document model renders to a application document json format correctly."""
    document: Document = TEST_APP_DOCUMENT
    document.doc_type = DocumentType.find_by_doc_type(document.document_type)
    doc_json = document.app_json
    test_json = copy.deepcopy(APP_DOC1)
    test_json["dateCreated"] = doc_json.get("dateCreated")
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
    assert document.author == json_data.get("author")
    assert document.consumer_reference_id == json_data.get("consumerReferenceId")


@pytest.mark.parametrize("doc_info, update_doc_info, update_class_type", TEST_UPDATE_JSON_DATA)
def test_update(session, doc_info, update_doc_info, update_class_type):
    """Assert that updating document information contains all expected elements."""

    save_doc: Document = Document.create_from_json(doc_info, doc_info.get("documentType"))
    save_doc.save()
    assert save_doc.id
    assert save_doc.document_service_id
    assert save_doc.consumer_document_id
    if not update_class_type:
        del update_doc_info["documentType"]
    save_doc.update(update_doc_info)
    save_doc.save()
    update_doc: Document = Document.find_by_doc_service_id(save_doc.document_service_id)
    assert update_doc
    assert update_doc.consumer_document_id == save_doc.consumer_document_id
    if update_class_type:
        assert update_doc.document_type == update_doc_info["documentType"]
    else:
        assert update_doc.document_type == doc_info["documentType"]
    assert update_doc.document_class == doc_info["documentClass"]
    doc_json = update_doc.json
    assert doc_json
    assert doc_json.get("documentClass") == save_doc.document_class
    assert doc_json.get("documentTypeDescription")
    assert doc_json.get("consumerDocumentId") == update_doc_info.get("consumerDocumentId")
    assert doc_json.get("consumerFilename") == update_doc_info.get("consumerFilename")
    assert doc_json.get("consumerIdentifier") == update_doc_info.get("consumerIdentifier")
    assert doc_json.get("consumerFilingDateTime") == update_doc_info.get("consumerFilingDateTime")
    assert doc_json.get("author") == update_doc_info.get("author")
    assert doc_json.get("consumerReferenceId") == update_doc_info.get("consumerReferenceId")


def test_find_history_by_document_id(session):
    """Assert that find doc history by consumer document id contains all expected elements."""
    # doc_id: str = "0100000191"
    doc_id: str = ""
    if doc_id:
        doc_history = Document.find_history_by_document_id(doc_id)
        logger.info(f"Checking doc id {doc_id} history")
        if doc_history:
            history_json = json.dumps(doc_history).encode("utf-8")
            logger.info(history_json)
