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
"""Test Suite to ensure the request utility functions are working as expected."""
import copy
import json

import pytest

from doc_api.models import Document, DocumentRequest, DocumentScanning, User
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes, RequestTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.services.abstract_storage_service import DocumentTypes as StorageDocTypes
from doc_api.utils.logging import logger

TEST_DATAFILE = "tests/unit/services/unit_test.pdf"
TEST_USER: User = User(username="testuser")
TEST_INFO: RequestInfo = RequestInfo(
    request_type=RequestTypes.ADD,
    request_path="path",
    doc_type=DocumentTypes.CORR,
    doc_storage_type=StorageDocTypes.NR,
)
TEST_DOCUMENT = Document(
    id=200000000,
    document_service_id="UT9999999",
    document_type=DocumentTypes.CORR.value,
    document_class=DocumentClasses.PPR.value,
    add_ts=model_utils.now_ts(),
    consumer_document_id="T0000001",
    consumer_identifier="T0000002",
    consumer_filename="test.pdf",
    consumer_filing_date=model_utils.ts_from_iso_date_noon("2024-07-01"),
    description="Original",
    consumer_reference_id = "800000"
)
TEST_TOKEN = {
    "username": "username_TEST1",
    "firstname": "given_name_TEST1",
    "lastname": "family_name_TEST1",
    "iss": "issuer_TEST1",
    "sub": "subject_TEST1",
    "idp_userid": "idp_userid_TEST1",
    "loginSource": "source_TEST1",
}
TEST_FILENAME = "updated_name.pdf"
DOC_SCAN = {
    "consumerDocumentId": "T0000002",
    "scanDateTime": "2024-07-01T19:00:00+00:00",
    "documentClass": "PPR",
    "accessionNumber": "AN-0001",
    "batchId": "1234",
    "author": "Jane Smith",
    "pageCount": 3,
}
UPDATE_DOC_SCAN = {
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
    "documentType": "CORR",
    "documentClass": "CORP",
    "consumerFilingDateTime": "2024-08-01T19:00:00+00:00",
    "description": "Updated description of the document.",
    "consumerReferenceId": "800001"
}
REMOVE_DOC = {
    "removed": True
}
TEST_DOC_REC_LEGACY = {
    "accountId": "123456",
    "consumerDocumentId": "99990950",
    "consumerIdentifier": "108924",
    "documentType": "REGC",
    "documentClass": "MHR",
    "author": "John Jones"
}
TEST_DOC_REC_MODERN = {
    "accountId": "123456",
    "consumerDocumentId": "1099990950",
    "consumerIdentifier": "108924",
    "documentType": "TRAN",
    "documentClass": "MHR",
    "author": "John Jones",
    "consumerReferenceId": "900000",
}
TEST_DOC_REC_UPDATE = {
    "accountId": "123456",
    "consumerDocumentId": "1099990950",
    "consumerIdentifier": "108925",
    "documentType": "CORR",
    "documentClass": "MHR",
    "author": "JAMES Jones",
    "consumerReferenceId": "900001",
}
TEST_DOCUMENT_DELETE = Document(
    id=200000001,
    document_service_id="UTD9999990",
    document_type=DocumentTypes.CORR.value,
    document_class=DocumentClasses.PPR.value,
    add_ts=model_utils.now_ts(),
    consumer_document_id="TD0000001",
    consumer_identifier="TD0000002",
    consumer_filename="test-delete.pdf",
    consumer_filing_date=model_utils.ts_from_iso_date_noon("2024-07-01"),
    description="Original",
)

