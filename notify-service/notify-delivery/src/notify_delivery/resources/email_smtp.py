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

import sys
from datetime import UTC, datetime
from http import HTTPStatus

from flask import Blueprint, request
from notify_api.models import (
    Notification,
    NotificationHistory,
    NotificationRequest,
    NotificationSendResponses,
)
from notify_api.services.gcp_queue import queue
from structured_logging import StructuredLogging

from notify_delivery.services.gcp_queue.gcp_auth import ensure_authorized_queue_user
from notify_delivery.services.providers.email_smtp import EmailSMTP

bp = Blueprint("smtp", __name__)
logger = StructuredLogging.get_logger()


@bp.route("/", methods=("POST",))
@ensure_authorized_queue_user
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
        if ce.type == "bc.registry.notify.smtp":
            process_message(ce.data)
        else:
            logger.error("Invalid queue message type")
            return {}, HTTPStatus.BAD_REQUEST

        logger.info(f"Event Message Processed: {ce.id}")
        return {}, HTTPStatus.OK
    except Exception as e:
        logger.error(f"Failed to process queue message: {e}")
        return {}, HTTPStatus.INTERNAL_SERVER_ERROR


def check_required_keys(data: dict, keys: list):
    """Check for required keys in the data dictionary."""
    for key in keys:
        if key not in data or not data[key]:
            raise Exception(f"{key} not found in notification data.")


def process_message(data: dict) -> NotificationHistory | Notification:
    """Delivery message through GC Notify service."""
    check_required_keys(data, ["notificationRequest", "notificationProvider"])

    notification_data = data["notificationRequest"]
    notification_provider = data["notificationProvider"]

    if notification_provider != Notification.NotificationProvider.SMTP:
        raise Exception("Notification provider is incorrect.")

    # create notification record in OCP database
    notification_request = NotificationRequest.model_validate_json(notification_data)

    for recipient in notification_request.recipients.split(","):
        notification: Notification = Notification.create_notification(notification_request, recipient.strip())
        notification.status_code = Notification.NotificationStatus.SENT
        notification.provider_code = notification_provider
        notification.sent_date = datetime.now(UTC)
        notification.update_notification()

        smtp_provider = EmailSMTP(notification)
        responses: NotificationSendResponses = smtp_provider.send()

        if responses:
            for response in responses.recipients:
                # save to history as per recipient
                history = NotificationHistory.create_history(notification, response.recipient, response.response_id)

            # clean notification record
            notification.delete_notification()
        else:
            notification.status_code = Notification.NotificationStatus.FAILURE
            notification.update_notification()
            return notification

    return history
