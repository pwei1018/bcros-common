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
"""Test Suite to ensure the model utility functions are working as expected."""

import pytest

from doc_api.models import utils as model_utils, Document
from doc_api.models.type_tables import DocumentTypes, DocumentClasses
from doc_api.utils.logging import logger


# testdata pattern is ({test_ts}, {expected_ts})
TEST_DATA_DATE_NOON = [
    ('2024-06-01T08:00:00', '2024-06-01T19:00:00+00:00'),
    ('2024-09-01T21:00:00', '2024-09-01T19:00:00+00:00'),
    ('2024-12-01T21:00:00', '2024-12-01T20:00:00+00:00'),
    ('2024-09-01T21:00:00-07:00', '2024-09-01T19:00:00+00:00'),
    ('2024-12-01T21:00:00-08:00', '2024-12-01T20:00:00+00:00'),
    ('2024-08-01', '2024-08-01T19:00:00+00:00'),
    ('2024-12-01', '2024-12-01T20:00:00+00:00')
]
# testdata pattern is ({test_ts}, {expected_ts})
TEST_DATA_DATE_START = [
    ('2024-06-01T08:00:00', '2024-06-01T07:00:00+00:00'),
    ('2024-09-01T21:00:00', '2024-09-01T07:00:00+00:00'),
    ('2024-12-01T21:00:00', '2024-12-01T08:00:00+00:00'),
    ('2024-09-01T21:00:00-07:00', '2024-09-01T07:00:00+00:00'),
    ('2024-12-01T21:00:00-08:00', '2024-12-01T08:00:00+00:00'),
    ('2024-08-01', '2024-08-01T07:00:00+00:00'),
    ('2024-12-01', '2024-12-01T08:00:00+00:00')
]
# testdata pattern is ({test_ts}, {expected_ts})
TEST_DATA_DATE_END = [
    ('2024-06-01T08:00:00', '2024-06-02T06:59:59+00:00'),
    ('2024-09-01T21:00:00', '2024-09-02T06:59:59+00:00'),
    ('2024-12-01T21:00:00', '2024-12-02T07:59:59+00:00'),
    ('2024-09-01T21:00:00-07:00', '2024-09-02T06:59:59+00:00'),
    ('2024-12-01T21:00:00-08:00', '2024-12-02T07:59:59+00:00'),
    ('2024-08-01', '2024-08-02T06:59:59+00:00'),
    ('2024-12-01', '2024-12-02T07:59:59+00:00')
]
# testdata pattern is ({doc_ts}, {doc_type}, {doc_service_id}, {content_type}, {name})
TEST_DATA_STORAGE_NAME = [
    ('2024-09-01T19:00:00+00:00', DocumentTypes.CORP_MISC.value, 'UT01111', model_utils.CONTENT_TYPE_PDF,
     '2024/09/01/corp_misc-UT01111.pdf'),
    ('2024-12-01T19:00:00+00:00', DocumentTypes.SOC_MISC.value, 'UT01111', model_utils.CONTENT_TYPE_ZIP,
     '2024/12/01/soc_misc-UT01111.zip')
]
# testdata pattern is ({doc_class}, {start_offset}, {doc_type}, {cons_id}, {no_results})
TEST_DATA_DOC_DATES = [
    (None, 10, None, None, True),
    (DocumentClasses.CORP, 10, None, None, False),
    (DocumentClasses.CORP, 1, DocumentTypes.MHR_MISC, None, True),
    (DocumentClasses.CORP.value, 10, DocumentTypes.CORP_MISC.value, None, False),
    (DocumentClasses.CORP.value, 5, None, 'XXXXXXX4', True),
    (DocumentClasses.CORP.value, 10, None, 'UT000004', False),
    (DocumentClasses.CORP.value, 10, DocumentTypes.CORP_MISC.value, 'UT000004', False)
]


@pytest.mark.parametrize('doc_class,start_offset,doc_type,cons_id,no_results', TEST_DATA_DOC_DATES)
def test_get_docs_by_dates(session, doc_class, start_offset, doc_type, cons_id, no_results):
    """Assert that get_docs_by_date_range works as expected."""
    end = model_utils.now_ts()
    start = model_utils.date_offset(end.date(), start_offset)
    results = model_utils.get_docs_by_date_range(doc_class, start.isoformat(), end.isoformat(), doc_type, cons_id)
    if no_results:
        assert not results
    elif results:
        for result in results:
            assert result.get('documentServiceId')
            assert result.get('createDateTime')
            assert result.get('documentType')
            assert result.get('documentTypeDescription')
            assert result.get('documentClass')
            assert 'documentURL' not in result


@pytest.mark.parametrize('doc_ts,doc_type,doc_service_id,content_type,name', TEST_DATA_STORAGE_NAME)
def test_doc_storage_name(session, doc_ts, doc_type, doc_service_id, content_type, name):
    """Assert that building a doc storage file name works as expected."""
    doc: Document = Document(add_ts=model_utils.ts_from_iso_format(doc_ts),
                             document_type=doc_type,
                             document_service_id=doc_service_id)
    storage_name = model_utils.get_doc_storage_name(doc, content_type)
    assert storage_name == name


@pytest.mark.parametrize('test_ts,expected_ts', TEST_DATA_DATE_NOON)
def test_ts_from_iso_format_noon(session, test_ts, expected_ts):
    """Assert that converting an ISO date/timestamp to 12 PM local time zone works as expected."""
    save_ts = model_utils.ts_from_iso_date_noon(test_ts)
    formatted_ts = model_utils.format_ts(save_ts)
    logger.info(f'In={save_ts} out={formatted_ts}')
    assert formatted_ts == expected_ts


@pytest.mark.parametrize('test_ts,expected_ts', TEST_DATA_DATE_START)
def test_ts_from_iso_format_start(session, test_ts, expected_ts):
    """Assert that converting an ISO date/timestamp to 00:00:00 PM local time zone works as expected."""
    save_ts = model_utils.ts_from_iso_date_start(test_ts)
    formatted_ts = model_utils.format_ts(save_ts)
    logger.info(f'In={save_ts} out={formatted_ts}')
    assert formatted_ts == expected_ts


@pytest.mark.parametrize('test_ts,expected_ts', TEST_DATA_DATE_END)
def test_ts_from_iso_format_end(session, test_ts, expected_ts):
    """Assert that converting an ISO date/timestamp to 23:59:59 local time zone works as expected."""
    save_ts = model_utils.ts_from_iso_date_end(test_ts)
    formatted_ts = model_utils.format_ts(save_ts)
    logger.info(f'In={save_ts} out={formatted_ts}')
    assert formatted_ts == expected_ts
