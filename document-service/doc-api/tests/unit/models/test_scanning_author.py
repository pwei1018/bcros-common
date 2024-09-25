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

from doc_api.models import ScanningAuthor

AUTHOR1 = {
    "firstName": "Bob",
    "lastName": "Smith",
    "jobTitle": "Analyst",
    "email": "bsmith-12@gmail.com",
    "phoneNumber": "250 721-1234",
}
TEST_AUTHOR = ScanningAuthor(
    id=1,
    first_name="Bob",
    last_name="Smith",
    job_title="Analyst",
    email="bsmith-12@gmail.com",
    phone_number="250 721-1234",
)

# testdata pattern is ({id}, {has_results})
TEST_ID_DATA = [
    (200000001, True),
    (300000000, False),
]


@pytest.mark.parametrize("author_id, has_results", TEST_ID_DATA)
def test_find_by_id(session, author_id, has_results):
    """Assert that find a scanning author by primary key contains all expected elements."""
    if not has_results:
        author: ScanningAuthor = ScanningAuthor.find_by_id(author_id)
        assert not author
    else:
        save_author: ScanningAuthor = ScanningAuthor.create_from_json(AUTHOR1)
        save_author.id = author_id
        save_author.save()
        author: ScanningAuthor = ScanningAuthor.find_by_id(author_id)
        assert author
        assert author.id == author_id


def test_find_all(session):
    """Assert that find all authors expected elements."""
    results = ScanningAuthor.find_all()
    if results:
        for author in results:
            assert author.id
            assert author.first_name
            assert author.last_name


def test_author_json(session):
    """Assert that the scanning author model renders to a json format correctly."""
    author: ScanningAuthor = TEST_AUTHOR
    author_json = author.json
    test_json = copy.deepcopy(AUTHOR1)
    assert author_json == test_json


def test_create_from_json(session):
    """Assert that the new scanning author record is created from a new request json data correctly."""
    json_data = copy.deepcopy(AUTHOR1)
    author: ScanningAuthor = ScanningAuthor.create_from_json(json_data)
    assert author
    assert not author.id
    assert author.first_name == json_data.get("firstName")
    assert author.last_name == json_data.get("lastName")
    assert author.job_title == json_data.get("jobTitle")
    assert author.email == json_data.get("email")
    assert author.phone_number == json_data.get("phoneNumber")
