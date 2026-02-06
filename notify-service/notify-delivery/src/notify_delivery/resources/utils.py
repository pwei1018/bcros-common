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
"""Utility functions for resource handlers."""

from flask import request
from notify_api.models import (
    Notification,
    NotificationHistory,
    NotificationSendResponses,
)
from notify_api.services.gcp_queue import queue
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()


def get_cloud_event():
    """Get the cloud event from the request."""
    if not request.data or request.data == b"":
        logger.info("No incoming raw message data")
        return None

    cloud_event = queue.get_simple_cloud_event(request, wrapped=True)
    if not cloud_event:
        logger.info("No incoming cloud event message")
        return None

    logger.info(f"Event Message Received: {cloud_event}")
    return cloud_event


def validate_event_type(cloud_event, expected_event_type: str):
    """Validate the cloud event type."""
    if cloud_event.type != expected_event_type:
        logger.error(f"Invalid queue message type: expected '{expected_event_type}', got '{cloud_event.type}'")
        return False
    return True


def process_notification(data: dict, provider_class):
    """Process a notification."""
    if not data:
        logger.error("No message content in queue data")
        raise ValueError("Invalid queue message data - empty data")

    notification_id = data.get("notificationId")
    if not notification_id:
        logger.error("Missing notificationId in queue data")
        raise ValueError("Invalid queue message data - missing notificationId")

    notification = fetch_notification(notification_id)
    validate_notification_content(notification)
    return send_notification(notification, provider_class)


def fetch_notification(notification_id: str) -> Notification:
    """Fetch a notification from the database."""
    try:
        notification = Notification.find_notification_by_id(notification_id)
    except Exception as error:
        logger.error(f"Database error while fetching notification {notification_id}: {error}")
        raise ValueError(f"Failed to fetch notification for notificationId {notification_id}") from error

    if notification is None:
        logger.error(f"Unknown notification for notificationId {notification_id}")
        raise ValueError(f"Unknown notification for notificationId {notification_id}")

    return notification


def validate_notification_content(notification: Notification):
    """Validate the notification content."""
    if not notification.content or len(notification.content) == 0:
        logger.error(f"No message content for notificationId {notification.id}")
        raise ValueError(f"No message content for notificationId {notification.id}")


def send_notification(notification: Notification, provider_class) -> NotificationHistory | Notification:
    """Send a notification using the specified provider."""
    try:
        provider = provider_class(notification)
        responses: NotificationSendResponses = provider.send()

        if responses and responses.recipients:
            notification.status_code = Notification.NotificationStatus.SENT
            notification.update_notification()

            history = None
            for response in responses.recipients:
                logger.info(f"Creating history for notification.id={notification.id}, recipient={response.recipient}")
                history = NotificationHistory.create_history(notification, response.recipient, response.response_id)

            notification.delete_notification()

            logger.info(f"Notification {notification.id} sent successfully to {len(responses.recipients)} recipients")
            return history
        else:
            notification.status_code = Notification.NotificationStatus.FAILURE
            notification.update_notification()

            logger.warning(f"Failed to send notification {notification.id} - no valid responses")
            return notification

    except Exception as error:
        logger.error(f"Error sending notification {notification.id}: {error}")
        notification.status_code = Notification.NotificationStatus.FAILURE
        notification.update_notification()
        raise ValueError(f"Failed to send notification {notification.id}") from error