# testdata pattern is ({req_type}, {req_path}, {doc_type}, {doc_storage_type}, {staff} , {ref_id})
TEST_DATA_REQUEST_INFO = [
    (RequestTypes.ADD.value, "/CORP/CORR", DocumentTypes.CORR.value, StorageDocTypes.BUSINESS.value, True, "UT0001"),
    (RequestTypes.GET.value, "/CORR", DocumentTypes.CORR.value, StorageDocTypes.MHR.value, False, None),
    (RequestTypes.REPLACE.value, "/CORR", DocumentTypes.CORR.value, StorageDocTypes.NR.value, True, None),
    (RequestTypes.UPDATE.value, "/CORR", DocumentTypes.CORR.value, StorageDocTypes.PPR.value, False, "UT0002"),
]
# testdata pattern is ({doc_ts}, {doc_type}, {doc_service_id}, {content_type}, {doc_storage_type})
TEST_DATA_SAVE_STORAGE = [
    (
        "2024-09-01T19:00:00+00:00",
        DocumentTypes.CORR,
        "UT000001111",
        model_utils.CONTENT_TYPE_PDF,
        StorageDocTypes.BUSINESS,
    )
]
# testdata pattern is ({info}, {user}, {doc_id}, {account_id})
TEST_DATA_DOC_REQUEST = [(TEST_INFO, TEST_USER, 100, "UT1234")]
# testdata pattern is ({doc_class}, {start_offset}, {doc_type}, {cons_id}, {no_results})
TEST_DATA_DOC_DATES = [
    (None, 10, None, None, True),
    (DocumentClasses.CORP, 10, None, None, False),
    (DocumentClasses.CORP, 1, DocumentTypes.CORR, None, True),
    (DocumentClasses.CORP.value, 10, None, "UT000004", False),
    (DocumentClasses.CORP.value, 10, DocumentTypes.CORR.value, "UT000004", False),
]
# testdata pattern is ({doc_class}, {storage_type})
TEST_DATA_STORAGE_TYPES = [
    (DocumentClasses.CORP, StorageDocTypes.BUSINESS),
    (DocumentClasses.COOP, StorageDocTypes.BUSINESS),
    (DocumentClasses.FIRM, StorageDocTypes.BUSINESS),
    (DocumentClasses.OTHER, StorageDocTypes.BUSINESS),
    (DocumentClasses.SOCIETY, StorageDocTypes.BUSINESS),
    (DocumentClasses.MHR, StorageDocTypes.MHR),
    (DocumentClasses.NR, StorageDocTypes.NR),
    (DocumentClasses.PPR, StorageDocTypes.PPR),
]
# testdata pattern is ({document}, {token}, {doc_class}, {scan_info}, {update_scan_info}, {update_class_type})
TEST_UPDATE_DATA = [
    (TEST_DOCUMENT, TEST_TOKEN, DocumentClasses.PPR.value, None, None, True),
    (TEST_DOCUMENT, TEST_TOKEN, DocumentClasses.PPR.value, DOC_SCAN, None, False),
    (TEST_DOCUMENT, TEST_TOKEN, DocumentClasses.PPR.value, None, UPDATE_DOC_SCAN, False),
    (TEST_DOCUMENT, TEST_TOKEN, DocumentClasses.PPR.value, DOC_SCAN, UPDATE_DOC_SCAN, True)
]
# testdata pattern is ({document}, {token}, {filename})
TEST_REPLACE_DATA = [(TEST_DOCUMENT, TEST_TOKEN, TEST_FILENAME)]
# testdata pattern is ({request_data}, {update})
TEST_CALLBACK_REC_DATA = [
    (TEST_DOC_REC_LEGACY, False),
    (TEST_DOC_REC_MODERN, True),
]
# testdata pattern is ({document}, {token}, {filename})
TEST_DELETE_DATA = [(TEST_DOCUMENT_DELETE, TEST_TOKEN, TEST_FILENAME)]
# testdata pattern is ({document}, {token}, {scan_info})
TEST_REMOVE_DATA = [
    (TEST_DOCUMENT, TEST_TOKEN, None),
    (TEST_DOCUMENT, TEST_TOKEN, DOC_SCAN)
]


