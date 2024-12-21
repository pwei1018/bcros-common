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
"""Test Suite to ensure the model search utility functions are working as expected."""

import pytest

from doc_api.models import search_utils
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes
from doc_api.resources.request_info import RequestInfo

# from doc_api.utils.logging import logger


PAGE_CLAUSE: str = " ORDER BY d.add_ts DESC) as q LIMIT {page_size} OFFSET {page_offset}"
# testdata pattern is ({doc_class}, {start_offset}, {doc_type}, {cons_id}, {no_results})
TEST_DATA_DOC_DATES = [
    (None, 10, None, None, True),
    (DocumentClasses.CORP, 10, None, None, False),
    (DocumentClasses.CORP, 1, DocumentTypes.MHR_MISC, None, True),
    (DocumentClasses.CORP.value, 10, DocumentTypes.CORP_MISC.value, None, False),
    (DocumentClasses.CORP.value, 5, None, "XXXXXXX4", True),
    (DocumentClasses.CORP.value, 10, None, "UT000004", False),
    (DocumentClasses.CORP.value, 10, DocumentTypes.CORP_MISC.value, "UT000004", False),
]
# testdata pattern is ({page_num}, {expected_offset})
TEST_DATA_PAGE_SIZE = [
    (0, 0),
    (1, 0),
    (2, search_utils.SEARCH_PAGE_SIZE),
    (5, 4 * search_utils.SEARCH_PAGE_SIZE)
]
# testdata pattern is ({doc_class}, {doc_type}, {start_date}, {end_date}, {cons_id}, {doc_id}, {filename})
TEST_DATA_SEARCH_FILTER = [
    (None, None, None, None, None, None, None),
    ('PPR', None, None, None, None, None, None),
    ('PPR', 'PPRS', None, None, None, None, None),
    ('CORP', None, None, None, 'BC0700', None, None),
    ('CORP', None, None, None, None, '2143', None),
    ('SOCIETY', None, '2024-09-01', '2024-09-02', None, '2143', None),
    ('CORP', None, None, None, None, None, 'change of add')
]


@pytest.mark.parametrize("page_num,expected_offset", TEST_DATA_PAGE_SIZE)
def test_page_clause(session, page_num, expected_offset):
    """Assert that building the search query page size clause works as expected."""
    req_info: RequestInfo = RequestInfo(None, None, None, None)
    req_info.page_number = page_num
    test_clause = PAGE_CLAUSE.format(page_size=search_utils.SEARCH_PAGE_SIZE, page_offset=expected_offset)
    clause = search_utils.build_page_clause(req_info)
    assert clause == test_clause


@pytest.mark.parametrize("doc_class,doc_type,start_dt,end_dt,cons_id,doc_id,filename", TEST_DATA_SEARCH_FILTER)
def test_build_search_filter(session, doc_class, doc_type, start_dt, end_dt, cons_id, doc_id, filename):
    """Assert that building the search base query from search parameters works as expected."""
    req_info: RequestInfo = RequestInfo(None, None, doc_type, None)
    req_info.document_class = doc_class
    req_info.query_start_date = start_dt
    req_info.query_end_date = end_dt
    req_info.consumer_identifier = cons_id
    req_info.consumer_doc_id = doc_id
    req_info.consumer_filename = filename
    query: str = search_utils.build_filter_clause(req_info)
    if doc_class:
        assert query.find(' AND d.document_class = ') != -1
    else:
        assert query.find(' AND d.document_class = ') == -1
    if doc_type:
        assert query.find(' AND d.document_type = ') != -1
    else:
        assert query.find(' AND d.document_type = ') == -1
    if start_dt and end_dt:
        assert query.find(' AND d.add_ts BETWEEN TO_TIMESTAMP') != -1
    else:
        assert query.find(' AND d.add_ts BETWEEN TO_TIMESTAMP') == -1
    if cons_id:
        assert query.find(f" AND d.consumer_identifier LIKE '%{cons_id}%'") != -1
    else:
        assert query.find(' AND d.consumer_identifier LIKE ') == -1
    if doc_id:
        assert query.find(f" AND d.consumer_document_id LIKE '{doc_id}%'") != -1
    else:
        assert query.find(' AND d.consumer_document_id LIKE ') == -1
    if filename:
        assert query.find(f" AND LOWER(d.consumer_filename) LIKE '{filename}%'") != -1
    else:
        assert query.find(' AND LOWER(d.consumer_filename) LIKE ') == -1


@pytest.mark.parametrize("doc_class,doc_type,start_dt,end_dt,cons_id,doc_id,filename", TEST_DATA_SEARCH_FILTER)
def test_search_count(session, doc_class, doc_type, start_dt, end_dt, cons_id, doc_id, filename):
    """Assert that executing the search count query from search parameters works as expected."""
    req_info: RequestInfo = RequestInfo(None, None, doc_type, None)
    req_info.document_class = doc_class
    req_info.query_start_date = start_dt
    req_info.query_end_date = end_dt
    req_info.consumer_identifier = cons_id
    req_info.consumer_doc_id = doc_id
    req_info.consumer_filename = filename
    filter_clause: str = search_utils.build_filter_clause(req_info)
    search_count: int = search_utils.get_search_count(filter_clause)
    assert search_count >= 0


@pytest.mark.parametrize("doc_class,doc_type,start_dt,end_dt,cons_id,doc_id,filename", TEST_DATA_SEARCH_FILTER)
def test_search_docs(session, doc_class, doc_type, start_dt, end_dt, cons_id, doc_id, filename):
    """Assert that executing the search from search parameters works as expected."""
    req_info: RequestInfo = RequestInfo(None, None, doc_type, None)
    req_info.document_class = doc_class
    req_info.query_start_date = start_dt
    req_info.query_end_date = end_dt
    req_info.consumer_identifier = cons_id
    req_info.consumer_doc_id = doc_id
    req_info.consumer_filename = filename
    search_results = search_utils.get_search_docs(req_info)
    assert search_results
    assert 'resultCount' in search_results
    if search_results.get('resultCount') > 0:
        assert search_results.get('results')
        for result in search_results.get('results'):
            assert result.get('documentServiceId')
            assert result.get('createDateTime')
            assert result.get('documentType')
            assert result.get('documentClass')
            assert result.get('documentTypeDescription')
            assert 'consumerDocumentId' in result
            assert 'consumerIdentifier' in result
            assert 'consumerFilenames' in result
            assert 'description' in result


@pytest.mark.parametrize("doc_class,start_offset,doc_type,cons_id,no_results", TEST_DATA_DOC_DATES)
def test_get_docs_by_dates(session, doc_class, start_offset, doc_type, cons_id, no_results):
    """Assert that get_docs_by_date_range works as expected."""
    end = model_utils.now_ts()
    start = model_utils.date_offset(end.date(), start_offset)
    results = search_utils.get_docs_by_date_range(doc_class, start.isoformat(), end.isoformat(), doc_type, cons_id)
    if no_results:
        assert not results
    elif results:
        for result in results:
            assert result.get("documentServiceId")
            assert result.get("createDateTime")
            assert result.get("documentType")
            assert result.get("documentTypeDescription")
            assert result.get("documentClass")
            assert "documentURL" not in result
            assert 'description' in result
