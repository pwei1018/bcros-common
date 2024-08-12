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

"""Tests to assure the MHR Type Table Models.

Test-Suite to ensure that the MHR Type Table Models are working as expected.
"""
import pytest

from doc_api.models import type_tables
from doc_api.models.type_tables import RequestTypes, DocumentClasses, DocumentTypes
# from doc_api.utils.logging import logger


# testdata pattern is ({doc_type}, {doc_class}, {exists})
TEST_DOC_TYPES = [
    ('XXX', None, False),
    (DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, True),
    (DocumentTypes.SOC_MISC.value, DocumentClasses.SOCIETY.value, True),
    (DocumentTypes.NR_MISC.value, DocumentClasses.NR.value, True),
    (DocumentTypes.PPR_MISC.value, DocumentClasses.PPR.value, True),
    (DocumentTypes.REG_101.value, DocumentClasses.MHR.value, True),
    (DocumentTypes.FIRM_MISC.value, DocumentClasses.FIRM.value, True),
    (DocumentTypes.LTR.value, DocumentClasses.OTHER.value, True)
]
# testdata pattern is ({doc_class}, {doc_type}, {has_results}, {type_exists})
TEST_DOC_TYPE_CLASSES = [
    ('XXX', None, False, False),
    (DocumentClasses.CORP.value, DocumentTypes.CORP_MISC.value, True, True),
    (DocumentClasses.SOCIETY.value, DocumentTypes.SOC_MISC.value, True, True),
    (DocumentClasses.NR.value, DocumentTypes.NR_MISC.value, True, True),
    (DocumentClasses.PPR.value, DocumentTypes.PPR_MISC.value, True, True),
    (DocumentClasses.MHR.value, DocumentTypes.REG_101.value, True, True),
    (DocumentClasses.FIRM.value, DocumentTypes.FIRM_MISC.value, True, True),
    (DocumentClasses.OTHER.value, DocumentTypes.LTR.value, True, True),
    (DocumentClasses.OTHER.value, DocumentTypes.PPR_MISC.value, True, False)
]
# testdata pattern is ({doc_class}, {exists})
TEST_DOC_CLASSES = [
    ('XXX', False),
    (DocumentClasses.CORP.value, True),
    (DocumentClasses.SOCIETY.value, True),
    (DocumentClasses.NR.value, True),
    (DocumentClasses.PPR.value, True),
    (DocumentClasses.MHR.value, True),
    (DocumentClasses.FIRM.value, True),
    (DocumentClasses.OTHER.value, True)
]


def test_request_type_findall(session):
    """Assert that the RequestType.find_all() works as expected."""
    results = type_tables.RequestType.find_all()
    assert results
    assert len(results) >= 5
    for result in results:
        assert result.request_type
        assert result.request_type in RequestTypes
        assert result.request_type_desc


def test_document_class_findall(session):
    """Assert that the DocumentClass.find_all() works as expected."""
    results = type_tables.DocumentClass.find_all()
    assert results
    assert len(results) >= 7
    for result in results:
        assert result.document_class
        assert result.document_class in DocumentClasses
        assert result.document_class_desc


def test_document_type_findall(session):
    """Assert that the DocumentClass.find_all() works as expected."""
    results = type_tables.DocumentType.find_all()
    assert results
    assert len(results) >= 90
    for result in results:
        assert result.document_type
        assert result.document_type in DocumentTypes
        assert result.document_class
        assert result.document_class in DocumentClasses
        assert result.document_type_desc
        assert result.product


@pytest.mark.parametrize('doc_type, doc_class, exists', TEST_DOC_TYPES)
def test_document_type_finddoctype(session, doc_type, doc_class, exists):
    """Assert that the DocumentClass.find_by_doc_type() works as expected."""
    result = type_tables.DocumentType.find_by_doc_type(doc_type) 
    if exists:
        assert result
        assert result.document_type
        assert result.document_type == doc_type
        assert result.document_class
        assert result.document_class == doc_class
        assert result.document_type_desc
        assert result.product
        assert result.doc_class
        assert result.doc_class.document_class_desc
    else:
        assert not result


@pytest.mark.parametrize('doc_class, doc_type, has_results, type_exists', TEST_DOC_TYPE_CLASSES)
def test_document_type_finddocclass(session, doc_class, doc_type, has_results, type_exists):
    """Assert that the DocumentClass.find_by_doc_class() works as expected."""
    results = type_tables.DocumentType.find_by_doc_class(doc_class) 
    if has_results:
        assert results
        exists = False
        for result in results:
            assert result.document_type
            if result.document_type == doc_type:
                exists = True
            assert result.document_class
            assert result.document_class == doc_class
            assert result.document_type_desc
            assert result.product
        assert exists == type_exists
    else:
        assert not results


@pytest.mark.parametrize('doc_class, exists', TEST_DOC_CLASSES)
def test_document_class_finddocclass(session, doc_class, exists):
    """Assert that the DocumentClass.find_by_doc_class() works as expected."""
    result = type_tables.DocumentClass.find_by_doc_class(doc_class) 
    if exists:
        assert result
        assert result.document_class == doc_class
        assert result.document_class_desc
    else:
        assert not result
