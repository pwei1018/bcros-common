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

"""Tests to verify the endpoints for maintaining name request documents.

Test-Suite to ensure that the /nro endpoint is working as expected.
"""
from http import HTTPStatus

import pytest
from flask import current_app

from doc_api.models import utils as model_utils, Document
from doc_api.models.type_tables import DocumentClasses, DocumentTypes
from doc_api.services.authz import BC_REGISTRY, STAFF_ROLE, COLIN_ROLE
from doc_api.utils.logging import logger

from tests.unit.services.utils import create_header_upload, create_header_account_upload, \
  create_header, create_header_account


TEST_DATAFILE = 'tests/unit/services/unit_test.pdf'
MOCK_AUTH_URL = 'https://bcregistry-bcregistry-mock.apigee.net/mockTarget/auth/api/v1/'
STAFF_ROLES = [STAFF_ROLE, BC_REGISTRY]
INVALID_ROLES = [COLIN_ROLE]
DOC_CLASS1 = DocumentClasses.NR.value
DOC_TYPE1 = DocumentTypes.NR_MISC.value
MEDIA_PDF = model_utils.CONTENT_TYPE_PDF
PARAMS1 = '?consumerIdentifier=UTBUS&consumerFilename=test.pdf&consumerFilingDate=2024-07-25&consumerScanDate=2024-05-01'
PATH: str = '/api/v1/nro/{doc_type}' + PARAMS1
PARAM_CONSUMER_ID = '?consumerIdentifier=UTBUS'
PARAM_CONSUMER_ID_NONE = '?consumerIdentifier=XXXXXXX'
PARAM_DOC_SERVICE_ID = '?documentServiceId=?'
PARAM_CONSUMER_DOC_ID = '?consumerDocumentId=?'
GET_PATH = '/api/v1/nro'

# testdata pattern is ({description}, {content_type}, {roles}, {account}, {doc_class}, {doc_type}, {status})
TEST_CREATE_DATA = [
    ('Invalid doc type', MEDIA_PDF, STAFF_ROLES, 'UT1234', DOC_CLASS1, 'JUNK', HTTPStatus.BAD_REQUEST),
    ('Invalid content type', 'XXXXX', STAFF_ROLES, 'UT1234', DOC_CLASS1, DOC_TYPE1, HTTPStatus.BAD_REQUEST),
    ('Staff missing account', MEDIA_PDF, STAFF_ROLES, None, DOC_CLASS1, DOC_TYPE1, HTTPStatus.BAD_REQUEST),
    ('Invalid role', MEDIA_PDF, INVALID_ROLES, 'UT1234', DOC_CLASS1, DOC_TYPE1, HTTPStatus.UNAUTHORIZED),
    ('Valid staff', MEDIA_PDF, STAFF_ROLES, 'UT1234', DOC_CLASS1, DOC_TYPE1, HTTPStatus.CREATED)
]
# testdata pattern is ({description}, {params}, {roles}, {account}, {doc_class}, {status})
TEST_GET_DATA = [
    ('Invalid no params', None, STAFF_ROLES, 'UT1234', DOC_CLASS1, HTTPStatus.BAD_REQUEST),
    ('Staff missing account', PARAM_CONSUMER_ID, STAFF_ROLES, None, DOC_CLASS1, HTTPStatus.BAD_REQUEST),
    ('Invalid role', PARAM_CONSUMER_ID, INVALID_ROLES, 'UT1234', DOC_CLASS1, HTTPStatus.UNAUTHORIZED),
    ('Valid no results', PARAM_CONSUMER_ID_NONE, STAFF_ROLES, 'UT1234', DOC_CLASS1, HTTPStatus.NOT_FOUND),
    ('Valid consumer id', PARAM_CONSUMER_ID, STAFF_ROLES, 'UT1234', DOC_CLASS1, HTTPStatus.OK)
]


@pytest.mark.parametrize('desc,params,roles,account,doc_class,status', TEST_GET_DATA)
def test_get(session, client, jwt, desc, params, roles, account, doc_class, status):
    """Assert that a get NR documents request works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account:
        headers = create_header_account(jwt, roles, 'UT-TEST', account)
    else:
        headers = create_header(jwt, roles)
    req_path = GET_PATH
    if params:
        req_path += params

    if status == HTTPStatus.OK:  # Create.
        raw_data = None
        with open(TEST_DATAFILE, 'rb') as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post('/api/v1/nro/NR_MISC' + PARAMS1,
                               data=raw_data,
                               headers=headers,
                               content_type=MEDIA_PDF)
        # logger.info(response.json)
    # test
    response = client.get(req_path, headers=headers)

    # check
    # logger.info(response.json)
    assert response.status_code == status
    if response.status_code == HTTPStatus.OK:
        results_json = response.json
        assert results_json
        for doc_json in results_json:
            assert doc_json
            assert doc_json.get('documentServiceId')
            assert doc_json.get('documentURL')
            assert doc_json.get('documentClass') == doc_class


@pytest.mark.parametrize('desc,content_type,roles,account,doc_class,doc_type,status', TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, content_type, roles, account, doc_class, doc_type, status):
    """Assert that a post save new NR document works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    json_data = {}
    if account:
        headers = create_header_account_upload(jwt, roles, 'UT-TEST', account, content_type)
    else:
        headers = create_header_upload(jwt, roles, content_type)
    req_path = PATH.format(doc_type=doc_type)
    # test
    if status != HTTPStatus.CREATED:
        response = client.post(req_path,
                               json=json_data,
                               headers=headers,
                               content_type=content_type)
    else:
        raw_data = None
        with open(TEST_DATAFILE, 'rb') as data_file:
            raw_data = data_file.read()
            data_file.close()
        response = client.post(req_path,
                               data=raw_data,
                               headers=headers,
                               content_type=content_type)
        logger.info(response.json)
    
    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        doc_json = response.json
        assert doc_json
        assert doc_json.get('documentServiceId')
        assert doc_json.get('documentURL')
        doc: Document = Document.find_by_doc_service_id(doc_json.get('documentServiceId'))
        assert doc
        assert doc.document_type == doc_type
