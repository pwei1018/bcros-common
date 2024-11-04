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
from datetime import UTC, datetime, timezone

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from flask import current_app
from simple_cloudevent import SimpleCloudEvent
from structured_logging import StructuredLogging

from notify_api.models import Notification, NotificationHistory, NotificationRequest, SafeList
from notify_api.services.gcp_queue import GcpQueue, queue

logger = StructuredLogging.get_logger()
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


class NotifyService:
    """Provides services to manages notification."""

    def __init__(self):
        """Return a Notification service instance."""

    @classmethod
    def get_provider(cls, notify_type: str, content_body: str) -> str:
        """Get the notify service provider."""
        if notify_type == Notification.NotificationType.TEXT:
            # Send TEXT through GC Notify
            return Notification.NotificationProvider.GC_NOTIFY

        # Send email through GC Notify if email body is not html
        if not bool(BeautifulSoup(content_body, "html.parser").find()):
            return Notification.NotificationProvider.GC_NOTIFY

        return Notification.NotificationProvider.SMTP

    def queue_publish(self, notification_request: NotificationRequest) -> Notification:
        """Send the notification."""
        provider: str = self.get_provider(notification_request.notify_type, notification_request.content.body)

        # Email must set in safe list of Dev and Test environment
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

        notification_status: str = Notification.NotificationStatus.QUEUED

        if provider == Notification.NotificationProvider.SMTP:
            # SMTP service handle by OpenShift;
            try:
                notification: Notification = Notification.create_notification(notification_request)

                delivery_topic = current_app.config.get("NOTIFY_DELIVERY_SMTP_TOPIC")
                data = {
                    "notificationId": notification.id,
                    "notificationProvider": provider,
                    "notificationRequest": notification_request.model_dump_json(),
                }

                cloud_event = SimpleCloudEvent(
                    id=str(uuid.uuid4()),
                    source="notify-api",
                    subject=None,
                    time=datetime.now(tz=UTC).isoformat(),
                    type=f"bc.registry.notify.{provider}",
                    data=data,
                )

                publish_future = queue.publish(delivery_topic, GcpQueue.to_queue_message(cloud_event))
                logger.info(
                    f"Queued {notification_request.recipients} {notification_request.content.subject} {publish_future}"
                )

                notification_status = Notification.NotificationStatus.FORWARDED
                notification.status_code = notification_status
                notification.provider_code = provider
                notification.sent_date = datetime.now(UTC)
                logger.info(f"{notification.recipients}")
                NotificationHistory.create_history(notification)
                notification.delete_notification()
            except Exception as err:  # pylint: disable=broad-except
                logger.error(f"Error processing notification for {notification_request.recipients}: {err}")
                notification.status_code = Notification.NotificationStatus.FAILURE
                notification.provider_code = provider
                notification.sent_date = datetime.now(UTC)
                notification.update_notification()
                return Notification(
                    recipients=notification_request.recipients, status_code=Notification.NotificationStatus.FAILURE
                )
        else:
            for recipient in notification_request.recipients.split(","):
                try:
                    notification: Notification = Notification.create_notification(
                        notification_request, recipient.strip()
                    )

                    delivery_topic = current_app.config.get("NOTIFY_DELIVERY_GCNOTIFY_TOPIC")
                    data = {
                        "notificationId": notification.id,
                    }

                    cloud_event = SimpleCloudEvent(
                        id=str(uuid.uuid4()),
                        source="notify-api",
                        subject=None,
                        time=datetime.now(tz=UTC).isoformat(),
                        type=f"bc.registry.notify.{provider}",
                        data=data,
                    )

                    publish_future = queue.publish(delivery_topic, GcpQueue.to_queue_message(cloud_event))
                    logger.info(f"Queued {recipient} {notification_request.content.subject} {publish_future}")

                    notification.status_code = notification_status
                    notification.provider_code = provider
                    notification.sent_date = datetime.now(UTC)
                    notification.update_notification()

                except Exception as err:  # pylint: disable=broad-except
                    logger.error(f"Error processing notification for {recipient}: {err}")
                    notification.status_code = Notification.NotificationStatus.FAILURE
                    notification.provider_code = provider
                    notification.sent_date = datetime.now(UTC)
                    notification.update_notification()
                    return Notification(recipients=recipient, status_code=Notification.NotificationStatus.FAILURE)

        return Notification(recipients=notification_request.recipients, status_code=notification_status)

    def queue_republish(self):
        """Republish notifications to queue."""
        notifications = Notification.find_resend_notifications()

        for notification in notifications:
            deliery_topic = current_app.config.get("NOTIFY_DELIVERY_GCNOTIFY_TOPIC")
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

            publish_future = queue.publish(deliery_topic, GcpQueue.to_queue_message(cloud_event))
            logger.info(f"resend {notification.recipients} {publish_future}")

            notification.status_code = Notification.NotificationStatus.QUEUED
            notification.update_notification()
