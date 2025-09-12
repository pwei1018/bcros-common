# Copyright © 2024 Province of British Columbia
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
"""Worker resource to handle incoming queue pushes from gcp."""

from http import HTTPStatus

from flask import Blueprint
from structured_logging import StructuredLogging

from notify_delivery.resources.utils import (
    get_cloud_event,
    process_notification,
    validate_event_type,
)
from notify_delivery.services.providers.gc_notify_housing import GCNotifyHousing

bp = Blueprint("gcnotify-housing", __name__)
logger = StructuredLogging.get_logger()

# Constants
EXPECTED_EVENT_TYPE = "bc.registry.notify.housing"


@bp.route("/", methods=("POST",))
def worker():
    """Worker to handle incoming queue pushes."""
    try:
        cloud_event = get_cloud_event()
        if not cloud_event:
            return {}, HTTPStatus.OK

        if not validate_event_type(cloud_event, EXPECTED_EVENT_TYPE):
            return {}, HTTPStatus.BAD_REQUEST

        process_notification(cloud_event.data, GCNotifyHousing)

        logger.info(f"Event Message Processed successfully: {cloud_event.id}")
        return {}, HTTPStatus.OK

    except ValueError as validation_error:
        logger.error(f"Validation error processing queue message: {validation_error}")
        return {}, HTTPStatus.BAD_REQUEST
    except Exception as error:
        logger.error(
            f"Unexpected error processing queue message: {error}", exc_info=True
        )
        return {}, HTTPStatus.INTERNAL_SERVER_ERROR
