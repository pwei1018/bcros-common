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

"""Tests to assure the scanning_box Model.

Test-Suite to ensure that the scanning_box Model is working as expected.
"""
import copy

import pytest

from doc_api.models import utils as model_utils, ScanningBox


BOX = {
    "boxId": 200000000,
    "boxNumber": 10,
    "sequenceNumber": 20,
    "scheduleNumber": 30,
    "openedDate": "2024-09-22",
    "closedDate": "2024-09-23",
    "pageCount": 1000,
}
UPDATE_BOX = {
    "boxId": 200000000,
    "boxNumber": 10,
    "sequenceNumber": 20,
    "scheduleNumber": 30,
    "openedDate": "2024-09-21",
    "closedDate": "2024-09-24",
    "pageCount": 1500,
}
TEST_BOX =  ScanningBox(
    id=200000000,
    box_number=10,
    sequence_number=20,
    schedule_number=30,
    opened_date=model_utils.ts_from_iso_date_noon("2024-09-22"),
    closed_date=model_utils.ts_from_iso_date_noon("2024-09-23"),
    page_count=1000,
)

# testdata pattern is ({id}, {has_results})
TEST_ID_DATA = [
    (200000001, True),
    (300000000, False),
]
# testdata pattern is ({sequence_num}, {schedule_num}, {has_results})
TEST_SEQUENCE_SCHEDULE_DATA = [
    (20, 30, True),
    (20, 40, False),
    (10, 30, False),
]


@pytest.mark.parametrize("box_id, has_results", TEST_ID_DATA)
def test_find_by_id(session, box_id, has_results):
    """Assert that find a scanning box by primary key contains all expected elements."""
    if not has_results:
        box: ScanningBox = ScanningBox.find_by_id(box_id)
        assert not box
    else:
        save_box: ScanningBox = ScanningBox.create_from_json(BOX)
        save_box.id = box_id
        save_box.save()
        box: ScanningBox = ScanningBox.find_by_id(box_id)
        assert box
        assert box.id == box_id
        assert box.box_number == save_box.box_number
        assert box.sequence_number == save_box.sequence_number
        assert box.page_count == save_box.page_count
        assert box.opened_date == save_box.opened_date
        assert box.closed_date == save_box.closed_date


@pytest.mark.parametrize("sequence_num, schedule_num, has_results", TEST_SEQUENCE_SCHEDULE_DATA)
def test_find_by_sequence_schedule(session, sequence_num, schedule_num, has_results):
    """Assert that find a scanning box by sequence and schedule numbers contains all expected elements."""
    save_box: ScanningBox = ScanningBox.create_from_json(BOX)
    save_box.id = 200000000
    save_box.save()
    boxes = ScanningBox.find_by_sequence_schedule(sequence_num, schedule_num)
    if has_results:
        assert boxes
        assert len(boxes) >= 1
        for box in boxes:
            assert box.sequence_number == sequence_num
            assert box.schedule_number == schedule_num
    else:
        assert not boxes


def test_find_all(session):
    """Assert that find all boxes contains the expected elements."""
    save_box: ScanningBox = ScanningBox.create_from_json(BOX)
    save_box.id = 200000001
    save_box.save()
    boxes = ScanningBox.find_all()
    assert boxes
    for box in boxes:
        assert box.id
        assert box.box_number
        assert box.sequence_number
        assert box.schedule_number


def test_box_json(session):
    """Assert that the scanning box model renders to a json format correctly."""
    box: ScanningBox = TEST_BOX
    box_json = box.json
    test_json = copy.deepcopy(BOX)
    box_json["openedDate"] = str(box_json["openedDate"])[0:10]
    box_json["closedDate"] = str(box_json["closedDate"])[0:10]
    assert box_json == test_json


def test_create_from_json(session):
    """Assert that the new scanning box record is created from a new request json data correctly."""
    json_data = copy.deepcopy(BOX)
    box: ScanningBox = ScanningBox.create_from_json(json_data)
    assert box
    assert not box.id
    assert box.box_number == json_data.get("boxNumber")
    assert box.sequence_number == json_data.get("sequenceNumber")
    assert box.schedule_number == json_data.get("scheduleNumber")
    assert box.opened_date
    assert box.closed_date
    assert box.page_count == json_data.get("pageCount")


def test_update(session):
    """Assert that updating a scanning box object works as expected."""
    box: ScanningBox = ScanningBox.create_from_json(BOX)
    json_data = copy.deepcopy(UPDATE_BOX)
    box.update(json_data)
    assert box.opened_date == model_utils.ts_from_iso_date_noon(json_data.get("openedDate"))
    assert box.closed_date == model_utils.ts_from_iso_date_noon(json_data.get("closedDate"))
    assert box.page_count == json_data.get("pageCount")