@pytest.mark.parametrize("request_data, update", TEST_CALLBACK_REC_DATA)
def test_save_callback_data(session, request_data, update):
    """Assert that POST request resource_utils.save_callback_create_rec works as expected."""
    info: RequestInfo = RequestInfo(RequestTypes.ADD.value, None, None, None)
    info = resource_utils.get_callback_request_info(request_data, info)
    result = None
    if update:
        doc: Document = Document.create_from_json(TEST_DOC_REC_UPDATE, TEST_DOC_REC_UPDATE.get("documentType"))
        doc.save()
        result = resource_utils.save_callback_update_rec(info, doc)
    else:
        result = resource_utils.save_callback_create_rec(info)
    assert result
    assert result.get("documentServiceId")
    assert result.get("createDateTime")
    assert result.get("documentType") == request_data.get("documentType")
    assert result.get("documentTypeDescription")
    assert result.get("documentClass") == request_data.get("documentClass")
    assert result.get("consumerDocumentId") == request_data.get("consumerDocumentId")
    assert result.get("consumerIdentifier") == request_data.get("consumerIdentifier")
    assert result.get("author") == request_data.get("author")
    assert not result.get("consumerFilename")
    assert not result.get("documentURL")
    assert not result.get("scanningInformation")
    if update:
        assert result.get("consumerReferenceId") == request_data.get("consumerReferenceId")


@pytest.mark.parametrize("document,token,filename", TEST_REPLACE_DATA)
def test_save_replace(session, document, token, filename):
    """Assert that PUT request resource_utils.save_replace works as expected."""
    doc: Document = copy.deepcopy(document)
    doc.save()
    assert not doc.doc_storage_url
    info: RequestInfo = RequestInfo(RequestTypes.REPLACE.value,
                                    None,
                                    doc.document_type,
                                    resource_utils.get_doc_storage_type(doc.document_class))
    info.account_id = "1234"
    info.document_service_id = doc.document_service_id
    info.staff = True
    info.document_class = doc.document_class
    info.consumer_filename = filename
    info.content_type = model_utils.CONTENT_TYPE_PDF
    raw_data = None
    with open(TEST_DATAFILE, "rb") as data_file:
        raw_data = data_file.read()
        data_file.close()
    result = resource_utils.save_replace(info, doc, token, raw_data)
    assert doc.doc_storage_url
    assert result.get("documentServiceId")
    assert result.get("createDateTime")
    assert result.get("documentType") == doc.document_type
    assert result.get("documentTypeDescription")
    assert result.get("documentClass")
    assert result.get("consumerDocumentId") == doc.consumer_document_id
    assert result.get("consumerIdentifier") == doc.consumer_identifier
    assert result.get("consumerFilename") == filename
    assert result.get("consumerFilingDateTime")
    assert result.get("documentURL")


@pytest.mark.parametrize("document,token,filename", TEST_DELETE_DATA)
def test_save_delete(session, document, token, filename):
    """Assert that DELETE request resource_utils.save_delete works as expected."""
    doc: Document = copy.deepcopy(document)
    doc.save()
    assert not doc.doc_storage_url
    info: RequestInfo = RequestInfo(RequestTypes.REPLACE.value,
                                    None,
                                    doc.document_type,
                                    resource_utils.get_doc_storage_type(doc.document_class))
    info.account_id = "1234"
    info.document_service_id = doc.document_service_id
    info.staff = True
    info.content_type = model_utils.CONTENT_TYPE_PDF
    info.document_class = doc.document_class
    info.consumer_filename = filename
    # info.document_class = doc_class
    raw_data = None
    with open(TEST_DATAFILE, "rb") as data_file:
        raw_data = data_file.read()
        data_file.close()
    result1 = resource_utils.save_replace(info, doc, token, raw_data)
    assert doc.doc_storage_url
    assert result1.get("documentURL")

    info.request_type = RequestTypes.DELETE.value
    del_doc: Document = Document.find_by_doc_service_id(doc.document_service_id)
    result = resource_utils.save_delete(info, del_doc, token)
    assert not doc.doc_storage_url
    assert not result.get("documentURL")


