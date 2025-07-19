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
# See the License for the specific language governing permissions andcurrent_app.
# limitations under the License.
"""Worker resource to handle incoming queue pushes from gcp."""

from http import HTTPStatus

from flask import Blueprint, request
from notify_api.models import Notification, NotificationHistory, NotificationSendResponses
from notify_api.services.gcp_queue import queue
from structured_logging import StructuredLogging

from notify_delivery.services.providers.gc_notify import GCNotify

bp = Blueprint("gcnotify", __name__)
logger = StructuredLogging.get_logger()


@bp.route("/", methods=("POST",))
def worker():
    """Worker to handle incoming queue pushes."""
    if not request.data:
        logger.info("No incoming raw msg.")
        return {}, HTTPStatus.OK

    if not (ce := queue.get_simple_cloud_event(request, wrapped=True)):
        logger.info("No incoming cloud event msg.")
        return {}, HTTPStatus.OK

    try:
        logger.info(f"Event Message Received: {ce}")

        # Validate event type
        expected_type = "bc.registry.notify.gc_notify"
        if ce.type == expected_type:
            process_message(ce.data)
        else:
            logger.error(f"Invalid queue message type: expected '{expected_type}', got '{ce.type}'")
            return {}, HTTPStatus.BAD_REQUEST

        logger.info(f"Event Message Processed: {ce.id}")
        return {}, HTTPStatus.OK
    except ValueError as ve:
        # Handle validation errors (missing content, unknown notifications, etc.)
        logger.error(f"Validation error processing queue message: {ve}")
        return {}, HTTPStatus.BAD_REQUEST
    except Exception as e:
        logger.error(f"Failed to process queue message: {e}")
        return {}, HTTPStatus.INTERNAL_SERVER_ERROR


def process_message(data: dict) -> NotificationHistory | Notification:
    """Delivery message through GC Notify service."""
    history: NotificationHistory = None

    # Validate input data
    if not data or "notificationId" not in data:
        logger.error("No message content or missing notificationId in queue data")
        raise ValueError("Invalid queue message data - missing notificationId")

    notification_id = data["notificationId"]

    try:
        notification: Notification = Notification.find_notification_by_id(notification_id)
    except Exception as e:
        logger.error(f"Database error while fetching notification {notification_id}: {e}")
        raise ValueError(f"Failed to fetch notification for notificationId {notification_id}") from e

    if notification is None:
        logger.error(f"Unknown notification for notificationId {notification_id}")
        raise ValueError(f"Unknown notification for notificationId {notification_id}")

    # Validate notification has content before processing
    if not notification.content or len(notification.content) == 0:
        logger.error(f"No message content for notificationId {notification_id}")
        raise ValueError(f"No message content for notificationId {notification_id}")

    gc_notify_provider = GCNotify(notification)

    responses: NotificationSendResponses = gc_notify_provider.send()

    if responses:
        notification.status_code = Notification.NotificationStatus.SENT
        notification.update_notification()

        for response in responses.recipients:
            history = NotificationHistory.create_history(notification, response.recipient, response.response_id)

        notification.delete_notification()
    else:
        notification.status_code = Notification.NotificationStatus.FAILURE
        notification.update_notification()
        return notification

    return history
