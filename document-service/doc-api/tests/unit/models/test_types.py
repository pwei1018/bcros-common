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
from doc_api.models.type_tables import DocumentClasses, DocumentTypes, RequestTypes

# from doc_api.utils.logging import logger


# testdata pattern is ({doc_type}, {doc_class}, {exists})
TEST_DOC_TYPES = [
    ("XXX", None, False),
    (DocumentTypes.CORP_MISC.value, DocumentClasses.CORP.value, True),
    (DocumentTypes.SOC_MISC.value, DocumentClasses.SOCIETY.value, True),
    (DocumentTypes.NR_MISC.value, DocumentClasses.NR.value, True),
    (DocumentTypes.PPR_MISC.value, DocumentClasses.PPR.value, True),
    (DocumentTypes.REG_101.value, DocumentClasses.MHR.value, True),
    (DocumentTypes.FIRM_MISC.value, DocumentClasses.FIRM.value, True),
    (DocumentTypes.ADMN.value, DocumentClasses.OTHER.value, True),
    (DocumentTypes.DELETED.value, DocumentClasses.DELETED.value, False),
    (DocumentTypes.COOP_MEMORANDUM.value, DocumentClasses.COOP.value, True),
    (DocumentTypes.CORP_AFFIDAVIT.value, DocumentClasses.CORP.value, True),
]
# testdata pattern is ({doc_class}, {doc_type}, {has_results}, {type_exists})
TEST_DOC_TYPE_CLASSES = [
    ("XXX", "XXX", False, False),
    (DocumentClasses.CORP.value, DocumentTypes.ADDR.value, True, True),
    (DocumentClasses.CORP.value, DocumentTypes.RPL.value, True, False),
    (DocumentClasses.SOCIETY.value, DocumentTypes.AMAL.value, True, True),
    (DocumentClasses.NR.value, DocumentTypes.CORR.value, True, True),
    (DocumentClasses.PPR.value, DocumentTypes.PPR_MISC.value, True, True),
    (DocumentClasses.MHR.value, DocumentTypes.REG_101.value, True, True),
    (DocumentClasses.MHR.value, DocumentTypes.AMAL.value, True, False),
    (DocumentClasses.FIRM.value, DocumentTypes.CORR.value, True, True),
    (DocumentClasses.FIRM.value, DocumentTypes.TRAN.value, True, False),
    (DocumentClasses.OTHER.value, DocumentTypes.LTR.value, True, False),
    (DocumentClasses.OTHER.value, DocumentTypes.ADMN.value, True, True),
    (DocumentClasses.DELETED.value, DocumentTypes.DELETED.value, False, False),
    (DocumentClasses.COOP.value, DocumentTypes.COOP_RULES.value, True, True),
    (DocumentClasses.CORP.value, DocumentTypes.DIRECTOR_AFFIDAVIT.value, True, True),
]
# testdata pattern is ({doc_class}, {exists})
TEST_DOC_CLASSES = [
    ("XXX", False),
    (DocumentClasses.CORP.value, True),
    (DocumentClasses.SOCIETY.value, True),
    (DocumentClasses.NR.value, True),
    (DocumentClasses.PPR.value, True),
    (DocumentClasses.MHR.value, True),
    (DocumentClasses.FIRM.value, True),
    (DocumentClasses.OTHER.value, True),
    (DocumentClasses.DELETED.value, False)
]
# testdata pattern is ({doc_class}, {type_count})
TEST_DOC_TYPE_CLASSES_ALL = [
    ("XP", 0),
    ("COOP", 5),
    ("CORP", 5),
    ("FIRM", 5),
    ("LP_LLP", 5),
    ("MHR", 5),
    ("NR", 3),
    ("OTHER", 5),
    ("PPR", 5),
    ("SOCIETY", 5),
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


def test_document_class_findall_scanning(session):
    """Assert that the DocumentClass.find_all_scanning() and DocumentClass.scanning_json work as expected."""
    results = type_tables.DocumentClass.find_all_scanning()
    assert results
    assert len(results) >= 7
    for result in results:
        class_json = result.scanning_json
        assert class_json.get("ownerType")
        assert class_json.get("documentClass")
        assert class_json.get("documentClassDescription")
        assert "active" in class_json
        assert "scheduleNumber" in class_json


def test_document_type_findall(session):
    """Assert that the DocumentType.find_all() works as expected."""
    results = type_tables.DocumentType.find_all()
    assert results
    assert len(results) >= 90
    for result in results:
        assert result.document_type
        assert result.document_type in DocumentTypes
        assert result.document_type_desc
        assert result.product


def test_document_type_findall_scanning(session):
    """Assert that the DocumentType.find_all_scanning() and DocumentType.scanning_json work as expected."""
    results = type_tables.DocumentType.find_all()
    assert results
    assert len(results) >= 90
    for result in results:
        type_json = result.scanning_json
        assert type_json.get("documentType")
        assert type_json.get("documentTypeDescription")
        assert "active" in type_json
        assert type_json.get("applicationId")


@pytest.mark.parametrize("doc_type, doc_class, exists", TEST_DOC_TYPES)
def test_document_type_finddoctype(session, doc_type, doc_class, exists):
    """Assert that the DocumentType.find_by_doc_type() works as expected."""
    result = type_tables.DocumentType.find_by_doc_type(doc_type)
    if exists:
        assert result
        assert result.document_type
        assert result.document_type == doc_type
        assert result.document_type_desc
        assert result.product
        assert result.doc_type_class
        if doc_class:
            found: bool = False
            for type_class in result.doc_type_class:
                if type_class.document_class == doc_class:
                    found = True
                    break
            assert found
    else:
        assert not result


@pytest.mark.parametrize("doc_class, doc_type, has_results, type_exists", TEST_DOC_TYPE_CLASSES)
def test_document_type_class_classes(session, doc_class, doc_type, has_results, type_exists):
    """Assert that the DocumentTypeClass.find_by_doc_class() works as expected."""
    results = type_tables.DocumentTypeClass.find_by_doc_class(doc_class)
    if has_results:
        assert results
        exists = False
        for result in results:
            assert result.document_class == doc_class
            assert result.document_type
            if result.document_type == doc_type:
                exists = True
                break
            assert result.active
        assert exists == type_exists
    else:
        assert not results


@pytest.mark.parametrize("doc_class, exists", TEST_DOC_CLASSES)
def test_document_class_finddocclass(session, doc_class, exists):
    """Assert that the DocumentClass.find_by_doc_class() works as expected."""
    result = type_tables.DocumentClass.find_by_doc_class(doc_class)
    if exists:
        assert result
        assert result.document_class == doc_class
        assert result.document_class_desc
    else:
        assert not result


@pytest.mark.parametrize("doc_class, doc_type, has_results, type_exists", TEST_DOC_TYPE_CLASSES)
def test_document_type_class_types(session, doc_class, doc_type, has_results, type_exists):
    """Assert that the DocumentTypeClass.find_by_doc_type() works as expected."""
    results = type_tables.DocumentTypeClass.find_by_doc_type(doc_type)
    if has_results:
        assert results
        exists = False
        for result in results:
            assert result.document_type
            assert result.document_type == doc_type
            if result.document_class == doc_class:
                exists = True
                break
            assert result.active
        assert exists == type_exists
    else:
        assert not results


@pytest.mark.parametrize("doc_class, type_count", TEST_DOC_TYPE_CLASSES_ALL)
def test_document_type_class_all(session, doc_class, type_count):
    """Assert that the DocumentTypeClass.find_all() and find_all_json() works as expected."""
    results = type_tables.DocumentTypeClass.find_all_json()
    assert results
    if type_count > 0:
        assert results.get(doc_class)
        assert len(results.get(doc_class)) >= type_count
        for type_json in results.get(doc_class):
            assert type_json.get("documentType")
            assert type_json.get("documentTypeDescription")
    else:
        assert not results.get(doc_class)