@pytest.mark.parametrize("document,token,,doc_class,scan_info,update_scan_info,update_class_type", TEST_UPDATE_DATA)
def test_save_update(session, document, token, doc_class, scan_info,  update_scan_info, update_class_type):
    """Assert that patch request resource_utils.save_update works as expected."""
    doc: Document = copy.deepcopy(document)
    doc.save()
    existing_doc = doc.json
    if scan_info:
        scan_doc: DocumentScanning = DocumentScanning.create_from_json(scan_info,
                                                                       UPDATE_DOC.get("consumerDocumentId"),
                                                                       doc_class)
        scan_doc.id = 200000000
        scan_doc.save()
        existing_doc["scanningInformation"] = scan_info
    info: RequestInfo = RequestInfo(RequestTypes.UPDATE.value, None, UPDATE_DOC.get("documentType"), None)
    request_data = copy.deepcopy(UPDATE_DOC)
    request_data["existingDocument"] = existing_doc
    if not update_class_type:
        del request_data["documentClass"]
    if update_scan_info:
        request_data['scanningInformation'] = update_scan_info
    info.request_data = request_data
    info.account_id = "1234"
    info.document_class = doc_class
    info.consumer_doc_id = request_data.get("consumerDocumentId")
    info.consumer_identifier = request_data.get("consumerIdentifier")
    info.consumer_filename = request_data.get("consumerFilename")
    info.consumer_filedate = request_data.get("consumerFilingDateTime")
    info.description = request_data.get("description")
    logger.info(info.request_data)
    result = resource_utils.save_update(info, doc, token)
    assert result.get("documentServiceId")
    assert result.get("createDateTime")
    assert result.get("documentTypeDescription")
    if update_class_type:
        assert result.get("documentType") == request_data.get("documentType")
    else:
        assert result.get("documentType") == doc.document_type
    assert result.get("documentClass") == doc.document_class
    assert result.get("consumerDocumentId") == request_data.get("consumerDocumentId")
    assert result.get("consumerFilename") == request_data.get("consumerFilename")
    assert result.get("consumerIdentifier") == request_data.get("consumerIdentifier")
    assert result.get("description") == request_data.get("description")
    assert result.get("consumerFilingDateTime") == request_data.get("consumerFilingDateTime")
    assert not result.get("documentURL")
    if scan_info:
        assert result.get("scanningInformation")
        scan_json = result.get("scanningInformation")
        if not update_scan_info:
            assert scan_json.get("scanDateTime") == scan_info.get("scanDateTime")
            assert scan_json.get("accessionNumber") == scan_info.get("accessionNumber")
            assert scan_json.get("batchId") == scan_info.get("batchId")
            assert scan_json.get("author") == scan_info.get("author")
            assert scan_json.get("pageCount") == scan_info.get("pageCount")
        else:
            assert scan_json.get("scanDateTime") == update_scan_info.get("scanDateTime")
            assert scan_json.get("accessionNumber") == update_scan_info.get("accessionNumber")
            assert scan_json.get("batchId") == update_scan_info.get("batchId")
            assert scan_json.get("author") == update_scan_info.get("author")
            assert scan_json.get("pageCount") == update_scan_info.get("pageCount")
    else:
        assert not result.get("scanningInformation")
    assert result.get("consumerReferenceId") == request_data.get("consumerReferenceId")


@pytest.mark.parametrize("document,token,scan_info", TEST_REMOVE_DATA)
def test_save_remove(session, document, token, scan_info):
    """Assert that patch request resource_utils.save_update works as expected when removing a doc record."""
    doc: Document = copy.deepcopy(document)
    doc.save()
    scan_doc: DocumentScanning = None
    if scan_info:
        scan_doc = DocumentScanning.create_from_json(scan_info, doc.consumer_document_id, doc.document_class)
        scan_doc.id = 200000000
        scan_doc.save()
    info: RequestInfo = RequestInfo(RequestTypes.UPDATE.value, None, doc.document_type, None)
    request_data = copy.deepcopy(REMOVE_DOC)
    info.request_data = request_data
    info.account_id = "1234"
    info.document_class = doc.document_class
    info.document_type = doc.document_type
    info.document_service_id = doc.document_service_id
    result = resource_utils.save_update(info, doc, token)
    assert not result
    test_doc = Document.find_by_id(doc.id)
    assert test_doc
    if scan_doc:
        test_scan = DocumentScanning.find_by_id(scan_doc.id)
        assert test_scan


