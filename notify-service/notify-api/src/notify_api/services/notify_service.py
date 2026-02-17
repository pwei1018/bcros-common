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

import base64
from datetime import UTC, datetime
import uuid
import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from flask import current_app
from simple_cloudevent import SimpleCloudEvent
from structured_logging import StructuredLogging

from notify_api.models import (
    Notification,
    NotificationRequest,
    SafeList,
)
from notify_api.models.db import db
from notify_api.services.gcp_queue import GcpQueue, queue

logger = StructuredLogging.get_logger()
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Constants
CLOUD_EVENT_SOURCE = "notify-api"
CLOUD_EVENT_TYPE_PREFIX = "bc.registry.notify"
STRR_REQUEST_IDENTIFIER = "STRR"


class NotifyService:
    """Provides services to manages notification."""

    def __init__(self):
        """Return a Notification service instance."""

    @classmethod
    def get_provider(cls, request_by: str, content_body: str, notification_request: NotificationRequest = None) -> str:
        """Get the notify service provider based on a set of rules.

        Args:
            request_by: The service requesting the notification.
            content_body: The email body content to analyze.
            notification_request: The full notification request to check for attachments.

        Returns:
            The appropriate notification provider.
        """
        if not isinstance(request_by, str):
            logger.warning(f"Invalid request_by parameter type: {type(request_by)}, defaulting to GC_NOTIFY")
            return Notification.NotificationProvider.GC_NOTIFY

        # Rule-based provider selection
        provider_rules = [
            (
                lambda: request_by.upper() == STRR_REQUEST_IDENTIFIER,
                Notification.NotificationProvider.HOUSING,
                "HOUSING provider for STRR request",
            ),
            (
                lambda: notification_request and cls._has_large_attachments(notification_request),
                Notification.NotificationProvider.SMTP,
                "SMTP provider for large attachments (>6MB)",
            ),
            (
                lambda: content_body and cls._contains_html(content_body),
                Notification.NotificationProvider.SMTP,
                "SMTP provider for HTML content",
            ),
        ]

        for condition, provider, reason in provider_rules:
            try:
                if condition():
                    logger.debug(f"Using {reason}")
                    return provider
            except Exception as e:
                logger.error(f"Error evaluating provider rule for {reason}, defaulting to SMTP: {e}")
                return Notification.NotificationProvider.SMTP

        logger.debug("Using GC_NOTIFY provider as default")
        return Notification.NotificationProvider.GC_NOTIFY

    @classmethod
    def _contains_html(cls, content: str) -> bool:
        """Check if content contains HTML tags.

        Args:
            content: The content to check

        Returns:
            True if HTML tags are found, False otherwise
        """
        try:
            return bool(BeautifulSoup(content, "html.parser").find())
        except Exception as err:
            logger.warning(f"Error parsing content for HTML: {err}")
            return False

    @classmethod
    def _has_large_attachments(cls, notification_request: NotificationRequest) -> bool:
        """Check if the total size of attachments exceeds 6MB.

        Args:
            notification_request: The notification request to check

        Returns:
            True if total attachment size > 6MB, False otherwise
        """
        if not notification_request.content or not notification_request.content.attachments:
            return False

        total_size = 0
        max_size = 6 * 1024 * 1024  # 6MB in bytes

        try:
            for attachment in notification_request.content.attachments:
                attachment_size = cls._calculate_attachment_size(attachment)
                total_size += attachment_size

                # Early exit if we exceed the limit
                if total_size > max_size:
                    logger.debug(f"Total attachment size ({total_size} bytes) exceeds 6MB limit")
                    return True

            logger.debug(f"Total attachment size: {total_size} bytes (within 6MB limit)")
            return False

        except Exception as err:
            logger.warning(f"Error calculating attachment sizes: {err}")
            # Default to SMTP if we can't calculate size (safer approach)
            return True

    @classmethod
    def _calculate_attachment_size(cls, attachment) -> int:
        """Calculate the size of a single attachment.

        Args:
            attachment: The attachment request object

        Returns:
            Size in bytes

        Raises:
            Exception: If attachment size cannot be determined
        """
        if attachment.file_bytes:
            # For base64 encoded content, decode and get length
            decoded_bytes = base64.b64decode(attachment.file_bytes)
            return len(decoded_bytes)
        if attachment.file_url:
            # For file URLs, we would need to download to get exact size
            # For now, we'll estimate based on typical file sizes or return 0
            # This could be enhanced to make a HEAD request to get Content-Length
            logger.debug(f"Cannot determine exact size for file URL: {attachment.file_url}")
            return 0
        return 0

    @staticmethod
    def _get_delivery_topic(provider: str) -> str | None:
        """Get the appropriate delivery topic for the given provider.

        Args:
            provider: The notification provider

        Returns:
            The delivery topic configuration key or None if not found
        """
        topic_mapping = {
            Notification.NotificationProvider.GC_NOTIFY: current_app.config.get("DELIVERY_GCNOTIFY_TOPIC"),
            Notification.NotificationProvider.SMTP: current_app.config.get("DELIVERY_SMTP_TOPIC"),
            Notification.NotificationProvider.HOUSING: current_app.config.get("DELIVERY_GCNOTIFY_HOUSING_TOPIC"),
        }

        topic = topic_mapping.get(provider)
        if not topic:
            logger.error(f"No delivery topic configured for provider: {provider}")

        return topic

    @staticmethod
    def _filter_safe_recipients(recipients: str) -> list[str]:
        """Filter recipients based on the safe list in the development environment.

        Args:
            recipients: A comma-separated string of recipient email addresses.

        Returns:
            A list of safe-listed recipients.
        """
        recipient_list = [r.strip() for r in recipients.split(",")]

        if not current_app.config.get("DEVELOPMENT"):
            return recipient_list

        safe_list_emails = {safe.email.lower() for safe in SafeList.find_all()}

        safe_recipients = [r for r in recipient_list if r.lower() in safe_list_emails]

        unsafe_recipients = [r for r in recipient_list if r.lower() not in safe_list_emails]

        if unsafe_recipients:
            logger.info(f"Recipients not in safe list and were filtered out: {unsafe_recipients}")

        return safe_recipients

    @staticmethod
    def _create_cloud_event(provider: str, notification_data: dict) -> SimpleCloudEvent:
        """Create a cloud event for the notification.

        Args:
            provider: The notification provider
            notification_data: The notification data

        Returns:
            A configured SimpleCloudEvent
        """
        return SimpleCloudEvent(
            id=str(uuid.uuid4()),
            source=CLOUD_EVENT_SOURCE,
            subject=None,
            time=datetime.now(tz=UTC).isoformat(),
            type=f"{CLOUD_EVENT_TYPE_PREFIX}.{provider}",
            data=notification_data,
        )

    @staticmethod
    def _update_notification_status(notification: Notification, provider: str, status: str) -> None:
        """Update notification status and metadata.

        Args:
            notification: The notification to update
            provider: The provider code
            status: The status to set
        """
        notification.status_code = status
        if provider:
            notification.provider_code = provider
        notification.sent_date = datetime.now(UTC)
        notification.update_notification()

    def queue_publish(self, notification_request: NotificationRequest) -> Notification:
        """Send the notification to the appropriate queue.

        Args:
            notification_request: The notification request to process

        Returns:
            A Notification object with the processing result
        """
        try:
            provider = self.get_provider(
                notification_request.request_by,
                notification_request.content.body,
                notification_request,
            )

            # Filter recipients based on safe list in development
            safe_recipients = NotifyService._filter_safe_recipients(notification_request.recipients)

            if not safe_recipients:
                logger.warning("No valid recipients after safe list filtering")
                notification = Notification()
                notification.recipients = None
                notification.status_code = Notification.NotificationStatus.FAILURE
                return notification

            # Get delivery topic for the provider
            delivery_topic = NotifyService._get_delivery_topic(provider)
            if not delivery_topic:
                logger.error(f"No delivery topic configured for provider: {provider}")
                notification = Notification()
                notification.recipients = notification_request.recipients
                notification.status_code = Notification.NotificationStatus.FAILURE
                return notification

            # Prepare notification data template
            notification_data = {
                "notificationId": None,
                "notificationProvider": provider,
                "notificationRequest": notification_request.model_dump_json(),
            }

            successful_notifications = []

            # Process each recipient
            for recipient in safe_recipients:
                clean_recipient = recipient.strip()
                if not clean_recipient:
                    continue

                notification = NotifyService._process_single_recipient(
                    clean_recipient, notification_request, provider, delivery_topic, notification_data
                )
                if notification:
                    successful_notifications.append(notification)
                else:
                    logger.error(f"Failed to process notification for recipient: {clean_recipient}")
                    notification = Notification()
                    notification.recipients = clean_recipient
                    notification.status_code = Notification.NotificationStatus.FAILURE
                    return notification

            logger.info(f"Successfully queued notifications for {len(successful_notifications)} recipients")

            # Return the first notification to match expected response format
            # If multiple recipients were handled, they are all queued, but API returns one object structure
            if successful_notifications:
                return successful_notifications[0]

            notification = Notification()
            notification.recipients = ",".join(safe_recipients)
            notification.status_code = Notification.NotificationStatus.QUEUED
            return notification

        except Exception as err:
            logger.error(f"Unexpected error in queue_publish: {err}")
            notification = Notification()
            notification.recipients = notification_request.recipients
            notification.status_code = Notification.NotificationStatus.FAILURE
            return notification

    @staticmethod
    def _process_single_recipient(
        recipient: str,
        notification_request: NotificationRequest,
        provider: str,
        delivery_topic: str,
        notification_data: dict,
    ) -> Notification | None:
        """Process notification for a single recipient.

        Args:
            recipient: The recipient email address
            notification_request: The notification request
            provider: The notification provider
            delivery_topic: The delivery topic
            notification_data: The notification data template

        Returns:
            The created Notification object if successful, None otherwise
        """
        try:
            # Create notification record
            notification = Notification.create_notification(notification_request, recipient, provider)
            notification_data["notificationId"] = notification.id

            # Create and publish cloud event
            cloud_event = NotifyService._create_cloud_event(provider, notification_data)
            publish_future = queue.publish(delivery_topic, GcpQueue.to_queue_message(cloud_event))

            logger.info(
                f"Queued notification for {recipient} - Subject: {notification_request.content.subject} - "
                f"Future: {publish_future}"
            )

            # Update notification status
            NotifyService._update_notification_status(notification, provider, Notification.NotificationStatus.QUEUED)

            # Expunge from session so accessing attributes later won't trigger
            # a lazy-load SELECT (which would fail if the delivery service
            # already processed and deleted the row).
            db.session.expunge(notification)

            return notification

        except Exception as err:
            logger.error(f"Error processing notification for {recipient}: {err}")

            # Try to update notification status to failure if notification was created
            try:
                if "notification" in locals():
                    NotifyService._update_notification_status(
                        notification, provider, Notification.NotificationStatus.FAILURE
                    )
            except Exception as update_err:
                logger.error(f"Failed to update notification status for {recipient}: {update_err}")

            return None

    @staticmethod
    def queue_republish() -> None:
        """Republish notifications to queue.

        This method finds notifications that need to be resent and republishes
        them to the appropriate queue based on their provider.
        """
        try:
            notifications = Notification.find_resend_notifications()

            if not notifications:
                logger.info("No notifications found for republishing")
                return

            logger.info(f"Found {len(notifications)} notifications to republish")

            successful_count = 0
            failed_count = 0

            for notification in notifications:
                if NotifyService._republish_single_notification(notification):
                    successful_count += 1
                else:
                    failed_count += 1

            logger.info(f"Republish completed - Success: {successful_count}, Failed: {failed_count}")

        except Exception as err:
            logger.error(f"Error in queue_republish: {err}")

    @staticmethod
    def _republish_single_notification(notification: Notification) -> bool:
        """Republish a single notification.

        Args:
            notification: The notification to republish

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get delivery topic for the provider
            delivery_topic = NotifyService._get_delivery_topic(notification.provider_code)
            if not delivery_topic:
                logger.error(
                    f"No delivery topic for provider {notification.provider_code}, notification ID: {notification.id}"
                )
                return False

            # Prepare republish data
            republish_data = {
                "notificationId": notification.id,
            }

            # Create and publish cloud event
            cloud_event = NotifyService._create_cloud_event(notification.provider_code, republish_data)
            publish_future = queue.publish(delivery_topic, GcpQueue.to_queue_message(cloud_event))

            logger.info(
                f"Republished notification ID {notification.id} for {notification.recipients} - "
                f"Future: {publish_future}"
            )

            # Update notification status
            NotifyService._update_notification_status(
                notification, notification.provider_code, Notification.NotificationStatus.QUEUED
            )

            return True

        except Exception as err:
            logger.error(f"Error republishing notification ID {notification.id}: {err}")
            return False
