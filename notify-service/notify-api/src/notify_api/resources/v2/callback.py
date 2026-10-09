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
"""API endpoint for receiving BC Notify callback events."""

from http import HTTPStatus
import sys

from flask import Blueprint
from flask_pydantic import validate
from structured_logging import StructuredLogging

from notify_api.models import BCNotifyCallback, BCNotifyCallbackRequest, Notification, NotificationHistory, db
from notify_api.utils.auth import jwt
from notify_api.utils.enums import Role

logger = StructuredLogging.get_logger()
bp = Blueprint("CALLBACK", __name__, url_prefix="/callback")


def process_bc_notify_callback(body: BCNotifyCallbackRequest) -> NotificationHistory | Notification | None:
    """Persist a callback and archive its notification only after successful completion."""
    BCNotifyCallback.save(body)
    response_id = body.data.notify_id
    notification = Notification.find_by_response_id(response_id)

    if notification:
        if body.data.status.lower() not in {"success", "completed"}:
            return notification

        try:
            notification.status_code = Notification.NotificationStatus.DELIVERED
            notification.update_notification(commit=False)
            history = NotificationHistory.create_history(notification, response_id=response_id, commit=False)
            history.notify_status = body.data.status
            notification.delete_notification(commit=False)
            db.session.commit()
            return history
        except Exception:
            db.session.rollback()
            raise

    history = NotificationHistory.find_by_response_id(response_id)
    if history:
        history.notify_status = body.data.status
        history.update()
    return history


@bp.route("/", methods=["POST", "OPTIONS"])
@jwt.requires_auth
@jwt.has_one_of_roles([Role.BC_NOTIFY_CALLBACK.value])
@validate()
def callback(body: BCNotifyCallbackRequest):  # pylint: disable=unused-argument
    """Persist a BC Notify status event and update its notification history."""
    try:
        process_bc_notify_callback(body)

    except Exception as err:  # pylint: disable=broad-except,unused-variable
        logger.error(f"Callback error: {err}, details: {sys.exc_info()}")
    return {}, HTTPStatus.OK
