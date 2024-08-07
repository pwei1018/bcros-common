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

import pytest

from doc_api.models import Document, DocumentRequest, utils as model_utils, User
from doc_api.models.type_tables import DocumentTypes, RequestTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.services.abstract_storage_service import DocumentTypes as StorageDocTypes
from doc_api.utils.logging import logger


TEST_DATAFILE = 'tests/unit/services/unit_test.pdf'
TEST_USER: User = User(username='testuser')
TEST_INFO: RequestInfo = RequestInfo(request_type=RequestTypes.ADD,
                                     request_path='path',
                                     doc_type=DocumentTypes.NR_MISC,
                                     doc_storage_type=StorageDocTypes.NR)

# testdata pattern is ({req_type}, {req_path}, {doc_type}, {doc_storage_type}, {staff})
TEST_DATA_REQUEST_INFO = [
    (RequestTypes.ADD.value, '/CORP/CORP_MISC', DocumentTypes.CORP_MISC.value, StorageDocTypes.BUSINESS.value, True),
    (RequestTypes.GET.value, '/MHR_MISC', DocumentTypes.MHR_MISC.value, StorageDocTypes.MHR.value, False),
    (RequestTypes.REPLACE.value, '/NR_MISC', DocumentTypes.NR_MISC.value, StorageDocTypes.NR.value, True),
    (RequestTypes.UPDATE.value, '/PPR_MISC', DocumentTypes.PPR_MISC.value, StorageDocTypes.PPR.value, False)
]
# testdata pattern is ({doc_ts}, {doc_type}, {doc_service_id}, {content_type}, {doc_storage_type})
TEST_DATA_SAVE_STORAGE = [
    ('2024-09-01T19:00:00+00:00', DocumentTypes.CORP_MISC, 'UT000001111', model_utils.CONTENT_TYPE_PDF,
     StorageDocTypes.BUSINESS)
]
# testdata pattern is ({info}, {user}, {doc_id}, {account_id})
TEST_DATA_DOC_REQUEST = [
    (TEST_INFO, TEST_USER, 100, 'UT1234')
]


@pytest.mark.parametrize('info,user,doc_id,account_id', TEST_DATA_DOC_REQUEST)
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


@pytest.mark.parametrize('req_type,req_path,doc_type,doc_storage_type,staff', TEST_DATA_REQUEST_INFO)
def test_request_info(session, req_type, req_path, doc_type, doc_storage_type, staff):
    """Assert that building the base request info works as expected."""
    info: RequestInfo = RequestInfo(req_type, req_path, doc_type, doc_storage_type)
    assert info.request_type == req_type
    assert info.request_path == req_path
    assert info.document_type == doc_type
    assert info.document_storage_type == doc_storage_type
    info.staff = staff
    info_json = info.json
    assert info_json.get('staff') == staff
    assert info_json.get('documentType') == doc_type
    assert 'documentServiceId' in info_json
    assert 'accept' in info_json
    assert 'contentType' in info_json
    assert 'consumerDocumentId' in info_json
    assert 'consumerFilename' in info_json
    assert 'consumerFiledate' in info_json
    assert 'consumerIdentifer' in info_json
    assert 'consumerScanDate' in info_json


@pytest.mark.parametrize('doc_ts,doc_type,doc_service_id,content_type,doc_storage_type', TEST_DATA_SAVE_STORAGE)
def test_save_doc_storage(session, doc_ts, doc_type, doc_service_id, content_type, doc_storage_type):
    """Assert that uploading a doc to document storage works as expected."""
    doc: Document = Document(add_ts=model_utils.ts_from_iso_format(doc_ts),
                             document_type=doc_type,
                             document_service_id=doc_service_id)
    info: RequestInfo = RequestInfo('ADD', '/business/CORP/CORP_MISC', doc_type, doc_storage_type)
    info.content_type = content_type
    raw_data = None
    with open(TEST_DATAFILE, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    doc_link = resource_utils.save_to_doc_storage(doc, info, raw_data)
    assert doc_link
    assert doc.doc_storage_url
