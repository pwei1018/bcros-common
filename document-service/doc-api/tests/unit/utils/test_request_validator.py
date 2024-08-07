# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Registration non-party validator tests."""
import copy

from flask import current_app
import pytest
# from registry_schemas import utils as schema_utils

from doc_api.utils import request_validator as validator
from doc_api.utils.logging import logger
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentTypes, RequestTypes, DocumentClasses
from doc_api.resources.request_info import RequestInfo


# test data pattern is ({description}, {valid}, {req_type}, {doc_type}, {content_type}, {doc_class}, {message_content})
TEST_DATA_ADD = [
    ('Valid', True, RequestTypes.ADD, DocumentTypes.CORP_MISC, model_utils.CONTENT_TYPE_PDF, DocumentClasses.CORP, None),
    ('Invalid missing doc type', False, RequestTypes.ADD, None, model_utils.CONTENT_TYPE_PDF, DocumentClasses.CORP,
     validator.MISSING_DOC_TYPE),
    ('Invalid doc type', False, RequestTypes.ADD, 'JUNK', model_utils.CONTENT_TYPE_PDF, DocumentClasses.CORP,
     validator.INVALID_DOC_TYPE),
    ('Invalid doc class', False, RequestTypes.ADD, DocumentTypes.CORP_MISC, model_utils.CONTENT_TYPE_PDF, 'JUNK',
     validator.INVALID_DOC_CLASS),
    ('Invalid missing content', False, RequestTypes.ADD, DocumentTypes.CORP_MISC, None, DocumentClasses.CORP,
      validator.MISSING_CONTENT_TYPE),
    ('Invalid content', False, RequestTypes.ADD, DocumentTypes.CORP_MISC, 'XXXXX', DocumentClasses.CORP,
     validator.INVALID_CONTENT_TYPE)
]
# test data pattern is ({description}, {valid}, {doc_class}, {doc_service_id}, {doc_id}, {cons_id}, {start}, {end}, {message_content})
TEST_DATA_GET = [
    ('Valid service id', True, DocumentClasses.CORP, '1234', None, None, None, None, None),
    ('Valid doc id', True, DocumentClasses.CORP, None, '1234', None, None, None, None),
    ('Valid consumer id', True, DocumentClasses.CORP, None, None, '1234', None, None, None),
    ('Valid query dates', True, DocumentClasses.CORP, None, None, None, '2024-07-01', '2024-07-05', None),
    ('Invalid doc class', False, 'XXXX', None, None, None, '2024-07-01', '2024-07-05', validator.INVALID_DOC_CLASS),
    ('Missing doc class', False, None, '1234', None, None, None, None, validator.MISSING_DOC_CLASS),
    ('Missing params', False, DocumentClasses.CORP, None, None, None, None, None, validator.MISSING_QUERY_PARAMS),
    ('Invalid query dates', False, DocumentClasses.CORP, None, None, None, '2024-07-01', None,
     validator.INVALID_DATE_PARAMS),
    ('Invalid query dates', False, DocumentClasses.CORP, None, None, None, None, '2024-07-01',
     validator.INVALID_DATE_PARAMS)
]


@pytest.mark.parametrize('desc,valid,doc_class,service_id,doc_id,cons_id,start,end,message_content', TEST_DATA_GET)
def test_validate_get(session, desc, valid, doc_class, service_id, doc_id, cons_id, start, end, message_content):
    """Assert that get documents request validation works as expected."""
    # setup
    info: RequestInfo = RequestInfo(RequestTypes.GET.value, 'NA', 'NA', 'NA')
    info.account_id = 'NA'
    if doc_class:
        info.document_class = doc_class
    if service_id:
        info.document_service_id = service_id
    if doc_id:
        info.consumer_doc_id = doc_id
    if cons_id:
        info.consumer_identifier = cons_id
    if start:
        info.query_start_date = start
    if end:
        info.query_end_date = end
    
    error_msg = validator.validate_request(info)
    if valid:
        assert error_msg == ''
    else:
        assert error_msg != ''
        if message_content:
            err_msg:str = message_content
            if desc == 'Invalid doc class':
                err_msg = validator.INVALID_DOC_CLASS.format(doc_class=doc_class)
            assert error_msg.find(err_msg) != -1


@pytest.mark.parametrize('desc,valid,req_type,doc_type,content_type,doc_class,message_content', TEST_DATA_ADD)
def test_validate_add(session, desc, valid, req_type, doc_type, content_type, doc_class, message_content):
    """Assert that new add request validation works as expected."""
    # setup
    info: RequestInfo = RequestInfo(req_type, 'NA', doc_type, 'NA')
    info.content_type = content_type
    info.account_id = 'NA'
    if doc_class:
        info.document_class = doc_class
    error_msg = validator.validate_request(info)
    if valid:
        assert error_msg == ''
    else:
        assert error_msg != ''
        if message_content:
            err_msg:str = message_content
            if desc == 'Invalid doc type':
                err_msg = validator.INVALID_DOC_TYPE.format(doc_type=doc_type)
            elif desc == 'Invalid doc class':
                err_msg = validator.INVALID_DOC_CLASS.format(doc_class=doc_class)
            elif desc == 'Invalid content':
                err_msg = validator.INVALID_CONTENT_TYPE.format(content_type=content_type)
            assert error_msg.find(err_msg) != -1
