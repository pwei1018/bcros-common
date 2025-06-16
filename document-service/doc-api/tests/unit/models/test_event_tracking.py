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

"""Tests to assure the EventTracking Model.

Test-Suite to ensure that the EventTracking Model is working as expected.
"""
from http import HTTPStatus

import pytest

from doc_api.models import EventTracking, utils as model_utils
from doc_api.models.type_tables import EventTrackingTypes


# testdata pattern is ({description}, {exists}, {search_value})
TEST_DATA_ID = [
    ('Exists', True, 200000000),
    ('Does not exist', False, 300000000)
]
# testdata pattern is ({description}, {exists}, {search_value})
TEST_DATA_KEY_ID = [
    ('Exists', True, 200000008),
    ('Does not exist', False, 300000000)
]
# testdata pattern is ({description}, {results_size}, {key_id}, {type})
TEST_DATA_KEY_ID_TYPE = [
    ('No results', 0, 200000000, EventTrackingTypes.DOC_PAYMENT.value),
    ('1 result convert', 1, 200000009, EventTrackingTypes.PDF_CONVERT.value),
    ('2 results clean', 2, 200000100, EventTrackingTypes.PDF_CLEAN.value),
] 
# testdata pattern is ({description}, {key_id}, {type}, {status}, {message})
TEST_DATA_CREATE = [
    ('PDF Convert', 200000010, EventTrackingTypes.PDF_CONVERT, int(HTTPStatus.OK), 'message'),
    ('PDF Clean', 200000011, EventTrackingTypes.PDF_CLEAN, int(HTTPStatus.OK), 'message'),
    ('CC payment', 200000015, EventTrackingTypes.DOC_PAYMENT, int(HTTPStatus.OK), 'Payment pending initial state.')
]


@pytest.mark.parametrize('desc,exists,search_value', TEST_DATA_ID)
def test_find_by_id(session, desc, exists, search_value):
    """Assert that find event tracking by id contains all expected elements."""
    if exists:
        exists_event = create_event_tracking(search_value, search_value, int(HTTPStatus.OK), EventTrackingTypes.PDF_CONVERT)
        assert exists_event.id
    event_tracking = EventTracking.find_by_id(search_value)
    if exists:
        assert event_tracking
        assert event_tracking.id == search_value
        assert event_tracking.key_id
        assert event_tracking.event_ts
        assert event_tracking.event_tracking_type == EventTrackingTypes.PDF_CONVERT
    else:
        assert not event_tracking


@pytest.mark.parametrize('desc,exists,search_value', TEST_DATA_KEY_ID)
def test_find_by_key_id(session, desc, exists, search_value):
    """Assert that find event tracking by key id contains all expected elements."""
    if exists:
        exists_event = create_event_tracking(search_value, search_value, int(HTTPStatus.OK), EventTrackingTypes.PDF_CONVERT)
        assert exists_event.id
    events = EventTracking.find_by_key_id(search_value)
    if exists:
        assert events
        assert events[0].id > 0
        assert events[0].key_id == search_value
        assert events[0].event_ts
        assert events[0].event_tracking_type == EventTrackingTypes.PDF_CONVERT
    else:
        assert not events


@pytest.mark.parametrize('desc,results_size,key_id,event_type', TEST_DATA_KEY_ID_TYPE)
def test_find_by_id_type(session, desc, results_size, key_id, event_type):
    """Assert that find event tracking by key id and type contains all expected elements."""
    if results_size > 0:
        exists_event = create_event_tracking(key_id, key_id, int(HTTPStatus.OK), event_type)
        assert exists_event.id
    if results_size == 2:
        exists_event = create_event_tracking(key_id + 1, key_id, int(HTTPStatus.OK), event_type)
        assert exists_event.id
    events = EventTracking.find_by_key_id_type(key_id, event_type)
    if results_size > 0:
        assert events
        assert len(events) >= results_size
    else:
        assert not events


@pytest.mark.parametrize('desc,key_id,type,status,message', TEST_DATA_CREATE)
def test_create(session, desc, key_id, type, status, message):
    """Assert that create event tracking works as expected."""
    event_tracking = EventTracking.create(key_id, type, status, message)
    assert event_tracking
    assert event_tracking.id > 0
    assert event_tracking.event_ts
    assert event_tracking.event_tracking_type == type
    assert event_tracking.status == status
    assert event_tracking.message == message


def test_event_tracking_json(session):
    """Assert that the event tracking model renders to a json format correctly."""
    now_ts = model_utils.now_ts()
    tracking = EventTracking(
        id=1000,
        key_id=1000,
        event_ts=now_ts,
        event_tracking_type=EventTrackingTypes.PDF_CLEAN,
        status=200,
        message='message',
        email_id='test@gmail.com'
    )

    tracking_json = {
        'eventTrackingId': tracking.id,
        'keyId': tracking.key_id,
        'type': tracking.event_tracking_type,
        'createDateTime': model_utils.format_ts(tracking.event_ts),
        'status': tracking.status,
        'message': tracking.message,
        'emailAddress': tracking.email_id
    }
    assert tracking.json == tracking_json


def create_event_tracking(id: int, key_id: int, status: int, tracking_type: str) -> EventTracking:
    """Create a test event tracking record."""
    tracking: EventTracking = EventTracking(
        id=id,
        key_id=key_id,
        event_ts=model_utils.now_ts(),
        event_tracking_type=tracking_type,
        status=status,
        message='message',
        email_id='test@gmail.com'
    )
    tracking.save()
    return tracking