@pytest.mark.parametrize("doc_class,start_offset,doc_type,cons_id,no_results", TEST_DATA_DOC_DATES)
def test_get_docs_by_dates(session, doc_class, start_offset, doc_type, cons_id, no_results):
    """Assert that get_docs_by_date_range works as expected."""
    info: RequestInfo = RequestInfo(RequestTypes.GET.value, None, doc_type, None)
    info.account_id = "1234"
    info.document_class = doc_class
    info.consumer_identifier = cons_id
    end = model_utils.now_ts()
    start = model_utils.date_offset(end.date(), start_offset)
    info.query_start_date = start.isoformat()
    info.query_end_date = end.isoformat()
    results = resource_utils.get_docs(info)
    if no_results:
        assert not results
    elif results:
        for result in results:
            assert result.get("documentServiceId")
            assert result.get("createDateTime")
            assert result.get("documentType")
            assert result.get("documentTypeDescription")
            assert result.get("documentClass")
            if doc_type:
                assert result.get("documentType") == doc_type
            if cons_id:
                assert result.get("consumerIdentifier") == cons_id
            assert not result.get("documentURL")


@pytest.mark.parametrize("info,user,doc_id,account_id", TEST_DATA_DOC_REQUEST)
def test_build_doc_request(session, info, user, doc_id, account_id):
    """Assert that building the document request model from the request works as expected."""
    info: RequestInfo = copy.deepcopy(info)
    info.staff = True
    info.account_id = account_id
    doc_request: DocumentRequest = resource_utils.build_doc_request(info, user, doc_id)
    assert doc_request
    assert doc_request.request_ts
    assert doc_request.document_id
    assert doc_request.account_id == account_id
    assert doc_request.document_id == doc_id
    assert doc_request.username == user.username
    assert doc_request.request_data


@pytest.mark.parametrize("req_type,req_path,doc_type,doc_storage_type,staff,ref_id", TEST_DATA_REQUEST_INFO)
def test_request_info(session, req_type, req_path, doc_type, doc_storage_type, staff, ref_id):
    """Assert that building the base request info works as expected."""
    info: RequestInfo = RequestInfo(req_type, req_path, doc_type, doc_storage_type)
    assert info.request_type == req_type
    assert info.request_path == req_path
    assert info.document_type == doc_type
    assert info.document_storage_type == doc_storage_type
    info.staff = staff
    info.consumer_reference_id = ref_id
    info_json = info.json
    assert info_json.get("staff") == staff
    assert info_json.get("documentType") == doc_type
    assert "documentServiceId" in info_json
    assert "accept" in info_json
    assert "contentType" in info_json
    assert "consumerDocumentId" in info_json
    assert "consumerFilename" in info_json
    assert "consumerFilingDate" in info_json
    assert "consumerIdentifier" in info_json
    assert "consumerReferenceId" in info_json
    if ref_id:
        assert info_json.get("consumerReferenceId") == ref_id


@pytest.mark.parametrize("doc_ts,doc_type,doc_service_id,content_type,doc_storage_type", TEST_DATA_SAVE_STORAGE)
def test_save_doc_storage(session, doc_ts, doc_type, doc_service_id, content_type, doc_storage_type):
    """Assert that uploading a doc to document storage works as expected."""
    doc: Document = Document(
        add_ts=model_utils.ts_from_iso_format(doc_ts), document_type=doc_type, document_service_id=doc_service_id
    )
    info: RequestInfo = RequestInfo("ADD", "/business/CORP/CORR", doc_type, doc_storage_type)
    info.content_type = content_type
    raw_data = None
    with open(TEST_DATAFILE, "rb") as data_file:
        raw_data = data_file.read()
        data_file.close()
    doc_link = resource_utils.save_to_doc_storage(doc, info, raw_data)
    assert doc_link
    assert doc.doc_storage_url


@pytest.mark.parametrize("doc_class,storage_type", TEST_DATA_STORAGE_TYPES)
def test_get_storage_type(session, doc_class, storage_type):
    """Assert that get_docs_by_date_range works as expected."""
    test_type = resource_utils.get_doc_storage_type(doc_class)
    assert test_type == storage_type
