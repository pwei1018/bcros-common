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

"""Tests to assure the scanning_parameter Model.

Test-Suite to ensure that the scanning_parameter Model is working as expected.
"""
import copy

import pytest

from doc_api.models import ScanningParameter


PARAMETERS = {
    "useDocumentFeeder": True,
    "showTwainUi": True,
    "showTwainProgress": True,
    "useFullDuplex": True,
    "useLowResolution": True,
    "maxPagesInBox": 1000,
}
UPDATE_PARAMETERS = {
    "useDocumentFeeder": False,
    "showTwainUi": False,
    "showTwainProgress": False,
    "useFullDuplex": False,
    "useLowResolution": False,
    "maxPagesInBox": 10,
}
TEST_PARAMETERS = ScanningParameter(
    id=1,
    use_document_feeder=True,
    show_twain_ui=True,
    show_twain_progress=True,
    use_full_duplex=True,
    use_low_resolution=True,
    max_pages_in_box=1000,
)

# testdata pattern is ({id}, {has_results})
TEST_ID_DATA = [
    (200000001, True),
    (300000000, False),
]


@pytest.mark.parametrize("params_id, has_results", TEST_ID_DATA)
def test_find_by_id(session, params_id, has_results):
    """Assert that find a scanning schedule by primary key contains all expected elements."""
    if not has_results:
        parameters: ScanningParameter = ScanningParameter.find_by_id(params_id)
        assert not parameters
    else:
        save_parameters: ScanningParameter = ScanningParameter.create_from_json(PARAMETERS)
        save_parameters.id = params_id
        save_parameters.save()
        parameters: ScanningParameter = ScanningParameter.find_by_id(params_id)
        assert parameters
        assert parameters.id == params_id
        assert parameters.use_document_feeder
        assert parameters.show_twain_ui
        assert parameters.show_twain_progress
        assert parameters.use_full_duplex
        assert parameters.use_low_resolution
        assert parameters.max_pages_in_box > 0


def test_find(session):
    """Assert that find all parameterss expected elements."""
    save_parameters: ScanningParameter = ScanningParameter.create_from_json(PARAMETERS)
    save_parameters.id = 200000001
    save_parameters.save()
    parameters: ScanningParameter = ScanningParameter.find()
    assert parameters
    assert parameters.id
    assert parameters.use_document_feeder
    assert parameters.show_twain_ui
    assert parameters.show_twain_progress
    assert parameters.use_full_duplex
    assert parameters.use_low_resolution
    assert parameters.max_pages_in_box > 0


def test_parameters_json(session):
    """Assert that the scanning parameters model renders to a json format correctly."""
    parameters: ScanningParameter = TEST_PARAMETERS
    params_json = parameters.json
    test_json = copy.deepcopy(PARAMETERS)
    assert params_json == test_json


def test_create_from_json(session):
    """Assert that the new scanning parameters record is created from a new request json data correctly."""
    json_data = copy.deepcopy(PARAMETERS)
    parameters: ScanningParameter = ScanningParameter.create_from_json(json_data)
    assert parameters
    assert not parameters.id
    assert parameters.use_document_feeder == json_data.get("useDocumentFeeder")
    assert parameters.show_twain_ui == json_data.get("showTwainUi")
    assert parameters.show_twain_progress == json_data.get("showTwainProgress")
    assert parameters.use_full_duplex == json_data.get("useFullDuplex")
    assert parameters.use_low_resolution == json_data.get("useLowResolution")
    assert parameters.max_pages_in_box == json_data.get("maxPagesInBox")


def test_update(session):
    """Assert that updating a scanning parameters object works as expected."""
    parameters: ScanningParameter = ScanningParameter.create_from_json(PARAMETERS)
    json_data = copy.deepcopy(UPDATE_PARAMETERS)
    parameters.update(json_data)
    assert parameters.use_document_feeder == json_data.get("useDocumentFeeder")
    assert parameters.show_twain_ui == json_data.get("showTwainUi")
    assert parameters.show_twain_progress == json_data.get("showTwainProgress")
    assert parameters.use_full_duplex == json_data.get("useFullDuplex")
    assert parameters.use_low_resolution == json_data.get("useLowResolution")
    assert parameters.max_pages_in_box == json_data.get("maxPagesInBox")
