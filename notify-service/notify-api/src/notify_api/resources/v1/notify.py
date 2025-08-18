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
"""API endpoints for managing a notify resource."""

from http import HTTPStatus

from flask import Blueprint, jsonify
from flask_pydantic import validate

from notify_api.models import Notification, NotificationRequest
from notify_api.services import notify
from notify_api.utils.auth import jwt
from notify_api.utils.enums import Role

bp = Blueprint("Notify", __name__, url_prefix="/notify")


@bp.route("", methods=["POST"])
@jwt.requires_auth
@jwt.has_one_of_roles([Role.SYSTEM.value, Role.PUBLIC_USER.value, Role.STAFF.value])
@validate()
def send_notification(body: NotificationRequest):
    """Create and send EMAIL notification endpoint."""
    body.notify_type = Notification.NotificationType.EMAIL
    notification = notify.queue_publish(body)

    return jsonify(notification.json), HTTPStatus.OK


@bp.route("/<string:notification_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
@jwt.has_one_of_roles([Role.SYSTEM.value, Role.JOB.value, Role.STAFF.value])
def find_notification(notification_id: str):
    """Get notification endpoint by id."""
    if not notification_id or not notification_id.isdigit():
        return {"error": "Requires a valid notification id."}, HTTPStatus.BAD_REQUEST

    notification = Notification.find_notification_by_id(notification_id)
    if notification is None:
        return {"error": "Notification not found."}, HTTPStatus.NOT_FOUND

    return jsonify(notification.json), HTTPStatus.OK


@bp.route("/status/<string:notification_status>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
@jwt.has_one_of_roles([Role.SYSTEM.value, Role.JOB.value])
def find_notifications(notification_status: str):
    """Get pending or failure notifications."""
    if notification_status.upper() not in {
        Notification.NotificationStatus.PENDING.name,
        Notification.NotificationStatus.FAILURE.name,
    }:
        return {"error": "Requires a valid notification status (PENDING, FAILURE)."}, HTTPStatus.BAD_REQUEST

    notifications = Notification.find_notifications_by_status(notification_status.upper())

    response_list = [notification.json for notification in notifications]
    return jsonify(notifications=response_list), HTTPStatus.OK
