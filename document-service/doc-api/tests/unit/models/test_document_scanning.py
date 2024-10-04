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

from doc_api.models import DocumentScanning
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses

DOC_SCAN1 = {
    "consumerDocumentId": "T0000001",
    "scanDateTime": "2024-07-01T19:00:00+00:00",
    "documentClass": "MHR",
    "accessionNumber": "AN-0001",
    "batchId": "1234",
    "author": "Jane Smith",
    "pageCount": 3,
}
DOC_SCAN2 = {
    "scanDateTime": "2024-08-15T19:00:00+00:00",
    "accessionNumber": "AN-0002",
    "batchId": "12345",
    "author": "Janet Smith",
    "pageCount": 4,
}
TEST_DOC_SCAN = DocumentScanning(
    id=1,
    consumer_document_id="T0000001",
    scan_date=model_utils.ts_from_iso_date_noon("2024-07-01"),
    document_class=DocumentClasses.MHR.value,
    accession_number="AN-0001",
    batch_id="1234",
    author="Jane Smith",
    page_count=3,
)

# testdata pattern is ({id}, {has_results}, {consumer_doc_id), {doc_class})
TEST_ID_DATA = [
    (200000001, True, "99990000", DocumentClasses.PPR.value),
    (300000000, False, "99990000", DocumentClasses.PPR.value),
]
# testdata pattern is ({id}, {consumer_doc_id), {doc_class}, {update_doc_id}, {update_doc_class})
TEST_UPDATE_DATA = [
    (200000001, "99990000", DocumentClasses.PPR.value, None, None),
    (200000001, "99990000", DocumentClasses.PPR.value, "99990000", DocumentClasses.CORP.value),
]
# testdata pattern is ({consumer_doc_id}, {doc_type})
TEST_CREATE_JSON_DATA = [("99990000", DocumentClasses.PPR.value), ("99990001", DocumentClasses.MHR.value)]
# testdata pattern is ({batch_id}, {accession_num}, {query_accession_num}, {expected_id})
TEST_MAX_BATCH_ID_DATA = [
    ("1000", "UT-MAX-0001", "UT-MAX-0001", 1000),
    ("1000", "UT-MAX-0001", "UT-MAX-10001", 0),
]


@pytest.mark.parametrize("scan_id, has_results, cons_doc_id, doc_class", TEST_ID_DATA)
def test_find_by_id(session, scan_id, has_results, cons_doc_id, doc_class):
    """Assert that find document scanning by primary key contains all expected elements."""
    if not has_results:
        doc_scan: DocumentScanning = DocumentScanning.find_by_id(scan_id)
        assert not doc_scan
    else:
        save_scan: DocumentScanning = DocumentScanning.create_from_json(DOC_SCAN1, cons_doc_id, doc_class)
        save_scan.id = scan_id
        save_scan.save()
        assert save_scan.id
        assert save_scan.consumer_document_id
        doc_scan: DocumentScanning = DocumentScanning.find_by_id(save_scan.id)
        assert doc_scan
        assert doc_scan.consumer_document_id == save_scan.consumer_document_id
        assert doc_scan.document_class == doc_class
        scan_json = doc_scan.json
        assert scan_json
        assert scan_json.get("documentClass") == doc_class
        assert scan_json.get("consumerDocumentId") == cons_doc_id
        assert scan_json.get("scanDateTime")


@pytest.mark.parametrize("scan_id, has_results, cons_doc_id, doc_class", TEST_ID_DATA)
def test_find_by_consumer_id(session, scan_id, has_results, cons_doc_id, doc_class):
    """Assert that find document scanning by consumer identifier and document class contains all expected elements."""
    if not has_results:
        doc_scan: DocumentScanning = DocumentScanning.find_by_document_id(cons_doc_id, doc_class)
        assert not doc_scan
    else:
        save_scan: DocumentScanning = DocumentScanning.create_from_json(DOC_SCAN1, cons_doc_id, doc_class)
        save_scan.id = scan_id
        save_scan.save()
        assert save_scan.id
        assert save_scan.consumer_document_id
        doc_scan: DocumentScanning = DocumentScanning.find_by_document_id(cons_doc_id, doc_class)
        assert doc_scan
        assert doc_scan.consumer_document_id == save_scan.consumer_document_id
        assert doc_scan.document_class == doc_class
        scan_json = doc_scan.json
        assert scan_json
        assert scan_json.get("documentClass") == doc_class
        assert scan_json.get("consumerDocumentId") == cons_doc_id
        assert scan_json.get("scanDateTime")


