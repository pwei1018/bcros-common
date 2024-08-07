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
"""Google storage service tests."""
import pytest

from doc_api.services.abstract_storage_service import DocumentTypes
from doc_api.services.document_storage.storage_service import GoogleStorageService
from doc_api.utils.logging import logger


TEST_GET_NAME = 'unit_test/unit_test.pdf'  # Never delete
TEST_DATAFILE = 'tests/unit/services/unit_test.pdf'
TEST_SAVE_NAME = 'unit_test/2022/05/06/unit_test.pdf'
MEDIA_PDF = 'application/pdf'

# testdata pattern is ({filename}, {doc_type}, {is_link})
TEST_DATA_GET = [
    (TEST_GET_NAME, DocumentTypes.BUSINESS, False),
    (TEST_GET_NAME, DocumentTypes.BUSINESS, True),
    (TEST_GET_NAME, DocumentTypes.MHR, True),
    (TEST_GET_NAME, DocumentTypes.PPR, True),
    (TEST_GET_NAME, DocumentTypes.NR, True)
]
# testdata pattern is ({file}, {filename}, {doc_type}, {is_link}, {content_type}, {delete})
TEST_DATA_SAVE = [
    (TEST_DATAFILE, TEST_SAVE_NAME, DocumentTypes.BUSINESS, False, MEDIA_PDF, True),
    (TEST_DATAFILE, TEST_SAVE_NAME, DocumentTypes.BUSINESS, True, MEDIA_PDF, False),
    (TEST_DATAFILE, TEST_SAVE_NAME, DocumentTypes.MHR, True, MEDIA_PDF, True),
    (TEST_DATAFILE, TEST_SAVE_NAME, DocumentTypes.NR, True, MEDIA_PDF, True),
    (TEST_DATAFILE, TEST_SAVE_NAME, DocumentTypes.PPR, True, MEDIA_PDF, False)
]


@pytest.mark.parametrize('name, doc_type, is_link', TEST_DATA_GET)
def test_get_document(session, name, doc_type, is_link):
    """Assert that getting a document from google cloud storage works as expected."""
    if is_link:
        download_link = GoogleStorageService.get_document_link(name, doc_type, 2)
        logger.info(f'Get doc link={download_link}')
        assert download_link
    else:
        raw_data = GoogleStorageService.get_document(name, doc_type)
        assert raw_data
        assert len(raw_data) > 0
        logger.info(f'Get doc file size={len(raw_data)}')


@pytest.mark.parametrize('file, name, doc_type, is_link, content_type, delete', TEST_DATA_SAVE)
def test_save_delete_document(session, file, name, doc_type, is_link, content_type, delete):
    """Assert that saving then deleting a document from google cloud storage works as expected."""
    raw_data = None
    with open(file, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    if is_link:
        response = GoogleStorageService.save_document_link(name, raw_data, doc_type, 2, content_type)
        logger.info(response)
        assert response
    else:
        response = GoogleStorageService.save_document(name, raw_data, doc_type, content_type)
        assert response
    if delete:
        response = GoogleStorageService.delete_document(name, doc_type)
        assert not response
    else:
        download_link = GoogleStorageService.get_document_link(name, doc_type, 2)
        assert download_link
