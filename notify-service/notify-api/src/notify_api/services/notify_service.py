# Copyright © 2022 Province of British Columbia
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
"""This provides the service for email notify calls."""

import uuid
import warnings
from datetime import UTC, datetime

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from flask import current_app
from simple_cloudevent import SimpleCloudEvent
from structured_logging import StructuredLogging

from notify_api.models import (
    Notification,
    NotificationRequest,
    SafeList,
)
from notify_api.services.gcp_queue import GcpQueue, queue

logger = StructuredLogging.get_logger()
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


class NotifyService:
    """Provides services to manages notification."""

    def __init__(self):
        """Return a Notification service instance."""

    @classmethod
    def get_provider(cls, request_by: str, content_body: str) -> str:
        """Get the notify service provider."""
        if request_by.upper() == "STRR":
            # Send email through GC Notify Housing service
            return Notification.NotificationProvider.HOUSING

        # Send email through GC Notify if email body is not html
        if not bool(BeautifulSoup(content_body, "html.parser").find()):
            return Notification.NotificationProvider.GC_NOTIFY

        return Notification.NotificationProvider.SMTP

    def queue_publish(self, notification_request: NotificationRequest) -> Notification:
        """Send the notification."""
        provider: str = self.get_provider(
            notification_request.request_by,
            notification_request.content.body,
        )

        # Email must be set in safe list of Dev and Test environment
        if current_app.config.get("DEVELOPMENT"):
            recipients = [
                r.strip()
                for r in notification_request.recipients.split(",")
                if SafeList.is_in_safe_list(r.lower().strip())
            ]
            unsafe_recipients = [r for r in notification_request.recipients.split(",") if r.strip() not in recipients]
            if unsafe_recipients:
                logger.info(f"{unsafe_recipients} are not in the safe list")

            notification_request.recipients = ",".join(recipients) if recipients else None

        if not notification_request.recipients:
            return Notification(
                recipients=None,
                status_code=Notification.NotificationStatus.FAILURE,
            )

        notification_data = {
            "notificationId": None,
            "notificationProvider": provider,
            "notificationRequest": notification_request.model_dump_json(),
        }

        delivery_topic = current_app.config.get("DELIVERY_GCNOTIFY_TOPIC")

        if notification.provider_code == Notification.NotificationProvider.SMTP:
            delivery_topic = current_app.config.get("DELIVERY_SMTP_TOPIC")
        elif notification.provider_code == Notification.NotificationProvider.HOUSING:
            delivery_topic = current_app.config.get("DELIVERY_GCNOTIFY_HOUSING_TOPIC")

        for recipient in notification_request.recipients.split(","):
            try:
                notification: Notification = Notification.create_notification(notification_request, recipient.strip())
                notification_data["notificationId"] = notification.id

                cloud_event = SimpleCloudEvent(
                    id=str(uuid.uuid4()),
                    source="notify-api",
                    subject=None,
                    time=datetime.now(tz=UTC).isoformat(),
                    type=f"bc.registry.notify.{provider}",
                    data=notification_data,
                )

                publish_future = queue.publish(delivery_topic, GcpQueue.to_queue_message(cloud_event))
                logger.info(f"Queued {recipient} {notification_request.content.subject} {publish_future}")

                notification.status_code = Notification.NotificationStatus.QUEUED
                notification.provider_code = provider
                notification.sent_date = datetime.now(UTC)
                notification.update_notification()

            except Exception as err:  # pylint: disable=broad-except
                logger.error(f"Error processing notification for {recipient}: {err}")
                notification.status_code = Notification.NotificationStatus.FAILURE
                notification.provider_code = provider
                notification.sent_date = datetime.now(UTC)
                notification.update_notification()
                return Notification(
                    recipients=recipient,
                    status_code=Notification.NotificationStatus.FAILURE,
                )

        return Notification(
            recipients=notification_request.recipients,
            status_code=Notification.NotificationStatus.QUEUED,
        )

    def queue_republish(self):
        """Republish notifications to queue."""
        notifications = Notification.find_resend_notifications()

        for notification in notifications:
            delivery_topic = current_app.config.get("DELIVERY_GCNOTIFY_TOPIC")

            if notification.provider_code == Notification.NotificationProvider.SMTP:
                delivery_topic = current_app.config.get("DELIVERY_SMTP_TOPIC")
            elif notification.provider_code == Notification.NotificationProvider.HOUSING:
                delivery_topic = current_app.config.get("DELIVERY_GCNOTIFY_HOUSING_TOPIC")

            data = {
                "notificationId": notification.id,
            }

            cloud_event = SimpleCloudEvent(
                id=str(uuid.uuid4()),
                source="notify-api",
                subject=None,
                time=datetime.now(tz=UTC).isoformat(),
                type=f"bc.registry.notify.{notification.provider_code}",
                data=data,
            )

            publish_future = queue.publish(delivery_topic, GcpQueue.to_queue_message(cloud_event))
            logger.info(f"resend {notification.recipients} {publish_future}")

            notification.status_code = Notification.NotificationStatus.QUEUED
            notification.update_notification()
