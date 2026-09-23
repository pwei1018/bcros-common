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
"""Notification data model."""

from datetime import UTC, datetime, timedelta
from enum import auto

from email_validator import EmailNotValidError, validate_email
from flask import current_app
import phonenumbers
from pydantic import BaseModel, ConfigDict, Field, field_validator

from notify_api.utils.base import BaseEnum
from notify_api.utils.util import to_camel

from .content import Content, ContentRequest
from .db import db


class NotificationRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Notification model for resquest."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    recipients: str = Field(alias="recipients")
    request_by: str | None = Field(default="", alias="requestBy")
    notify_type: str | None = Field(default=None, alias="notifyType")
    content: ContentRequest | None = None

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v_field):
        """Validate recipients."""
        if not v_field:
            raise ValueError("The recipients must not empty")

        for recipient in v_field.split(","):
            try:
                parsed_phone = phonenumbers.parse(recipient)
                if not phonenumbers.is_valid_number(parsed_phone):
                    raise ValueError(f"Invalid recipient: {recipient}.")
            except phonenumbers.NumberParseException:
                try:
                    validate_email(recipient.strip())
                except EmailNotValidError as error_msg:
                    raise ValueError(f"Invalid recipient: {recipient}.") from error_msg

        return v_field


class NotificationSendResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Model for GC notify send response."""

    response_id: str | None = None
    recipient: str | None = None


class NotificationSendResponses(BaseModel):  # pylint: disable=too-few-public-methods
    """Notification model for resquest."""

    recipients: list[NotificationSendResponse] = []


class Notification(db.Model):
    """Immutable Notification record. Represents Notification."""

    class NotificationType(BaseEnum):
        """Enum for the Notification Type."""

        EMAIL = auto()
        TEXT = auto()

    class NotificationStatus(BaseEnum):
        """Enum for the Notification Status."""

        PENDING = auto()
        QUEUED = auto()
        SENT = auto()
        DELIVERED = auto()
        FAILURE = auto()
        FORWARDED = auto()
        EXPIRED = auto()

    class NotificationProvider(BaseEnum):
        """Enum for the Notification Provider."""

        SMTP = auto()
        GC_NOTIFY = auto()
        HOUSING = auto()

    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    recipients = db.Column(db.String(2000), nullable=False)
    request_date = db.Column(db.DateTime(timezone=True), default=datetime.now, nullable=True)
    request_by = db.Column(db.String(100), nullable=True)
    sent_date = db.Column(db.DateTime(timezone=True), default=datetime.now, nullable=True)
    type_code = db.Column(db.Enum(NotificationType), default=NotificationType.EMAIL)
    status_code = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.PENDING)
    provider_code = db.Column(db.Enum(NotificationProvider), nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False, server_default="0")

    # relationships
    content = db.relationship("Content")

    @property
    def json(self) -> dict:
        """Return a dict of this object, with keys in JSON format."""
        notification_json = {
            "id": self.id,
            "recipients": self.recipients,
            "requestDate": getattr(self.request_date, "isoformat", lambda: None)(),
            "requestBy": self.request_by,
            "sentDate": getattr(self.sent_date, "isoformat", lambda: None)(),
            "notifyType": getattr(self.type_code, "name", None),
            "notifyStatus": getattr(self.status_code, "name", None),
            "notifyProvider": getattr(self.provider_code, "name", None),
        }

        if len(self.content) > 0:
            notification_json["content"] = self.content[0].json

        return notification_json

    @classmethod
    def find_notification_by_id(cls, identifier: str | None = None):
        """Return a Notification by the id."""
        notification = None
        if identifier:
            notification = db.session.get(cls, identifier)

        return notification

    @classmethod
    def find_notifications_by_status(cls, status: str | None = None):
        """Return all Notifications by the status."""
        notifications = None
        if status:
            notifications = cls.query.filter_by(status_code=status).all()
        return notifications

    # Notifications older than this are considered stale/time-sensitive-expired
    # and must not be auto-resent (e.g. annual report reminders, renewal notices).
    RESEND_MAX_AGE_HOURS = 48

    # Notifications younger than this may still be in-flight (queued but not
    # yet processed by the delivery worker) - skip them to avoid duplicate sends.
    RESEND_MIN_AGE_MINUTES = 10

    # Stop retrying a notification after this many resend attempts.
    RESEND_MAX_RETRY_COUNT = 5

    # Notifications stuck in a non-terminal state for longer than this are
    # considered unrecoverable and get archived (moved to history, deleted here).
    ARCHIVE_AFTER_DAYS = 30

    @classmethod
    def _config_int(cls, key: str, default: int) -> int:
        """Read an int override from the current app config, falling back to a default.

        Reading via ``current_app`` must happen lazily (inside a method call, within an
        active application context) rather than at class-body evaluation time, since the
        latter runs at module import and has no Flask app context available yet.
        """
        return current_app.config.get(key, default)

    @classmethod
    def find_resend_notifications(cls):
        """Return Notifications that need to resend.

        Excludes notifications that are:
          - too young (may still be in-flight, not yet processed)
          - too old (time-sensitive content has expired; resending is stale/wrong)
          - already exhausted their retry budget
        """
        resend_statuses = (
            Notification.NotificationStatus.QUEUED.value,
            Notification.NotificationStatus.PENDING.value,
            Notification.NotificationStatus.FAILURE.value,
        )

        max_age_hours = cls._config_int("RESEND_MAX_AGE_HOURS", cls.RESEND_MAX_AGE_HOURS)
        min_age_minutes = cls._config_int("RESEND_MIN_AGE_MINUTES", cls.RESEND_MIN_AGE_MINUTES)
        max_retry_count = cls._config_int("RESEND_MAX_RETRY_COUNT", cls.RESEND_MAX_RETRY_COUNT)

        now = datetime.now(UTC)
        oldest_allowed = now - timedelta(hours=max_age_hours)
        newest_allowed = now - timedelta(minutes=min_age_minutes)

        return cls.query.filter(
            Notification.status_code.in_(resend_statuses),
            Notification.request_date >= oldest_allowed,
            Notification.request_date <= newest_allowed,
            Notification.retry_count < max_retry_count,
        ).all()

    @classmethod
    def find_archivable_notifications(cls):
        """Return Notifications that have been stuck too long and should be archived.

        This includes any status that never reached a clean terminal state
        (PENDING/QUEUED/FAILURE) as well as SENT rows that failed to be
        cleaned up after a successful delivery (see delete_notification).
        """
        archivable_statuses = (
            Notification.NotificationStatus.PENDING.value,
            Notification.NotificationStatus.QUEUED.value,
            Notification.NotificationStatus.FAILURE.value,
            Notification.NotificationStatus.SENT.value,
        )

        archive_after_days = cls._config_int("ARCHIVE_AFTER_DAYS", cls.ARCHIVE_AFTER_DAYS)
        cutoff = datetime.now(UTC) - timedelta(days=archive_after_days)

        return cls.query.filter(
            Notification.status_code.in_(archivable_statuses),
            Notification.request_date < cutoff,
        ).all()

    @classmethod
    def create_notification(cls, notification: NotificationRequest, recipient: str = "", provider: str = None):
        """Create notification."""
        db_notification = Notification(
            recipients=recipient or notification.recipients,
            request_date=datetime.now(UTC),
            request_by=notification.request_by,
            type_code=notification.notify_type or Notification.NotificationType.EMAIL,
            provider_code=provider,
        )
        db.session.add(db_notification)
        db.session.commit()
        db.session.refresh(db_notification)

        # save email content
        Content.create_content(content=notification.content, notification_id=db_notification.id)

        return db_notification

    def update_notification(self):
        """Update notification."""
        db.session.add(self)
        db.session.flush()
        db.session.commit()

        return self

    def delete_notification(self):
        """Delete notification content."""
        self.content[0].delete_content()
        db.session.delete(self)
        db.session.commit()