@pytest.mark.parametrize("scan_id, cons_doc_id, doc_class, update_doc_id, update_doc_class", TEST_UPDATE_DATA)
def test_update(session, scan_id, cons_doc_id, doc_class, update_doc_id, update_doc_class):
    """Assert that update document scanning by consumer identifier and document class contains all expected elements."""
    save_scan: DocumentScanning = DocumentScanning.create_from_json(DOC_SCAN1, cons_doc_id, doc_class)
    save_scan.id = scan_id
    save_scan.save()
    assert save_scan.id
    assert save_scan.consumer_document_id == cons_doc_id
    assert save_scan.document_class == doc_class
    save_scan.update(DOC_SCAN2, update_doc_id, update_doc_class)
    if update_doc_id:
        assert save_scan.consumer_document_id == update_doc_id
    if update_doc_class:
        assert save_scan.document_class == update_doc_class
    save_scan.save()
    test_doc_id: str = update_doc_id if update_doc_id else cons_doc_id
    test_doc_class: str = update_doc_class if update_doc_class else doc_class
    doc_scan: DocumentScanning = DocumentScanning.find_by_document_id(test_doc_id, test_doc_class)
    assert doc_scan
    assert doc_scan.consumer_document_id == save_scan.consumer_document_id
    assert doc_scan.document_class == save_scan.document_class
    scan_json = doc_scan.json
    assert scan_json
    assert scan_json.get("documentClass") == test_doc_class
    assert scan_json.get("consumerDocumentId") == test_doc_id
    assert scan_json.get("scanDateTime") == DOC_SCAN2.get("scanDateTime")
    assert scan_json.get("accessionNumber") == DOC_SCAN2.get("accessionNumber")
    assert scan_json.get("batchId") == DOC_SCAN2.get("batchId")
    assert scan_json.get("author") == DOC_SCAN2.get("author")
    assert scan_json.get("pageCount") == DOC_SCAN2.get("pageCount")


def test_doc_scan_json(session):
    """Assert that the document scann model renders to a json format correctly."""
    doc_scan: DocumentScanning = TEST_DOC_SCAN
    doc_json = doc_scan.json
    test_json = copy.deepcopy(DOC_SCAN1)
    assert doc_json == test_json


@pytest.mark.parametrize("cons_doc_id, doc_class", TEST_CREATE_JSON_DATA)
def test_create_from_json(session, cons_doc_id, doc_class):
    """Assert that the new document scanning record is created from a new request json data correctly."""
    json_data = copy.deepcopy(DOC_SCAN1)
    doc_scan: DocumentScanning = DocumentScanning.create_from_json(json_data, cons_doc_id, doc_class)
    assert doc_scan
    assert not doc_scan.id
    assert doc_scan.consumer_document_id == cons_doc_id
    assert doc_scan.scan_date
    assert doc_scan.document_class == doc_class
    assert doc_scan.batch_id == json_data.get("batchId")
    assert doc_scan.accession_number == json_data.get("accessionNumber")
    assert doc_scan.author == json_data.get("author")
    assert doc_scan.page_count == json_data.get("pageCount")


# testdata pattern is ({batch_id}, {accession_num}, {query_accession_num}, {expected_id})
@pytest.mark.parametrize("batch_id, accession_num, query_accession_num, expected_id", TEST_MAX_BATCH_ID_DATA)
def test_get_max_batch_id(session, batch_id, accession_num, query_accession_num, expected_id):
    """Assert that getting the maximum batch id by accession number works as expected."""
    save_scan: DocumentScanning = DocumentScanning.create_from_json(DOC_SCAN1, "UT99999999", DocumentClasses.PPR.value)
    save_scan.id = 200000000
    save_scan.batch_id = batch_id
    save_scan.accession_number = accession_num
    save_scan.save()
    max_batch_id: int = DocumentScanning.get_max_batch_id(query_accession_num)
    assert max_batch_id == expected_id
