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

"""Tests to assure the scanning_schedule Model.

Test-Suite to ensure that the scanning_schedule Model is working as expected.
"""
import copy

import pytest

from doc_api.models import ScanningSchedule

SCHEDULE = {
    "scheduleNumber": 20,
    "sequenceNumber": 10,
}
TEST_SCHEDULE = ScanningSchedule(
    id=1,
    schedule_number=20,
    sequence_number=10,
)

# testdata pattern is ({id}, {has_results})
TEST_ID_DATA = [
    (200000001, True),
    (300000000, False),
]


@pytest.mark.parametrize("sched_id, has_results", TEST_ID_DATA)
def test_find_by_id(session, sched_id, has_results):
    """Assert that find a scanning schedule by primary key contains all expected elements."""
    if not has_results:
        schedule: ScanningSchedule = ScanningSchedule.find_by_id(sched_id)
        assert not schedule
    else:
        save_schedule: ScanningSchedule = ScanningSchedule.create_from_json(SCHEDULE)
        save_schedule.id = sched_id
        save_schedule.save()
        schedule: ScanningSchedule = ScanningSchedule.find_by_id(sched_id)
        assert schedule
        assert schedule.id == sched_id


def test_find_all(session):
    """Assert that find all schedules expected elements."""
    results = ScanningSchedule.find_all()
    if results:
        for schedule in results:
            assert schedule.id
            assert schedule.schedule_number
            assert schedule.sequence_number


def test_schedule_json(session):
    """Assert that the scanning schedule model renders to a json format correctly."""
    schedule: ScanningSchedule = TEST_SCHEDULE
    schedule_json = schedule.json
    test_json = copy.deepcopy(SCHEDULE)
    assert schedule_json == test_json


def test_create_from_json(session):
    """Assert that the new scanning schedule record is created from a new request json data correctly."""
    json_data = copy.deepcopy(SCHEDULE)
    schedule: ScanningSchedule = ScanningSchedule.create_from_json(json_data)
    assert schedule
    assert not schedule.id
    assert schedule.schedule_number == json_data.get("scheduleNumber")
    assert schedule.sequence_number == json_data.get("sequenceNumber")
